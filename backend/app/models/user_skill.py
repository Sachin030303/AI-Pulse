"""Database model for user skills."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    proficiency_level: Mapped[str] = mapped_column(
        String(30),
        default="Beginner",
        nullable=False,
    )

    target_level: Mapped[str] = mapped_column(
        String(30),
        default="Advanced",
        nullable=False,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="Medium",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Not Started",
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
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
            "progress >= 0 AND progress <= 100",
            name="ck_user_skills_progress",
        ),
        CheckConstraint(
            "proficiency_level IN "
            "('Beginner', 'Intermediate', 'Advanced', 'Expert')",
            name="ck_user_skills_proficiency",
        ),
        CheckConstraint(
            "target_level IN "
            "('Beginner', 'Intermediate', 'Advanced', 'Expert')",
            name="ck_user_skills_target",
        ),
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High')",
            name="ck_user_skills_priority",
        ),
        CheckConstraint(
            "status IN "
            "('Not Started', 'Learning', 'Practicing', 'Mastered')",
            name="ck_user_skills_status",
        ),
        Index(
            "ix_user_skills_category",
            "category",
        ),
        Index(
            "ix_user_skills_status",
            "status",
        ),
        Index(
            "ix_user_skills_priority",
            "priority",
        ),
    )