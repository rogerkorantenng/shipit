from datetime import datetime
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.activity import Activity


async def log(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    action: str,
    task_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> Activity:
    activity = Activity(
        project_id=project_id,
        user_id=user_id,
        action=action,
        task_id=task_id,
        details=details,
    )
    db.add(activity)
    await db.flush()
    return activity


async def get_recent(
    db: AsyncSession,
    project_id: int,
    limit: int = 50,
    since: Optional[datetime] = None,
) -> list[Activity]:
    stmt = (
        select(Activity)
        .options(joinedload(Activity.user))
        .where(Activity.project_id == project_id)
    )
    if since:
        stmt = stmt.where(Activity.created_at >= since)
    stmt = stmt.order_by(desc(Activity.created_at)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_for_task(db: AsyncSession, task_id: int) -> list[Activity]:
    stmt = (
        select(Activity)
        .options(joinedload(Activity.user))
        .where(Activity.task_id == task_id)
        .order_by(desc(Activity.created_at))
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())
