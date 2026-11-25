
"""Main FastAPI application for AI-Pulse."""

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from app.api.v1 import (
    news,
    sources,
    ingestion,
    knowledge,
    skills,
    projects,
    progress,
    briefing,
)
from app.api.v1 import chat
from app.core.config import settings
from app.core.authorization import require_admin
# AI_PULSE_ADMIN_GUARD_V1


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Your personalized Agentic AI learning and news assistant.",
    version="1.0.0",
    debug=settings.DEBUG,
)


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to AI Pulse!",
        "status": "running",
        "version": "1.0.0",
    }


# ==========================================
# HEALTH CHECK ENDPOINT
# ==========================================

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }


# ==========================================
# REGISTER API V1 ROUTERS
# ==========================================

# News API
app.include_router(
    news.router,
    prefix=settings.API_V1_PREFIX,
)

# News Sources API
app.include_router(
    sources.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# RSS Ingestion API
app.include_router(
    ingestion.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# Knowledge API
app.include_router(
    knowledge.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# Skills Management API
app.include_router(
    skills.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# Projects Management API
app.include_router(
    projects.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# Progress Tracking API
app.include_router(
    progress.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# AI Briefing API
app.include_router(
    briefing.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)

# AI Chat API
app.include_router(
    chat.router,
    dependencies=[Depends(require_admin)],
    prefix=settings.API_V1_PREFIX,
)
# AI-Pulse read-only Agent API
from app.api.v1.agent import router as agent_router
app.include_router(
    agent_router,
    dependencies=[Depends(require_admin)],
    prefix="/api/v1/agent",
    tags=["agent"],
)

# Gemini read-only function-calling endpoint
from app.api.v1.agent_tools import router as agent_tools_router

app.include_router(
    agent_tools_router,
    dependencies=[Depends(require_admin)],
    prefix="/api/v1/agent/tools",
    tags=["agent-tools"],
)

# AI-Pulse task planning preview API
from app.api.v1.task_planning import router as task_planning_router

app.include_router(
    task_planning_router,
    dependencies=[Depends(require_admin)],
    prefix="/api/v1/agent/task-plans",
    tags=["task-planning"],
)

# AI-Pulse authentication endpoints
from app.api.v1.auth import router as auth_router

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["authentication"],
)



# AI_PULSE_RECOVERY_PAGES_V1

RECOVERY_WEB_DIR = Path(__file__).resolve().parent / "web"


@app.get("/forgot-password", include_in_schema=False)
@app.get("/reset-password", include_in_schema=False)
def recovery_page():
    return FileResponse(
        RECOVERY_WEB_DIR / "recovery.html",
        media_type="text/html",
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": (
                "default-src 'none'; "
                "script-src 'self'; "
                "style-src 'unsafe-inline'; "
                "connect-src 'self'; "
                "form-action 'none'; "
                "base-uri 'none'; "
                "frame-ancestors 'none'"
            ),
        },
    )


@app.get("/assets/recovery.js", include_in_schema=False)
def recovery_javascript():
    return FileResponse(
        RECOVERY_WEB_DIR / "recovery.js",
        media_type="text/javascript",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


# AI_PULSE_SAVED_BRIEFINGS_V1
from app.api.v1.saved_briefings import router as saved_briefings_router
app.include_router(saved_briefings_router)
