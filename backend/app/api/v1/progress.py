
"""FastAPI endpoints for AI-Pulse Progress Tracking."""

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.progress import (
    GoalStatus,
    ProgressPriority,
    ActivityType,
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
from app.services import progress_service as service


router = APIRouter(
    prefix="/progress",
    tags=["Progress Tracking"],
)


# ==========================================
# SERVICE ERROR HANDLING
# ==========================================


def execute_service(function, *args, **kwargs):
    """Translate service exceptions into HTTP responses."""

    try:
        return function(*args, **kwargs)

    except (
        service.LearningGoalNotFoundError,
        service.ImplementationLogNotFoundError,
        service.ProgressReferenceNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except service.InvalidProgressDataError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# ==========================================
# PROGRESS STATISTICS
# ==========================================


@router.get(
    "/stats",
    response_model=ProgressStatsResponse,
    summary="Get overall progress statistics",
)
def get_progress_stats(
    db: Session = Depends(get_db),
):
    """Retrieve learning-goal and activity statistics."""

    return execute_service(
        service.progress_statistics,
        db,
    )


# ==========================================
# LEARNING GOAL ENDPOINTS
# ==========================================


@router.post(
    "/goals",
    response_model=LearningGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a learning goal",
)
def create_goal(
    payload: LearningGoalCreate,
    db: Session = Depends(get_db),
):
    """Create a learning goal with validation."""

    return execute_service(
        service.add_learning_goal,
        db,
        payload,
    )


@router.get(
    "/goals",
    response_model=LearningGoalListResponse,
    summary="List learning goals",
)
def list_goals(
    skill_id: int | None = Query(
        default=None,
        ge=1,
    ),
    status: GoalStatus | None = Query(
        default=None,
    ),
    priority: ProgressPriority | None = Query(
        default=None,
    ),
    q: str | None = Query(
        default=None,
        max_length=200,
    ),
    overdue_only: bool = Query(
        default=False,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    """Retrieve filtered and paginated learning goals."""

    return execute_service(
        service.get_learning_goals,
        db=db,
        skill_id=skill_id,
        status=status,
        priority=priority,
        q=q,
        overdue_only=overdue_only,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/goals/{goal_id}",
    response_model=LearningGoalResponse,
    summary="Get a learning goal",
)
def get_goal(
    goal_id: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    """Retrieve a learning goal by ID."""

    return execute_service(
        service.get_learning_goal,
        db,
        goal_id,
    )


@router.patch(
    "/goals/{goal_id}",
    response_model=LearningGoalResponse,
    summary="Update a learning goal",
)
def update_goal(
    payload: LearningGoalUpdate,
    goal_id: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    """Partially update a learning goal."""

    return execute_service(
        service.modify_learning_goal,
        db,
        goal_id,
        payload,
    )


@router.delete(
    "/goals/{goal_id}",
    response_model=LearningGoalDeleteResponse,
    summary="Delete a learning goal",
)
def delete_goal(
    goal_id: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    """Delete a learning goal."""

    return execute_service(
        service.remove_learning_goal,
        db,
        goal_id,
    )


# ==========================================
# IMPLEMENTATION LOG ENDPOINTS
# ==========================================


@router.post(
    "/logs",
    response_model=ImplementationLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an implementation log",
)
def create_log(
    payload: ImplementationLogCreate,
    db: Session = Depends(get_db),
):
    """Record learning or development activity."""

    return execute_service(
        service.add_implementation_log,
        db,
        payload,
    )


@router.get(
    "/logs",
    response_model=ImplementationLogListResponse,
    summary="List implementation logs",
)
def list_logs(
    project_id: int | None = Query(
        default=None,
        ge=1,
    ),
    goal_id: int | None = Query(
        default=None,
        ge=1,
    ),
    activity_type: ActivityType | None = Query(
        default=None,
    ),
    start_date: date | None = Query(
        default=None,
    ),
    end_date: date | None = Query(
        default=None,
    ),
    q: str | None = Query(
        default=None,
        max_length=200,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    """Retrieve filtered and paginated activity logs."""

    return execute_service(
        service.get_implementation_logs,
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


@router.get(
    "/logs/{log_id}",
    response_model=ImplementationLogResponse,
    summary="Get an implementation log",
)
def get_log(
    log_id: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    """Retrieve an implementation log by ID."""

    return execute_service(
        service.get_implementation_log,
        db,
        log_id,
    )


@router.patch(
    "/logs/{log_id}",
    response_model=ImplementationLogResponse,
    summary="Update an implementation log",
)
def update_log(
    payload: ImplementationLogUpdate,
    log_id: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    """Partially update an implementation log."""

    return execute_service(
        service.modify_implementation_log,
        db,
        log_id,
        payload,
    )


@router.delete(
    "/logs/{log_id}",
    response_model=ImplementationLogDeleteResponse,
    summary="Delete an implementation log",
)
def delete_log(
    log_id: int = Path(ge=1),
    db: Session = Depends(get_db),
):
    """Delete an implementation log."""

    return execute_service(
        service.remove_implementation_log,
        db,
        log_id,
    )
