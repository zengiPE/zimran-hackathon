from types import SimpleNamespace

import httpx
import openai
import pytest

from app.story import THEMES, ClueFact, get_theme, narrate_case, template_clue, validate_text
from app.story.narrative import _LLMBatch, _LLMClue

LAKE = get_theme("lake-house")

FACTS = [
    ClueFact("f1", "Maya was not in the Kitchen.", ("Maya", "Kitchen")),
    ClueFact("f2", "Whoever had a fishing rod arrived before Leo.", ("a fishing rod", "Leo")),
    ClueFact("f3", "Either Priya or Sam was on the Porch at 8:00 PM.", ("Priya", "Sam", "Porch", "8:00 PM")),
]


class FakeClient:
    """Stands in for openai.OpenAI: returns canned texts as JSON, or raises."""

    def __init__(self, texts=None, error=None, refusal=None, raw=None):
        self.calls = 0
        self.kwargs = None
        self._texts, self._error, self._refusal, self._raw = texts or {}, error, refusal, raw
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        if self._error:
            raise self._error
        batch = _LLMBatch(clues=[_LLMClue(fact_id=k, text=v) for k, v in self._texts.items()])
        content = self._raw if self._raw is not None else batch.model_dump_json()
        message = SimpleNamespace(content=None if self._refusal else content,
                                  refusal=self._refusal)
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])


# --- themes ------------------------------------------------------------------------------


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda t: t.id)
def test_theme_grid_is_complete_and_unique(theme):
    for values in (theme.suspect_names, theme.rooms, theme.times, theme.items):
        assert len(values) == 5
        assert len({v.lower() for v in values}) == 5
    vocab = [*theme.suspect_names, *theme.rooms, *theme.times, *theme.items]
    assert len({v.lower() for v in vocab}) == len(vocab), "a value appears in two categories"
    assert theme.formats and theme.witnesses


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda t: t.id)
def test_witnesses_are_not_suspects(theme):
    for w in theme.witnesses:
        for name in theme.suspect_names:
            assert name.lower() not in w.lower()


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda t: t.id)
def test_intro_mentions_room_and_time(theme):
    intro = theme.intro(theme.rooms[2], theme.times[3])
    assert theme.rooms[2] in intro and theme.times[3] in intro


def test_room_prepositions():
    assert LAKE.at_room("Kitchen") == "in the Kitchen"
    assert LAKE.at_room("Porch") == "on the Porch"
    assert get_theme("office-party").at_room("Rooftop") == "on the Rooftop"


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda t: t.id)
def test_on_rooms_are_real_rooms(theme):
    assert theme.on_rooms <= set(theme.rooms)


def test_unknown_theme():
    with pytest.raises(ValueError):
        get_theme("haunted-castle")


# --- validation ----------------------------------------------------------------------------


def test_validation_accepts_faithful_text():
    assert validate_text(LAKE, FACTS[0], "Rosa texted: Maya never set foot in the Kitchen all night.") is None


@pytest.mark.parametrize(
    "text, reason",
    [
        ("Rosa texted: she never went in the Kitchen.", "missing mention 'Maya'"),
        ("Maya was not in the Kitchen, but Jordan was.", "mentions unrelated 'Jordan'"),
        ("Maya was not in the Kitchen; she was in the Loft.", "mentions unrelated 'Loft'"),
        ("Maya skipped the Kitchen and played with a deck of cards.", "mentions unrelated 'a deck of cards'"),
        ("Maya was not in the Kitchen at 9:00 PM.", "mentions unrelated '9:00 PM'"),
        ("", "empty"),
    ],
)
def test_validation_rejects(text, reason):
    assert validate_text(LAKE, FACTS[0], text) == reason


def test_validation_rejects_long_text():
    assert validate_text(LAKE, FACTS[0], "Maya was not in the Kitchen. " + "x" * 400).startswith("too long")


def test_validation_matches_whole_words_only():
    # "Sam" must not be found inside "same"; "8:00" must not match "18:00"
    fact = ClueFact("x", "Maya was not in the Kitchen.", ("Maya", "Kitchen"))
    assert validate_text(LAKE, fact, "Same as always: Maya was not in the Kitchen.") is None
    # names ending in "am"/"pm" are not times: "Sam" must stay "Sam"
    sam = ClueFact("s", "Sam was not on the Porch.", ("Sam", "Porch"))
    assert validate_text(LAKE, sam, "Sam was not on the Porch.") is None
    assert validate_text(LAKE, sam, "S was not on the Porch.") == "missing mention 'Sam'"
    time_fact = ClueFact("t", "Leo arrived at 8:00 PM.", ("Leo", "8:00 PM"))
    assert validate_text(LAKE, time_fact, "Leo arrived at 18:00.") == "missing mention '8:00 PM'"


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda t: t.id)
def test_every_template_passes_validation(theme):
    s, r, t, i = theme.suspect_names, theme.rooms, theme.times, theme.items
    facts = [
        ClueFact(f"a{n}", f"{s[n]} was not in the {r[n]}.", (s[n], r[n])) for n in range(5)
    ] + [
        ClueFact(f"b{n}", f"Whoever had {i[n]} arrived after {t[n]}.", (i[n], t[n])) for n in range(5)
    ]
    for fact in facts:  # covers every format/witness combination many times over
        clue = template_clue(theme, fact)
        assert validate_text(theme, fact, clue.text) is None, clue.text
        assert clue.source == "template" and clue.statement == fact.statement


# --- narrate_case --------------------------------------------------------------------------


def test_llm_texts_used_when_valid():
    client = FakeClient(
        texts={
            "f1": "Text from Rosa, the caretaker: Maya swore she never entered the Kitchen.",
            "f2": "Mr. Dunn noticed whoever carried a fishing rod showed up before Leo did.",
            "f3": "Guestbook: it was either Priya or Sam out on the Porch at 8:00 PM, laughing.",
        }
    )
    clues = narrate_case(LAKE, FACTS, client=client)
    assert client.calls == 1, "all clues of a case come from a single LLM call"
    assert client.kwargs["response_format"] == {"type": "json_object"}
    assert [c.source for c in clues] == ["llm", "llm", "llm"]
    assert [c.fact_id for c in clues] == ["f1", "f2", "f3"]
    assert all(c.statement == f.statement for c, f in zip(clues, FACTS))


def test_bad_llm_text_falls_back_per_clue():
    client = FakeClient(
        texts={
            "f1": "Text from Rosa: Maya swore she never entered the Kitchen.",
            "f2": "Leo arrived after Jordan, who had a fishing rod.",  # invents a fact about Jordan
            # f3 missing from the response entirely
        }
    )
    clues = narrate_case(LAKE, FACTS, client=client)
    assert [c.source for c in clues] == ["llm", "template", "template"]


@pytest.mark.parametrize(
    "error",
    [
        openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")),
        openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")),
    ],
)
def test_api_failure_uses_templates(error):
    clues = narrate_case(LAKE, FACTS, client=FakeClient(error=error))
    assert [c.source for c in clues] == ["template"] * 3


def test_refusal_uses_templates():
    client = FakeClient(texts={"f1": "Maya was not in the Kitchen."}, refusal="I can't help.")
    assert all(c.source == "template" for c in narrate_case(LAKE, FACTS, client=client))


@pytest.mark.parametrize("raw", ["not json at all", '{"clues": "oops"}', ""])
def test_malformed_json_uses_templates(raw):
    clues = narrate_case(LAKE, FACTS, client=FakeClient(raw=raw))
    assert [c.source for c in clues] == ["template"] * 3


def test_no_api_key_uses_templates(monkeypatch):
    monkeypatch.setattr("app.story.narrative._default_client", lambda: None)
    assert all(c.source == "template" for c in narrate_case(LAKE, FACTS))


def test_templates_are_deterministic():
    a = narrate_case(LAKE, FACTS, use_llm=False)
    b = narrate_case(LAKE, FACTS, use_llm=False)
    assert a == b


def test_duplicate_fact_ids_rejected():
    with pytest.raises(ValueError):
        narrate_case(LAKE, [FACTS[0], FACTS[0]], use_llm=False)
