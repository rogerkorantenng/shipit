from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Pulse(Base):
    __tablename__ = "pulses"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", "date", name="uq_pulse_user_project_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    energy: Mapped[int] = mapped_column(Integer)  # 1-5
    mood: Mapped[int] = mapped_column(Integer)  # 1-5
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
