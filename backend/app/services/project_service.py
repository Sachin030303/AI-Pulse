"""Business logic for Projects Management."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Project
from app.repositories import project_repository
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
)


# ==========================================
# CUSTOM EXCEPTIONS
# ==========================================


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist."""

    pass


class ProjectTaskNotFoundError(Exception):
    """Raised when a project task does not exist."""

    pass


class DuplicateProjectError(Exception):
    """Raised when a project name already exists."""

    pass


class InvalidProjectDateError(Exception):
    """Raised when project dates are invalid."""

    pass


# ==========================================
# INTERNAL HELPERS
# ==========================================


def require_project(
    db: Session,
    project_id: int,
) -> Project:
    """Retrieve a project or raise an exception."""

    project = project_repository.get_project_by_id(
        db,
        project_id,
    )

    if project is None:
        raise ProjectNotFoundError(
            f"Project with ID {project_id} was not found."
        )

    return project


def build_project_response(
    project: Project,
    progress: dict,
) -> ProjectResponse:
    """Combine project details with calculated progress."""

    project_data = {
        field: getattr(project, field)
        for field in ProjectCreate.model_fields
    }

    return ProjectResponse(
        **project_data,
        id=project.id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        **progress,
    )


def is_duplicate_error(
    error: IntegrityError,
) -> bool:
    """Identify PostgreSQL unique constraint violations."""

    error_code = (
        getattr(error.orig, "sqlstate", None)
        or getattr(error.orig, "pgcode", None)
    )

    return error_code == "23505"


# ==========================================
# PROJECT MANAGEMENT
# ==========================================


def add_project(
    db: Session,
    payload: ProjectCreate,
) -> ProjectResponse:
    """Create a new project."""

    existing = project_repository.get_project_by_name(
        db,
        payload.name,
    )

    if existing is not None:
        raise DuplicateProjectError(
            f"Project '{payload.name}' already exists."
        )

    try:
        project = project_repository.create_project(
            db,
            payload,
        )

    except IntegrityError as error:

        if is_duplicate_error(error):
            raise DuplicateProjectError(
                f"Project '{payload.name}' already exists."
            ) from error

        raise

    progress = project_repository.get_project_progress(
        db,
        [project.id],
    )[project.id]

    return build_project_response(
        project,
        progress,
    )


def get_project(
    db: Session,
    project_id: int,
) -> ProjectResponse:
    """Retrieve project details and progress."""

    project = require_project(
        db,
        project_id,
    )

    progress = project_repository.get_project_progress(
        db,
        [project_id],
    )[project_id]

    return build_project_response(
        project,
        progress,
    )


def get_projects(
    db: Session,
    category: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ProjectListResponse:
    """Retrieve filtered and paginated projects."""

    projects, total = project_repository.list_projects(
        db=db,
        category=category,
        status=status,
        priority=priority,
        q=q,
        page=page,
        page_size=page_size,
    )

    project_ids = [
        project.id
        for project in projects
    ]

    progress_map = project_repository.get_project_progress(
        db,
        project_ids,
    )

    return ProjectListResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        items=[
            build_project_response(
                project,
                progress_map[project.id],
            )
            for project in projects
        ],
    )


def modify_project(
    db: Session,
    project_id: int,
    payload: ProjectUpdate,
) -> ProjectResponse:
    """Update an existing project."""

    project = require_project(
        db,
        project_id,
    )

    update_data = payload.model_dump(
        exclude_unset=True
    )

    if payload.name is not None:

        existing = project_repository.get_project_by_name(
            db,
            payload.name,
        )

        if (
            existing is not None
            and existing.id != project_id
        ):
            raise DuplicateProjectError(
                f"Project '{payload.name}' already exists."
            )

    start_date = update_data.get(
        "start_date",
        project.start_date,
    )

    due_date = update_data.get(
        "due_date",
        project.due_date,
    )

    if (
        start_date is not None
        and due_date is not None
        and due_date < start_date
    ):
        raise InvalidProjectDateError(
            "Due date cannot be before start date."
        )

    try:
        project = project_repository.update_project(
            db,
            project,
            payload,
        )

    except IntegrityError as error:

        if is_duplicate_error(error):
            raise DuplicateProjectError(
                "A project with this name already exists."
            ) from error

        raise

    progress = project_repository.get_project_progress(
        db,
        [project_id],
    )[project_id]

    return build_project_response(
        project,
        progress,
    )


def remove_project(
    db: Session,
    project_id: int,
) -> ProjectDeleteResponse:
    """Delete a project and all associated tasks."""

    project = require_project(
        db,
        project_id,
    )

    project_repository.delete_project(
        db,
        project,
    )

    return ProjectDeleteResponse(
        message="Project and associated tasks deleted successfully.",
        project_id=project_id,
    )


# ==========================================
# PROJECT TASK MANAGEMENT
# ==========================================


def add_project_task(
    db: Session,
    project_id: int,
    payload: ProjectTaskCreate,
) -> ProjectTaskResponse:
    """Create a task for an existing project."""

    require_project(db, project_id)

    task = project_repository.create_task(
        db,
        project_id,
        payload,
    )

    return ProjectTaskResponse.model_validate(
        task
    )


def get_project_task(
    db: Session,
    project_id: int,
    task_id: int,
) -> ProjectTaskResponse:
    """Retrieve a specific project task."""

    require_project(db, project_id)

    task = project_repository.get_task_by_id(
        db,
        project_id,
        task_id,
    )

    if task is None:
        raise ProjectTaskNotFoundError(
            f"Task {task_id} was not found in project {project_id}."
        )

    return ProjectTaskResponse.model_validate(
        task
    )


def get_project_tasks(
    db: Session,
    project_id: int,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ProjectTaskListResponse:
    """Retrieve filtered and paginated project tasks."""

    require_project(db, project_id)

    tasks, total = project_repository.list_tasks(
        db=db,
        project_id=project_id,
        status=status,
        priority=priority,
        q=q,
        page=page,
        page_size=page_size,
    )

    return ProjectTaskListResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        items=[
            ProjectTaskResponse.model_validate(task)
            for task in tasks
        ],
    )


def modify_project_task(
    db: Session,
    project_id: int,
    task_id: int,
    payload: ProjectTaskUpdate,
) -> ProjectTaskResponse:
    """Update an existing project task."""

    require_project(db, project_id)

    task = project_repository.get_task_by_id(
        db,
        project_id,
        task_id,
    )

    if task is None:
        raise ProjectTaskNotFoundError(
            f"Task {task_id} was not found in project {project_id}."
        )

    task = project_repository.update_task(
        db,
        task,
        payload,
    )

    return ProjectTaskResponse.model_validate(
        task
    )


def remove_project_task(
    db: Session,
    project_id: int,
    task_id: int,
) -> ProjectTaskDeleteResponse:
    """Delete an individual project task."""

    require_project(db, project_id)

    task = project_repository.get_task_by_id(
        db,
        project_id,
        task_id,
    )

    if task is None:
        raise ProjectTaskNotFoundError(
            f"Task {task_id} was not found in project {project_id}."
        )

    project_repository.delete_task(
        db,
        task,
    )

    return ProjectTaskDeleteResponse(
        message="Project task deleted successfully.",
        project_id=project_id,
        task_id=task_id,
    )


# ==========================================
# PROJECT STATISTICS
# ==========================================


def project_statistics(
    db: Session,
) -> ProjectStatsResponse:
    """Retrieve overall project statistics."""

    stats = project_repository.get_project_stats(
        db
    )

    return ProjectStatsResponse(**stats)