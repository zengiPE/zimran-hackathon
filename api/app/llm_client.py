"""The one place that knows which LLM provider we use (OpenAI).

Both LLM features (clue narration, AI teammates' chat lines) only restyle text the engine
already decided, and both fall back to templates, so the game works with no key at all.
"""

from __future__ import annotations

import logging
import re

import openai

from app.config import get_settings

log = logging.getLogger(__name__)


def openai_client(timeout: float, max_retries: int) -> openai.OpenAI | None:
    key = get_settings().openai_api_key
    if not key:
        return None
    return openai.OpenAI(api_key=key, timeout=timeout, max_retries=max_retries)


def model() -> str:
    return get_settings().openai_model


def reasoning_effort_for(model_name: str, effort: str) -> str | None:
    """The reasoning_effort to send for this model, or None if the model doesn't take it.

    OpenAI rejects the parameter (HTTP 400) on non-reasoning models such as gpt-4.1 or
    gpt-4o, so it is sent only to reasoning models: the gpt-5 family (not its -chat
    variants) and the o-series. The o-series has no "minimal" level, so it gets "low".
    """
    effort = effort.strip().lower()
    m = model_name.strip().lower()
    if not effort:
        return None
    if m.startswith("gpt-5") and "chat" not in m:
        return effort
    if re.match(r"^o\d", m):
        return "low" if effort in ("minimal", "none") else effort
    return None


def extra_params() -> dict[str, str]:
    """Request params that depend on the model: reasoning effort where the model supports it."""
    s = get_settings()
    effort = reasoning_effort_for(s.openai_model, s.openai_reasoning_effort)
    return {"reasoning_effort": effort} if effort else {}


def chat(client: openai.OpenAI, **kwargs):
    """chat.completions.create with the model-dependent params added.

    If OpenAI still rejects reasoning_effort (a model this code doesn't know yet), retry once
    without it: a 400 comes back fast, so the retry fits the request's time budget.
    """
    params = {**kwargs, **extra_params()}
    try:
        return client.chat.completions.create(**params)
    except openai.BadRequestError as e:
        if "reasoning_effort" not in params or "reasoning" not in str(e).lower():
            raise
        log.warning("model %s rejected reasoning_effort, retrying without it", params["model"])
        params.pop("reasoning_effort")
        return client.chat.completions.create(**params)


def message_text(response) -> str | None:
    """Text of the first choice, or None on refusal / content filter / empty output."""
    if not response.choices:
        return None
    choice = response.choices[0]
    if choice.finish_reason == "content_filter" or getattr(choice.message, "refusal", None):
        return None
    return (choice.message.content or "").strip() or None
