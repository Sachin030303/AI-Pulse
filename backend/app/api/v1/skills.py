"""Skills Management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse,
    SkillStatsResponse,
    SkillDeleteResponse,
    ProficiencyLevel,
    SkillPriority,
    SkillStatus,
)
from app.services.skill_service import (
    add_skill,
    get_skill,
    get_skills,
    modify_skill,
    remove_skill,
    skill_statistics,
    SkillNotFoundError,
    DuplicateSkillError,
)


router = APIRouter(
    prefix="/skills",
    tags=["Skills"],
)


@router.get(
    "/",
    response_model=SkillListResponse,
)
def list_user_skills(
    category: str | None = None,
    proficiency_level: ProficiencyLevel | None = None,
    priority: SkillPriority | None = None,
    status: SkillStatus | None = None,
    q: str | None = Query(default=None, max_length=150),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List and filter user skills."""

    return get_skills(
        db=db,
        category=category,
        proficiency_level=proficiency_level,
        priority=priority,
        status=status,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=SkillResponse,
    status_code=201,
)
def create_user_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
):
    """Create a new skill."""

    try:
        return add_skill(db, payload)

    except DuplicateSkillError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@router.get(
    "/stats",
    response_model=SkillStatsResponse,
)
def get_user_skill_stats(
    db: Session = Depends(get_db),
):
    """Retrieve learning statistics."""

    return skill_statistics(db)


@router.get(
    "/{skill_id}",
    response_model=SkillResponse,
)
def retrieve_user_skill(
    skill_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a skill by ID."""

    try:
        return get_skill(db, skill_id)

    except SkillNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.patch(
    "/{skill_id}",
    response_model=SkillResponse,
)
def update_user_skill(
    skill_id: int,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a skill."""

    try:
        return modify_skill(
            db,
            skill_id,
            payload,
        )

    except SkillNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except DuplicateSkillError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@router.delete(
    "/{skill_id}",
    response_model=SkillDeleteResponse,
)
def delete_user_skill(
    skill_id: int,
    db: Session = Depends(get_db),
):
    """Delete an existing skill."""

    try:
        return remove_skill(db, skill_id)

    except SkillNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error