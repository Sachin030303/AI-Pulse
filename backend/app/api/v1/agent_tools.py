"""Read-only Gemini function-calling API."""

import logging

import httpx
from fastapi import APIRouter, HTTPException

from app.db.session import SessionLocal
from app.schemas.agent_tools import AgentToolRequest, AgentToolResponse
from app.services.agent_tools_service import run_agent_tools

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ask", response_model=AgentToolResponse)
def ask_agent_tools(payload: AgentToolRequest):
    try:
        with SessionLocal() as db:
            return run_agent_tools(db, payload)

    except (httpx.HTTPError, ValueError) as error:
        logger.warning(
            "Agent tool execution failed: %s",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="Gemini tool execution failed. Check server logs.",
        ) from error
