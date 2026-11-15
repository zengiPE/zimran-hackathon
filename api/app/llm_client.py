"""The one place that knows which LLM provider we use (OpenAI).

Both LLM features (clue narration, AI teammates' chat lines) only restyle text the engine
already decided, and both fall back to templates, so the game works with no key at all.
"""

from __future__ import annotations

import openai

from app.config import get_settings


def openai_client(timeout: float, max_retries: int) -> openai.OpenAI | None:
    key = get_settings().openai_api_key
    if not key:
        return None
    return openai.OpenAI(api_key=key, timeout=timeout, max_retries=max_retries)


def model() -> str:
    return get_settings().openai_model


def extra_params() -> dict[str, str]:
    """Request params that depend on the model: reasoning effort, unless it is switched off."""
    effort = get_settings().openai_reasoning_effort.strip()
    return {"reasoning_effort": effort} if effort else {}


def message_text(response) -> str | None:
    """Text of the first choice, or None on refusal / content filter / empty output."""
    if not response.choices:
        return None
    choice = response.choices[0]
    if choice.finish_reason == "content_filter" or getattr(choice.message, "refusal", None):
        return None
    return (choice.message.content or "").strip() or None
