from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class AgentToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=3, ge=1, le=5)
    verified_only: bool = False


class AgentToolResponse(BaseModel):
    status: Literal["answered"]
    answer: str
    model: str
    tools_used: list[str]
    tool_calls: list[dict]
