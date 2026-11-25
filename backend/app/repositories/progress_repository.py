
"""Database operations for Progress Tracking."""

from datetime import date
from datetime import date, datetime
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import LearningGoal, ImplementationLog

from app.schemas.progress import (
    LearningGoalCreate,
    LearningGoalUpdate,
    ImplementationLogCreate,
    ImplementationLogUpdate,
)


# ==========================================
# TRANSACTION MANAGEMENT
# ==========================================


def commit_changes(db: Session) -> None:
    """Commit changes safely."""

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


# ==========================================
# LEARNING GOAL CRUD
# ==========================================



def create_learning_goal(
    db: Session,
    payload: LearningGoalCreate,
    completed_at: datetime | None = None,
) -> LearningGoal:
    """Create a goal and its completion time atomically."""

    goal = LearningGoal(
        **payload.model_dump(),
        completed_at=completed_at,
    )

    db.add(goal)
    commit_changes(db)
    db.refresh(goal)

    return goal



def get_learning_goal_by_id(
    db: Session,
    goal_id: int,
) -> LearningGoal | None:
    """Retrieve a learning goal by ID."""

    return db.get(LearningGoal, goal_id)


def list_learning_goals(
    db: Session,
    skill_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    overdue_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[LearningGoal], int]:
    """List learning goals with filters and pagination."""

    filters = []

    if skill_id is not None:
        filters.append(
            LearningGoal.skill_id == skill_id
        )

    if status:
        filters.append(
            LearningGoal.status == status
        )

    if priority:
        filters.append(
            LearningGoal.priority == priority
        )

    if q and q.strip():
        keyword = q.strip()

        filters.append(
            or_(
                LearningGoal.title.icontains(
                    keyword,
                    autoescape=True,
                ),
                LearningGoal.description.icontains(
                    keyword,
                    autoescape=True,
                ),
            )
        )

    if overdue_only:
        filters.extend([
            LearningGoal.target_date < date.today(),
            LearningGoal.status != "Completed",
        ])

    total = db.scalar(
        select(func.count())
        .select_from(LearningGoal)
        .where(*filters)
    ) or 0

    statement = (
        select(LearningGoal)
        .where(*filters)
        .order_by(
            LearningGoal.created_at.desc(),
            LearningGoal.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    goals = list(
        db.scalars(statement).all()
    )

    return goals, total


def update_learning_goal(
    db: Session,
    goal: LearningGoal,
    payload: LearningGoalUpdate,
) -> LearningGoal:
    """Partially update a learning goal."""

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(goal, field, value)

    commit_changes(db)
    db.refresh(goal)

    return goal


def delete_learning_goal(
    db: Session,
    goal: LearningGoal,
) -> None:
    """Delete a learning goal."""

    db.delete(goal)
    commit_changes(db)


# ==========================================
# IMPLEMENTATION LOG CRUD
# ==========================================


def create_implementation_log(
    db: Session,
    payload: ImplementationLogCreate,
) -> ImplementationLog:
    """Create a development activity log."""

    log = ImplementationLog(
        **payload.model_dump()
    )

    db.add(log)
    commit_changes(db)
    db.refresh(log)

    return log


def get_implementation_log_by_id(
    db: Session,
    log_id: int,
) -> ImplementationLog | None:
    """Retrieve an activity log by ID."""

    return db.get(ImplementationLog, log_id)


def list_implementation_logs(
    db: Session,
    project_id: int | None = None,
    goal_id: int | None = None,
    activity_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ImplementationLog], int]:
    """List activity logs with filters and pagination."""

    filters = []

    if project_id is not None:
        filters.append(
            ImplementationLog.project_id == project_id
        )

    if goal_id is not None:
        filters.append(
            ImplementationLog.goal_id == goal_id
        )

    if activity_type:
        filters.append(
            ImplementationLog.activity_type == activity_type
        )

    if start_date is not None:
        filters.append(
            ImplementationLog.activity_date >= start_date
        )

    if end_date is not None:
        filters.append(
            ImplementationLog.activity_date <= end_date
        )

    if q and q.strip():
        keyword = q.strip()

        filters.append(
            or_(
                ImplementationLog.title.icontains(
                    keyword,
                    autoescape=True,
                ),
                ImplementationLog.description.icontains(
                    keyword,
                    autoescape=True,
                ),
            )
        )

    total = db.scalar(
        select(func.count())
        .select_from(ImplementationLog)
        .where(*filters)
    ) or 0

    statement = (
        select(ImplementationLog)
        .where(*filters)
        .order_by(
            ImplementationLog.activity_date.desc(),
            ImplementationLog.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    logs = list(
        db.scalars(statement).all()
    )

    return logs, total


def update_implementation_log(
    db: Session,
    log: ImplementationLog,
    payload: ImplementationLogUpdate,
) -> ImplementationLog:
    """Partially update an activity log."""

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(log, field, value)

    commit_changes(db)
    db.refresh(log)

    return log


def delete_implementation_log(
    db: Session,
    log: ImplementationLog,
) -> None:
    """Delete a development activity log."""

    db.delete(log)
    commit_changes(db)


# ==========================================
# PROGRESS STATISTICS
# ==========================================


def get_progress_stats(
    db: Session,
) -> dict:
    """Calculate learning and activity statistics."""

    today = date.today()

    # --------------------------------------
    # Learning goal statistics
    # --------------------------------------

    goal_statement = select(
        func.count(LearningGoal.id)
        .label("total_goals"),

        func.count(LearningGoal.id)
        .filter(
            LearningGoal.status == "Not Started"
        )
        .label("not_started"),

        func.count(LearningGoal.id)
        .filter(
            LearningGoal.status == "In Progress"
        )
        .label("in_progress"),

        func.count(LearningGoal.id)
        .filter(
            LearningGoal.status == "Completed"
        )
        .label("completed"),

        func.count(LearningGoal.id)
        .filter(
            LearningGoal.status == "Paused"
        )
        .label("paused"),

        func.count(LearningGoal.id)
        .filter(
            LearningGoal.target_date < today,
            LearningGoal.status != "Completed",
        )
        .label("overdue_goals"),

        func.avg(LearningGoal.progress)
        .label("average_goal_progress"),
    )

    goal_row = db.execute(
        goal_statement
    ).one()

    # --------------------------------------
    # Activity log statistics
    # --------------------------------------

    log_statement = select(
        func.count(ImplementationLog.id)
        .label("total_logs"),

        func.coalesce(
            func.sum(
                ImplementationLog.duration_minutes
            ),
            0,
        )
        .label("total_minutes"),
    )

    log_row = db.execute(
        log_statement
    ).one()

    total_minutes = int(
        log_row.total_minutes
    )

    total_hours = round(
        total_minutes / 60,
        2,
    )

    # --------------------------------------
    # Activity breakdown by type
    # --------------------------------------

    activity_count = func.count(
        ImplementationLog.id
    )

    activity_duration = func.sum(
        ImplementationLog.duration_minutes
    )

    activity_statement = (
        select(
            ImplementationLog.activity_type,

            activity_count.label("count"),

            activity_duration.label(
                "duration_minutes"
            ),
        )
        .group_by(
            ImplementationLog.activity_type
        )
        .order_by(
            activity_duration.desc(),
            ImplementationLog.activity_type.asc(),
        )
    )

    activity_rows = db.execute(
        activity_statement
    ).all()

    activity_by_type = [
        {
            "activity_type": row.activity_type,
            "count": row.count,
            "duration_minutes": (
                row.duration_minutes
            ),
        }
        for row in activity_rows
    ]

    return {
        "total_goals": goal_row.total_goals,
        "not_started": goal_row.not_started,
        "in_progress": goal_row.in_progress,
        "completed": goal_row.completed,
        "paused": goal_row.paused,
        "overdue_goals": goal_row.overdue_goals,

        "average_goal_progress": round(
            float(
                goal_row.average_goal_progress or 0
            ),
            2,
        ),

        "total_logs": log_row.total_logs,
        "total_minutes": total_minutes,
        "total_hours": total_hours,

        "activity_by_type": activity_by_type,
    }
