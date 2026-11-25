
"""Pydantic schemas for the AI-Pulse Chat API."""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ==========================================
# SHARED TYPES
# ==========================================

ChatMode = Literal[
    "auto",
    "knowledge",
    "learning",
    "projects",
]

ChatRole = Literal[
    "user",
    "assistant",
]

ChatContextType = Literal[
    "articles",
    "skills",
    "learning_goals",
    "projects",
]


# ==========================================
# CONVERSATION HISTORY
# ==========================================

class ChatHistoryMessage(BaseModel):
    """A previous message in the conversation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    role: ChatRole

    content: str = Field(
        min_length=1,
        max_length=4000,
    )


# ==========================================
# CHAT REQUEST
# ==========================================

class ChatRequest(BaseModel):
    """Request for a grounded AI-Pulse chat response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    message: str = Field(
        min_length=1,
        max_length=4000,
        description="The user's current question.",
    )

    mode: ChatMode = Field(
        default="auto",
        description=(
            "Context selection mode. Auto lets the "
            "service determine which context to retrieve."
        ),
    )

    max_sources: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of article sources.",
    )

    verified_only: bool = Field(
        default=False,
        description=(
            "Use only articles marked verified "
            "when retrieving article sources."
        ),
    )

    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=8,
        description="Recent conversation turns.",
    )


# ==========================================
# ARTICLE SOURCE
# ==========================================

class ChatSource(BaseModel):
    """Article source supporting a chat answer."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    source_index: int = Field(
        ge=1,
    )

    id: int = Field(
        ge=1,
    )

    title: str

    url: str

    category: str | None = None

    published_at: datetime | None = None

    is_verified: bool = False


# ==========================================
# CHAT RESPONSE
# ==========================================

class ChatResponse(BaseModel):
    """Structured response from the AI-Pulse chat assistant."""

    model_config = ConfigDict(
        extra="forbid",
    )

    status: Literal[
        "answered",
        "no_context",
    ]

    message: str

    answer: str = Field(
        min_length=1,
    )

    mode: ChatMode

    model: str | None = None

    generated_at: datetime

    sources_used: int = Field(
        ge=0,
    )

    sources: list[ChatSource] = Field(
        default_factory=list,
    )

    context_used: list[ChatContextType] = Field(
        default_factory=list,
        description=(
            "Types of contextual information "
            "used to generate the answer."
        ),
    )

    @model_validator(mode="after")
    def validate_response(self):
        """Validate source counts and response state."""

        if self.sources_used != len(self.sources):
            raise ValueError(
                "sources_used must match the number "
                "of article sources."
            )

        source_indices = [
            source.source_index
            for source in self.sources
        ]

        if source_indices != list(
            range(1, len(self.sources) + 1)
        ):
            raise ValueError(
                "Source indices must be sequential "
                "and start at 1."
            )

        if self.status == "no_context":
            if self.sources_used != 0:
                raise ValueError(
                    "A no-context response cannot "
                    "contain article sources."
                )

            if self.context_used:
                raise ValueError(
                    "A no-context response cannot "
                    "claim contextual data was used."
                )

        return self
