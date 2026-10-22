"""Gemini wrapper. Everything that needs the LLM goes through complete()."""
from __future__ import annotations
import logging

from ..config import settings

logger = logging.getLogger("bookleaf.ai")


class AIUnavailable(Exception):
    """No key, API error, timeout, rate limit... callers should use their fallback."""


_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.ai_active:
        raise AIUnavailable("AI is disabled or GEMINI_API_KEY is not set")
    try:
        from google import genai
        _client = genai.Client(api_key=settings.gemini_api_key)
        return _client
    except Exception as e:  # noqa: BLE001
        raise AIUnavailable(f"could not create Gemini client: {e}")


def complete(*, system: str, user: str, max_tokens: int = 600,
             temperature: float = 0.3) -> str:
    client = _get_client()
    try:
        from google.genai import types
        resp = client.models.generate_content(
            model=settings.ai_model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=temperature,
                # thinking tokens would eat into max_output_tokens and we don't need them here
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                http_options=types.HttpOptions(timeout=20000),
            ),
        )
        return (resp.text or "").strip()
    except Exception as e:  # noqa: BLE001
        logger.warning("gemini call failed: %s", e)
        raise AIUnavailable(str(e))
