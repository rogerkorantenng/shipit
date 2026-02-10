"""Projects API — CRUD, members, workload."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models import User, Project, ProjectMember, Task
from app.api.auth import get_current_user
from app.services import activity_service

router = APIRouter()


# --- Helpers ---

async def verify_membership(project_id: int, user_id: int, db: AsyncSession) -> Project:
    stmt = (
        select(Project)
        .options(joinedload(Project.members))
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalars().unique().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    member_ids = [m.user_id for m in project.members]
    if user_id not in member_ids:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# --- Schemas ---

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class MemberAdd(BaseModel):
    name: str

class JoinByCode(BaseModel):
    join_code: str


# --- Endpoints ---

@router.post("/")
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = Project(name=data.name, description=data.description, owner_id=user.id)
    db.add(project)
    await db.flush()

    member = ProjectMember(project_id=project.id, user_id=user.id, role="owner")
    db.add(member)

    await activity_service.log(db, project.id, user.id, "created", details={"name": data.name})
    await db.commit()
    await db.refresh(project)

    return {"id": project.id, "name": project.name, "description": project.description, "join_code": project.join_code}


@router.get("/")
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id)
        .options(joinedload(Project.members))
    )
    result = await db.execute(stmt)
    projects = result.scalars().unique().all()

    out = []
    for p in projects:
        # Get task counts
        count_stmt = (
            select(
                func.count().filter(Task.status == "todo").label("todo"),
                func.count().filter(Task.status == "in_progress").label("in_progress"),
                func.count().filter(Task.status == "done").label("done"),
                func.count().filter(Task.status == "blocked").label("blocked"),
            )
            .where(Task.project_id == p.id, Task.parent_task_id.is_(None))
        )
        counts = (await db.execute(count_stmt)).first()

        out.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "member_count": len(p.members),
            "task_counts": {
                "todo": counts.todo if counts else 0,
                "in_progress": counts.in_progress if counts else 0,
                "done": counts.done if counts else 0,
                "blocked": counts.blocked if counts else 0,
            },
            "created_at": p.created_at.isoformat(),
        })
    return out


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_membership(project_id, user.id, db)

    count_stmt = (
        select(
            func.count().filter(Task.status == "todo").label("todo"),
            func.count().filter(Task.status == "in_progress").label("in_progress"),
            func.count().filter(Task.status == "done").label("done"),
            func.count().filter(Task.status == "blocked").label("blocked"),
        )
        .where(Task.project_id == project.id, Task.parent_task_id.is_(None))
    )
    counts = (await db.execute(count_stmt)).first()

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "owner_id": project.owner_id,
        "join_code": project.join_code,
        "task_counts": {
            "todo": counts.todo if counts else 0,
            "in_progress": counts.in_progress if counts else 0,
            "done": counts.done if counts else 0,
            "blocked": counts.blocked if counts else 0,
        },
        "created_at": project.created_at.isoformat(),
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_membership(project_id, user.id, db)
    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete a project")
    await db.delete(project)
    await db.commit()
    return {"ok": True}


@router.post("/{project_id}/members")
async def add_member(
    project_id: int,
    data: MemberAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    # Find or create user by name
    name = data.name.strip()
    result = await db.execute(select(User).where(User.name == name))
    target = result.scalar_one_or_none()
    if not target:
        target = User(name=name, email=f"{name.lower().replace(' ', '')}@demo", password_hash="")
        db.add(target)
        await db.flush()

    # Check if already a member
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    member = ProjectMember(project_id=project_id, user_id=target.id, role="member")
    db.add(member)
    await activity_service.log(
        db, project_id, user.id, "member_added", details={"member_name": name}
    )
    await db.commit()

    return {"id": target.id, "name": target.name, "role": "member"}


@router.get("/{project_id}/members")
async def list_members(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_membership(project_id, user.id, db)

    members = []
    for m in project.members:
        # Count assigned non-done tasks
        count_stmt = (
            select(func.count())
            .where(
                Task.project_id == project_id,
                Task.assignee_id == m.user_id,
                Task.status != "done",
            )
        )
        count = (await db.execute(count_stmt)).scalar() or 0

        # Get the user name
        member_user = await db.get(User, m.user_id)
        members.append({
            "id": m.user_id,
            "name": member_user.name if member_user else "Unknown",
            "role": m.role,
            "workload": count,
        })

    return members


@router.delete("/{project_id}/members/{user_id}")
async def remove_member(
    project_id: int,
    user_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_membership(project_id, user.id, db)
    if project.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the owner")

    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    await db.commit()
    return {"ok": True}


@router.post("/join")
async def join_by_code(
    data: JoinByCode,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a project using its invite code."""
    code = data.join_code.strip().upper()
    stmt = select(Project).where(Project.join_code == code)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Invalid join code")

    # Check if already a member
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "project_id": project.id, "message": "Already a member"}

    member = ProjectMember(project_id=project.id, user_id=user.id, role="member")
    db.add(member)
    await activity_service.log(
        db, project.id, user.id, "member_joined", details={"via": "join_code"}
    )
    await db.commit()
    return {"ok": True, "project_id": project.id, "project_name": project.name}
