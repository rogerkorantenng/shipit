"""Generic service connection credentials table."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class ServiceConnection(Base):
    __tablename__ = "service_connections"
    __table_args__ = (
        UniqueConstraint("project_id", "service_type", name="uq_service_conn_project_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    service_type: Mapped[str] = mapped_column(String(50))  # gitlab, figma, slack, datadog, sentry
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_token: Mapped[str] = mapped_column(String(500))
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
