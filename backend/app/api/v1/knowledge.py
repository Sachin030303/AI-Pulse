"""Knowledge endpoints placeholder."""
"""Knowledge API endpoints."""

import httpx

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.knowledge import (
    KnowledgeSearchResponse,
    KnowledgeTopicsResponse,
    KnowledgeStatsResponse,
    KnowledgeAskRequest,
    KnowledgeAskResponse,
)
from app.services.knowledge_service import (
    search_knowledge,
    list_knowledge_topics,
    knowledge_statistics,
    ask_knowledge,
)


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"],
)


@router.get(
    "/search",
    response_model=KnowledgeSearchResponse,
)
def search(
    q: str = Query(..., min_length=1, max_length=500),
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search articles in the knowledge base."""

    return search_knowledge(
        db=db,
        query=q,
        category=category,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/topics",
    response_model=KnowledgeTopicsResponse,
)
def topics(
    db: Session = Depends(get_db),
):
    """Retrieve available knowledge topics."""

    return list_knowledge_topics(db)


@router.get(
    "/stats",
    response_model=KnowledgeStatsResponse,
)
def statistics(
    db: Session = Depends(get_db),
):
    """Retrieve knowledge base statistics."""

    return knowledge_statistics(db)


@router.post(
    "/ask",
    response_model=KnowledgeAskResponse,
)
def ask(
    payload: KnowledgeAskRequest,
    db: Session = Depends(get_db),
):
    """Answer questions using retrieved articles."""

    try:
        return ask_knowledge(
            db=db,
            question=payload.question,
            category=payload.category,
            max_sources=payload.max_sources,
        )

    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="The AI model took too long to respond.",
        ) from error

    except httpx.ConnectError as error:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Ollama.",
        ) from error

    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="The AI model returned an error.",
        ) from error