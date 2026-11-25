
"""Read-only context retrieval for the AI-Pulse Chat API."""

import re
from datetime import datetime

from sqlalchemy import (
    and_,
    case,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.models import (
    Article,
    UserSkill,
    LearningGoal,
    Project,
)


# ==========================================
# CHAT SEARCH CONFIGURATION
# ==========================================

SEARCH_STOPWORDS = {
    "a", "an", "the", "and", "or", "but",
    "is", "are", "was", "were", "be",
    "been", "being", "to", "of", "in",
    "on", "at", "for", "from", "with",
    "by", "about", "as", "it", "its",
    "this", "that", "these", "those",
    "what", "which", "who", "when",
    "where", "why", "how", "can",
    "could", "would", "should", "do",
    "does", "did", "has", "have",
    "had", "will", "you", "your",
    "me", "my", "we", "our",
    "tell", "show", "give", "please",
    "latest", "recent", "today",
    "news", "update", "updates",
    "developments", "new", "explain",
}


# ==========================================
# INTERNAL HELPERS
# ==========================================

def extract_search_terms(
    query: str,
    max_terms: int = 6,
) -> list[str]:
    """Extract bounded, meaningful search keywords."""

    if max_terms < 1:
        raise ValueError(
            "max_terms must be positive."
        )

    tokens = re.findall(
        r"[a-z0-9]+(?:[-_.][a-z0-9]+)*",
        query.casefold(),
    )

    terms = []
    seen = set()

    for token in tokens:
        if len(token) < 2:
            continue

        if token in SEARCH_STOPWORDS:
            continue

        if token in seen:
            continue

        seen.add(token)
        terms.append(token)

        if len(terms) >= max_terms:
            break

    return terms


def validate_limit(
    limit: int,
    maximum: int,
) -> None:
    """Validate bounded retrieval limits."""

    if not 1 <= limit <= maximum:
        raise ValueError(
            f"Limit must be between 1 and {maximum}."
        )


def has_usable_article_text():
    """Require article content or a non-empty summary."""

    return or_(
        and_(
            Article.content.is_not(None),
            func.length(
                func.trim(Article.content)
            ) > 0,
        ),
        and_(
            Article.summary.is_not(None),
            func.length(
                func.trim(Article.summary)
            ) > 0,
        ),
    )


# ==========================================
# ARTICLE RETRIEVAL
# ==========================================

def get_chat_articles(
    db: Session,
    query: str,
    max_sources: int = 3,
    verified_only: bool = False,
    published_after: datetime | None = None,
) -> list[Article]:
    """
    Retrieve relevant articles for grounded chat responses.

    Articles are ranked by keyword matches:
        Title   = 5 points
        Summary = 2 points
        Content = 1 point

    More relevant matches rank first.
    Publication date breaks relevance ties.

    published_after optionally limits results to recent news.
    """

    validate_limit(max_sources, 5)

    if (
        published_after is not None
        and published_after.tzinfo is None
    ):
        raise ValueError(
            "published_after must be timezone-aware."
        )

    terms = extract_search_terms(query)

    if not terms:
        return []

    filters = [
        has_usable_article_text(),
    ]

    if verified_only:
        filters.append(
            Article.is_verified.is_(True)
        )

    if published_after is not None:
        filters.append(
            Article.published_at >= published_after
        )

    match_conditions = []
    score_parts = []

    for term in terms:
        # PostgreSQL word-boundary regex.
        # Escape user-supplied terms before passing them
        # to SQLAlchemy as bound query parameters.
        pattern = rf"\m{re.escape(term)}\M"

        title_match = Article.title.op("~*")(
            pattern
        )

        summary_match = Article.summary.op("~*")(
            pattern
        )

        content_match = Article.content.op("~*")(
            pattern
        )

        match_conditions.extend([
            title_match,
            summary_match,
            content_match,
        ])

        score_parts.append(
            case(
                (title_match, 5),
                else_=0,
            )
            +
            case(
                (summary_match, 2),
                else_=0,
            )
            +
            case(
                (content_match, 1),
                else_=0,
            )
        )

    relevance_score = sum(
        score_parts[1:],
        score_parts[0],
    )

    statement = (
        select(Article)
        .where(
            *filters,
            or_(*match_conditions),
        )
        .order_by(
            relevance_score.desc(),
            Article.published_at.desc().nulls_last(),
            Article.id.desc(),
        )
        .limit(max_sources)
    )

    return list(
        db.scalars(statement).all()
    )


# ==========================================
# SKILLS CONTEXT
# ==========================================

def get_chat_skills(
    db: Session,
    limit: int = 10,
) -> list[UserSkill]:
    """Retrieve skills for personalized chat context."""

    validate_limit(limit, 20)

    statement = (
        select(UserSkill)
        .order_by(
            UserSkill.updated_at.desc(),
            UserSkill.id.desc(),
        )
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


# ==========================================
# LEARNING GOALS CONTEXT
# ==========================================

def get_chat_learning_goals(
    db: Session,
    limit: int = 10,
) -> list[LearningGoal]:
    """Retrieve learning goals, prioritizing active goals."""

    validate_limit(limit, 20)

    status_order = case(
        (
            LearningGoal.status == "In Progress",
            0,
        ),
        (
            LearningGoal.status == "Not Started",
            1,
        ),
        (
            LearningGoal.status == "Paused",
            2,
        ),
        else_=3,
    )

    statement = (
        select(LearningGoal)
        .order_by(
            status_order.asc(),
            LearningGoal.updated_at.desc(),
            LearningGoal.id.desc(),
        )
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


# ==========================================
# PROJECT CONTEXT
# ==========================================

def get_chat_projects(
    db: Session,
    limit: int = 10,
) -> list[Project]:
    """Retrieve development projects, prioritizing active work."""

    validate_limit(limit, 20)

    status_order = case(
        (
            Project.status == "In Progress",
            0,
        ),
        (
            Project.status == "Not Started",
            1,
        ),
        else_=2,
    )

    statement = (
        select(Project)
        .order_by(
            status_order.asc(),
            Project.updated_at.desc(),
            Project.id.desc(),
        )
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )
