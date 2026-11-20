from fastapi import FastAPI
from app.api.v1 import news, sources, ingestion, knowledge, skills
from app.api.v1 import news, sources, ingestion, knowledge
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


app.include_router(
    news.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    sources.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    ingestion.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    knowledge.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    skills.router,
    prefix=settings.API_V1_PREFIX,
)