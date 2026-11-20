"""Business logic for Skills Management."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories import skill_repository
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse,
    SkillStatsResponse,
    SkillDeleteResponse,
)


class SkillNotFoundError(Exception):
    """Raised when a skill does not exist."""

    pass


class DuplicateSkillError(Exception):
    """Raised when a skill name already exists."""

    pass


def add_skill(
    db: Session,
    payload: SkillCreate,
) -> SkillResponse:
    """Create a new skill."""

    existing = skill_repository.get_skill_by_name(
        db,
        payload.name,
    )

    if existing is not None:
        raise DuplicateSkillError(
            f"Skill '{payload.name}' already exists."
        )

    try:
        skill = skill_repository.create_skill(
            db,
            payload,
        )

    except IntegrityError as error:
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise DuplicateSkillError(
                f"Skill '{payload.name}' already exists."
            ) from error

        raise

    return SkillResponse.model_validate(skill)


def get_skill(
    db: Session,
    skill_id: int,
) -> SkillResponse:
    """Retrieve a skill by ID."""

    skill = skill_repository.get_skill_by_id(
        db,
        skill_id,
    )

    if skill is None:
        raise SkillNotFoundError(
            f"Skill with ID {skill_id} was not found."
        )

    return SkillResponse.model_validate(skill)


def get_skills(
    db: Session,
    category: str | None = None,
    proficiency_level: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> SkillListResponse:
    """Retrieve paginated and filtered skills."""

    skills, total = skill_repository.list_skills(
        db=db,
        category=category,
        proficiency_level=proficiency_level,
        priority=priority,
        status=status,
        q=q,
        page=page,
        page_size=page_size,
    )

    return SkillListResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        items=[
            SkillResponse.model_validate(skill)
            for skill in skills
        ],
    )


def modify_skill(
    db: Session,
    skill_id: int,
    payload: SkillUpdate,
) -> SkillResponse:
    """Update an existing skill."""

    skill = skill_repository.get_skill_by_id(
        db,
        skill_id,
    )

    if skill is None:
        raise SkillNotFoundError(
            f"Skill with ID {skill_id} was not found."
        )

    if payload.name is not None:

        existing = skill_repository.get_skill_by_name(
            db,
            payload.name,
        )

        if existing is not None and existing.id != skill_id:
            raise DuplicateSkillError(
                f"Skill '{payload.name}' already exists."
            )

    try:
        skill = skill_repository.update_skill(
            db,
            skill,
            payload,
        )

    except IntegrityError as error:
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise DuplicateSkillError(
                "A skill with this name already exists."
            ) from error

        raise

    return SkillResponse.model_validate(skill)


def remove_skill(
    db: Session,
    skill_id: int,
) -> SkillDeleteResponse:
    """Delete an existing skill."""

    skill = skill_repository.get_skill_by_id(
        db,
        skill_id,
    )

    if skill is None:
        raise SkillNotFoundError(
            f"Skill with ID {skill_id} was not found."
        )

    skill_repository.delete_skill(
        db,
        skill,
    )

    return SkillDeleteResponse(
        message="Skill deleted successfully.",
        skill_id=skill_id,
    )


def skill_statistics(
    db: Session,
) -> SkillStatsResponse:
    """Retrieve overall skill statistics."""

    stats = skill_repository.get_skill_stats(db)

    return SkillStatsResponse(**stats)