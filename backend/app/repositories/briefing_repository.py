
"""Read-only article retrieval for AI-Pulse Briefings."""

from datetime import datetime

from sqlalchemy import (
    and_,
    case,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.models import Article


def _has_usable_text():
    """Require non-empty article content or summary."""

    return or_(
        and_(
            Article.content.is_not(None),
            func.length(func.trim(Article.content)) > 0,
        ),
        and_(
            Article.summary.is_not(None),
            func.length(func.trim(Article.summary)) > 0,
        ),
    )


def _focus_score(focus: str):
    """Prioritize matching titles, then summaries and content."""

    return case(
        (
            Article.title.icontains(
                focus,
                autoescape=True,
            ),
            3,
        ),
        (
            Article.summary.icontains(
                focus,
                autoescape=True,
            ),
            2,
        ),
        (
            Article.content.icontains(
                focus,
                autoescape=True,
            ),
            1,
        ),
        else_=0,
    )


def select_briefing_articles(
    db: Session,
    window_start: datetime,
    window_end: datetime,
    max_articles: int = 5,
    category: str | None = None,
    focus: str | None = None,
    verified_only: bool = False,
) -> tuple[list[Article], int]:
    """
    Retrieve articles eligible for a news briefing.

    Returns:
        articles: Selected Article ORM objects.
        total: Total eligible articles before the limit.

    The function performs read-only SQL queries.
    """

    if (
        window_start.tzinfo is None
        or window_end.tzinfo is None
    ):
        raise ValueError(
            "Briefing window datetimes must be timezone-aware."
        )

    if window_end < window_start:
        raise ValueError(
            "Briefing window end cannot precede its start."
        )

    if not 1 <= max_articles <= 10:
        raise ValueError(
            "max_articles must be between 1 and 10."
        )

    filters = [
        Article.published_at >= window_start,
        Article.published_at <= window_end,
        _has_usable_text(),
    ]

    # Exact category matching, ignoring case and surrounding spaces.
    if category is not None and category.strip():
        filters.append(
            func.lower(
                func.trim(Article.category)
            ) == category.strip().lower()
        )

    # Only include explicitly verified records when requested.
    if verified_only:
        filters.append(
            Article.is_verified.is_(True)
        )

    # Count all eligible articles before limiting results.
    count_statement = (
        select(func.count())
        .select_from(Article)
        .where(*filters)
    )

    total = db.scalar(count_statement) or 0

    statement = select(Article).where(*filters)

    ordering = []

    # Focus is a ranking preference, not a strict filter.
    # If no focus matches exist, recent articles remain eligible.
    if focus is not None and focus.strip():
        ordering.append(
            _focus_score(focus.strip()).desc()
        )

    # Prefer recently published material.
    ordering.append(
        Article.published_at.desc()
    )

    # Use available relevance scores as a secondary signal.
    ordering.append(
        func.coalesce(
            Article.relevance_score,
            0.0,
        ).desc()
    )

    # Deterministic ordering for equally ranked articles.
    ordering.append(
        Article.id.desc()
    )

    statement = (
        statement
        .order_by(*ordering)
        .limit(max_articles)
    )

    articles = list(
        db.scalars(statement).all()
    )

    return articles, total
