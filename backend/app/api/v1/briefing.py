
"""FastAPI endpoints for AI-Pulse news briefings."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.briefing import (
    BriefingGenerateRequest,
    BriefingResponse,
)
from app.services.briefing_service import (
    BriefingGenerationError,
    generate_briefing,
)


router = APIRouter(
    prefix="/briefing",
    tags=["AI Briefings"],
)


@router.post(
    "/generate",
    response_model=BriefingResponse,
    summary="Generate a personalized AI news briefing",
    description=(
        "Select recent articles from PostgreSQL and "
        "generate a source-linked briefing using Ollama."
    ),
)
def create_briefing(
    payload: BriefingGenerateRequest,
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """Generate a news briefing from eligible articles."""

    try:
        return generate_briefing(
            db=db,
            payload=payload,
        )

    except BriefingGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
