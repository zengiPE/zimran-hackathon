"""Turns engine facts into in-world clue texts ("a text message", "a receipt note", ...).

Contract with the engine (Person 1): the engine owns the truth. For every clue it hands us a
ClueFact with a canonical English sentence and the exact names/values that sentence asserts.
We only restyle it. Rules from the spec:

* The LLM never decides what is true; the structured fact is always shown under the text.
* Texts are generated once, when the case is created (``narrate_case``), never on the fly.
* If the LLM is unavailable or a text fails validation, that clue uses a template instead.

Validation of an LLM text: it must contain every required mention verbatim and must not
mention any *other* suspect, room, time or item of the theme (that would plant a fake clue).
"""

from __future__ import annotations

import json
import logging
import re
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import openai
from pydantic import BaseModel

from app import llm_client
from app.story.themes import ClueFormat, Theme

log = logging.getLogger(__name__)

MAX_TEXT_CHARS = 320
# Narration runs inside POST /api/cases, and Vercel stops a function after 60 s. One try of
# at most 20 s leaves room for the engine and the database; on timeout we use templates.
LLM_TIMEOUT_S = 20.0
LLM_MAX_RETRIES = 0


@dataclass(frozen=True)
class ClueFact:
    """One atomic fact from the engine.

    statement: canonical sentence, e.g. "Maya was not in the Kitchen." (shown under the clue)
    mentions:  names/values the statement asserts, e.g. ("Maya", "Kitchen"); each must
               appear verbatim in the narrated text.
    """

    id: str
    statement: str
    mentions: tuple[str, ...]


@dataclass(frozen=True)
class ClueText:
    fact_id: str
    format_key: str
    format_label: str
    text: str
    statement: str  # the structured fact, rendered under the text
    source: Literal["llm", "template"]


# --- deterministic assignment ------------------------------------------------------------


def _pick(options: Sequence, key: str):
    """Stable choice (same fact id -> same option across runs and machines)."""
    return options[zlib.crc32(key.encode()) % len(options)]


def _assign(theme: Theme, fact: ClueFact) -> tuple[ClueFormat, str]:
    return _pick(theme.formats, f"fmt:{fact.id}"), _pick(theme.witnesses, f"wit:{fact.id}")


def template_clue(theme: Theme, fact: ClueFact) -> ClueText:
    fmt, witness = _assign(theme, fact)
    text = fmt.template.format(statement=fact.statement, witness=witness)
    text = text[:1].upper() + text[1:]  # "the caterer swears" -> "The caterer swears"
    return ClueText(fact.id, fmt.key, fmt.label, text, fact.statement, "template")


# --- validation --------------------------------------------------------------------------

_ARTICLE = re.compile(r"^(a|an|the)\s+", re.IGNORECASE)


def _core(term: str) -> str:
    """'a bottle of rosé' -> 'bottle of rosé'; '7:00 PM' -> '7:00'."""
    term = _ARTICLE.sub("", term.strip())
    # only a time suffix: "7:00 PM" -> "7:00", but "Sam" stays "Sam"
    return re.sub(r"(?<=\d)\s*(AM|PM)$", "", term, flags=re.IGNORECASE)


def _contains(text: str, term: str) -> bool:
    core = re.escape(_core(term))
    return re.search(rf"(?<![\w:]){core}(?![\w:])", text, re.IGNORECASE) is not None


def _theme_vocabulary(theme: Theme) -> list[str]:
    return [*theme.suspect_names, *theme.rooms, *theme.times, *theme.items]


def validate_text(theme: Theme, fact: ClueFact, text: str) -> str | None:
    """Return None if the text is acceptable, otherwise a short reason."""
    if not text or not text.strip():
        return "empty"
    if len(text) > MAX_TEXT_CHARS:
        return f"too long ({len(text)} chars)"
    for m in fact.mentions:
        if not _contains(text, m):
            return f"missing mention {m!r}"
    required = {_core(m).lower() for m in fact.mentions}
    for term in _theme_vocabulary(theme):
        if _core(term).lower() not in required and _contains(text, term):
            return f"mentions unrelated {term!r}"
    return None


# --- LLM ---------------------------------------------------------------------------------


class _LLMClue(BaseModel):
    fact_id: str
    text: str


class _LLMBatch(BaseModel):
    clues: list[_LLMClue]


SYSTEM_PROMPT = f"""You write clues for Casefile, a week-long mystery game played by groups of friends.
A logic engine has already decided every fact. Your only job is to restyle each fact as a short
in-world document in the requested format, so it feels like real evidence.

Hard rules (a clue that breaks any rule is thrown away):
1. Keep the fact's meaning exactly. Do not add, soften, strengthen or contradict anything.
   Do not add any other claim about where someone was, when, or what they carried.
2. Every word listed under "must include" appears in the text exactly as written
   (same spelling, same time format like "8:00 PM").
3. Never use any word from the "never mention" list. Those are other suspects, rooms,
   times and items; mentioning them would plant a fake clue.
4. Use the given format and, where it fits, the given witness as the author or speaker.
   Witnesses are not suspects.
5. 1-3 sentences, at most {MAX_TEXT_CHARS - 60} characters. Plain text, no markdown, no emojis.
6. Light, friendly tone. No violence, no crime vocabulary like murder or blood.

Return one entry per fact, using the fact_id you were given."""


def _user_prompt(theme: Theme, facts: Sequence[ClueFact]) -> str:
    items = []
    for f in facts:
        fmt, witness = _assign(theme, f)
        required = {_core(m).lower() for m in f.mentions}
        forbidden = [t for t in _theme_vocabulary(theme) if _core(t).lower() not in required]
        items.append(
            {
                "fact_id": f.id,
                "fact": f.statement,
                "format": fmt.label,
                "witness": witness,
                "must_include": list(f.mentions),
                "never_mention": forbidden,
            }
        )
    return (
        f"Theme: {theme.title}\n"
        f"Voice: {theme.voice}\n"
        f"Setting: {theme.setting}\n\n"
        f"Facts to restyle:\n{json.dumps(items, ensure_ascii=False, indent=1)}"
    )


JSON_FORMAT = (
    '\n\nReply with a JSON object only: {"clues": [{"fact_id": "...", "text": "..."}]}, '
    "one entry per fact."
)


def _llm_texts(client: openai.OpenAI, theme: Theme, facts: Sequence[ClueFact]) -> dict[str, str]:
    response = client.chat.completions.create(
        model=llm_client.model(),
        max_completion_tokens=8000,
        **llm_client.extra_params(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + JSON_FORMAT},
            {"role": "user", "content": _user_prompt(theme, facts)},
        ],
    )
    raw = llm_client.message_text(response)
    if raw is None:
        log.warning("narrative: no usable LLM output")
        return {}
    batch = _LLMBatch.model_validate_json(raw)  # ValidationError is a ValueError
    return {c.fact_id: c.text.strip() for c in batch.clues}


def _default_client() -> openai.OpenAI | None:
    return llm_client.openai_client(timeout=LLM_TIMEOUT_S, max_retries=LLM_MAX_RETRIES)


def narrate_case(
    theme: Theme,
    facts: Sequence[ClueFact],
    *,
    client: openai.OpenAI | None = None,
    use_llm: bool = True,
) -> list[ClueText]:
    """Narrate all clues of a case in one LLM call. Never raises because of the LLM.

    Returns one ClueText per fact, in input order. Clues the LLM got wrong fall back to
    templates individually; if the LLM is unreachable, every clue uses a template.
    """
    if len({f.id for f in facts}) != len(facts):
        raise ValueError("fact ids must be unique")

    texts: dict[str, str] = {}
    if use_llm and facts:
        client = client or _default_client()
        if client is not None:
            try:
                texts = _llm_texts(client, theme, facts)
            except (openai.APIError, ValueError) as e:  # network/API/parse problems
                log.warning("narrative: LLM call failed, using templates: %s", e)

    out: list[ClueText] = []
    for fact in facts:
        text = texts.get(fact.id)
        reason = "no text" if text is None else validate_text(theme, fact, text)
        if reason is None:
            fmt, _ = _assign(theme, fact)
            out.append(ClueText(fact.id, fmt.key, fmt.label, text, fact.statement, "llm"))
        else:
            if texts:  # only worth logging when the LLM actually answered
                log.info("narrative: fact %s -> template (%s)", fact.id, reason)
            out.append(template_clue(theme, fact))
    return out
