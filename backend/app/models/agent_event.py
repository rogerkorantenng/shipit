"""Agent event audit log table."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    source_agent: Mapped[str] = mapped_column(String(100), index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
