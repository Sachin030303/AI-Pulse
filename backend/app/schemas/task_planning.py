"""Schemas for read-only AI project task planning."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(ge=1)
    objective: str = Field(default="", max_length=500)
    max_proposals: int = Field(default=3, ge=1, le=5)


class ProposedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=1000)
    priority: Literal["Low", "Medium", "High"]
    reason: str = Field(min_length=5, max_length=500)


class TaskPlanResponse(BaseModel):
    status: Literal["preview"] = "preview"
    project_id: int
    project_name: str
    existing_tasks: int
    proposed_tasks: list[ProposedTask]
    saved: bool = False
