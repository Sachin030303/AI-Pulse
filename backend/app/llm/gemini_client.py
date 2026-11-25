"""Gemini text generation client for AI-Pulse."""

import httpx

from app.core.config import settings


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
) -> str:
    """Generate text through Google's Gemini REST API."""

    api_key = settings.GEMINI_API_KEY.strip()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from the environment."
        )

    url = (
        "https://generativelanguage.googleapis.com"
        f"/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }

    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [
                {"text": system_prompt}
            ]
        }

    response = httpx.post(
        url,
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=settings.GEMINI_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "Gemini did not return a valid text response."
        ) from error

    text = "\n".join(
        part["text"]
        for part in parts
        if isinstance(part, dict)
        and isinstance(part.get("text"), str)
    ).strip()

    if not text:
        raise ValueError(
            "Gemini returned an empty text response."
        )

    return text
