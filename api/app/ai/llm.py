"""One chat line from an AI teammate. The engine decides what it believes; the LLM only words it.

Never raises: on any API problem it returns None and the caller uses a template.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import openai

from app import llm_client

log = logging.getLogger(__name__)

TIMEOUT_S = 8.0  # the player is waiting on POST /board
MAX_CHARS = 220

INTENTS = {
    "hypothesis": "Say who it could still be, using only names from 'possible'.",
    "ask": "Ask {who} whether they have anything about {x}.",
    "react": "React briefly to the last message, then say who is still possible for you.",
}

SYSTEM_PROMPT = f"""You are an AI teammate in Casefile, a mystery game a group of friends solves in a
group chat. You write ONE chat message.

Hard rules (a message that breaks any rule is thrown away):
1. You only know the clues listed under "my_clues". Never state or hint at any other fact
   about where someone was, when, or what they had.
2. When you name suspects as possible culprits, use only names from "possible".
3. Never claim to be sure unless "possible" has exactly one name.
4. 1-2 sentences, at most {MAX_CHARS - 40} characters, casual group-chat English.
   No markdown, no hashtags. Stay in your persona's style.
5. Light, friendly tone. No violence or crime vocabulary like murder or blood."""


@dataclass(frozen=True)
class ReplyContext:
    persona_name: str
    persona_style: str
    intent: str  # hypothesis | ask | react
    intro: str
    my_clues: list[str]  # clue sentences this AI knows
    possible: list[str]  # suspect names still possible for this AI
    recent: list[str]  # "Name: text", oldest first
    who: str  # the human teammate
    x: str  # suspect to ask about (intent "ask")


def _client() -> openai.OpenAI | None:
    return llm_client.openai_client(timeout=TIMEOUT_S, max_retries=0)


def _prompt(ctx: ReplyContext) -> str:
    payload = {
        "you": {"name": ctx.persona_name, "style": ctx.persona_style},
        "case": ctx.intro,
        "my_clues": ctx.my_clues,
        "possible": ctx.possible,
        "recent_chat": ctx.recent,
        "task": INTENTS[ctx.intent].format(who=ctx.who, x=ctx.x),
    }
    return json.dumps(payload, ensure_ascii=False, indent=1)


def chat_line(ctx: ReplyContext) -> str | None:
    client = _client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model=llm_client.model(),
            max_completion_tokens=2000,
            **llm_client.extra_params(),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _prompt(ctx)},
            ],
        )
    except openai.APIError as e:
        log.warning("ai chat: LLM call failed, using template: %s", e)
        return None
    return llm_client.message_text(response)
