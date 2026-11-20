"""Pydantic schemas for the Skills Management API."""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


ProficiencyLevel = Literal[
    "Beginner",
    "Intermediate",
    "Advanced",
    "Expert",
]

SkillPriority = Literal[
    "Low",
    "Medium",
    "High",
]

SkillStatus = Literal[
    "Not Started",
    "Learning",
    "Practicing",
    "Mastered",
]


class SkillBase(BaseModel):
    """Common skill fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    proficiency_level: ProficiencyLevel = "Beginner"

    target_level: ProficiencyLevel = "Advanced"

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    priority: SkillPriority = "Medium"

    status: SkillStatus = "Not Started"

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    notes: str | None = Field(
        default=None,
        max_length=10000,
    )


class SkillCreate(SkillBase):
    """Request schema for creating a skill."""

    pass


class SkillUpdate(BaseModel):
    """Request schema for partially updating a skill."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    proficiency_level: ProficiencyLevel | None = None

    target_level: ProficiencyLevel | None = None

    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    priority: SkillPriority | None = None

    status: SkillStatus | None = None

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    notes: str | None = Field(
        default=None,
        max_length=10000,
    )

    @model_validator(mode="after")
    def validate_non_nullable_fields(self):
        non_nullable_fields = {
            "name",
            "category",
            "proficiency_level",
            "target_level",
            "progress",
            "priority",
            "status",
        }

        for field in non_nullable_fields:
            if (
                field in self.model_fields_set
                and getattr(self, field) is None
            ):
                raise ValueError(
                    f"{field} cannot be null"
                )

        return self


class SkillResponse(SkillBase):
    """Response schema for a skill."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime


class SkillListResponse(BaseModel):
    """Paginated skill list."""

    total: int

    page: int

    page_size: int

    pages: int

    items: list[SkillResponse]


class SkillCategoryStats(BaseModel):
    """Skill count grouped by category."""

    category: str

    count: int


class SkillStatsResponse(BaseModel):
    """Overall learning and skill statistics."""

    total_skills: int

    not_started: int

    learning: int

    practicing: int

    mastered: int

    average_progress: float

    high_priority_skills: int

    categories: list[SkillCategoryStats]


class SkillDeleteResponse(BaseModel):
    """Response after deleting a skill."""

    message: str

    skill_id: int