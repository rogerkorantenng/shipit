"""Tasks API — CRUD, board view."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models import User, Task, Sprint
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services import activity_service, gamification_service

router = APIRouter()


# --- Schemas ---

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"
    priority: str = "medium"
    assignee_id: Optional[int] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    parent_task_id: Optional[int] = None
    ai_generated: bool = False
    sprint_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    sprint_id: Optional[int] = None


# --- Helpers ---

def _task_to_dict(task: Task, subtask_count: int = 0, subtasks_done: int = 0) -> dict:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "parent_task_id": task.parent_task_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "assignee_id": task.assignee_id,
        "assignee_name": task.assignee.name if task.assignee else None,
        "due_date": task.due_date,
        "estimated_hours": task.estimated_hours,
        "ai_generated": task.ai_generated,
        "jira_issue_key": task.jira_issue_key,
        "sprint_id": task.sprint_id,
        "position": task.position,
        "subtask_count": subtask_count,
        "subtasks_done": subtasks_done,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


# --- Endpoints ---

@router.get("/{project_id}/tasks")
async def get_board(
    project_id: int,
    sprint_id: Optional[int] = None,
    backlog: Optional[bool] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    # Build base query for top-level tasks
    stmt = (
        select(Task)
        .options(joinedload(Task.assignee))
        .where(Task.project_id == project_id, Task.parent_task_id.is_(None))
    )

    # Apply sprint filtering
    if sprint_id is not None:
        stmt = stmt.where(Task.sprint_id == sprint_id)
    elif backlog:
        stmt = stmt.where(Task.sprint_id.is_(None))
    else:
        # Default: try active sprint, else all tasks
        active_stmt = select(Sprint).where(
            Sprint.project_id == project_id,
            Sprint.status == "active",
        )
        active_result = await db.execute(active_stmt)
        active_sprint = active_result.scalar_one_or_none()
        if active_sprint:
            stmt = stmt.where(Task.sprint_id == active_sprint.id)

    stmt = stmt.order_by(Task.position, Task.created_at)
    result = await db.execute(stmt)
    tasks = result.scalars().unique().all()

    board = {"todo": [], "in_progress": [], "done": [], "blocked": []}
    for task in tasks:
        # Count subtasks
        sub_total = (await db.execute(
            select(func.count()).where(Task.parent_task_id == task.id)
        )).scalar() or 0
        sub_done = (await db.execute(
            select(func.count()).where(Task.parent_task_id == task.id, Task.status == "done")
        )).scalar() or 0

        task_dict = _task_to_dict(task, sub_total, sub_done)
        if task.status in board:
            board[task.status].append(task_dict)

    return board


@router.post("/{project_id}/tasks")
async def create_task(
    project_id: int,
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    task = Task(
        project_id=project_id,
        parent_task_id=data.parent_task_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        assignee_id=data.assignee_id,
        due_date=data.due_date,
        estimated_hours=data.estimated_hours,
        ai_generated=data.ai_generated,
        sprint_id=data.sprint_id,
    )
    db.add(task)
    await db.flush()

    await activity_service.log(
        db, project_id, user.id, "created", task_id=task.id,
        details={"title": task.title},
    )
    await db.commit()
    await db.refresh(task, ["assignee"])

    return _task_to_dict(task)


@router.get("/{project_id}/tasks/{task_id}")
async def get_task(
    project_id: int,
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    stmt = (
        select(Task)
        .options(joinedload(Task.assignee), joinedload(Task.subtasks).joinedload(Task.assignee))
        .where(Task.id == task_id, Task.project_id == project_id)
    )
    result = await db.execute(stmt)
    task = result.scalars().unique().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_dict = _task_to_dict(task, len(task.subtasks), sum(1 for s in task.subtasks if s.status == "done"))
    task_dict["subtasks"] = [
        _task_to_dict(s) for s in sorted(task.subtasks, key=lambda x: x.position)
    ]
    return task_dict


@router.put("/{project_id}/tasks/{task_id}")
async def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    task = await db.get(Task, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()

    # Log status change + gamification
    gamification_result = None
    if "status" in updates and updates["status"] != old_status:
        await activity_service.log(
            db, project_id, user.id, "status_changed", task_id=task.id,
            details={"from": old_status, "to": updates["status"], "title": task.title},
        )
        # Award XP when task moves to done
        if updates["status"] == "done":
            gamification_result = await gamification_service.award_task_completion(
                db, user.id, project_id, task.priority
            )

    # Log assignment
    if "assignee_id" in updates:
        await activity_service.log(
            db, project_id, user.id, "assigned", task_id=task.id,
            details={"assignee_id": updates["assignee_id"], "title": task.title},
        )

    await db.commit()
    await db.refresh(task, ["assignee"])

    result = _task_to_dict(task)
    if gamification_result:
        result["gamification"] = gamification_result
    return result


@router.delete("/{project_id}/tasks/{task_id}")
async def delete_task(
    project_id: int,
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    stmt = (
        select(Task)
        .options(joinedload(Task.subtasks))
        .where(Task.id == task_id, Task.project_id == project_id)
    )
    result = await db.execute(stmt)
    task = result.scalars().unique().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"ok": True}
