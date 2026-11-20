"""Pydantic schemas for Projects Management."""

from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


ProjectStatus = Literal[
    "Not Started",
    "In Progress",
    "Completed",
    "On Hold",
    "Cancelled",
]

TaskStatus = Literal[
    "Not Started",
    "In Progress",
    "Completed",
    "Blocked",
]

ProjectPriority = Literal[
    "Low",
    "Medium",
    "High",
]


# ==========================================
# PROJECT SCHEMAS
# ==========================================


class ProjectBase(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    status: ProjectStatus = "Not Started"

    priority: ProjectPriority = "Medium"

    start_date: date | None = None

    due_date: date | None = None

    repository_url: str | None = Field(
        default=None,
        max_length=1500,
    )

    @model_validator(mode="after")
    def validate_dates(self):

        if (
            self.start_date is not None
            and self.due_date is not None
            and self.due_date < self.start_date
        ):
            raise ValueError(
                "Due date cannot be before start date."
            )

        return self


class ProjectCreate(ProjectBase):
    """Request schema for creating projects."""

    pass


class ProjectUpdate(BaseModel):
    """Request schema for partially updating projects."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    status: ProjectStatus | None = None

    priority: ProjectPriority | None = None

    start_date: date | None = None

    due_date: date | None = None

    repository_url: str | None = Field(
        default=None,
        max_length=1500,
    )

    @model_validator(mode="after")
    def validate_update(self):

        required_fields = {
            "name",
            "category",
            "status",
            "priority",
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
            and self.due_date is not None
            and self.due_date < self.start_date
        ):
            raise ValueError(
                "Due date cannot be before start date."
            )

        return self


class ProjectResponse(ProjectBase):
    """Complete project response."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    total_tasks: int = Field(ge=0)

    completed_tasks: int = Field(ge=0)

    progress: float = Field(ge=0, le=100)

    created_at: datetime

    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated project list."""

    total: int

    page: int

    page_size: int

    pages: int

    items: list[ProjectResponse]


# ==========================================
# PROJECT TASK SCHEMAS
# ==========================================


class ProjectTaskBase(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(
        min_length=1,
        max_length=250,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    status: TaskStatus = "Not Started"

    priority: ProjectPriority = "Medium"

    due_date: date | None = None


class ProjectTaskCreate(ProjectTaskBase):
    """Request schema for creating tasks."""

    pass


class ProjectTaskUpdate(BaseModel):
    """Request schema for partially updating tasks."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=250,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    status: TaskStatus | None = None

    priority: ProjectPriority | None = None

    due_date: date | None = None

    @model_validator(mode="after")
    def validate_update(self):

        required_fields = {
            "title",
            "status",
            "priority",
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


class ProjectTaskResponse(ProjectTaskBase):
    """Complete project task response."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    project_id: int

    completed_at: datetime | None

    created_at: datetime

    updated_at: datetime


class ProjectTaskListResponse(BaseModel):
    """Paginated project tasks."""

    total: int

    page: int

    page_size: int

    pages: int

    items: list[ProjectTaskResponse]


# ==========================================
# STATISTICS SCHEMAS
# ==========================================


class ProjectCategoryStats(BaseModel):

    category: str

    count: int


class ProjectStatsResponse(BaseModel):
    """Overall project and task statistics."""

    total_projects: int

    not_started: int

    in_progress: int

    completed: int

    on_hold: int

    cancelled: int

    total_tasks: int

    completed_tasks: int

    pending_tasks: int

    blocked_tasks: int

    overdue_projects: int

    overdue_tasks: int

    overall_progress: float = Field(
        ge=0,
        le=100,
    )

    categories: list[ProjectCategoryStats]


# ==========================================
# DELETE RESPONSE SCHEMAS
# ==========================================


class ProjectDeleteResponse(BaseModel):

    message: str

    project_id: int


class ProjectTaskDeleteResponse(BaseModel):

    message: str

    project_id: int

    task_id: int