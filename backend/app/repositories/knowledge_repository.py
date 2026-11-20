"""Database queries for the AI-Pulse Knowledge API."""

import re

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Article


STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "which", "who", "how", "why", "when",
    "where", "of", "to", "for", "in", "on",
    "and", "or", "with", "about", "me", "tell",
    "can", "you", "explain", "please",
}


def extract_keywords(query: str) -> list[str]:
    """Extract useful search terms from a query."""

    words = re.findall(r"\w+", query.lower())

    keywords = [
        word
        for word in words
        if word not in STOP_WORDS
    ]

    return list(dict.fromkeys(keywords or words))[:15]


def search_articles(
    db: Session,
    query: str,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Article], int]:
    """Search articles using weighted keyword matching."""

    keywords = extract_keywords(query)

    if not keywords:
        return [], 0

    conditions = []
    relevance = 0

    for keyword in keywords:
        pattern = f"%{keyword}%"

        title_match = Article.title.ilike(pattern)
        summary_match = Article.summary.ilike(pattern)
        content_match = Article.content.ilike(pattern)

        conditions.append(
            or_(
                title_match,
                summary_match,
                content_match,
            )
        )

        relevance = relevance + (
            case((title_match, 5), else_=0)
            + case((summary_match, 3), else_=0)
            + case((content_match, 1), else_=0)
        )

    filters = [or_(*conditions)]

    if category:
        filters.append(Article.category == category)

    total = db.scalar(
        select(func.count())
        .select_from(Article)
        .where(*filters)
    ) or 0

    statement = (
        select(Article)
        .where(*filters)
        .order_by(
            relevance.desc(),
            Article.relevance_score.desc().nulls_last(),
            Article.published_at.desc().nulls_last(),
            Article.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    articles = list(db.scalars(statement).all())

    return articles, total


def get_topics(db: Session) -> list[dict]:
    """Return article categories and their article counts."""

    article_count = func.count(Article.id)

    statement = (
        select(
            Article.category,
            article_count.label("article_count"),
        )
        .where(
            Article.category.is_not(None),
            func.trim(Article.category) != "",
        )
        .group_by(Article.category)
        .order_by(
            article_count.desc(),
            Article.category.asc(),
        )
    )

    rows = db.execute(statement).all()

    return [
        {
            "category": row.category,
            "article_count": row.article_count,
        }
        for row in rows
    ]


def get_knowledge_stats(db: Session) -> dict:
    """Calculate knowledge base statistics."""

    classified = (
        Article.category.is_not(None)
        & (func.trim(Article.category) != "")
    )

    statement = select(
        func.count(Article.id).label("total_articles"),

        func.count(Article.id)
        .filter(classified)
        .label("classified_articles"),

        func.count(Article.id)
        .filter(
            Article.content.is_not(None),
            func.trim(Article.content) != "",
        )
        .label("articles_with_content"),

        func.count(Article.id)
        .filter(
            Article.summary.is_not(None),
            func.trim(Article.summary) != "",
        )
        .label("articles_with_summary"),

        func.count(
            func.distinct(Article.category)
        )
        .filter(classified)
        .label("total_topics"),
    )

    row = db.execute(statement).one()

    return {
        "total_articles": row.total_articles,
        "classified_articles": row.classified_articles,
        "unclassified_articles": (
            row.total_articles - row.classified_articles
        ),
        "articles_with_content": row.articles_with_content,
        "articles_with_summary": row.articles_with_summary,
        "total_topics": row.total_topics,
    }