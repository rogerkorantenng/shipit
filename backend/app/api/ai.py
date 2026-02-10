"""AI endpoints — breakdown, meeting notes, blockers, digest."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models import User, Task, ProjectMember, Sprint
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services import ai_service, activity_service

router = APIRouter()


# --- Schemas ---

class BreakdownRequest(BaseModel):
    description: str

class BreakdownApply(BaseModel):
    title: str
    priority: str = "medium"
    subtasks: list[dict]

class ExtractTasksRequest(BaseModel):
    text: str

class SprintPlanRequest(BaseModel):
    capacity_hours: float = 40.0

class SprintPlanApply(BaseModel):
    sprint_name: str = "Sprint"
    goal: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    capacity_hours: Optional[float] = None
    assignments: list[dict]  # [{task_id, assignee}]

class PriorityApply(BaseModel):
    updates: list[dict]  # [{task_id, priority}]

class MeetingNotesRequest(BaseModel):
    notes: str

class MeetingNotesApply(BaseModel):
    tasks: list[dict]
    updates: list[dict] = []  # [{task_id, new_status, new_priority, new_assignee}]


# --- Helpers ---

async def _get_member_names(db: AsyncSession, project_id: int) -> list[str]:
    stmt = (
        select(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
    )
    result = await db.execute(stmt)
    members = result.scalars().unique().all()
    return [m.user.name for m in members]


async def _get_all_tasks(db: AsyncSession, project_id: int) -> list[dict]:
    stmt = (
        select(Task)
        .options(joinedload(Task.assignee))
        .where(Task.project_id == project_id)
        .order_by(Task.created_at)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().unique().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "assignee": t.assignee.name if t.assignee else None,
            "due_date": t.due_date,
            "estimated_hours": t.estimated_hours,
        }
        for t in tasks
    ]


async def _find_user_by_name(db: AsyncSession, name: str) -> User | None:
    if not name:
        return None
    result = await db.execute(select(User).where(User.name == name))
    return result.scalar_one_or_none()


# --- Endpoints ---

@router.post("/{project_id}/ai/breakdown")
async def ai_breakdown(
    project_id: int,
    data: BreakdownRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    members = await _get_member_names(db, project_id)

    try:
        result = await ai_service.break_down_task(data.description, members)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/breakdown/apply")
async def ai_breakdown_apply(
    project_id: int,
    data: BreakdownApply,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    # Create parent task
    parent = Task(
        project_id=project_id,
        title=data.title,
        priority=data.priority,
        ai_generated=True,
    )
    db.add(parent)
    await db.flush()

    # Create subtasks
    for i, st in enumerate(data.subtasks):
        assignee = await _find_user_by_name(db, st.get("suggested_assignee", ""))
        subtask = Task(
            project_id=project_id,
            parent_task_id=parent.id,
            title=st.get("title", "Untitled"),
            description=st.get("description", ""),
            priority=st.get("priority", "medium"),
            estimated_hours=st.get("estimated_hours"),
            assignee_id=assignee.id if assignee else None,
            ai_generated=True,
            position=i,
        )
        db.add(subtask)

    await activity_service.log(
        db, project_id, user.id, "ai_breakdown", task_id=parent.id,
        details={"title": data.title, "subtask_count": len(data.subtasks)},
    )
    await db.commit()

    return {"ok": True, "task_id": parent.id, "subtask_count": len(data.subtasks)}


@router.post("/{project_id}/ai/extract-tasks")
async def ai_extract_tasks(
    project_id: int,
    data: ExtractTasksRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    members = await _get_member_names(db, project_id)
    existing_tasks = await _get_all_tasks(db, project_id)

    try:
        result = await ai_service.extract_tasks_from_text(data.text, members, existing_tasks)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/meeting-notes")
async def ai_meeting_notes(
    project_id: int,
    data: MeetingNotesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    members = await _get_member_names(db, project_id)
    existing_tasks = await _get_all_tasks(db, project_id)

    try:
        result = await ai_service.extract_meeting_notes(data.notes, members, existing_tasks)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/meeting-notes/apply")
async def ai_meeting_notes_apply(
    project_id: int,
    data: MeetingNotesApply,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    # Create new tasks
    created = []
    for i, t in enumerate(data.tasks):
        assignee = await _find_user_by_name(db, t.get("suggested_assignee", ""))
        task = Task(
            project_id=project_id,
            title=t.get("title", "Untitled"),
            description=t.get("description", ""),
            priority=t.get("priority", "medium"),
            estimated_hours=t.get("estimated_hours"),
            assignee_id=assignee.id if assignee else None,
            ai_generated=True,
            position=i,
        )
        db.add(task)
        await db.flush()
        created.append(task.id)

        await activity_service.log(
            db, project_id, user.id, "created", task_id=task.id,
            details={"title": task.title, "source": "meeting_notes"},
        )

    # Apply updates to existing tasks
    updated = 0
    for upd in data.updates:
        task_id = upd.get("task_id")
        if not task_id:
            continue
        task = await db.get(Task, task_id)
        if not task or task.project_id != project_id:
            continue

        old_status = task.status
        new_status = upd.get("new_status")
        new_priority = upd.get("new_priority")
        new_assignee_name = upd.get("new_assignee")

        if new_status and new_status in ("todo", "in_progress", "done", "blocked"):
            task.status = new_status
        if new_priority and new_priority in ("low", "medium", "high", "urgent"):
            task.priority = new_priority
        if new_assignee_name:
            assignee = await _find_user_by_name(db, new_assignee_name)
            if assignee:
                task.assignee_id = assignee.id

        updated += 1
        await activity_service.log(
            db, project_id, user.id, "status_changed", task_id=task.id,
            details={"from": old_status, "to": task.status, "source": "meeting_notes", "reason": upd.get("reason", "")},
        )

    await db.commit()
    return {"ok": True, "created_count": len(created), "task_ids": created, "updated_count": updated}


@router.post("/{project_id}/ai/blockers")
async def ai_blockers(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    tasks = await _get_all_tasks(db, project_id)

    if not tasks:
        return {"blockers": []}

    try:
        result = await ai_service.detect_blockers(tasks)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/digest")
async def ai_digest(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    tasks = await _get_all_tasks(db, project_id)
    recent = await activity_service.get_recent(db, project_id, limit=50)
    activities_data = [
        {
            "action": a.action,
            "user": a.user.name if a.user else "Unknown",
            "details": a.details,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent
    ]

    try:
        result = await ai_service.generate_digest(activities_data, tasks)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/sprint-plan")
async def ai_sprint_plan(
    project_id: int,
    data: SprintPlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    tasks = await _get_all_tasks(db, project_id)
    members = await _get_member_names(db, project_id)

    # Build member data with workload
    member_data = []
    for name in members:
        member_user = (await db.execute(select(User).where(User.name == name))).scalar_one_or_none()
        workload = 0
        if member_user:
            workload = (await db.execute(
                select(func.count()).where(
                    Task.project_id == project_id,
                    Task.assignee_id == member_user.id,
                    Task.status != "done",
                )
            )).scalar() or 0
        member_data.append({"name": name, "current_tasks": workload})

    # Only plan for non-done tasks
    open_tasks = [t for t in tasks if t["status"] != "done"]

    try:
        result = await ai_service.plan_sprint(open_tasks, member_data, data.capacity_hours)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/sprint-plan/apply")
async def ai_sprint_plan_apply(
    project_id: int,
    data: SprintPlanApply,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply sprint plan — creates a real Sprint record, assigns tasks to it."""
    await verify_membership(project_id, user.id, db)

    # Create Sprint record
    sprint = Sprint(
        project_id=project_id,
        name=data.sprint_name,
        goal=data.goal,
        start_date=data.start_date,
        end_date=data.end_date,
        capacity_hours=data.capacity_hours,
    )
    db.add(sprint)
    await db.flush()

    # Assign tasks to sprint and set assignees
    applied = 0
    for item in data.assignments:
        task = await db.get(Task, item.get("task_id"))
        if not task or task.project_id != project_id:
            continue
        task.sprint_id = sprint.id
        assignee_name = item.get("assignee")
        if assignee_name:
            assignee = await _find_user_by_name(db, assignee_name)
            if assignee:
                task.assignee_id = assignee.id
        applied += 1

    await activity_service.log(
        db, project_id, user.id, "sprint_created",
        details={"sprint_name": sprint.name, "tasks_assigned": applied, "source": "ai_planner"},
    )
    await db.commit()
    return {"ok": True, "sprint_id": sprint.id, "applied": applied}


@router.post("/{project_id}/ai/priority-score")
async def ai_priority_score(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    tasks = await _get_all_tasks(db, project_id)

    if not tasks:
        return {"recommendations": []}

    try:
        result = await ai_service.score_priorities(tasks)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.post("/{project_id}/ai/priority-score/apply")
async def ai_priority_score_apply(
    project_id: int,
    data: PriorityApply,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply AI-suggested priority changes."""
    await verify_membership(project_id, user.id, db)

    applied = 0
    for item in data.updates:
        task = await db.get(Task, item.get("task_id"))
        if not task or task.project_id != project_id:
            continue
        new_priority = item.get("priority")
        if new_priority in ("low", "medium", "high", "urgent"):
            task.priority = new_priority
            applied += 1

    await db.commit()
    return {"ok": True, "applied": applied}


@router.post("/{project_id}/ai/standup")
async def ai_standup(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    tasks = await _get_all_tasks(db, project_id)
    members = await _get_member_names(db, project_id)
    recent = await activity_service.get_recent(db, project_id, limit=50)
    activities_data = [
        {
            "action": a.action,
            "user": a.user.name if a.user else "Unknown",
            "details": a.details,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent
    ]

    try:
        result = await ai_service.generate_standup(activities_data, tasks, members)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result


@router.get("/{project_id}/ai/analytics")
async def ai_analytics(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Team analytics — task distribution, workload, velocity."""
    await verify_membership(project_id, user.id, db)

    # Task counts by status
    status_counts = {}
    for status in ("todo", "in_progress", "done", "blocked"):
        count = (await db.execute(
            select(func.count()).where(
                Task.project_id == project_id,
                Task.parent_task_id.is_(None),
                Task.status == status,
            )
        )).scalar() or 0
        status_counts[status] = count

    # Priority distribution
    priority_counts = {}
    for priority in ("low", "medium", "high", "urgent"):
        count = (await db.execute(
            select(func.count()).where(
                Task.project_id == project_id,
                Task.parent_task_id.is_(None),
                Task.priority == priority,
            )
        )).scalar() or 0
        priority_counts[priority] = count

    # Workload per member
    members = await _get_member_names(db, project_id)
    workload = []
    for name in members:
        member_user = (await db.execute(select(User).where(User.name == name))).scalar_one_or_none()
        if not member_user:
            continue
        assigned = (await db.execute(
            select(func.count()).where(
                Task.project_id == project_id,
                Task.assignee_id == member_user.id,
                Task.status != "done",
            )
        )).scalar() or 0
        completed = (await db.execute(
            select(func.count()).where(
                Task.project_id == project_id,
                Task.assignee_id == member_user.id,
                Task.status == "done",
            )
        )).scalar() or 0
        total_hours = (await db.execute(
            select(func.coalesce(func.sum(Task.estimated_hours), 0)).where(
                Task.project_id == project_id,
                Task.assignee_id == member_user.id,
                Task.status != "done",
            )
        )).scalar() or 0
        workload.append({
            "name": name,
            "assigned": assigned,
            "completed": completed,
            "estimated_hours": round(float(total_hours), 1),
        })

    total = sum(status_counts.values())
    completion_rate = round(status_counts["done"] / total * 100, 1) if total > 0 else 0

    return {
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "workload": workload,
        "total_tasks": total,
        "completion_rate": completion_rate,
    }
