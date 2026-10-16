"""
Thin wrapper around the Anthropic API.

The ONLY place that talks to the LLM. Everything else calls `complete()` and
gets back either text or a clear AIUnavailable error. This isolates:
  * the API key (read from settings, never passed around),
  * the model name,
  * and — most importantly — the failure handling.

Graceful degradation (assignment requirement D.3):
If the key is missing, or the API errors / times out / is rate-limited, we do
NOT crash the request. We raise AIUnavailable, and the caller decides what to
do (fall back to a rule-based category, or let the admin write manually).
"""
from __future__ import annotations
import logging

from ..config import settings

logger = logging.getLogger("bookleaf.ai")


class AIUnavailable(Exception):
    """Raised when the AI could not produce a result for any reason."""


# The SDK is imported lazily so the app still boots even if the package or key
# is absent (e.g. a reviewer who just wants to see the portals without a key).
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.ai_active:
        raise AIUnavailable("AI disabled or no ANTHROPIC_API_KEY configured")
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return _client
    except Exception as e:  # noqa: BLE001
        raise AIUnavailable(f"Could not initialise Anthropic client: {e}")


def complete(*, system: str, user: str, max_tokens: int = 600,
             temperature: float = 0.3) -> str:
    """Send one message and return the model's text, or raise AIUnavailable."""
    client = _get_client()
    try:
        msg = client.messages.create(
            model=settings.ai_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if block.type == "text").strip()
    except Exception as e:  # noqa: BLE001 — includes rate limits, timeouts, API errors
        logger.warning("AI call failed: %s", e)
        raise AIUnavailable(str(e))
