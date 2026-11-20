from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import NewsSource
from app.schemas.source import (
    SourceCreate,
    SourceListResponse,
    SourceResponse,
    SourceUpdate,
)

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/", response_model=SourceListResponse)
def get_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    is_active: bool | None = None,
    q: str | None = Query(None, min_length=1, max_length=200),
    db: Session = Depends(get_db),
):
    filters = []

    if source_type:
        filters.append(NewsSource.source_type == source_type)

    if is_active is not None:
        filters.append(NewsSource.is_active == is_active)

    if q:
        search = f"%{q.strip()}%"
        filters.append(
            or_(
                NewsSource.name.ilike(search),
                NewsSource.url.ilike(search),
                NewsSource.description.ilike(search),
            )
        )

    total = db.scalar(
        select(func.count()).select_from(NewsSource).where(*filters)
    ) or 0

    statement = (
        select(NewsSource)
        .where(*filters)
        .order_by(NewsSource.created_at.desc(), NewsSource.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    sources = db.execute(statement).scalars().all()
    pages = (total + page_size - 1) // page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "items": sources,
    }


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(NewsSource, source_id)

    if source is None:
        raise HTTPException(status_code=404, detail="News source not found")

    return source


@router.post("/", response_model=SourceResponse, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = NewsSource(**payload.model_dump())
    db.add(source)

    try:
        db.commit()
        db.refresh(source)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A news source with this URL already exists",
        )

    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
):
    source = db.get(NewsSource, source_id)

    if source is None:
        raise HTTPException(status_code=404, detail="News source not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(source, field, value)

    try:
        db.commit()
        db.refresh(source)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A news source with this URL already exists",
        )

    return source
