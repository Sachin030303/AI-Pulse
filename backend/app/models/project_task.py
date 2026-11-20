"""Database model for project tasks."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Not Started",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="Medium",
        nullable=False,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(
        back_populates="tasks",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('Not Started', 'In Progress', "
            "'Completed', 'Blocked')",
            name="ck_project_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High')",
            name="ck_project_tasks_priority",
        ),
        Index(
            "ix_project_tasks_project_id",
            "project_id",
        ),
        Index(
            "ix_project_tasks_status",
            "status",
        ),
        Index(
            "ix_project_tasks_due_date",
            "due_date",
        ),
    )