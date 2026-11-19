
from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    description="Your personalized Agentic AI learning and news assistant.",
    version="1.0.0",
    debug=settings.DEBUG,
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to AI Pulse!",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
