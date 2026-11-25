
"""FastAPI endpoints for the AI-Pulse Chat API."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.chat_service import (
    ChatGenerationError,
    generate_chat_response,
)


# ==========================================
# CHAT ROUTER
# ==========================================

router = APIRouter(
    prefix="/chat",
    tags=["AI Chat"],
)


# ==========================================
# CHAT ENDPOINT
# ==========================================

@router.post(
    "/ask",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the AI-Pulse assistant",
    description=(
        "Generate a grounded AI response using "
        "stored articles, skills, learning goals, "
        "or software projects. "
        "Uses the configured local Ollama model."
    ),
)
def ask_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Generate an AI-Pulse chat response.

    Supported modes:
        auto
        knowledge
        learning
        projects

    This endpoint is read-only.
    """

    try:
        return generate_chat_response(
            db=db,
            payload=payload,
        )

    except ChatGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
