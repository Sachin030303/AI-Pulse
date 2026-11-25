"""Validate and explicitly approve selected project tasks."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project_task import ProjectTask
from app.repositories.project_repository import get_project_by_id
from app.schemas.project import ProjectTaskCreate
from app.schemas.task_plan_approval import (
    TaskPlanApplyRequest,
    TaskPlanApplyResponse,
)


class DuplicateTaskError(ValueError):
    """A selected task already exists or is repeated."""


def normalized_title(value: str) -> str:
    return " ".join(value.casefold().split())


def apply_task_plan(
    db: Session,
    payload: TaskPlanApplyRequest,
) -> TaskPlanApplyResponse:

    project = get_project_by_id(
        db,
        project_id=payload.project_id,
    )

    if project is None:
        raise LookupError("Project not found")

    project_name = project.name

    existing_titles = db.execute(
        select(ProjectTask.title).where(
            ProjectTask.project_id == payload.project_id
        )
    ).scalars().all()

    known = {
        normalized_title(title)
        for title in existing_titles
    }

    selected = set()

    # Reject duplicates before attempting any inserts.
    for task in payload.tasks:
        key = normalized_title(task.title)

        if not key:
            raise ValueError("Task title cannot be blank")

        if key in known:
            raise DuplicateTaskError(
                f"Task already exists: {task.title}"
            )

        if key in selected:
            raise DuplicateTaskError(
                f"Task selected more than once: {task.title}"
            )

        selected.add(key)

    # Dry-run is the default; no inserts or commits.
    if payload.dry_run:
        return TaskPlanApplyResponse(
            status="dry_run",
            project_id=payload.project_id,
            project_name=project_name,
            selected_count=len(payload.tasks),
            created_count=0,
            created_task_ids=[],
            saved=False,
        )

    # A real write requires explicit approval.
    if not payload.approved:
        raise ValueError(
            "Explicit approval is required to create tasks"
        )

    created = []

    try:
        for proposal in payload.tasks:
            validated = ProjectTaskCreate(
                title=proposal.title.strip(),
                description=proposal.description,
                status="Not Started",
                priority=proposal.priority,
            )

            record = ProjectTask(
                project_id=payload.project_id,
                **validated.model_dump(exclude_none=True),
            )

            db.add(record)
            created.append(record)

        # One transaction for all selected tasks.
        db.flush()

        created_ids = [
            task.id for task in created
        ]

        db.commit()

    except Exception:
        db.rollback()
        raise

    return TaskPlanApplyResponse(
        status="created",
        project_id=payload.project_id,
        project_name=project_name,
        selected_count=len(payload.tasks),
        created_count=len(created_ids),
        created_task_ids=created_ids,
        saved=True,
    )
