"""Projects and Project Tasks API endpoints."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    ProjectTaskResponse,
    ProjectTaskListResponse,
    ProjectStatsResponse,
    ProjectDeleteResponse,
    ProjectTaskDeleteResponse,
    ProjectStatus,
    TaskStatus,
    ProjectPriority,
)

from app.services.project_service import (
    add_project,
    get_project,
    get_projects,
    modify_project,
    remove_project,
    add_project_task,
    get_project_task,
    get_project_tasks,
    modify_project_task,
    remove_project_task,
    project_statistics,
    ProjectNotFoundError,
    ProjectTaskNotFoundError,
    DuplicateProjectError,
    InvalidProjectDateError,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


# ==========================================
# PROJECT LISTING AND CREATION
# ==========================================


@router.get(
    "/",
    response_model=ProjectListResponse,
)
def list_user_projects(
    category: str | None = Query(
        default=None,
        max_length=100,
    ),
    status: ProjectStatus | None = None,
    priority: ProjectPriority | None = None,
    q: str | None = Query(
        default=None,
        max_length=200,
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List projects with filters and pagination."""

    return get_projects(
        db=db,
        category=category,
        status=status,
        priority=priority,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=201,
)
def create_user_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a project."""

    try:
        return add_project(db, payload)

    except DuplicateProjectError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


# ==========================================
# PROJECT STATISTICS
# ==========================================


@router.get(
    "/stats",
    response_model=ProjectStatsResponse,
)
def get_user_project_stats(
    db: Session = Depends(get_db),
):
    """Retrieve overall project statistics."""

    return project_statistics(db)


# ==========================================
# INDIVIDUAL PROJECT OPERATIONS
# ==========================================


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def retrieve_user_project(
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Retrieve project details and progress."""

    try:
        return get_project(db, project_id)

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_user_project(
    payload: ProjectUpdate,
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Partially update a project."""

    try:
        return modify_project(
            db=db,
            project_id=project_id,
            payload=payload,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except DuplicateProjectError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except InvalidProjectDateError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.delete(
    "/{project_id}",
    response_model=ProjectDeleteResponse,
)
def delete_user_project(
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Delete a project and its tasks."""

    try:
        return remove_project(db, project_id)

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


# ==========================================
# PROJECT TASK LISTING AND CREATION
# ==========================================


@router.post(
    "/{project_id}/tasks",
    response_model=ProjectTaskResponse,
    status_code=201,
)
def create_user_project_task(
    payload: ProjectTaskCreate,
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Create a task for a project."""

    try:
        return add_project_task(
            db=db,
            project_id=project_id,
            payload=payload,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.get(
    "/{project_id}/tasks",
    response_model=ProjectTaskListResponse,
)
def list_user_project_tasks(
    project_id: int = Path(..., ge=1),
    status: TaskStatus | None = None,
    priority: ProjectPriority | None = None,
    q: str | None = Query(
        default=None,
        max_length=250,
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List tasks belonging to a project."""

    try:
        return get_project_tasks(
            db=db,
            project_id=project_id,
            status=status,
            priority=priority,
            q=q,
            page=page,
            page_size=page_size,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


# ==========================================
# INDIVIDUAL TASK OPERATIONS
# ==========================================


@router.get(
    "/{project_id}/tasks/{task_id}",
    response_model=ProjectTaskResponse,
)
def retrieve_user_project_task(
    project_id: int = Path(..., ge=1),
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Retrieve an individual task."""

    try:
        return get_project_task(
            db=db,
            project_id=project_id,
            task_id=task_id,
        )

    except (
        ProjectNotFoundError,
        ProjectTaskNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.patch(
    "/{project_id}/tasks/{task_id}",
    response_model=ProjectTaskResponse,
)
def update_user_project_task(
    payload: ProjectTaskUpdate,
    project_id: int = Path(..., ge=1),
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Partially update a project task."""

    try:
        return modify_project_task(
            db=db,
            project_id=project_id,
            task_id=task_id,
            payload=payload,
        )

    except (
        ProjectNotFoundError,
        ProjectTaskNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.delete(
    "/{project_id}/tasks/{task_id}",
    response_model=ProjectTaskDeleteResponse,
)
def delete_user_project_task(
    project_id: int = Path(..., ge=1),
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """Delete an individual project task."""

    try:
        return remove_project_task(
            db=db,
            project_id=project_id,
            task_id=task_id,
        )

    except (
        ProjectNotFoundError,
        ProjectTaskNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error