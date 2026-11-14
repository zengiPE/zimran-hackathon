"""AI teammates' chat line through the OpenAI client: text in, None on any problem."""

from types import SimpleNamespace

import httpx
import openai
import pytest

from app.ai import llm

CTX = llm.ReplyContext(
    persona_name="Nora", persona_style="Dry skeptic.", intent="hypothesis", intro="Case.",
    my_clues=["Maya was not in the Kitchen."], possible=["Priya", "Leo"], recent=[],
    who="Ann", x="Leo")


def fake(content=None, refusal=None, finish="stop", error=None):
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        if error:
            raise error
        msg = SimpleNamespace(content=content, refusal=refusal)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason=finish)])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
                           calls=calls)


def test_returns_model_text(monkeypatch) -> None:
    client = fake(content="  Could be Priya or Leo.  ")
    monkeypatch.setattr(llm, "_client", lambda: client)
    assert llm.chat_line(CTX) == "Could be Priya or Leo."
    sent = client.calls[0]
    assert sent["model"] == "gpt-5-mini"
    assert [m["role"] for m in sent["messages"]] == ["system", "user"]


@pytest.mark.parametrize("kwargs", [
    {"refusal": "I can't help with that."},
    {"content": "x", "finish": "content_filter"},
    {"content": "   "},
    {"error": openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))},
])
def test_problems_return_none(monkeypatch, kwargs) -> None:
    monkeypatch.setattr(llm, "_client", lambda: fake(**kwargs))
    assert llm.chat_line(CTX) is None


def test_no_key_means_no_call() -> None:
    assert llm._client() is None  # OPENAI_API_KEY is empty in tests
    assert llm.chat_line(CTX) is None
