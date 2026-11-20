from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int | None
    title: str
    url: str
    summary: str | None
    category: str | None
    published_at: datetime | None
    relevance_score: float | None
    importance_level: str | None
    is_verified: bool
    created_at: datetime


class ArticleDetail(ArticleListItem):
    content: str | None


class ArticleListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[ArticleListItem]
