"""Database operations for user skills."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import UserSkill
from app.schemas.skill import SkillCreate, SkillUpdate


def create_skill(
    db: Session,
    payload: SkillCreate,
) -> UserSkill:
    """Create a new skill."""

    skill = UserSkill(
        **payload.model_dump()
    )

    try:
        db.add(skill)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(skill)

    return skill


def get_skill_by_id(
    db: Session,
    skill_id: int,
) -> UserSkill | None:
    """Retrieve a skill by ID."""

    return db.get(UserSkill, skill_id)


def get_skill_by_name(
    db: Session,
    name: str,
) -> UserSkill | None:
    """Retrieve a skill by case-insensitive name."""

    statement = select(UserSkill).where(
        func.lower(UserSkill.name) == name.strip().lower()
    )

    return db.scalars(statement).first()


def list_skills(
    db: Session,
    category: str | None = None,
    proficiency_level: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[UserSkill], int]:
    """List skills with filtering and pagination."""

    filters = []

    if category:
        filters.append(
            func.lower(UserSkill.category)
            == category.strip().lower()
        )

    if proficiency_level:
        filters.append(
            UserSkill.proficiency_level == proficiency_level
        )

    if priority:
        filters.append(
            UserSkill.priority == priority
        )

    if status:
        filters.append(
            UserSkill.status == status
        )

    if q and q.strip():
        pattern = f"%{q.strip()}%"

        filters.append(
            or_(
                UserSkill.name.ilike(pattern),
                UserSkill.category.ilike(pattern),
                UserSkill.description.ilike(pattern),
            )
        )

    total = db.scalar(
        select(func.count())
        .select_from(UserSkill)
        .where(*filters)
    ) or 0

    statement = (
        select(UserSkill)
        .where(*filters)
        .order_by(
            UserSkill.created_at.desc(),
            UserSkill.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    skills = list(
        db.scalars(statement).all()
    )

    return skills, total


def update_skill(
    db: Session,
    skill: UserSkill,
    payload: SkillUpdate,
) -> UserSkill:
    """Partially update an existing skill."""

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(skill, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(skill)

    return skill


def delete_skill(
    db: Session,
    skill: UserSkill,
) -> None:
    """Delete an existing skill."""

    try:
        db.delete(skill)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_skill_stats(
    db: Session,
) -> dict:
    """Calculate overall skill statistics."""

    statement = select(
        func.count(UserSkill.id).label(
            "total_skills"
        ),

        func.count(UserSkill.id)
        .filter(UserSkill.status == "Not Started")
        .label("not_started"),

        func.count(UserSkill.id)
        .filter(UserSkill.status == "Learning")
        .label("learning"),

        func.count(UserSkill.id)
        .filter(UserSkill.status == "Practicing")
        .label("practicing"),

        func.count(UserSkill.id)
        .filter(UserSkill.status == "Mastered")
        .label("mastered"),

        func.avg(UserSkill.progress).label(
            "average_progress"
        ),

        func.count(UserSkill.id)
        .filter(UserSkill.priority == "High")
        .label("high_priority_skills"),
    )

    row = db.execute(statement).one()

    category_count = func.count(UserSkill.id)

    category_statement = (
        select(
            UserSkill.category,
            category_count.label("count"),
        )
        .group_by(UserSkill.category)
        .order_by(
            category_count.desc(),
            UserSkill.category.asc(),
        )
    )

    category_rows = db.execute(
        category_statement
    ).all()

    return {
        "total_skills": row.total_skills,
        "not_started": row.not_started,
        "learning": row.learning,
        "practicing": row.practicing,
        "mastered": row.mastered,
        "average_progress": round(
            float(row.average_progress or 0),
            2,
        ),
        "high_priority_skills": row.high_priority_skills,
        "categories": [
            {
                "category": item.category,
                "count": item.count,
            }
            for item in category_rows
        ],
    }