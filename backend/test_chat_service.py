
"""Tests for AI-Pulse Chat Service."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.schemas.chat import ChatRequest
from app.services.chat_service import (
    ChatGenerationError,
    generate_chat_response,
    select_context_types,
)


db = object()

article = SimpleNamespace(
    id=100,
    title="NVIDIA announces an AI research platform",
    url="https://example.com/nvidia-ai",
    summary="NVIDIA introduced an AI research platform.",
    content="Details of an AI research platform.",
    category="Research",
    published_at=datetime.now(timezone.utc),
    is_verified=False,
)

project = SimpleNamespace(
    id=2,
    name="AI-Pulse",
    status="In Progress",
    category="Software",
    priority="High",
    due_date=None,
    repository_url=None,
    description="AI-powered news and learning assistant.",
)

skill = SimpleNamespace(
    id=1,
    name="Python",
    category="Programming",
    proficiency_level="Intermediate",
    target_level="Advanced",
    progress=60,
    status="In Progress",
    description="Python development skills.",
)

goal = SimpleNamespace(
    id=1,
    title="Improve Python",
    status="In Progress",
    priority="High",
    progress=40,
    skill_id=1,
    target_date=None,
    description="Study advanced Python.",
)


# ==========================================
# TEST 1: AUTO ROUTING
# ==========================================

assert select_context_types(
    "auto",
    "What is new in NVIDIA AI?",
) == ["articles"]

assert select_context_types(
    "auto",
    "What is my project status?",
) == ["projects"]

assert select_context_types(
    "auto",
    "What is my skill progress?",
) == [
    "skills",
    "learning_goals",
]

print("PASS 1: Automatic context selection")


# ==========================================
# TEST 2: KNOWLEDGE RESPONSE
# ==========================================

with (
    patch(
        "app.services.chat_service.get_chat_articles",
        return_value=[article],
    ),
    patch(
        "app.services.chat_service.generate_response",
        return_value="NVIDIA announced a research platform [1].",
    ) as mocked_model,
):

    result = generate_chat_response(
        db,
        ChatRequest(
            message="What is new in NVIDIA AI?",
            mode="knowledge",
        ),
    )

    assert result.status == "answered"
    assert result.sources_used == 1
    assert result.context_used == ["articles"]
    assert "[1]" in result.answer
    assert result.sources[0].id == 100

    mocked_model.assert_called_once()

print("PASS 2: Grounded knowledge response")


# ==========================================
# TEST 3: EMPTY KNOWLEDGE
# ==========================================

with (
    patch(
        "app.services.chat_service.get_chat_articles",
        return_value=[],
    ),
    patch(
        "app.services.chat_service.generate_response",
    ) as mocked_model,
):

    result = generate_chat_response(
        db,
        ChatRequest(
            message="Find an unknown research article.",
            mode="knowledge",
        ),
    )

    assert result.status == "no_context"
    assert result.sources_used == 0
    assert result.model is None

    mocked_model.assert_not_called()

print("PASS 3: Empty knowledge context")


# ==========================================
# TEST 4: PROJECT RESPONSE
# ==========================================

with (
    patch(
        "app.services.chat_service.get_chat_projects",
        return_value=[project],
    ),
    patch(
        "app.services.chat_service.generate_response",
        return_value="AI-Pulse is In Progress.",
    ),
):

    result = generate_chat_response(
        db,
        ChatRequest(
            message="What is my AI-Pulse project status?",
            mode="projects",
        ),
    )

    assert result.status == "answered"
    assert result.context_used == ["projects"]
    assert result.sources_used == 0
    assert "In Progress" in result.answer

print("PASS 4: Project context response")


# ==========================================
# TEST 5: LEARNING RESPONSE
# ==========================================

with (
    patch(
        "app.services.chat_service.get_chat_skills",
        return_value=[skill],
    ),
    patch(
        "app.services.chat_service.get_chat_learning_goals",
        return_value=[goal],
    ),
    patch(
        "app.services.chat_service.generate_response",
        return_value="Your Python skill progress is 60.",
    ),
):

    result = generate_chat_response(
        db,
        ChatRequest(
            message="What is my skill progress?",
            mode="learning",
        ),
    )

    assert result.status == "answered"
    assert result.context_used == [
        "skills",
        "learning_goals",
    ]
    assert result.sources_used == 0

print("PASS 5: Learning context response")


# ==========================================
# TEST 6: INVALID CITATION
# ==========================================

with (
    patch(
        "app.services.chat_service.get_chat_articles",
        return_value=[article],
    ),
    patch(
        "app.services.chat_service.generate_response",
        return_value="Unsupported announcement [9].",
    ),
):

    try:
        generate_chat_response(
            db,
            ChatRequest(
                message="NVIDIA AI announcement",
                mode="knowledge",
            ),
        )
    except ChatGenerationError:
        print("PASS 6: Invalid citations rejected")
    else:
        raise AssertionError(
            "Invalid citations were accepted."
        )


# ==========================================
# TEST 7: OLLAMA CONNECTION FAILURE
# ==========================================

with (
    patch(
        "app.services.chat_service.get_chat_projects",
        return_value=[project],
    ),
    patch(
        "app.services.chat_service.generate_response",
        side_effect=httpx.ConnectError(
            "Connection refused"
        ),
    ),
):

    try:
        generate_chat_response(
            db,
            ChatRequest(
                message="Show my project.",
                mode="projects",
            ),
        )
    except ChatGenerationError:
        print("PASS 7: Ollama failure handled")
    else:
        raise AssertionError(
            "Ollama connection failure was not handled."
        )


print("\nALL 7 CHAT SERVICE TESTS PASSED")
