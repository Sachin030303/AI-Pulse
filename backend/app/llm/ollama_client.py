"""Compatibility adapter: delegates old imports to Gemini."""

from app.llm.gemini_client import generate_response

__all__ = ["generate_response"]
