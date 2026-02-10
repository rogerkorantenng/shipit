"""Authentication API — username-based auth with distinct usernames."""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models import User

router = APIRouter()


# --- Schemas ---

class AuthRequest(BaseModel):
    name: str


class AuthResponse(BaseModel):
    id: int
    name: str


# --- Dependencies ---

async def get_current_user(
    x_user_id: int = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.get(User, x_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# --- Endpoints ---

@router.post("/register", response_model=AuthResponse)
async def register(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Username must be unique."""
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Username is required")
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Username must be at least 2 characters")

    result = await db.execute(select(User).where(User.name == name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(name=name, email=f"{name.lower().replace(' ', '')}@shipit", password_hash="")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return AuthResponse(id=user.id, name=user.name)


@router.post("/login", response_model=AuthResponse)
async def login(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    """Log in with an existing username."""
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Username is required")

    result = await db.execute(select(User).where(User.name == name))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Username not found. Need to sign up first?")

    return AuthResponse(id=user.id, name=user.name)


@router.post("/enter", response_model=AuthResponse)
async def enter(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    """Legacy — find or create. Kept for backward compatibility."""
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    result = await db.execute(select(User).where(User.name == name))
    user = result.scalar_one_or_none()

    if not user:
        user = User(name=name, email=f"{name.lower().replace(' ', '')}@shipit", password_hash="")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return AuthResponse(id=user.id, name=user.name)
