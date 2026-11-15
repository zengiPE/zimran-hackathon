"""AI teammates: they only use what they know, they never claim more than the solver allows,
and a solo case plays from creation to reveal with no LLM at all."""

import random

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlmodel import Session, select

from app.ai import friends, llm
from app.ai.personas import PERSONAS
from app.config import get_settings
from app.db import add_missing_columns, get_engine
from app.engine import candidates, generate_case
from app.engine.facts import Fact
from app.game_models import BoardPost, Player
from app.main import app
from app.story import THEMES

client = TestClient(app)


def facts_of(case, pred):
    return [Fact.from_dict(c["fact"]) for c in case["clues"] if pred(c)]


# ---------- engine ----------

@pytest.mark.parametrize("seed", range(20))
def test_candidates_properties(seed: int) -> None:
    case = generate_case(seed, 4, 3)
    culprit = case["solution"]["culprit"]
    assert candidates(case, facts_of(case, lambda c: True)) == [culprit]
    for p in range(4):
        solo = candidates(case, facts_of(case, lambda c, p=p: c["player"] == p))
        assert len(solo) >= 2 and culprit in solo
    assert candidates(case, []) == candidates(case, [])


# ---------- personas and knowledge ----------

def test_persona_names_never_collide_with_theme_words() -> None:
    for theme in THEMES.values():
        vocab = {w.lower() for w in (*theme.suspect_names, *theme.rooms, *theme.items,
                                     *theme.witnesses)}
        for p in PERSONAS:
            assert p.name.lower() not in vocab
            assert all(p.name.lower() not in w for w in vocab)


def test_known_clues_exclude_other_private_clues() -> None:
    case = generate_case(3, 4, 3)
    known = friends.known_clues(case, 2, 2, set(), set())
    assert known and all(c["player"] == 2 and c["day"] <= 2 for c in known)
    other = next(c for c in case["clues"] if c["player"] == 0 and c["day"] == 1)
    with_board = friends.known_clues(case, 2, 2, set(), {other["id"]})
    assert other in with_board


@pytest.mark.parametrize("seed", range(40))
def test_template_lines_stay_within_candidates(seed: int, monkeypatch) -> None:
    monkeypatch.setattr(llm, "chat_line", lambda ctx: None)
    case = generate_case(seed, 4, 3, theme=sorted(THEMES)[seed % 2])
    rng = random.Random(seed)
    idx = seed % 4
    clues = friends.known_clues(case, idx, 1 + seed % 3, set(), set())
    poss = friends.suspect_names(case, friends.possible(case, clues))
    for persona in PERSONAS:
        for intent in ("hypothesis", "ask", "react"):
            text_, source = friends.write_line(case, persona, intent, rng, clues, poss, [],
                                               "Ann", poss[0])
            assert source == "template"
            mentioned = {m for c in clues for m in c["mentions"]}
            allowed = set(poss) if intent == "hypothesis" else set(poss) | mentioned
            assert friends.validate_reply(case["theme"], text_, allowed, mentioned | set(poss)) \
                is None, text_


def test_llm_line_is_validated(monkeypatch) -> None:
    case = generate_case(5, 4, 3)
    clues = friends.known_clues(case, 0, 1, set(), set())
    poss_ids = friends.possible(case, clues)
    poss = friends.suspect_names(case, poss_ids)
    outsider = next(s["name"] for s in case["suspects"] if s["id"] not in poss_ids) \
        if len(poss_ids) < 5 else None
    rng = random.Random(1)
    persona = PERSONAS[0]

    good = f"Honestly it could be {poss[0]} or {poss[1]}."
    monkeypatch.setattr(llm, "chat_line", lambda ctx: good)
    assert friends.write_line(case, persona, "hypothesis", rng, clues, poss, [], "Ann",
                              poss[0]) == (good, "llm")

    unknown_room = next(r for r in THEMES[case["theme"]].rooms
                        if all(r not in c["mentions"] for c in clues)
                        and r != case["labels"]["room"][case["crime_room"]])
    bad_lines = [f"It was totally someone in the {unknown_room}.", "x" * 400]
    if outsider:
        bad_lines.append(f"I bet it's {outsider}.")
    for bad in bad_lines:
        monkeypatch.setattr(llm, "chat_line", lambda ctx, bad=bad: bad)
        _, source = friends.write_line(case, persona, "hypothesis", rng, clues, poss, [],
                                       "Ann", poss[0])
        assert source == "template", bad


# ---------- solo game end to end (templates only) ----------

def me(case_id: str, token: str) -> dict:
    resp = client.get(f"/api/cases/{case_id}/me", params={"token": token})
    assert resp.status_code == 200, resp.text
    return resp.json()


def advance(case: dict) -> dict:
    resp = client.post(f"/api/cases/{case['case_id']}/advance",
                       json={"host_token": case["host_token"]})
    assert resp.status_code == 200, resp.text
    return resp.json()


def solo_case(seed: int = 7) -> dict:
    resp = client.post("/api/cases", json={"solo": {"me": "Ann"}, "seed": seed})
    assert resp.status_code == 201, resp.text
    return resp.json()


def ai_posts(state: dict) -> list[dict]:
    return [b for b in state["board"] if b["is_ai"]]


def test_solo_game_from_create_to_reveal() -> None:
    case = solo_case()
    cid = case["case_id"]
    human = case["invites"][0]
    assert not human["ai"] and [i["ai"] for i in case["invites"]] == [False, True, True, True]
    assert case["days"] == 3
    ai_names = {i["name"] for i in case["invites"] if i["ai"]}

    state = me(cid, human["token"])
    assert {p["name"] for p in state["players"] if p["is_ai"]} == ai_names
    shares = ai_posts(state)
    assert len(shares) == 3
    for post in shares:  # each AI shares only its own clue
        assert post["fact"]["from"] == post["author"]
    assert state["typing"] == []

    # Sharing someone else's clue is refused
    other = next(c for c in shares)["fact"]["id"]
    resp = client.post(f"/api/cases/{cid}/board",
                       json={"token": human["token"], "fact_id": other})
    assert resp.status_code == 403

    # Share my own clue: at least one AI answers
    mine = state["my_clues"][0]["id"]
    resp = client.post(f"/api/cases/{cid}/board",
                       json={"token": human["token"], "text": "Here's mine", "fact_id": mine})
    assert resp.status_code == 201 and resp.json()["fact"]["id"] == mine
    state = me(cid, human["token"])
    after = state["board"][[b["text"] for b in state["board"]].index("Here's mine") + 1:]
    assert 1 <= len([b for b in after if b["is_ai"]]) <= 2

    advance(case)
    advance(case)
    state = me(cid, human["token"])
    assert len([b for b in ai_posts(state) if b["fact"]]) == 9  # 3 AIs x 3 days

    assert advance(case)["phase"] == "vote"
    state = me(cid, human["token"])
    assert all(p["voted"] for p in state["players"] if p["is_ai"])
    assert state["phase"] == "vote"

    resp = client.post(f"/api/cases/{cid}/vote", json={"token": human["token"], "suspect": 0})
    assert resp.json()["phase"] == "reveal"
    rev = client.get(f"/api/cases/{cid}/reveal").json()
    assert {v["player"] for v in rev["votes"]} == ai_names | {"Ann"}
    assert rev["chain"][-1]["remaining"] == [rev["culprit"]["name"]]


def test_ai_votes_are_within_their_candidates() -> None:
    for seed in (1, 2, 3):
        case = solo_case(seed)
        for _ in range(3):
            advance(case)
        me(case["case_id"], case["invites"][0]["token"])  # triggers AI votes
        with Session(get_engine()) as s:
            from app.game_models import Case, Vote

            row = s.get(Case, case["case_id"])
            data = row.data
            board_ids = friends.board_fact_ids(s, row.id)
            votes = {v.player_idx: v.suspect
                     for v in s.exec(select(Vote).where(Vote.case_id == row.id)).all()}
            for idx in (1, 2, 3):
                known = friends.known_clues(data, idx, data["days"], set(row.shared), board_ids)
                assert votes[idx] in friends.possible(data, known)


def test_ai_posts_never_attach_foreign_facts() -> None:
    case = solo_case(11)
    for _ in range(2):
        advance(case)
    me(case["case_id"], case["invites"][0]["token"])
    with Session(get_engine()) as s:
        players = {p.idx: p for p in s.exec(
            select(Player).where(Player.case_id == case["case_id"])).all()}
        posts = s.exec(select(BoardPost).where(BoardPost.case_id == case["case_id"])).all()
        for post in posts:
            if post.is_ai and post.fact_clue_id:
                assert post.fact_clue_id.endswith(f"p{post.player_idx}")
                assert players[post.player_idx].is_ai


def test_typing_delay_hides_posts(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "ai_delay_scale", 100.0)
    case = solo_case(21)
    state = me(case["case_id"], case["invites"][0]["token"])
    assert ai_posts(state) == []
    assert sorted(state["typing"]) == sorted(i["name"] for i in case["invites"] if i["ai"])


# ---------- "Nora, anything about Leo?" ----------

def _replies_after(state: dict, text: str) -> list[dict]:
    texts = [b["text"] for b in state["board"]]
    return [b for b in state["board"][texts.index(text) + 1:] if b["is_ai"]]


def _belief(case_id: str, ai_name: str) -> tuple[dict, list[dict], list[str]]:
    """What the named AI knows and believes right now, straight from the engine."""
    from app.db import get_engine as _engine
    from app.game_models import Case

    with Session(_engine()) as s:
        case = s.get(Case, case_id)
        ai = s.exec(select(Player).where(Player.case_id == case_id,
                                         Player.name == ai_name)).one()
        data = case.data
        clues = friends.known_clues(data, ai.idx, 1, set(case.shared),
                                    friends.board_fact_ids(s, case_id))
        return data, clues, friends.suspect_names(data, friends.possible(data, clues))


@pytest.mark.parametrize("seed", [7, 11, 23])
@pytest.mark.parametrize("ai_name", ["Nora", "Felix", "Kai"])
def test_named_ai_answers_about_the_named_suspect(seed: int, ai_name: str) -> None:
    case = solo_case(seed)
    cid, human = case["case_id"], case["invites"][0]
    state = me(cid, human["token"])
    data = client.get(f"/api/cases/{cid}/me", params={"token": human["token"]}).json()
    for suspect in [s["name"] for s in data["suspects"]][:3]:
        question = f"{ai_name.lower()}, anything about {suspect}?"  # any case works
        resp = client.post(f"/api/cases/{cid}/board",
                           json={"token": human["token"], "text": question})
        assert resp.status_code == 201
        state = me(cid, human["token"])
        replies = _replies_after(state, question)
        assert replies and replies[0]["author"] == ai_name, replies
        answer = replies[0]["text"]
        assert suspect in answer

        _, _, poss = _belief(cid, ai_name)
        if poss == [suspect]:
            assert answer.startswith(f"It's {suspect}")
        elif suspect in poss:
            assert "Still possible" in answer
        else:
            assert f"{suspect} is out for me" in answer


def test_ruled_out_answer_cites_a_clue_that_really_rules_them_out() -> None:
    for seed in range(30):
        case = generate_case(seed=seed, theme="lake-house", players=4, days=3)
        clues = [c for c in case["clues"] if c["player"] == 1]
        poss = friends.possible(case, clues)
        out = [i for i in range(len(case["suspects"])) if i not in poss]
        for sid in out:
            reason = friends.ruling_out_clue(case, clues, sid)
            if reason is None:  # only several clues together rule them out
                continue
            rest = [c for c in clues if c["text"] != reason]
            assert sid in friends.possible(case, rest)
            assert reason in {c["text"] for c in clues}


def test_answer_lines_follow_the_engine() -> None:
    assert friends.answer_line(["Leo"], "Leo", None).startswith("It's Leo")
    assert "Still possible" in friends.answer_line(["Leo", "Maya"], "Leo", None)
    out = friends.answer_line(["Maya", "Sam"], "Leo", "Leo was not in the Kitchen.")
    assert out.startswith("Leo is out for me") and "Leo was not in the Kitchen." in out


def test_llm_answer_may_name_the_asked_suspect(monkeypatch) -> None:
    for seed in range(50):  # a case where this AI has already ruled someone out
        case = generate_case(seed=seed, theme="lake-house", players=4, days=3)
        clues = [c for c in case["clues"] if c["player"] == 1]
        poss = friends.suspect_names(case, friends.possible(case, clues))
        outsider = next((s["name"] for s in case["suspects"] if s["name"] not in poss), None)
        if outsider:
            break
    assert outsider
    monkeypatch.setattr(llm, "chat_line", lambda ctx: f"{outsider} is out for me.")
    text, source = friends.write_line(case, PERSONAS[0], "answer", random.Random(1), clues,
                                      poss, [], "Ann", outsider)
    assert source == "llm" and text == f"{outsider} is out for me."


@pytest.mark.parametrize("line", [
    "Leo's still on the list since he's in \"possible,\" but who knows.",
    "Leo is in possible for me.",
    "Per my_clues, Leo is out.",
])
def test_lines_quoting_prompt_fields_are_rejected(line: str) -> None:
    assert friends.validate_reply("lake-house", line, {"Leo"}, set()) == \
        "quotes the prompt's field names"


def test_plain_possible_wording_is_fine() -> None:
    assert friends.validate_reply("lake-house", "Leo is still possible for me.", {"Leo"},
                                  set()) is None


def test_first_named_picks_the_earliest_whole_word() -> None:
    names = ["Nora", "Kai", "Felix"]
    assert friends.first_named("hey KAI and nora", names) == "Kai"
    assert friends.first_named("Kaiser roll? Noranda?", names) is None
    assert friends.first_named("", names) is None


def test_mixed_seats_and_flag_off(monkeypatch) -> None:
    resp = client.post("/api/cases", json={
        "players": ["Ann", "Bo", {"name": "Robo", "ai": True}], "demo": True, "seed": 4})
    assert resp.status_code == 201
    assert [i["ai"] for i in resp.json()["invites"]] == [False, False, True]
    assert client.post("/api/cases", json={
        "players": [{"name": "A", "ai": True}] * 3}).status_code == 422

    case = resp.json()
    monkeypatch.setattr(get_settings(), "ai_friends_enabled", False)
    assert client.post("/api/cases", json={"solo": {"me": "Ann"}}).status_code == 409
    # With AI off, the AI seat behaves like a dropout: its clue becomes shared next day
    advance(case)
    shared = me(case["case_id"], case["invites"][0]["token"])["shared_clues"]
    assert "d1p2" in {c["id"] for c in shared}


def test_add_missing_columns_migrates_old_tables(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path}/old.db")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE players (token VARCHAR PRIMARY KEY, case_id VARCHAR, "
                          "idx INTEGER, name VARCHAR, joined_at DATETIME)"))
    added = add_missing_columns(engine)
    assert {"players.is_ai", "players.persona"} <= set(added)
    cols = {c["name"] for c in inspect(engine).get_columns("players")}
    assert {"is_ai", "persona"} <= cols
    assert add_missing_columns(engine) == []
