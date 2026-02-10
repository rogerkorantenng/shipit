"""Jira integration API — connect, export, import, sync."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models import User, Task, JiraConnection, Sprint
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services.jira_service import JiraService
from app.services import activity_service

router = APIRouter()


# --- Schemas ---

class JiraConnectRequest(BaseModel):
    jira_site: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str


# --- Helpers ---

async def _get_connection(db: AsyncSession, project_id: int) -> JiraConnection:
    result = await db.execute(
        select(JiraConnection).where(JiraConnection.project_id == project_id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Jira not connected")
    return conn


def _jira_service(conn: JiraConnection) -> JiraService:
    return JiraService(conn.jira_site, conn.jira_email, conn.jira_api_token)


async def _find_or_create_sprint(
    db: AsyncSession, project_id: int, jira_sprint: dict
) -> Sprint:
    """Find a local Sprint by jira_sprint_id, or create one."""
    jira_id = jira_sprint.get("id")
    if jira_id:
        stmt = select(Sprint).where(
            Sprint.project_id == project_id,
            Sprint.jira_sprint_id == jira_id,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    sprint = Sprint(
        project_id=project_id,
        name=jira_sprint.get("name", "Jira Sprint"),
        goal=jira_sprint.get("goal", "") or "",
        status=JiraService.parse_jira_sprint_state(jira_sprint.get("state", "future")),
        start_date=jira_sprint.get("startDate", "")[:10] if jira_sprint.get("startDate") else None,
        end_date=jira_sprint.get("endDate", "")[:10] if jira_sprint.get("endDate") else None,
        jira_sprint_id=jira_id,
    )
    db.add(sprint)
    await db.flush()
    return sprint


# --- Endpoints ---

@router.post("/{project_id}/jira/connect")
async def jira_connect(
    project_id: int,
    data: JiraConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    # Test the connection first
    svc = JiraService(data.jira_site, data.jira_email, data.jira_api_token)
    try:
        myself = await svc.test_connection()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not connect to Jira. Check credentials.")

    # Auto-discover board ID for agile API
    board_id = None
    try:
        boards = await svc.get_boards(data.jira_project_key)
        if boards:
            board_id = boards[0].get("id")
    except Exception:
        pass  # Board discovery is optional

    # Upsert connection
    result = await db.execute(
        select(JiraConnection).where(JiraConnection.project_id == project_id)
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.jira_site = data.jira_site
        conn.jira_email = data.jira_email
        conn.jira_api_token = data.jira_api_token
        conn.jira_project_key = data.jira_project_key
        conn.jira_board_id = board_id
        conn.enabled = True
    else:
        conn = JiraConnection(
            project_id=project_id,
            jira_site=data.jira_site,
            jira_email=data.jira_email,
            jira_api_token=data.jira_api_token,
            jira_project_key=data.jira_project_key,
            jira_board_id=board_id,
        )
        db.add(conn)

    await db.commit()
    return {
        "ok": True,
        "jira_user": myself.get("displayName", myself.get("emailAddress", "")),
        "jira_project_key": data.jira_project_key,
        "jira_board_id": board_id,
    }


@router.get("/{project_id}/jira/connection")
async def jira_connection_status(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    result = await db.execute(
        select(JiraConnection).where(JiraConnection.project_id == project_id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        return {"connected": False}

    return {
        "connected": True,
        "jira_site": conn.jira_site,
        "jira_email": conn.jira_email,
        "jira_project_key": conn.jira_project_key,
        "enabled": conn.enabled,
        "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        "jira_board_id": conn.jira_board_id,
        "sprints_available": conn.jira_board_id is not None,
    }


@router.delete("/{project_id}/jira/connection")
async def jira_disconnect(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)
    await db.delete(conn)
    await db.commit()
    return {"ok": True}


@router.get("/{project_id}/jira/projects")
async def jira_list_projects(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)
    svc = _jira_service(conn)

    try:
        projects = await svc.list_projects()
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch Jira projects")

    return [{"key": p["key"], "name": p["name"]} for p in projects]


@router.post("/{project_id}/jira/export")
async def jira_export(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Push ShipIt tasks to Jira. Creates issues for tasks without jira_issue_key."""
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)
    svc = _jira_service(conn)

    # Get tasks that haven't been exported yet
    stmt = (
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.parent_task_id.is_(None),
            Task.jira_issue_key.is_(None),
        )
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    exported = 0
    for task in tasks:
        try:
            issue = await svc.create_issue(
                conn.jira_project_key,
                task.title,
                task.description,
                task.priority,
            )
            task.jira_issue_key = issue["key"]
            exported += 1

            # Transition to correct status if not todo
            if task.status != "todo":
                await svc.transition_issue(issue["key"], task.status)

            # Move to Jira sprint if task has one with jira_sprint_id
            if task.sprint_id:
                sprint = await db.get(Sprint, task.sprint_id)
                if sprint and sprint.jira_sprint_id:
                    try:
                        await svc.move_issues_to_sprint(sprint.jira_sprint_id, [issue["key"]])
                    except Exception:
                        pass
        except Exception:
            continue

    conn.last_sync_at = datetime.utcnow()
    await activity_service.log(
        db, project_id, user.id, "jira_export",
        details={"exported": exported},
    )
    await db.commit()
    return {"ok": True, "exported": exported}


@router.post("/{project_id}/jira/import")
async def jira_import(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull Jira issues into ShipIt as tasks."""
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)
    svc = _jira_service(conn)

    try:
        issues = await svc.search_issues(conn.jira_project_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Jira issues: {exc}")

    # Get existing jira keys to skip duplicates
    stmt = select(Task.jira_issue_key).where(
        Task.project_id == project_id,
        Task.jira_issue_key.isnot(None),
    )
    result = await db.execute(stmt)
    existing_keys = {row[0] for row in result.all()}

    imported = 0
    for issue in issues:
        key = issue["key"]
        if key in existing_keys:
            continue

        fields = issue["fields"]
        status_name = (fields.get("status") or {}).get("name", "To Do")
        priority_name = (fields.get("priority") or {}).get("name", "")

        # Check for sprint data
        sprint_id_local = None
        jira_sprint = fields.get("sprint")
        if jira_sprint and isinstance(jira_sprint, dict) and jira_sprint.get("id"):
            local_sprint = await _find_or_create_sprint(db, project_id, jira_sprint)
            sprint_id_local = local_sprint.id

        task = Task(
            project_id=project_id,
            title=fields.get("summary", "Untitled"),
            description=JiraService.extract_plain_text(fields.get("description")),
            status=JiraService.parse_jira_status(status_name),
            priority=JiraService.parse_jira_priority(priority_name),
            jira_issue_key=key,
            sprint_id=sprint_id_local,
            position=imported,
        )
        db.add(task)
        imported += 1

    conn.last_sync_at = datetime.utcnow()
    await activity_service.log(
        db, project_id, user.id, "jira_import",
        details={"imported": imported},
    )
    await db.commit()
    return {"ok": True, "imported": imported}


@router.post("/{project_id}/jira/sync")
async def jira_sync(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full bidirectional sync: push local changes to Jira, pull Jira changes back."""
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)
    svc = _jira_service(conn)

    updated_local = 0
    updated_remote = 0

    # 1. Sync existing linked tasks
    stmt = (
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.jira_issue_key.isnot(None),
        )
    )
    result = await db.execute(stmt)
    linked_tasks = result.scalars().all()

    for task in linked_tasks:
        try:
            issue = await svc.get_issue(task.jira_issue_key)
        except Exception:
            continue

        fields = issue["fields"]
        jira_status = JiraService.parse_jira_status(
            (fields.get("status") or {}).get("name", "To Do")
        )

        if jira_status != task.status:
            # If local task was updated after last sync, push to Jira
            local_is_newer = (
                conn.last_sync_at is None
                or task.updated_at > conn.last_sync_at
            )
            if local_is_newer:
                try:
                    await svc.transition_issue(task.jira_issue_key, task.status)
                    updated_remote += 1
                except Exception:
                    pass
            else:
                # Jira changed since last sync, pull to local
                task.status = jira_status
                task.updated_at = datetime.utcnow()
                updated_local += 1

    # 2. Export un-exported tasks
    stmt = (
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.parent_task_id.is_(None),
            Task.jira_issue_key.is_(None),
        )
    )
    result = await db.execute(stmt)
    new_tasks = result.scalars().all()

    for task in new_tasks:
        try:
            issue = await svc.create_issue(
                conn.jira_project_key,
                task.title,
                task.description,
                task.priority,
            )
            task.jira_issue_key = issue["key"]
            updated_remote += 1
            if task.status != "todo":
                await svc.transition_issue(issue["key"], task.status)
        except Exception:
            continue

    # 3. Import new Jira issues
    try:
        issues = await svc.search_issues(conn.jira_project_key)
    except Exception:
        issues = []

    existing_keys_stmt = select(Task.jira_issue_key).where(
        Task.project_id == project_id,
        Task.jira_issue_key.isnot(None),
    )
    result = await db.execute(existing_keys_stmt)
    existing_keys = {row[0] for row in result.all()}

    imported = 0
    for issue in issues:
        key = issue["key"]
        if key in existing_keys:
            continue

        fields = issue["fields"]
        status_name = (fields.get("status") or {}).get("name", "To Do")
        priority_name = (fields.get("priority") or {}).get("name", "")

        # Check for sprint data
        sprint_id_local = None
        jira_sprint = fields.get("sprint")
        if jira_sprint and isinstance(jira_sprint, dict) and jira_sprint.get("id"):
            local_sprint = await _find_or_create_sprint(db, project_id, jira_sprint)
            sprint_id_local = local_sprint.id

        task = Task(
            project_id=project_id,
            title=fields.get("summary", "Untitled"),
            description=JiraService.extract_plain_text(fields.get("description")),
            status=JiraService.parse_jira_status(status_name),
            priority=JiraService.parse_jira_priority(priority_name),
            jira_issue_key=key,
            sprint_id=sprint_id_local,
        )
        db.add(task)
        imported += 1

    # 4. Sync sprint statuses from Jira (if board is available)
    sprints_synced = 0
    if conn.jira_board_id:
        try:
            jira_sprints = await svc.get_sprints(conn.jira_board_id)
            for js in jira_sprints:
                jira_id = js.get("id")
                if not jira_id:
                    continue
                stmt = select(Sprint).where(
                    Sprint.project_id == project_id,
                    Sprint.jira_sprint_id == jira_id,
                )
                result = await db.execute(stmt)
                local = result.scalar_one_or_none()
                if local:
                    new_status = JiraService.parse_jira_sprint_state(js.get("state", "future"))
                    if local.status != new_status:
                        local.status = new_status
                        local.updated_at = datetime.utcnow()
                        sprints_synced += 1
        except Exception:
            pass

    conn.last_sync_at = datetime.utcnow()
    await activity_service.log(
        db, project_id, user.id, "jira_sync",
        details={
            "updated_local": updated_local,
            "updated_remote": updated_remote,
            "imported": imported,
            "sprints_synced": sprints_synced,
        },
    )
    await db.commit()

    return {
        "ok": True,
        "updated_local": updated_local,
        "updated_remote": updated_remote,
        "imported": imported,
        "sprints_synced": sprints_synced,
    }


@router.post("/{project_id}/jira/import-sprints")
async def jira_import_sprints(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull all Jira sprints into local Sprint records, assign issues to them."""
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)

    if not conn.jira_board_id:
        raise HTTPException(status_code=400, detail="No Jira board found. Sprints not available.")

    svc = _jira_service(conn)

    try:
        jira_sprints = await svc.get_sprints(conn.jira_board_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Jira sprints: {exc}")

    created = 0
    tasks_assigned = 0
    for js in jira_sprints:
        local_sprint = await _find_or_create_sprint(db, project_id, js)
        if local_sprint.created_at == local_sprint.updated_at:
            created += 1

        # Get issues in this sprint and assign them
        try:
            sprint_issues = await svc.get_sprint_issues(js["id"])
            for issue in sprint_issues:
                key = issue["key"]
                stmt = select(Task).where(
                    Task.project_id == project_id,
                    Task.jira_issue_key == key,
                )
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if task and task.sprint_id != local_sprint.id:
                    task.sprint_id = local_sprint.id
                    tasks_assigned += 1
        except Exception:
            continue

    await activity_service.log(
        db, project_id, user.id, "jira_import_sprints",
        details={"created": created, "tasks_assigned": tasks_assigned},
    )
    await db.commit()
    return {"ok": True, "sprints_created": created, "tasks_assigned": tasks_assigned}


@router.post("/{project_id}/jira/export-sprint/{sprint_id}")
async def jira_export_sprint(
    project_id: int,
    sprint_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a sprint in Jira and move linked issues into it."""
    await verify_membership(project_id, user.id, db)
    conn = await _get_connection(db, project_id)

    if not conn.jira_board_id:
        raise HTTPException(status_code=400, detail="No Jira board found. Sprints not available.")

    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    svc = _jira_service(conn)

    # Create sprint in Jira if it doesn't have a jira_sprint_id yet
    if not sprint.jira_sprint_id:
        try:
            jira_sprint = await svc.create_sprint(
                conn.jira_board_id,
                sprint.name,
                sprint.start_date,
                sprint.end_date,
                sprint.goal,
            )
            sprint.jira_sprint_id = jira_sprint["id"]
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to create Jira sprint: {exc}")

    # Move linked issues into the sprint
    stmt = select(Task).where(
        Task.sprint_id == sprint_id,
        Task.jira_issue_key.isnot(None),
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    issue_keys = [t.jira_issue_key for t in tasks]

    moved = 0
    if issue_keys:
        try:
            await svc.move_issues_to_sprint(sprint.jira_sprint_id, issue_keys)
            moved = len(issue_keys)
        except Exception:
            pass

    await activity_service.log(
        db, project_id, user.id, "jira_export_sprint",
        details={"sprint_name": sprint.name, "issues_moved": moved},
    )
    await db.commit()
    return {"ok": True, "jira_sprint_id": sprint.jira_sprint_id, "issues_moved": moved}
