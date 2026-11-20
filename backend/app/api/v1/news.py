from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Article
from app.schemas.news import ArticleDetail, ArticleListResponse


router = APIRouter(prefix="/news", tags=["News"])


@router.get("/", response_model=ArticleListResponse)
def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    importance_level: str | None = None,
    q: str | None = Query(None, min_length=1, max_length=200),
    sort_by: Literal["published_at", "created_at"] = "published_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
):
    filters = []

    if category:
        filters.append(Article.category == category)

    if importance_level:
        filters.append(Article.importance_level == importance_level)

    if q:
        search = f"%{q.strip()}%"
        filters.append(
            or_(
                Article.title.ilike(search),
                Article.summary.ilike(search),
                Article.content.ilike(search),
            )
        )

    total = db.scalar(
        select(func.count()).select_from(Article).where(*filters)
    ) or 0

    order_column = (
        Article.published_at
        if sort_by == "published_at"
        else Article.created_at
    )

    ordering = (
        order_column.desc().nullslast()
        if sort_order == "desc"
        else order_column.asc().nullsfirst()
    )

    statement = (
        select(Article)
        .where(*filters)
        .order_by(ordering, Article.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    articles = db.execute(statement).scalars().all()
    pages = (total + page_size - 1) // page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "items": articles,
    }


@router.get("/{article_id}", response_model=ArticleDetail)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return article
