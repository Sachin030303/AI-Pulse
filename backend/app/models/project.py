"""Database model for development projects."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
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
    from app.models.project_task import ProjectTask


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
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

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    repository_url: Mapped[str | None] = mapped_column(
        String(1500),
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

    tasks: Mapped[list["ProjectTask"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('Not Started', 'In Progress', "
            "'Completed', 'On Hold', 'Cancelled')",
            name="ck_projects_status",
        ),
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High')",
            name="ck_projects_priority",
        ),
        CheckConstraint(
            "due_date IS NULL OR start_date IS NULL "
            "OR due_date >= start_date",
            name="ck_projects_dates",
        ),
        Index("ix_projects_category", "category"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_priority", "priority"),
        Index("ix_projects_due_date", "due_date"),
    )