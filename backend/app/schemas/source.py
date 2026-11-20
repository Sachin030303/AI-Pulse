from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    url: str = Field(min_length=1, max_length=1000)
    source_type: str = Field(min_length=1, max_length=50)
    description: str | None = None
    is_active: bool = True


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    url: str | None = Field(default=None, min_length=1, max_length=1000)
    source_type: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    is_active: bool | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    source_type: str
    description: str | None
    is_active: bool
    last_fetched_at: datetime | None
    created_at: datetime


class SourceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[SourceResponse]
