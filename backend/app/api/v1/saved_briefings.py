"""Admin-protected read access to locally saved AI-Pulse briefings."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.core.authorization import require_admin

router = APIRouter(
    prefix="/api/v1/briefings",
    tags=["Saved briefings"],
    dependencies=[Depends(require_admin)],
)

BRIEFING_DIR = Path(__file__).resolve().parents[3] / "data" / "briefings"


@router.get("/latest", summary="Read latest saved daily briefing")
def latest_saved_briefing():
    files = sorted(BRIEFING_DIR.glob("briefing-????-??-??.json"))
    if not files:
        raise HTTPException(status_code=404, detail="No saved briefing available")

    try:
        document = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise HTTPException(status_code=500, detail="Saved briefing is unreadable") from None

    if not isinstance(document, dict) or not isinstance(document.get("briefing"), dict):
        raise HTTPException(status_code=500, detail="Saved briefing has an invalid format")

    return JSONResponse(document, headers={"Cache-Control": "no-store"})
