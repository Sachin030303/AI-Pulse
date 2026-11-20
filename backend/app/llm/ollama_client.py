"""Ollama client placeholder."""
import httpx

from app.core.config import settings


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
) -> str:
    """
    Generate a response using the configured local Ollama model.
    """

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    if system_prompt:
        payload["system"] = system_prompt

    response = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=settings.OLLAMA_TIMEOUT,
    )

    response.raise_for_status()

    result = response.json()

    return result["response"].strip()