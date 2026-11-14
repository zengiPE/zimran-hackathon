"""Retention loop: after the reveal the same crew opens its next case, behind the paywall,
and sees its record (cases solved, streak) grow."""

import secrets

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import get_settings
from app.db import get_engine
from app.game_models import Case
from app.main import app
from app.payments.models import Payment

client = TestClient(app)


def solo(seed: int | None = None) -> dict:
    body = {"solo": {"me": "Ann"}}
    if seed is not None:
        body["seed"] = seed
    resp = client.post("/api/cases", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def culprit(case_id: str) -> int:
    with Session(get_engine()) as s:
        return s.get(Case, case_id).data["solution"]["culprit"]


def play_to_reveal(case: dict, correct: bool) -> None:
    cid, tok = case["case_id"], case["invites"][0]["token"]
    client.get(f"/api/cases/{cid}/me", params={"token": tok})
    for _ in range(case["days"]):  # day 1 -> days+1 = voting
        client.post(f"/api/cases/{cid}/advance", json={"host_token": case["host_token"]})
    answer = culprit(cid) if correct else (culprit(cid) + 1) % 5
    resp = client.post(f"/api/cases/{cid}/vote", json={"token": tok, "suspect": answer})
    assert resp.json()["phase"] == "reveal", resp.text


def pay(case_id: str, plan: str = "case") -> None:
    with Session(get_engine()) as s:
        s.add(Payment(id=f"cs_test_{secrets.token_hex(4)}", case_id=case_id, plan=plan,
                      amount_cents=1200 if plan == "case" else 799, status="paid"))
        s.commit()


def me(case_id: str, token: str) -> dict:
    return client.get(f"/api/cases/{case_id}/me", params={"token": token}).json()


def test_next_case_keeps_the_crew_and_rotates_theme() -> None:
    first = solo(seed=31)
    play_to_reveal(first, correct=True)
    tok = first["invites"][0]["token"]

    resp = client.post(f"/api/cases/{first['case_id']}/next", json={"token": tok})
    assert resp.status_code == 201, resp.text
    nxt = resp.json()
    assert nxt["case_id"] != first["case_id"]
    assert [(i["name"], i["ai"]) for i in nxt["invites"]] == \
        [(i["name"], i["ai"]) for i in first["invites"]]
    assert nxt["theme"] == "office-party"  # lake-house -> office-party
    assert nxt["you"]["idx"] == 0

    # Idempotent: a second click (or another player) gets the same case
    again = client.post(f"/api/cases/{first['case_id']}/next",
                        json={"host_token": first["host_token"]}).json()
    assert again["case_id"] == nxt["case_id"] and again["you"] is None

    # Old links lead every player to their own seat in the new case
    old = me(first["case_id"], tok)
    assert old["next_case"]["case_id"] == nxt["case_id"]
    assert old["next_case"]["url"] == nxt["invites"][0]["url"]
    host = client.get(f"/api/cases/{first['case_id']}/host",
                      params={"token": first["host_token"]}).json()
    assert host["next_case"]["host_url"] == nxt["host_url"]

    # The new case is case #2 of the crew; AI teammates keep their personas and play
    state = me(nxt["case_id"], nxt["invites"][0]["token"])
    assert state["crew"]["case_number"] == 2
    assert state["crew"]["cases_played"] == 1 and state["crew"]["streak"] == 1
    assert len([b for b in state["board"] if b["is_ai"]]) == 3


def test_streak_and_records_across_cases() -> None:
    first = solo()
    play_to_reveal(first, correct=True)
    second = client.post(f"/api/cases/{first['case_id']}/next",
                         json={"token": first["invites"][0]["token"]}).json()
    play_to_reveal(second, correct=True)
    rev = client.get(f"/api/cases/{second['case_id']}/reveal").json()
    assert rev["crew"]["cases_solved"] == 2 and rev["crew"]["streak"] == 2
    ann = rev["crew"]["members"][0]
    assert ann == {"name": "Ann", "is_ai": False, "played": 2, "correct": 2}
    assert all(m["played"] == 2 for m in rev["crew"]["members"])  # AI votes counted too

    third = client.post(f"/api/cases/{second['case_id']}/next",
                        json={"token": second["invites"][0]["token"]}).json()
    play_to_reveal(third, correct=False)
    crew = client.get(f"/api/cases/{third['case_id']}/reveal").json()["crew"]
    assert crew["cases_played"] == 3 and crew["cases_solved"] == 2 and crew["streak"] == 0
    assert [h["solved"] for h in crew["history"]] == [True, True, False]


def test_paywall_gates_the_next_case(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "stripe_secret_key", "sk_test_dummy")
    first = solo()
    play_to_reveal(first, correct=True)
    tok = first["invites"][0]["token"]
    url = f"/api/cases/{first['case_id']}/next"

    access = me(first["case_id"], tok)["next_access"]
    assert access == {"requires_payment": True, "paid": False, "plan": None,
                      "payments_enabled": True}
    assert client.post(url, json={"token": tok}).status_code == 402

    pay(first["case_id"])
    assert me(first["case_id"], tok)["next_access"]["paid"] is True
    second = client.post(url, json={"token": tok})
    assert second.status_code == 201

    # A one-off payment covers one case: the next one asks again
    second = second.json()
    play_to_reveal(second, correct=True)
    assert client.post(f"/api/cases/{second['case_id']}/next",
                       json={"token": second["invites"][0]["token"]}).status_code == 402


def test_club_subscription_unlocks_every_next_case(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "stripe_secret_key", "sk_test_dummy")
    first = solo()
    play_to_reveal(first, correct=True)
    pay(first["case_id"], plan="monthly")
    second = client.post(f"/api/cases/{first['case_id']}/next",
                         json={"token": first["invites"][0]["token"]}).json()
    play_to_reveal(second, correct=True)
    resp = client.post(f"/api/cases/{second['case_id']}/next",
                       json={"token": second["invites"][0]["token"]})
    assert resp.status_code == 201
    assert me(second["case_id"], second["invites"][0]["token"])["next_access"]["plan"] == \
        "monthly"


def test_next_case_rules() -> None:
    case = solo()
    url = f"/api/cases/{case['case_id']}/next"
    assert client.post(url, json={"token": case["invites"][0]["token"]}).status_code == 409
    assert client.post(url, json={"token": "nope"}).status_code == 403
    assert client.post(url, json={}).status_code == 403
    # During play the crew view has stats but no next-case block
    state = me(case["case_id"], case["invites"][0]["token"])
    assert state["crew"]["case_number"] == 1 and "next_case" not in state
    play_to_reveal(case, correct=True)
    assert client.post(url, json={"token": case["invites"][0]["token"],
                                  "theme": "nope"}).status_code == 422
