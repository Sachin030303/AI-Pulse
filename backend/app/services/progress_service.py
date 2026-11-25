
"""Business logic for AI-Pulse Progress Tracking."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models import UserSkill, Project
from app.repositories import progress_repository as repo
from app.schemas.progress import (
    LearningGoalCreate,
    LearningGoalUpdate,
    LearningGoalResponse,
    LearningGoalListResponse,
    LearningGoalDeleteResponse,
    ImplementationLogCreate,
    ImplementationLogUpdate,
    ImplementationLogResponse,
    ImplementationLogListResponse,
    ImplementationLogDeleteResponse,
    ProgressStatsResponse,
)


# ==========================================
# CUSTOM EXCEPTIONS
# ==========================================


class LearningGoalNotFoundError(Exception):
    """Requested learning goal does not exist."""


class ImplementationLogNotFoundError(Exception):
    """Requested implementation log does not exist."""


class ProgressReferenceNotFoundError(Exception):
    """A referenced skill, project or goal is missing."""


class InvalidProgressDataError(Exception):
    """Progress data violates a business rule."""


# ==========================================
# INTERNAL VALIDATION HELPERS
# ==========================================


def require_goal(db: Session, goal_id: int):
    goal = repo.get_learning_goal_by_id(db, goal_id)

    if goal is None:
        raise LearningGoalNotFoundError(
            f"Learning goal {goal_id} was not found."
        )

    return goal


def require_log(db: Session, log_id: int):
    log = repo.get_implementation_log_by_id(db, log_id)

    if log is None:
        raise ImplementationLogNotFoundError(
            f"Implementation log {log_id} was not found."
        )

    return log


def validate_skill(db: Session, skill_id: int | None):
    if skill_id is not None and db.get(UserSkill, skill_id) is None:
        raise ProgressReferenceNotFoundError(
            f"Skill {skill_id} was not found."
        )


def validate_project(db: Session, project_id: int | None):
    if project_id is not None and db.get(Project, project_id) is None:
        raise ProgressReferenceNotFoundError(
            f"Project {project_id} was not found."
        )


def validate_goal_reference(db: Session, goal_id: int | None):
    if goal_id is not None:
        require_goal(db, goal_id)


def validate_dates(
    start_date: date | None,
    target_date: date | None,
):
    if (
        start_date is not None
        and target_date is not None
        and target_date < start_date
    ):
        raise InvalidProgressDataError(
            "Target date cannot be before start date."
        )


def normalize_goal_state(
    data: dict,
    current_goal=None,
) -> dict:
    """Keep goal status, progress and completion time consistent."""

    data = data.copy()

    old_status = (
        current_goal.status
        if current_goal is not None
        else "Not Started"
    )

    old_progress = (
        current_goal.progress
        if current_goal is not None
        else 0
    )

    status = data.get("status", old_status)
    progress = data.get("progress", old_progress)

    status_explicit = "status" in data
    progress_explicit = "progress" in data

    if status == "Completed":
        if progress_explicit and progress != 100:
            raise InvalidProgressDataError(
                "A completed goal must have 100% progress."
            )

        data["progress"] = 100

        if (
            current_goal is None
            or old_status != "Completed"
            or current_goal.completed_at is None
        ):
            data["completed_at"] = datetime.now(timezone.utc)

    else:
        if progress == 100:
            if status_explicit:
                raise InvalidProgressDataError(
                    "Only a completed goal can have 100% progress."
                )

            data["status"] = "Completed"
            data["completed_at"] = datetime.now(timezone.utc)

        else:
            if status == "Not Started" and progress > 0:
                if status_explicit:
                    raise InvalidProgressDataError(
                        "A not-started goal must have 0% progress."
                    )

                data["status"] = "In Progress"

            elif status == "In Progress" and progress == 0:
                if status_explicit:
                    raise InvalidProgressDataError(
                        "An in-progress goal must have progress above 0%."
                    )

                data["status"] = "Not Started"

            if old_status == "Completed":
                data["completed_at"] = None

    return data


# ==========================================
# LEARNING GOAL MANAGEMENT
# ==========================================


def add_learning_goal(
    db: Session,
    payload: LearningGoalCreate,
) -> LearningGoalResponse:

    validate_skill(db, payload.skill_id)

    validate_dates(
        payload.start_date,
        payload.target_date,
    )

    data = normalize_goal_state(
    payload.model_dump(exclude_unset=True)
    )

    normalized_payload = LearningGoalCreate(
        **{
            key: value
            for key, value in data.items()
            if key in LearningGoalCreate.model_fields
        }
    )

    
    goal = repo.create_learning_goal(
        db,
        normalized_payload,
        completed_at=data.get("completed_at"),
    )

    return LearningGoalResponse.model_validate(goal)


    # The repository's create schema excludes completed_at.
    # Persist it separately for initially completed goals.
    if "completed_at" in data:
        goal.completed_at = data["completed_at"]
        repo.commit_changes(db)
        db.refresh(goal)

    return LearningGoalResponse.model_validate(goal)


def get_learning_goal(
    db: Session,
    goal_id: int,
) -> LearningGoalResponse:

    return LearningGoalResponse.model_validate(
        require_goal(db, goal_id)
    )


def get_learning_goals(
    db: Session,
    skill_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    overdue_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> LearningGoalListResponse:

    if page < 1 or not 1 <= page_size <= 100:
        raise InvalidProgressDataError(
            "Page must be >= 1 and page_size must be 1-100."
        )

    goals, total = repo.list_learning_goals(
        db=db,
        skill_id=skill_id,
        status=status,
        priority=priority,
        q=q,
        overdue_only=overdue_only,
        page=page,
        page_size=page_size,
    )

    return LearningGoalListResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        items=[
            LearningGoalResponse.model_validate(goal)
            for goal in goals
        ],
    )


def modify_learning_goal(
    db: Session,
    goal_id: int,
    payload: LearningGoalUpdate,
) -> LearningGoalResponse:

    goal = require_goal(db, goal_id)

    data = payload.model_dump(exclude_unset=True)

    if "skill_id" in data:
        validate_skill(db, data["skill_id"])

    validate_dates(
        data.get("start_date", goal.start_date),
        data.get("target_date", goal.target_date),
    )

    data = normalize_goal_state(data, goal)

    completed_at = data.pop("completed_at", None)
    should_update_completion = (
        "status" in data
        or "progress" in data
    )

    normalized_payload = LearningGoalUpdate(**data)

    if should_update_completion:
        # Preserve the current completion time when a completed
        # goal is edited without changing its completion state.
        if data.get("status", goal.status) == "Completed":
            goal.completed_at = (
                completed_at
                if completed_at is not None
                else goal.completed_at
            )
        else:
            goal.completed_at = None

    goal = repo.update_learning_goal(
        db,
        goal,
        normalized_payload,
    )

    return LearningGoalResponse.model_validate(goal)


def remove_learning_goal(
    db: Session,
    goal_id: int,
) -> LearningGoalDeleteResponse:

    goal = require_goal(db, goal_id)

    repo.delete_learning_goal(db, goal)

    return LearningGoalDeleteResponse(
        message="Learning goal deleted successfully.",
        goal_id=goal_id,
    )


# ==========================================
# IMPLEMENTATION LOG MANAGEMENT
# ==========================================


def add_implementation_log(
    db: Session,
    payload: ImplementationLogCreate,
) -> ImplementationLogResponse:

    validate_project(db, payload.project_id)
    validate_goal_reference(db, payload.goal_id)

    log = repo.create_implementation_log(
        db,
        payload,
    )

    return ImplementationLogResponse.model_validate(log)


def get_implementation_log(
    db: Session,
    log_id: int,
) -> ImplementationLogResponse:

    return ImplementationLogResponse.model_validate(
        require_log(db, log_id)
    )


def get_implementation_logs(
    db: Session,
    project_id: int | None = None,
    goal_id: int | None = None,
    activity_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ImplementationLogListResponse:

    if page < 1 or not 1 <= page_size <= 100:
        raise InvalidProgressDataError(
            "Page must be >= 1 and page_size must be 1-100."
        )

    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):
        raise InvalidProgressDataError(
            "End date cannot be before start date."
        )

    logs, total = repo.list_implementation_logs(
        db=db,
        project_id=project_id,
        goal_id=goal_id,
        activity_type=activity_type,
        start_date=start_date,
        end_date=end_date,
        q=q,
        page=page,
        page_size=page_size,
    )

    return ImplementationLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        items=[
            ImplementationLogResponse.model_validate(log)
            for log in logs
        ],
    )


def modify_implementation_log(
    db: Session,
    log_id: int,
    payload: ImplementationLogUpdate,
) -> ImplementationLogResponse:

    log = require_log(db, log_id)

    data = payload.model_dump(exclude_unset=True)

    if "project_id" in data:
        validate_project(db, data["project_id"])

    if "goal_id" in data:
        validate_goal_reference(db, data["goal_id"])

    log = repo.update_implementation_log(
        db,
        log,
        payload,
    )

    return ImplementationLogResponse.model_validate(log)


def remove_implementation_log(
    db: Session,
    log_id: int,
) -> ImplementationLogDeleteResponse:

    log = require_log(db, log_id)

    repo.delete_implementation_log(db, log)

    return ImplementationLogDeleteResponse(
        message="Implementation log deleted successfully.",
        log_id=log_id,
    )


# ==========================================
# OVERALL STATISTICS
# ==========================================


def progress_statistics(
    db: Session,
) -> ProgressStatsResponse:

    stats = repo.get_progress_stats(db)

    return ProgressStatsResponse(**stats)
