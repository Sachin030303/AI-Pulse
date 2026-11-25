
"""Pydantic schemas for the AI-Pulse Briefing API."""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ==========================================
# BRIEFING REQUEST
# ==========================================


class BriefingGenerateRequest(BaseModel):
    """Options for generating a personalized AI briefing."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Look back this many days.",
    )

    max_articles: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum articles used in the briefing.",
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Optional AI news category.",
    )

    focus: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Topic to emphasize in the briefing.",
    )

    verified_only: bool = Field(
        default=False,
        description="Use only articles marked verified.",
    )


# ==========================================
# ARTICLE SOURCE
# ==========================================


class BriefingSource(BaseModel):
    """Metadata for an article used in a briefing."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    source_index: int = Field(ge=1)

    id: int = Field(ge=1)

    title: str

    url: str

    category: str | None = None

    published_at: datetime | None = None

    importance_level: str | None = None

    is_verified: bool


# ==========================================
# BRIEFING RESPONSE
# ==========================================


class BriefingResponse(BaseModel):
    """Structured AI-generated news briefing."""

    status: Literal[
        "generated",
        "no_articles",
    ]

    generated_at: datetime

    window_start: datetime

    window_end: datetime

    period_days: int = Field(
        ge=1,
        le=30,
    )

    category: str | None = None

    focus: str | None = None

    verified_only: bool = False

    model: str | None = None

    briefing: str = Field(
        min_length=1,
    )

    sources_used: int = Field(
        ge=0,
    )

    sources: list[BriefingSource] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_response(self):
        """Ensure source metadata is internally consistent."""

        if self.window_end < self.window_start:
            raise ValueError(
                "Briefing window end cannot precede start."
            )

        if self.sources_used != len(self.sources):
            raise ValueError(
                "sources_used must match the number of sources."
            )

        if (
            self.status == "no_articles"
            and self.sources_used != 0
        ):
            raise ValueError(
                "A no-articles response cannot contain sources."
            )

        if (
            self.status == "generated"
            and self.sources_used == 0
        ):
            raise ValueError(
                "A generated briefing must contain sources."
            )

        return self
