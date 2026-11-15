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


def test_sends_minimal_reasoning_effort(monkeypatch) -> None:
    client = fake(content="Could be Priya.")
    monkeypatch.setattr(llm, "_client", lambda: client)
    llm.chat_line(CTX)
    assert client.calls[0]["reasoning_effort"] == "minimal"


@pytest.mark.parametrize("model, effort, expected", [
    ("gpt-5-mini", "minimal", "minimal"),
    ("gpt-5", "minimal", "minimal"),
    ("gpt-5-nano", "low", "low"),
    ("gpt-5-chat-latest", "minimal", None),  # chat variant takes no reasoning_effort
    ("gpt-4.1-mini", "minimal", None),
    ("gpt-4o-mini", "minimal", None),
    ("o4-mini", "minimal", "low"),  # o-series has no "minimal"
    ("o3", "high", "high"),
    ("gpt-5-mini", "", None),
    (" GPT-5-Mini ", "Minimal", "minimal"),
])
def test_reasoning_effort_only_for_reasoning_models(model, effort, expected) -> None:
    from app.llm_client import reasoning_effort_for

    assert reasoning_effort_for(model, effort) == expected


def test_non_reasoning_model_gets_no_reasoning_effort(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "openai_model", "gpt-4.1-mini")
    client = fake(content="Could be Priya.")
    monkeypatch.setattr(llm, "_client", lambda: client)
    assert llm.chat_line(CTX) == "Could be Priya."
    assert "reasoning_effort" not in client.calls[0]


def _bad_request(msg: str) -> openai.BadRequestError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return openai.BadRequestError(msg, response=httpx.Response(400, request=req), body=None)


def flaky(first_error, content="Could be Priya."):
    """Fails the first call with first_error, then answers."""
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise first_error
        msg = SimpleNamespace(content=content, refusal=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
                           calls=calls)


def test_rejected_reasoning_effort_is_retried_without_it(monkeypatch) -> None:
    client = flaky(_bad_request("Unsupported parameter: 'reasoning_effort' is not supported "
                                "with this model."))
    monkeypatch.setattr(llm, "_client", lambda: client)
    assert llm.chat_line(CTX) == "Could be Priya."
    assert len(client.calls) == 2
    assert client.calls[0]["reasoning_effort"] == "minimal"
    assert "reasoning_effort" not in client.calls[1]


def test_other_bad_requests_are_not_retried(monkeypatch) -> None:
    client = flaky(_bad_request("Invalid value for 'messages'."))
    monkeypatch.setattr(llm, "_client", lambda: client)
    assert llm.chat_line(CTX) is None  # template fallback, no second call
    assert len(client.calls) == 1


def test_empty_reasoning_effort_is_not_sent(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "openai_reasoning_effort", "")
    client = fake(content="Could be Priya.")
    monkeypatch.setattr(llm, "_client", lambda: client)
    llm.chat_line(CTX)
    assert "reasoning_effort" not in client.calls[0]
