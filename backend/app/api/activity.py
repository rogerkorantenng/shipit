"""Activity log API."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models import User
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services import activity_service

router = APIRouter()


def _activity_to_dict(a) -> dict:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "task_id": a.task_id,
        "user_id": a.user_id,
        "user_name": a.user.name if a.user else "Unknown",
        "action": a.action,
        "details": a.details,
        "created_at": a.created_at.isoformat(),
    }


@router.get("/{project_id}/activity")
async def list_activity(
    project_id: int,
    since: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            pass

    activities = await activity_service.get_recent(db, project_id, limit=50, since=since_dt)
    return [_activity_to_dict(a) for a in activities]


@router.get("/{project_id}/activity/task/{task_id}")
async def task_activity(
    project_id: int,
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_membership(project_id, user.id, db)
    activities = await activity_service.get_for_task(db, task_id)
    return [_activity_to_dict(a) for a in activities]
