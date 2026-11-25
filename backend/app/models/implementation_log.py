
"""Database model for development activity logs."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImplementationLog(Base):
    __tablename__ = "implementation_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    goal_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "learning_goals.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    activity_type: Mapped[str] = mapped_column(
        String(30),
        default="Coding",
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    activity_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False,
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

    __table_args__ = (
        CheckConstraint(
            "activity_type IN "
            "('Learning', 'Coding', 'Testing', "
            "'Research', 'Debugging', "
            "'Deployment', 'Other')",
            name="ck_implementation_logs_activity_type",
        ),
        CheckConstraint(
            "duration_minutes >= 0",
            name="ck_implementation_logs_duration",
        ),
        Index(
            "ix_implementation_logs_project_id",
            "project_id",
        ),
        Index(
            "ix_implementation_logs_goal_id",
            "goal_id",
        ),
        Index(
            "ix_implementation_logs_activity_date",
            "activity_date",
        ),
        Index(
            "ix_implementation_logs_activity_type",
            "activity_type",
        ),
    )
