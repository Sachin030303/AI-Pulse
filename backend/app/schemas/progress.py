
"""Pydantic schemas for the AI-Pulse Progress Tracking API."""

from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ==========================================
# SHARED FIELD TYPES
# ==========================================

GoalStatus = Literal[
    "Not Started",
    "In Progress",
    "Completed",
    "Paused",
]

ProgressPriority = Literal[
    "Low",
    "Medium",
    "High",
]

ActivityType = Literal[
    "Learning",
    "Coding",
    "Testing",
    "Research",
    "Debugging",
    "Deployment",
    "Other",
]


# ==========================================
# LEARNING GOAL SCHEMAS
# ==========================================

class LearningGoalBase(BaseModel):
    """Shared fields for learning goals."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    skill_id: int | None = Field(
        default=None,
        ge=1,
    )

    status: GoalStatus = "Not Started"

    priority: ProgressPriority = "Medium"

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    start_date: date | None = None

    target_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.target_date is not None
            and self.target_date < self.start_date
        ):
            raise ValueError(
                "Target date cannot be before start date."
            )

        return self


class LearningGoalCreate(LearningGoalBase):
    """Request schema for creating a learning goal."""

    pass


class LearningGoalUpdate(BaseModel):
    """Request schema for partially updating a goal."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    skill_id: int | None = Field(
        default=None,
        ge=1,
    )

    status: GoalStatus | None = None

    priority: ProgressPriority | None = None

    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    start_date: date | None = None

    target_date: date | None = None

    @model_validator(mode="after")
    def validate_update(self):
        required_fields = {
            "title",
            "status",
            "priority",
            "progress",
        }

        for field in required_fields:
            if (
                field in self.model_fields_set
                and getattr(self, field) is None
            ):
                raise ValueError(
                    f"{field} cannot be null."
                )

        if (
            self.start_date is not None
            and self.target_date is not None
            and self.target_date < self.start_date
        ):
            raise ValueError(
                "Target date cannot be before start date."
            )

        return self


class LearningGoalResponse(LearningGoalBase):
    """Complete learning goal response."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    completed_at: datetime | None

    created_at: datetime

    updated_at: datetime


class LearningGoalListResponse(BaseModel):
    """Paginated learning goals."""

    total: int

    page: int

    page_size: int

    pages: int

    items: list[LearningGoalResponse]


# ==========================================
# IMPLEMENTATION LOG SCHEMAS
# ==========================================

class ImplementationLogBase(BaseModel):
    """Shared fields for development activity logs."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    project_id: int | None = Field(
        default=None,
        ge=1,
    )

    goal_id: int | None = Field(
        default=None,
        ge=1,
    )

    activity_type: ActivityType = "Coding"

    duration_minutes: int = Field(
        default=0,
        ge=0,
    )

    activity_date: date = Field(
        default_factory=date.today,
    )


class ImplementationLogCreate(ImplementationLogBase):
    """Request schema for creating activity logs."""

    pass


class ImplementationLogUpdate(BaseModel):
    """Request schema for partially updating activity logs."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    project_id: int | None = Field(
        default=None,
        ge=1,
    )

    goal_id: int | None = Field(
        default=None,
        ge=1,
    )

    activity_type: ActivityType | None = None

    duration_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    activity_date: date | None = None

    @model_validator(mode="after")
    def validate_update(self):
        required_fields = {
            "title",
            "activity_type",
            "duration_minutes",
            "activity_date",
        }

        for field in required_fields:
            if (
                field in self.model_fields_set
                and getattr(self, field) is None
            ):
                raise ValueError(
                    f"{field} cannot be null."
                )

        return self


class ImplementationLogResponse(ImplementationLogBase):
    """Complete activity log response."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime


class ImplementationLogListResponse(BaseModel):
    """Paginated implementation logs."""

    total: int

    page: int

    page_size: int

    pages: int

    items: list[ImplementationLogResponse]


# ==========================================
# PROGRESS STATISTICS SCHEMAS
# ==========================================

class ActivityTypeStats(BaseModel):
    """Activity count and time grouped by type."""

    activity_type: str

    count: int

    duration_minutes: int


class ProgressStatsResponse(BaseModel):
    """Overall learning and implementation statistics."""

    total_goals: int

    not_started: int

    in_progress: int

    completed: int

    paused: int

    overdue_goals: int

    average_goal_progress: float = Field(
        ge=0,
        le=100,
    )

    total_logs: int

    total_minutes: int

    total_hours: float

    activity_by_type: list[ActivityTypeStats]


# ==========================================
# DELETE RESPONSE SCHEMAS
# ==========================================

class LearningGoalDeleteResponse(BaseModel):
    """Response after deleting a learning goal."""

    message: str

    goal_id: int


class ImplementationLogDeleteResponse(BaseModel):
    """Response after deleting an activity log."""

    message: str

    log_id: int
