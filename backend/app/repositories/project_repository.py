"""Database operations for projects and project tasks."""

from datetime import date, datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Project, ProjectTask
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectTaskCreate,
    ProjectTaskUpdate,
)


# ==========================================
# TRANSACTION HELPERS
# ==========================================


def commit_changes(db: Session) -> None:
    """Commit database changes with rollback protection."""

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


# ==========================================
# PROJECT CRUD OPERATIONS
# ==========================================


def create_project(
    db: Session,
    payload: ProjectCreate,
) -> Project:
    """Create a new project."""

    project = Project(**payload.model_dump())

    db.add(project)

    commit_changes(db)

    db.refresh(project)

    return project


def get_project_by_id(
    db: Session,
    project_id: int,
) -> Project | None:
    """Retrieve a project by ID."""

    return db.get(Project, project_id)


def get_project_by_name(
    db: Session,
    name: str,
) -> Project | None:
    """Retrieve a project by case-insensitive name."""

    statement = select(Project).where(
        func.lower(Project.name) == name.strip().lower()
    )

    return db.scalars(statement).first()


def list_projects(
    db: Session,
    category: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Project], int]:
    """List projects with filtering and pagination."""

    filters = []

    if category:
        filters.append(
            func.lower(Project.category)
            == category.strip().lower()
        )

    if status:
        filters.append(Project.status == status)

    if priority:
        filters.append(Project.priority == priority)

    if q and q.strip():
        keyword = q.strip()

        filters.append(
            or_(
                Project.name.icontains(
                    keyword,
                    autoescape=True,
                ),
                Project.description.icontains(
                    keyword,
                    autoescape=True,
                ),
                Project.category.icontains(
                    keyword,
                    autoescape=True,
                ),
            )
        )

    total = db.scalar(
        select(func.count())
        .select_from(Project)
        .where(*filters)
    ) or 0

    statement = (
        select(Project)
        .where(*filters)
        .order_by(
            Project.created_at.desc(),
            Project.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    projects = list(db.scalars(statement).all())

    return projects, total


def update_project(
    db: Session,
    project: Project,
    payload: ProjectUpdate,
) -> Project:
    """Partially update a project."""

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(project, field, value)

    commit_changes(db)

    db.refresh(project)

    return project


def delete_project(
    db: Session,
    project: Project,
) -> None:
    """Delete a project and its associated tasks."""

    db.delete(project)

    commit_changes(db)


# ==========================================
# PROJECT TASK CRUD OPERATIONS
# ==========================================


def create_task(
    db: Session,
    project_id: int,
    payload: ProjectTaskCreate,
) -> ProjectTask:
    """Create a task for an existing project."""

    task = ProjectTask(
        project_id=project_id,
        **payload.model_dump(),
    )

    if task.status == "Completed":
        task.completed_at = datetime.now(timezone.utc)

    db.add(task)

    commit_changes(db)

    db.refresh(task)

    return task


def get_task_by_id(
    db: Session,
    project_id: int,
    task_id: int,
) -> ProjectTask | None:
    """Retrieve a task belonging to a specific project."""

    statement = select(ProjectTask).where(
        ProjectTask.id == task_id,
        ProjectTask.project_id == project_id,
    )

    return db.scalar(statement)


def list_tasks(
    db: Session,
    project_id: int,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ProjectTask], int]:
    """List tasks belonging to a project."""

    filters = [
        ProjectTask.project_id == project_id
    ]

    if status:
        filters.append(
            ProjectTask.status == status
        )

    if priority:
        filters.append(
            ProjectTask.priority == priority
        )

    if q and q.strip():
        keyword = q.strip()

        filters.append(
            or_(
                ProjectTask.title.icontains(
                    keyword,
                    autoescape=True,
                ),
                ProjectTask.description.icontains(
                    keyword,
                    autoescape=True,
                ),
            )
        )

    total = db.scalar(
        select(func.count())
        .select_from(ProjectTask)
        .where(*filters)
    ) or 0

    statement = (
        select(ProjectTask)
        .where(*filters)
        .order_by(
            ProjectTask.created_at.desc(),
            ProjectTask.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    tasks = list(db.scalars(statement).all())

    return tasks, total


def update_task(
    db: Session,
    task: ProjectTask,
    payload: ProjectTaskUpdate,
) -> ProjectTask:
    """Update a task and manage its completion timestamp."""

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(task, field, value)

    if task.status == "Completed":
        if task.completed_at is None:
            task.completed_at = datetime.now(
                timezone.utc
            )
    else:
        task.completed_at = None

    commit_changes(db)

    db.refresh(task)

    return task


def delete_task(
    db: Session,
    task: ProjectTask,
) -> None:
    """Delete an individual project task."""

    db.delete(task)

    commit_changes(db)


# ==========================================
# AUTOMATIC PROJECT PROGRESS
# ==========================================


def get_project_progress(
    db: Session,
    project_ids: list[int],
) -> dict[int, dict]:
    """Calculate task-based progress for multiple projects."""

    if not project_ids:
        return {}

    results = {
        project_id: {
            "total_tasks": 0,
            "completed_tasks": 0,
            "progress": 0.0,
        }
        for project_id in project_ids
    }

    statement = (
        select(
            ProjectTask.project_id,

            func.count(ProjectTask.id)
            .label("total_tasks"),

            func.count(ProjectTask.id)
            .filter(
                ProjectTask.status == "Completed"
            )
            .label("completed_tasks"),
        )
        .where(
            ProjectTask.project_id.in_(project_ids)
        )
        .group_by(ProjectTask.project_id)
    )

    rows = db.execute(statement).all()

    for row in rows:

        total = row.total_tasks
        completed = row.completed_tasks

        progress = (
            round(completed / total * 100, 2)
            if total
            else 0.0
        )

        results[row.project_id] = {
            "total_tasks": total,
            "completed_tasks": completed,
            "progress": progress,
        }

    return results


# ==========================================
# PROJECT STATISTICS
# ==========================================


def get_project_stats(
    db: Session,
) -> dict:
    """Calculate overall project and task statistics."""

    today = date.today()

    project_statement = select(
        func.count(Project.id)
        .label("total_projects"),

        func.count(Project.id)
        .filter(Project.status == "Not Started")
        .label("not_started"),

        func.count(Project.id)
        .filter(Project.status == "In Progress")
        .label("in_progress"),

        func.count(Project.id)
        .filter(Project.status == "Completed")
        .label("completed"),

        func.count(Project.id)
        .filter(Project.status == "On Hold")
        .label("on_hold"),

        func.count(Project.id)
        .filter(Project.status == "Cancelled")
        .label("cancelled"),

        func.count(Project.id)
        .filter(
            Project.due_date < today,
            Project.status.notin_(
                ["Completed", "Cancelled"]
            ),
        )
        .label("overdue_projects"),
    )

    project_row = db.execute(
        project_statement
    ).one()

    task_statement = (
        select(
            func.count(ProjectTask.id)
            .label("total_tasks"),

            func.count(ProjectTask.id)
            .filter(
                ProjectTask.status == "Completed"
            )
            .label("completed_tasks"),

            func.count(ProjectTask.id)
            .filter(
                ProjectTask.status == "Blocked"
            )
            .label("blocked_tasks"),

            func.count(ProjectTask.id)
            .filter(
                ProjectTask.due_date < today,
                ProjectTask.status != "Completed",
                Project.status.notin_(
                    ["Completed", "Cancelled"]
                ),
            )
            .label("overdue_tasks"),
        )
        .select_from(ProjectTask)
        .join(
            Project,
            Project.id == ProjectTask.project_id,
        )
    )

    task_row = db.execute(
        task_statement
    ).one()

    total_tasks = task_row.total_tasks

    completed_tasks = task_row.completed_tasks

    overall_progress = (
        round(
            completed_tasks / total_tasks * 100,
            2,
        )
        if total_tasks
        else 0.0
    )

    category_count = func.count(Project.id)

    category_statement = (
        select(
            Project.category,
            category_count.label("count"),
        )
        .group_by(Project.category)
        .order_by(
            category_count.desc(),
            Project.category.asc(),
        )
    )

    category_rows = db.execute(
        category_statement
    ).all()

    return {
        "total_projects": project_row.total_projects,
        "not_started": project_row.not_started,
        "in_progress": project_row.in_progress,
        "completed": project_row.completed,
        "on_hold": project_row.on_hold,
        "cancelled": project_row.cancelled,

        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,

        "pending_tasks": (
            total_tasks - completed_tasks
        ),

        "blocked_tasks": task_row.blocked_tasks,

        "overdue_projects": project_row.overdue_projects,
        "overdue_tasks": task_row.overdue_tasks,

        "overall_progress": overall_progress,

        "categories": [
            {
                "category": row.category,
                "count": row.count,
            }
            for row in category_rows
        ],
    }