from pydantic import BaseModel


class IngestionSourceResult(BaseModel):
    source: str
    fetched: int
    inserted: int
    skipped: int
    extraction_successful: int
    extraction_failed: int
    extraction_not_needed: int


class IngestionFailure(BaseModel):
    source_id: int
    error: str


class IngestionAllResult(BaseModel):
    total_sources: int
    successful: int
    failed: int
    results: list[IngestionSourceResult]
    failures: list[IngestionFailure]