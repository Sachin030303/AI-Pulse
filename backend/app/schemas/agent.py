"""Request and response models for the AI-Pulse Agent."""

from typing import Literal

from pydantic import Field

from app.schemas.chat import ChatRequest, ChatResponse


class AgentRequest(ChatRequest):
    plan_with_gemini: bool = False


class AgentResponse(ChatResponse):
    planning_method: Literal["fast", "gemini", "explicit"]
    tools_used: list[str] = Field(default_factory=list)
