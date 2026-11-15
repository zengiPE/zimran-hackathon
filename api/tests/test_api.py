"""End-to-end game flow through the HTTP API (demo mode)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
NAMES = ["Ann", "Bo", "Cy", "Di"]


def create(demo: bool = True, **extra) -> dict:
    resp = client.post("/api/cases", json={"players": NAMES, "demo": demo, "seed": 7, **extra})
    assert resp.status_code == 201, resp.text
    return resp.json()


def me(case: dict, i: int) -> dict:
    resp = client.get(f"/api/cases/{case['case_id']}/me",
                      params={"token": case["invites"][i]["token"]})
    assert resp.status_code == 200, resp.text
    return resp.json()


def advance(case: dict) -> dict:
    resp = client.post(f"/api/cases/{case['case_id']}/advance",
                       json={"host_token": case["host_token"]})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_themes() -> None:
    ids = {t["id"] for t in client.get("/api/themes").json()}
    assert ids == {"lake-house", "office-party"}


def test_full_demo_game() -> None:
    case = create()
    assert case["days"] == 3
    assert len(case["invites"]) == 4

    states = [me(case, i) for i in range(4)]
    texts = [s["my_clues"][0]["text"] for s in states]
    assert len(set(texts)) == 4, "every player sees a different clue"
    assert all(len(s["my_clues"]) == 1 for s in states)
    assert all(s["phase"] == "play" and s["day"] == 1 for s in states)
    assert "solution" not in states[0] and "key" not in states[0]["my_clues"][0]
    clue = states[0]["my_clues"][0]
    assert clue["story"] and clue["format"]  # template narration without an LLM key
    assert case["invites"][0]["url"].startswith("https://web.test/play/")

    host = client.get(f"/api/cases/{case['case_id']}/host",
                      params={"token": case["host_token"]}).json()
    assert all(p["joined"] and p["opened_today"] for p in host["players"])

    post = client.post(f"/api/cases/{case['case_id']}/board",
                       json={"token": case["invites"][0]["token"], "text": "Bo looks nervous"})
    assert post.status_code == 201
    assert me(case, 1)["board"][-1]["text"] == "Bo looks nervous"

    # Day 2: everyone except Di opens their clue
    assert advance(case)["day"] == 2
    for i in range(3):
        assert len(me(case, i)["my_clues"]) == 2

    # Day 3: Di's unopened day-2 clue is now shared with the group
    advance(case)
    shared_ids = {c["id"] for c in me(case, 0)["shared_clues"]}
    assert "d2p3" in shared_ids

    early = client.post(f"/api/cases/{case['case_id']}/vote",
                        json={"token": case["invites"][0]["token"], "suspect": 0})
    assert early.status_code == 409

    assert advance(case)["phase"] == "vote"
    assert client.get(f"/api/cases/{case['case_id']}/reveal").status_code == 409
    for i in range(4):
        resp = client.post(f"/api/cases/{case['case_id']}/vote",
                           json={"token": case["invites"][i]["token"], "suspect": i % 5})
        assert resp.status_code == 200
    assert resp.json()["phase"] == "reveal"

    rev = client.get(f"/api/cases/{case['case_id']}/reveal").json()
    assert rev["chain"][-1]["remaining"] == [rev["culprit"]["name"]]
    assert len(rev["truth"]) == 5
    assert len(rev["votes"]) == 4
    assert rev["stats"]["worlds_total"] == 120**3
    assert rev["stats"]["worlds_public"] < rev["stats"]["worlds_total"]


def test_hint_shares_a_key_clue() -> None:
    case = create()
    resp = client.post(f"/api/cases/{case['case_id']}/hint",
                       json={"host_token": case["host_token"]})
    assert resp.status_code == 200
    hinted = resp.json()["shared"]["id"]
    owner = int(hinted.split("p")[1])
    other = (owner + 1) % 4
    assert hinted in {c["id"] for c in me(case, other)["shared_clues"]}


def test_auth_and_validation() -> None:
    case = create()
    cid = case["case_id"]
    assert client.get(f"/api/cases/{cid}/me", params={"token": "nope"}).status_code == 403
    assert client.get(f"/api/cases/{cid}/host", params={"token": "nope"}).status_code == 403
    assert client.get("/api/cases/missing/me", params={"token": "x"}).status_code == 404
    assert client.post("/api/cases", json={"players": ["A", "B"]}).status_code == 422
    assert client.post("/api/cases", json={"players": NAMES, "theme": "x"}).status_code == 422

    real = create(demo=False)
    resp = client.post(f"/api/cases/{real['case_id']}/advance",
                       json={"host_token": real["host_token"]})
    assert resp.status_code == 409
    assert real["days"] == 5


def test_player_named_like_a_suspect_is_rejected() -> None:
    # Lake House suspects include Leo; case and spaces don't matter.
    resp = client.post("/api/cases", json={"players": ["Ann", " leo ", "Cy"], "theme": "lake-house",
                                           "demo": True})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "leo is a suspect in this story. Add an initial, like leo K."
    solo = client.post("/api/cases", json={"solo": {"me": "Maya"}, "theme": "lake-house"})
    assert solo.status_code == 422
    # With an initial it's fine, and Leo is not a suspect in the office story.
    ok = client.post("/api/cases", json={"players": ["Ann", "Leo K", "Cy"], "theme": "lake-house",
                                         "demo": True})
    assert ok.status_code == 201, ok.text
    assert client.post("/api/cases", json={"players": ["Ann", "Leo", "Cy"], "theme": "office-party",
                                           "demo": True}).status_code == 201
