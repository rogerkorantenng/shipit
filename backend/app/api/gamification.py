"""Gamification API — stats, badges, leaderboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models import User, ProjectMember
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services import gamification_service

router = APIRouter()


@router.get("/{project_id}/stats")
async def get_my_stats(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's gamification stats."""
    await verify_membership(project_id, user.id, db)
    stats = await gamification_service.get_or_create_stats(db, user.id, project_id)
    await db.commit()
    return gamification_service.stats_to_dict(stats, user.name)


@router.get("/{project_id}/stats/badges")
async def get_my_badges(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all badges with unlock status for current user."""
    await verify_membership(project_id, user.id, db)
    stats = await gamification_service.get_or_create_stats(db, user.id, project_id)
    await db.commit()
    unlocked = gamification_service._get_unlocked_ids(stats)
    return gamification_service.all_badges_with_status(unlocked)


@router.get("/{project_id}/leaderboard")
async def get_leaderboard(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Team leaderboard — all members ranked by XP."""
    await verify_membership(project_id, user.id, db)

    # Get all members
    stmt = (
        select(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
    )
    result = await db.execute(stmt)
    members = result.scalars().unique().all()

    entries = []
    for m in members:
        stats = await gamification_service.get_or_create_stats(db, m.user_id, project_id)
        entries.append(gamification_service.stats_to_dict(stats, m.user.name))

    await db.commit()

    # Sort by XP descending
    entries.sort(key=lambda e: e["xp"], reverse=True)

    # Add rank
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    return entries
