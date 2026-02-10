from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.db.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="todo")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    assignee_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    due_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    jira_issue_key: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    sprint_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sprints.id"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")  # noqa: F821
    assignee: Mapped[Optional["User"]] = relationship(back_populates="assigned_tasks")  # noqa: F821
    sprint: Mapped[Optional["Sprint"]] = relationship(back_populates="tasks")  # noqa: F821
    parent_task: Mapped[Optional["Task"]] = relationship(
        back_populates="subtasks", remote_side="Task.id"
    )
    subtasks: Mapped[list["Task"]] = relationship(
        back_populates="parent_task", cascade="all, delete-orphan"
    )
