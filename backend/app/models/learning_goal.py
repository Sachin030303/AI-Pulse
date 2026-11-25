
"""Database model for learning goals."""

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


class LearningGoal(Base):
    __tablename__ = "learning_goals"

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

    skill_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "user_skills.id",
            ondelete="SET NULL",
        ),
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

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    target_date: Mapped[date | None] = mapped_column(
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

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('Not Started', 'In Progress', "
            "'Completed', 'Paused')",
            name="ck_learning_goals_status",
        ),
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High')",
            name="ck_learning_goals_priority",
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="ck_learning_goals_progress",
        ),
        CheckConstraint(
            "target_date IS NULL OR start_date IS NULL "
            "OR target_date >= start_date",
            name="ck_learning_goals_dates",
        ),
        Index(
            "ix_learning_goals_skill_id",
            "skill_id",
        ),
        Index(
            "ix_learning_goals_status",
            "status",
        ),
        Index(
            "ix_learning_goals_target_date",
            "target_date",
        ),
    )
