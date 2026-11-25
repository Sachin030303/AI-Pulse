"""Explicit approval for proposed AI-Pulse project tasks."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.task_planning import ProposedTask


class TaskPlanApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(ge=1)
    tasks: list[ProposedTask] = Field(min_length=1, max_length=5)
    dry_run: bool = True
    approved: bool = False


class TaskPlanApplyResponse(BaseModel):
    status: Literal["dry_run", "created"]
    project_id: int
    project_name: str
    selected_count: int
    created_count: int
    created_task_ids: list[int]
    saved: bool
