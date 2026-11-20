from fastapi import APIRouter, HTTPException

from app.schemas.ingestion import (
    IngestionAllResult,
    IngestionSourceResult,
)
from app.services.ingestion_service import (
    ingest_all_rss_sources,
    ingest_rss_source,
)


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post(
    "/source/{source_id}",
    response_model=IngestionSourceResult,
)
def ingest_single_source(source_id: int):
    """Ingest articles from one active news source."""

    try:
        return ingest_rss_source(source_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error


@router.post(
    "/all",
    response_model=IngestionAllResult,
)
def ingest_all_sources():
    """Ingest articles from all active RSS sources."""

    return ingest_all_rss_sources()