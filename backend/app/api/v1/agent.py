"""API endpoints for the read-only AI-Pulse Agent."""

import httpx

from fastapi import APIRouter, HTTPException

from app.db.session import SessionLocal
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_service import run_agent
from app.services.chat_service import ChatGenerationError


router = APIRouter()


@router.post("/ask", response_model=AgentResponse)
def ask_agent(payload: AgentRequest) -> AgentResponse:
    try:
        with SessionLocal() as db:
            return run_agent(db=db, payload=payload)

    except (ChatGenerationError, httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Agent generation is temporarily unavailable.",
        ) from exc
