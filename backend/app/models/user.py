from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")  # noqa: F821
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")  # noqa: F821
    assigned_tasks: Mapped[list["Task"]] = relationship(back_populates="assignee")  # noqa: F821
