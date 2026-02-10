"""Sprints API — CRUD, lifecycle, task management."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models import User, Task, Sprint
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services import activity_service

router = APIRouter()


# --- Schemas ---

class SprintCreate(BaseModel):
    name: str
    goal: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    capacity_hours: Optional[float] = None

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    capacity_hours: Optional[float] = None

class SprintMoveTasks(BaseModel):
    task_ids: list[int]
    action: str = "add"  # "add" or "remove"


# --- Helpers ---

def _sprint_to_dict(sprint: Sprint, task_counts: dict | None = None) -> dict:
    return {
        "id": sprint.id,
        "project_id": sprint.project_id,
        "name": sprint.name,
        "goal": sprint.goal,
        "status": sprint.status,
        "start_date": sprint.start_date,
        "end_date": sprint.end_date,
        "capacity_hours": sprint.capacity_hours,
        "jira_sprint_id": sprint.jira_sprint_id,
        "task_counts": task_counts or {},
        "created_at": sprint.created_at.isoformat(),
        "updated_at": sprint.updated_at.isoformat(),
    }


async def _get_task_counts(db: AsyncSession, sprint_id: int) -> dict:
    counts = {}
    for status in ("todo", "in_progress", "done", "blocked"):
        count = (await db.execute(
            select(func.count()).where(
                Task.sprint_id == sprint_id,
                Task.status == status,
                Task.parent_task_id.is_(None),
            )
        )).scalar() or 0
        counts[status] = count
    return counts


# --- Endpoints ---

@router.get("/{project_id}/sprints")
async def list_sprints(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    stmt = (
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .order_by(Sprint.created_at.desc())
    )
    result = await db.execute(stmt)
    sprints = result.scalars().all()

    out = []
    for s in sprints:
        counts = await _get_task_counts(db, s.id)
        out.append(_sprint_to_dict(s, counts))
    return out


@router.get("/{project_id}/sprints/active")
async def get_active_sprint(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    stmt = select(Sprint).where(
        Sprint.project_id == project_id,
        Sprint.status == "active",
    )
    result = await db.execute(stmt)
    sprint = result.scalar_one_or_none()
    if not sprint:
        return None

    counts = await _get_task_counts(db, sprint.id)
    return _sprint_to_dict(sprint, counts)


@router.post("/{project_id}/sprints")
async def create_sprint(
    project_id: int,
    data: SprintCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    sprint = Sprint(
        project_id=project_id,
        name=data.name,
        goal=data.goal,
        start_date=data.start_date,
        end_date=data.end_date,
        capacity_hours=data.capacity_hours,
    )
    db.add(sprint)
    await db.flush()

    await activity_service.log(
        db, project_id, user.id, "sprint_created",
        details={"sprint_name": sprint.name},
    )
    await db.commit()
    await db.refresh(sprint)

    return _sprint_to_dict(sprint, {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0})


@router.put("/{project_id}/sprints/{sprint_id}")
async def update_sprint(
    project_id: int,
    sprint_id: int,
    data: SprintUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(sprint, field, value)
    sprint.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(sprint)

    counts = await _get_task_counts(db, sprint.id)
    return _sprint_to_dict(sprint, counts)


@router.delete("/{project_id}/sprints/{sprint_id}")
async def delete_sprint(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Move tasks back to backlog
    stmt = select(Task).where(Task.sprint_id == sprint_id)
    result = await db.execute(stmt)
    for task in result.scalars().all():
        task.sprint_id = None

    await db.delete(sprint)
    await db.commit()
    return {"ok": True}


@router.post("/{project_id}/sprints/{sprint_id}/start")
async def start_sprint(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Auto-complete any currently active sprint
    stmt = select(Sprint).where(
        Sprint.project_id == project_id,
        Sprint.status == "active",
    )
    result = await db.execute(stmt)
    for active in result.scalars().all():
        active.status = "completed"
        active.updated_at = datetime.utcnow()

    sprint.status = "active"
    if not sprint.start_date:
        sprint.start_date = datetime.utcnow().strftime("%Y-%m-%d")
    sprint.updated_at = datetime.utcnow()

    await activity_service.log(
        db, project_id, user.id, "sprint_started",
        details={"sprint_name": sprint.name},
    )
    await db.commit()
    await db.refresh(sprint)

    counts = await _get_task_counts(db, sprint.id)
    return _sprint_to_dict(sprint, counts)


@router.post("/{project_id}/sprints/{sprint_id}/complete")
async def complete_sprint(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    sprint.status = "completed"
    sprint.updated_at = datetime.utcnow()

    # Move incomplete tasks to backlog (sprint_id=None)
    stmt = select(Task).where(
        Task.sprint_id == sprint_id,
        Task.status != "done",
    )
    result = await db.execute(stmt)
    moved = 0
    for task in result.scalars().all():
        task.sprint_id = None
        moved += 1

    await activity_service.log(
        db, project_id, user.id, "sprint_completed",
        details={"sprint_name": sprint.name, "tasks_moved_to_backlog": moved},
    )
    await db.commit()
    await db.refresh(sprint)

    counts = await _get_task_counts(db, sprint.id)
    return _sprint_to_dict(sprint, counts)


@router.post("/{project_id}/sprints/{sprint_id}/tasks")
async def move_tasks(
    project_id: int,
    sprint_id: int,
    data: SprintMoveTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    moved = 0
    for task_id in data.task_ids:
        task = await db.get(Task, task_id)
        if not task or task.project_id != project_id:
            continue
        if data.action == "add":
            task.sprint_id = sprint_id
        else:
            task.sprint_id = None
        moved += 1

    await db.commit()
    return {"ok": True, "moved": moved}


@router.get("/{project_id}/backlog")
async def get_backlog(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    stmt = (
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.parent_task_id.is_(None),
            Task.sprint_id.is_(None),
        )
        .order_by(Task.position, Task.created_at)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "assignee_id": t.assignee_id,
            "estimated_hours": t.estimated_hours,
        }
        for t in tasks
    ]
