"""Gamification service — XP, streaks, badges, levels."""

import json
import math
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_stats import UserStats

# --- XP ---

XP_BY_PRIORITY = {
    "urgent": 40,
    "high": 30,
    "medium": 20,
    "low": 10,
}


def calculate_level(xp: int) -> int:
    """Level = floor(sqrt(xp / 50)) + 1. So L2=50xp, L3=200xp, L5=800xp."""
    if xp <= 0:
        return 1
    return int(math.floor(math.sqrt(xp / 50))) + 1


def xp_for_level(level: int) -> int:
    """XP required to reach a given level."""
    if level <= 1:
        return 0
    return (level - 1) ** 2 * 50


# --- Badges ---

BADGES = [
    {
        "id": "first_blood",
        "name": "First Blood",
        "description": "Complete your first task",
        "icon": "target",
        "check": lambda s: s.tasks_completed >= 1,
    },
    {
        "id": "streak_3",
        "name": "On Fire",
        "description": "3-day ship streak",
        "icon": "flame",
        "check": lambda s: s.longest_streak >= 3,
    },
    {
        "id": "streak_7",
        "name": "Unstoppable",
        "description": "7-day ship streak",
        "icon": "zap",
        "check": lambda s: s.longest_streak >= 7,
    },
    {
        "id": "streak_14",
        "name": "Machine",
        "description": "14-day ship streak",
        "icon": "bot",
        "check": lambda s: s.longest_streak >= 14,
    },
    {
        "id": "xp_100",
        "name": "Getting Started",
        "description": "Earn 100 XP",
        "icon": "star",
        "check": lambda s: s.xp >= 100,
    },
    {
        "id": "xp_500",
        "name": "Power User",
        "description": "Earn 500 XP",
        "icon": "sparkles",
        "check": lambda s: s.xp >= 500,
    },
    {
        "id": "xp_1000",
        "name": "Legend",
        "description": "Earn 1000 XP",
        "icon": "trophy",
        "check": lambda s: s.xp >= 1000,
    },
    {
        "id": "tasks_5",
        "name": "Warming Up",
        "description": "Complete 5 tasks",
        "icon": "dumbbell",
        "check": lambda s: s.tasks_completed >= 5,
    },
    {
        "id": "tasks_25",
        "name": "Workhorse",
        "description": "Complete 25 tasks",
        "icon": "horse",
        "check": lambda s: s.tasks_completed >= 25,
    },
    {
        "id": "tasks_50",
        "name": "Centurion",
        "description": "Complete 50 tasks",
        "icon": "shield",
        "check": lambda s: s.tasks_completed >= 50,
    },
    {
        "id": "sprint_shipper",
        "name": "Sprint Shipper",
        "description": "Complete all tasks in a sprint",
        "icon": "rocket",
        "check": lambda _: False,  # Checked separately via award_sprint_clear
    },
]

BADGE_MAP = {b["id"]: b for b in BADGES}


def _get_unlocked_ids(stats: UserStats) -> list[str]:
    try:
        return json.loads(stats.badges)
    except (json.JSONDecodeError, TypeError):
        return []


def _check_badges(stats: UserStats) -> list[str]:
    """Return list of newly unlocked badge IDs."""
    current = set(_get_unlocked_ids(stats))
    newly = []
    for badge in BADGES:
        if badge["id"] not in current and badge["check"](stats):
            newly.append(badge["id"])
    return newly


# --- Core Functions ---

async def get_or_create_stats(db: AsyncSession, user_id: int, project_id: int) -> UserStats:
    stmt = select(UserStats).where(
        UserStats.user_id == user_id,
        UserStats.project_id == project_id,
    )
    result = await db.execute(stmt)
    stats = result.scalar_one_or_none()
    if not stats:
        stats = UserStats(user_id=user_id, project_id=project_id)
        db.add(stats)
        await db.flush()
    return stats


async def award_task_completion(
    db: AsyncSession, user_id: int, project_id: int, priority: str
) -> dict:
    """Called when a task is moved to done. Returns XP gained + new badges."""
    stats = await get_or_create_stats(db, user_id, project_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    # XP
    xp_gained = XP_BY_PRIORITY.get(priority, 20)
    stats.xp += xp_gained
    stats.level = calculate_level(stats.xp)
    stats.tasks_completed += 1

    # Streak
    if stats.last_active_date != today:
        if stats.last_active_date == yesterday:
            stats.current_streak += 1
        elif stats.last_active_date is None or stats.last_active_date < yesterday:
            stats.current_streak = 1
        stats.last_active_date = today
        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak

    # Badges
    new_badges = _check_badges(stats)
    if new_badges:
        current = _get_unlocked_ids(stats)
        current.extend(new_badges)
        stats.badges = json.dumps(current)

    stats.updated_at = datetime.utcnow()

    return {
        "xp_gained": xp_gained,
        "total_xp": stats.xp,
        "level": stats.level,
        "current_streak": stats.current_streak,
        "new_badges": new_badges,
    }


async def award_sprint_clear(db: AsyncSession, user_id: int, project_id: int) -> list[str]:
    """Award the sprint_shipper badge. Called when a sprint completes with all tasks done."""
    stats = await get_or_create_stats(db, user_id, project_id)
    current = _get_unlocked_ids(stats)
    if "sprint_shipper" not in current:
        current.append("sprint_shipper")
        stats.badges = json.dumps(current)
        stats.updated_at = datetime.utcnow()
        return ["sprint_shipper"]
    return []


def stats_to_dict(stats: UserStats, user_name: str = "") -> dict:
    unlocked = _get_unlocked_ids(stats)
    next_level = stats.level + 1
    xp_current_level = xp_for_level(stats.level)
    xp_next_level = xp_for_level(next_level)
    xp_progress = stats.xp - xp_current_level
    xp_needed = xp_next_level - xp_current_level

    return {
        "user_id": stats.user_id,
        "user_name": user_name,
        "xp": stats.xp,
        "level": stats.level,
        "xp_progress": xp_progress,
        "xp_needed": xp_needed,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "tasks_completed": stats.tasks_completed,
        "badges": unlocked,
        "last_active_date": stats.last_active_date,
    }


def all_badges_with_status(unlocked_ids: list[str]) -> list[dict]:
    unlocked_set = set(unlocked_ids)
    return [
        {
            "id": b["id"],
            "name": b["name"],
            "description": b["description"],
            "icon": b["icon"],
            "unlocked": b["id"] in unlocked_set,
        }
        for b in BADGES
    ]
