"""Generate and save a personal AI-Pulse briefing."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.db.session import SessionLocal
from app.schemas.briefing import BriefingGenerateRequest
from app.services.briefing_service import generate_briefing


ROOT = Path(__file__).resolve().parents[2]
BRIEFING_DIR = ROOT / "data" / "briefings"
INDIA_TIME = timezone(timedelta(hours=5, minutes=30))


def create_daily_briefing(
    *,
    days: int = 7,
    max_articles: int = 5,
) -> dict:
    """Generate a briefing using the existing Gemini service.

    Save the complete response locally, but return only safe metrics.
    """

    if not 1 <= days <= 30:
        raise ValueError("days must be between 1 and 30")

    if not 1 <= max_articles <= 20:
        raise ValueError("max_articles must be between 1 and 20")

    payload = BriefingGenerateRequest(
        days=days,
        max_articles=max_articles,
        category=None,
        focus=None,
        verified_only=False,
    )

    with SessionLocal() as db:
        response = generate_briefing(db, payload)

    # The existing service returns a Pydantic response model.
    briefing_data = response.model_dump(mode="json")

    if not briefing_data:
        raise RuntimeError("Briefing response is empty")

    generated_at = datetime.now(timezone.utc)
    local_date = generated_at.astimezone(
        INDIA_TIME
    ).date().isoformat()

    document = {
        "generated_at_utc": generated_at.isoformat(),
        "date": local_date,
        "request": {
            "days": days,
            "max_articles": max_articles,
        },
        "briefing": briefing_data,
    }

    BRIEFING_DIR.mkdir(parents=True, exist_ok=True)

    destination = (
        BRIEFING_DIR / f"briefing-{local_date}.json"
    )

    # Save atomically: avoid leaving a partially written briefing.
    temporary = destination.with_name(
        destination.name + f".{uuid4().hex}.tmp"
    )

    try:
        temporary.write_text(
            json.dumps(
                document,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)

    return {"generated": 1}
