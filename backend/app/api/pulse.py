"""Pulse API — daily mood/energy tracking with AI insights."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.database import get_db
from app.models import User, Pulse, ProjectMember
from app.api.auth import get_current_user
from app.api.projects import verify_membership
from app.services import ai_service

router = APIRouter()


# --- Schemas ---

class PulseLog(BaseModel):
    energy: int  # 1-5
    mood: int  # 1-5
    note: Optional[str] = None


# --- Helpers ---

def _pulse_to_dict(pulse: Pulse, user_name: str = "") -> dict:
    return {
        "id": pulse.id,
        "user_id": pulse.user_id,
        "user_name": user_name,
        "energy": pulse.energy,
        "mood": pulse.mood,
        "note": pulse.note,
        "date": pulse.date,
        "created_at": pulse.created_at.isoformat(),
    }


# --- Endpoints ---

@router.post("/{project_id}/pulse")
async def log_pulse(
    project_id: int,
    data: PulseLog,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log today's pulse (upsert — one per user per project per day)."""
    await verify_membership(project_id, user.id, db)

    if not (1 <= data.energy <= 5) or not (1 <= data.mood <= 5):
        raise HTTPException(status_code=400, detail="Energy and mood must be 1-5")

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Upsert
    stmt = select(Pulse).where(
        Pulse.user_id == user.id,
        Pulse.project_id == project_id,
        Pulse.date == today,
    )
    result = await db.execute(stmt)
    pulse = result.scalar_one_or_none()

    if pulse:
        pulse.energy = data.energy
        pulse.mood = data.mood
        pulse.note = data.note
    else:
        pulse = Pulse(
            user_id=user.id,
            project_id=project_id,
            energy=data.energy,
            mood=data.mood,
            note=data.note,
            date=today,
        )
        db.add(pulse)

    await db.commit()
    await db.refresh(pulse)
    return _pulse_to_dict(pulse, user.name)


@router.get("/{project_id}/pulse/today")
async def get_today_pulse(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's pulse for today."""
    await verify_membership(project_id, user.id, db)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    stmt = select(Pulse).where(
        Pulse.user_id == user.id,
        Pulse.project_id == project_id,
        Pulse.date == today,
    )
    result = await db.execute(stmt)
    pulse = result.scalar_one_or_none()
    if not pulse:
        return None
    return _pulse_to_dict(pulse, user.name)


@router.get("/{project_id}/pulse/history")
async def get_pulse_history(
    project_id: int,
    days: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's pulse history."""
    await verify_membership(project_id, user.id, db)

    stmt = (
        select(Pulse)
        .where(
            Pulse.user_id == user.id,
            Pulse.project_id == project_id,
        )
        .order_by(Pulse.date.desc())
        .limit(days)
    )
    result = await db.execute(stmt)
    pulses = result.scalars().all()
    return [_pulse_to_dict(p, user.name) for p in pulses]


@router.get("/{project_id}/pulse/team")
async def get_team_pulse(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's pulse for all team members (anonymous aggregate + individual if logged)."""
    await verify_membership(project_id, user.id, db)

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Get all today's pulses
    stmt = select(Pulse).where(
        Pulse.project_id == project_id,
        Pulse.date == today,
    )
    result = await db.execute(stmt)
    pulses = result.scalars().all()

    # Get member count
    member_count = (await db.execute(
        select(func.count()).where(ProjectMember.project_id == project_id)
    )).scalar() or 0

    # Get user names for pulses
    entries = []
    for p in pulses:
        u = await db.get(User, p.user_id)
        entries.append(_pulse_to_dict(p, u.name if u else "Unknown"))

    # Aggregate
    if pulses:
        avg_energy = round(sum(p.energy for p in pulses) / len(pulses), 1)
        avg_mood = round(sum(p.mood for p in pulses) / len(pulses), 1)
    else:
        avg_energy = 0
        avg_mood = 0

    return {
        "date": today,
        "logged_count": len(pulses),
        "member_count": member_count,
        "avg_energy": avg_energy,
        "avg_mood": avg_mood,
        "entries": entries,
    }


@router.get("/{project_id}/pulse/insights")
async def get_pulse_insights(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-generated insights from pulse + activity data."""
    await verify_membership(project_id, user.id, db)

    # Get pulse history
    stmt = (
        select(Pulse)
        .where(Pulse.user_id == user.id, Pulse.project_id == project_id)
        .order_by(Pulse.date.desc())
        .limit(30)
    )
    result = await db.execute(stmt)
    pulses = result.scalars().all()

    if len(pulses) < 3:
        return {"insights": "Log at least 3 days of pulse data to get insights.", "patterns": []}

    pulse_data = [
        {"date": p.date, "energy": p.energy, "mood": p.mood, "note": p.note or ""}
        for p in pulses
    ]

    # Get task completion data
    from app.models import Task
    stmt = (
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.assignee_id == user.id,
            Task.status == "done",
        )
        .order_by(Task.updated_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    done_tasks = [
        {"title": t.title, "completed_date": t.updated_at.strftime("%Y-%m-%d")}
        for t in result.scalars().all()
    ]

    try:
        result = await ai_service.generate_pulse_insights(pulse_data, done_tasks)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return result
