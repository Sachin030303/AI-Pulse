"""Knowledge schemas placeholder."""
"""Schemas for the AI-Pulse Knowledge API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeArticle(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    summary: str | None
    category: str | None
    published_at: datetime | None
    relevance_score: float | None
    importance_level: str | None


class KnowledgeSearchResponse(BaseModel):
    query: str
    total: int
    page: int
    page_size: int
    pages: int
    items: list[KnowledgeArticle]


class KnowledgeTopic(BaseModel):
    category: str
    article_count: int


class KnowledgeTopicsResponse(BaseModel):
    total_topics: int
    topics: list[KnowledgeTopic]


class KnowledgeStatsResponse(BaseModel):
    total_articles: int
    classified_articles: int
    unclassified_articles: int
    articles_with_content: int
    articles_with_summary: int
    total_topics: int


class KnowledgeAskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
    )

    category: str | None = None

    max_sources: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class KnowledgeAskResponse(BaseModel):
    question: str
    answer: str
    model: str | None = None
    sources_used: int
    sources: list[KnowledgeArticle]