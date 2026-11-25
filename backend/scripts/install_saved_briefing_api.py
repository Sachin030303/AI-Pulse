"""Install an admin-only endpoint for the latest saved AI-Pulse briefing.

Usage: python -m scripts.install_saved_briefing_api --check
       python -m scripts.install_saved_briefing_api --install

Does not modify PostgreSQL or briefing JSON documents.
"""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "app" / "main.py"
ROUTER = ROOT / "app" / "api" / "v1" / "saved_briefings.py"
BACKUP = ROOT / "app" / "main.py.pre-saved-briefings"
MARKER = "# AI_PULSE_SAVED_BRIEFINGS_V1"

ROUTER_SOURCE = '''"""Admin-protected read access to locally saved AI-Pulse briefings."""

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
'''

APP_SNIPPET = '''\n\n''' + MARKER + '''
from app.api.v1.saved_briefings import router as saved_briefings_router
app.include_router(saved_briefings_router)
'''


def main(argv=None):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--install", action="store_true")
    args = parser.parse_args(argv)

    if not MAIN.is_file():
        raise SystemExit("FastAPI main.py not found")

    source = MAIN.read_text(encoding="utf-8-sig")
    exists = MARKER in source
    print("FastAPI main found:", MAIN.is_file())
    print("Saved briefing endpoint installed:", exists)
    print("Saved briefing module present:", ROUTER.is_file())
    print("Main.py backup present:", BACKUP.is_file())

    if args.check:
        print("CHECK COMPLETE: no files changed")
        return 0

    if exists:
        raise SystemExit("Endpoint already installed. No changes made.")
    if ROUTER.exists() or BACKUP.exists():
        raise SystemExit("Existing router or backup found. Inspect before installing.")
    if "app.include_router" not in source or "app = FastAPI" not in source:
        raise SystemExit("Unrecognized FastAPI main.py layout. No changes made.")

    new_source = source + APP_SNIPPET
    compile(ROUTER_SOURCE, str(ROUTER), "exec")
    compile(new_source, str(MAIN), "exec")
    shutil.copy2(MAIN, BACKUP)
    try:
        ROUTER.write_text(ROUTER_SOURCE, encoding="utf-8")
        MAIN.write_text(new_source, encoding="utf-8")
    except Exception:
        MAIN.write_bytes(BACKUP.read_bytes())
        ROUTER.unlink(missing_ok=True)
        raise

    print("PASS: Admin-protected /api/v1/briefings/latest installed")
    print("PASS: FastAPI main.py backed up")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
