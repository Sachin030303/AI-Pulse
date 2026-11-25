
"""HTTP validation tests for the AI-Pulse Briefing API."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.main import app


URL = "/api/v1/briefing/generate"

# Simulated article. No database writes or external API calls.
article = SimpleNamespace(
    id=99999,
    title="Test AI Research Announcement",
    url="https://example.com/ai-research",
    content="A test article about an AI research announcement.",
    summary="A new AI research development was announced.",
    category="Research",
    published_at=datetime.now(timezone.utc),
    importance_level=None,
    is_verified=False,
)


def check(response, expected_status, name):
    assert response.status_code == expected_status, (
        f"{name}: expected {expected_status}, "
        f"got {response.status_code}: {response.text}"
    )
    print(f"PASS: {name} (HTTP {expected_status})")


with TestClient(app) as client:

    # TEST 1: Successful generation
    with (
        patch(
            "app.services.briefing_service.select_briefing_articles",
            return_value=([article], 1),
        ),
        patch(
            "app.services.briefing_service.generate_response",
            return_value="## Overview\nAI research update [1].",
        ),
    ):
        response = client.post(
            URL,
            json={"days": 7, "max_articles": 1},
        )

        check(response, 200, "Successful briefing")

        data = response.json()
        assert data["status"] == "generated"
        assert data["sources_used"] == 1
        assert data["sources"][0]["source_index"] == 1
        assert data["sources"][0]["id"] == article.id
        assert "[1]" in data["briefing"]

    # TEST 2: Empty verified-only selection
    with (
        patch(
            "app.services.briefing_service.select_briefing_articles",
            return_value=([], 0),
        ),
        patch(
            "app.services.briefing_service.generate_response",
        ) as mock_model,
    ):
        response = client.post(
            URL,
            json={"verified_only": True},
        )

        check(response, 200, "Empty article selection")

        assert response.json()["status"] == "no_articles"
        assert response.json()["sources_used"] == 0
        mock_model.assert_not_called()

    # TEST 3: Invalid number of days
    response = client.post(URL, json={"days": 0})
    check(response, 422, "Invalid days")

    # TEST 4: Article limit exceeds maximum
    response = client.post(URL, json={"max_articles": 11})
    check(response, 422, "Invalid article limit")

    # TEST 5: Blank category
    response = client.post(URL, json={"category": "   "})
    check(response, 422, "Blank category")

    # TEST 6: Unknown request field
    response = client.post(URL, json={"unknown_field": True})
    check(response, 422, "Unknown request field")

    # TEST 7: Ollama unavailable
    with (
        patch(
            "app.services.briefing_service.select_briefing_articles",
            return_value=([article], 1),
        ),
        patch(
            "app.services.briefing_service.generate_response",
            side_effect=httpx.ConnectError("Connection refused"),
        ),
    ):
        response = client.post(
            URL,
            json={"days": 7, "max_articles": 1},
        )

        check(response, 503, "Ollama connection failure")

    # TEST 8: Empty Ollama response
    with (
        patch(
            "app.services.briefing_service.select_briefing_articles",
            return_value=([article], 1),
        ),
        patch(
            "app.services.briefing_service.generate_response",
            return_value="   ",
        ),
    ):
        response = client.post(
            URL,
            json={"days": 7, "max_articles": 1},
        )

        check(response, 503, "Empty model response")


print("\nALL 8 BRIEFING HTTP TESTS PASSED")
