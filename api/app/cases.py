"""Case API: create a case, play it day by day, vote, reveal.

Players have no accounts: each one gets a private token in their invite link.
The organizer gets a separate host token for the host screen (and demo controls).
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.config import get_settings
from app.db import SessionDep
from app.engine import GenerationError, explain, generate_case
from app.events import log_event
from app.game_models import BoardPost, Case, ClueOpen, Player, Vote, utcnow
from app.story import THEMES, ClueFact, get_theme, narrate_case

router = APIRouter(prefix="/api", tags=["cases"])


def _aware(dt: datetime) -> datetime:
    """SQLite hands datetimes back without a timezone; they are stored as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _iso(dt: datetime) -> str:
    return _aware(dt).isoformat()


# ---------- request bodies ----------

class CreateCase(BaseModel):
    theme: str = "lake-house"
    players: list[str] = Field(min_length=3, max_length=6)
    demo: bool = False
    days: int | None = Field(default=None, ge=2, le=5)
    suspects: int = Field(default=5, ge=4, le=5)
    seed: int | None = None


class HostAction(BaseModel):
    host_token: str


class BoardIn(BaseModel):
    token: str
    text: str = Field(min_length=1, max_length=280)


class VoteIn(BaseModel):
    token: str
    suspect: int


# ---------- game clock ----------

def virtual_day(case: Case) -> int:
    """1-based day of the case: real days elapsed since start plus days skipped in demo."""
    elapsed = (utcnow() - _aware(case.started_at)).total_seconds()
    return 1 + int(elapsed // case.day_seconds) + case.day_offset


def next_unlock_at(case: Case) -> str:
    start = _aware(case.started_at)
    real_days = int((utcnow() - start).total_seconds() // case.day_seconds)
    return _iso(start + timedelta(seconds=(real_days + 1) * case.day_seconds))


def phase_of(day: int, days: int, joined: set[int], votes: dict[int, int]) -> str:
    if day <= days:
        return "play"
    if day >= days + 2:
        return "reveal"
    if joined and joined <= votes.keys():
        return "reveal"
    return "vote"


# ---------- helpers ----------

def _url(path: str) -> str:
    return get_settings().public_web_url.rstrip("/") + path


def _load(session: Session, case_id: str) -> Case:
    case = session.get(Case, case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    return case


def _player(session: Session, case: Case, token: str) -> Player:
    player = session.get(Player, token)
    if player is None or player.case_id != case.id:
        raise HTTPException(403, "invalid player token")
    return player


def _host(case: Case, token: str) -> None:
    if not secrets.compare_digest(case.host_token, token):
        raise HTTPException(403, "invalid host token")


class _Snapshot:
    """Everything one request needs about a case's live state."""

    def __init__(self, session: Session, case: Case) -> None:
        self.case = case
        self.data = case.data
        self.days = self.data["days"]
        self.day = virtual_day(case)
        self.clue_day = min(self.day, self.days)
        self.players = session.exec(
            select(Player).where(Player.case_id == case.id).order_by(Player.idx)).all()
        self.names = [p.name for p in self.players]
        self.votes = {v.player_idx: v.suspect
                      for v in session.exec(select(Vote).where(Vote.case_id == case.id)).all()}
        self.opened = set(session.exec(
            select(ClueOpen.clue_id).where(ClueOpen.case_id == case.id)).all())
        self.joined = {p.idx for p in self.players if p.joined_at is not None}
        self.phase = phase_of(self.day, self.days, self.joined, self.votes)
        self._auto_share(session)

    def _auto_share(self, session: Session) -> None:
        """A clue nobody opened within its day becomes visible to the whole group."""
        shared = set(self.case.shared)
        late = {c["id"] for c in self.data["clues"]
                if c["day"] < self.day and c["id"] not in self.opened}
        if not late <= shared:
            self.case.shared = sorted(shared | late)
            session.add(self.case)
            session.commit()

    def clue(self, c: dict) -> dict:
        return {
            "id": c["id"],
            "day": c["day"],
            "text": c["text"],
            "story": c.get("story"),
            "format": c.get("format"),
            "fact": c["fact"],
            "from": self.names[c["player"]],
        }

    def player_rows(self, with_tokens: bool = False) -> list[dict]:
        rows = []
        for p in self.players:
            today = f"d{self.clue_day}p{p.idx}"
            row = {
                "idx": p.idx,
                "name": p.name,
                "joined": p.joined_at is not None,
                "opened_today": today in self.opened,
                "voted": p.idx in self.votes,
            }
            if with_tokens:
                row["token"] = p.token
                row["url"] = _url(f"/play/{self.case.id}?token={p.token}")
            rows.append(row)
        return rows

    def common(self) -> dict:
        return {
            "case_id": self.case.id,
            "title": self.data["title"],
            "intro": self.data["intro"],
            "demo": self.case.demo,
            "day": self.clue_day,
            "days_total": self.days,
            "phase": self.phase,
            "next_unlock_at": next_unlock_at(self.case),
            "suspects": self.data["suspects"],
            "labels": self.data["labels"],
        }


# ---------- routes ----------

@router.get("/themes")
def themes() -> list[dict]:
    return [{"id": t.id, "title": t.title, "tagline": t.tagline} for t in THEMES.values()]


def _narrate(data: dict) -> None:
    """Restyle every clue once, at creation (LLM if configured, templates otherwise)."""
    theme = get_theme(data["theme"])
    facts = [ClueFact(c["id"], c["text"], tuple(c["mentions"])) for c in data["clues"]]
    for clue, out in zip(data["clues"], narrate_case(theme, facts)):
        clue["story"] = out.text
        clue["format"] = out.format_label
        clue["story_source"] = out.source


@router.post("/cases", status_code=201)
def create_case(body: CreateCase, session: SessionDep) -> dict:
    names = [n.strip()[:40] for n in body.players]
    if any(not n for n in names):
        raise HTTPException(422, "player names must be non-empty")
    if body.theme not in THEMES:
        raise HTTPException(422, f"unknown theme {body.theme}")
    days = body.days or (3 if body.demo else 5)
    seed = body.seed if body.seed is not None else secrets.randbelow(10**9)
    data = None
    for attempt in range(5):
        try:
            data = generate_case(seed + attempt, len(names), days, body.suspects, body.theme)
            break
        except GenerationError:
            continue
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
    if data is None:
        raise HTTPException(500, "could not build a case, try again")
    _narrate(data)

    case = Case(id=secrets.token_urlsafe(6), host_token=secrets.token_urlsafe(12),
                data=data, demo=body.demo)
    session.add(case)
    players = [Player(token=secrets.token_urlsafe(9), case_id=case.id, idx=i, name=n)
               for i, n in enumerate(names)]
    session.add_all(players)
    session.commit()
    log_event(session, "created", case.id, actor="host", players=len(names), days=days,
              theme=body.theme, demo=body.demo)
    return {
        "case_id": case.id,
        "host_token": case.host_token,
        "host_url": _url(f"/host/{case.id}?token={case.host_token}"),
        "days": days,
        "invites": [{"idx": p.idx, "name": p.name, "token": p.token,
                     "url": _url(f"/play/{case.id}?token={p.token}")} for p in players],
    }


@router.get("/cases/{case_id}/me")
def me(case_id: str, token: str,session: SessionDep) -> dict:
    case = _load(session, case_id)
    player = _player(session, case, token)
    snap = _Snapshot(session, case)

    mine = [c for c in snap.data["clues"]
            if c["player"] == player.idx and c["day"] <= snap.clue_day]
    events: list[tuple[str, dict]] = []
    if player.joined_at is None:
        player.joined_at = utcnow()
        session.add(player)
        snap.joined.add(player.idx)
        events.append(("joined", {}))
    for c in mine:  # viewing your clue counts as opening it
        if c["id"] not in snap.opened:
            session.add(ClueOpen(case_id=case.id, clue_id=c["id"]))
            snap.opened.add(c["id"])
            events.append(("clue_opened", {"clue_id": c["id"], "day": c["day"]}))
    if events:
        session.commit()
        for kind, extra in events:
            log_event(session, kind, case.id, actor=player.name, **extra)

    shared_ids = set(case.shared)
    shared = [c for c in snap.data["clues"] if c["player"] != player.idx and c["id"] in shared_ids]
    board = session.exec(select(BoardPost).where(BoardPost.case_id == case.id)
                         .order_by(BoardPost.id.desc()).limit(100)).all()
    return {
        **snap.common(),
        "me": {"idx": player.idx, "name": player.name},
        "my_clues": [snap.clue(c) for c in mine],
        "shared_clues": [snap.clue(c) for c in shared],
        "board": [{"author": snap.names[b.player_idx], "text": b.text,
                   "ts": _iso(b.created_at)} for b in reversed(board)],
        "players": snap.player_rows(),
        "my_vote": snap.votes.get(player.idx),
    }


@router.get("/cases/{case_id}/host")
def host(case_id: str, token: str,session: SessionDep) -> dict:
    case = _load(session, case_id)
    _host(case, token)
    snap = _Snapshot(session, case)
    return {**snap.common(), "players": snap.player_rows(with_tokens=True),
            "votes_count": len(snap.votes)}


@router.post("/cases/{case_id}/board", status_code=201)
def post_board(case_id: str, body: BoardIn, session: SessionDep) -> dict:
    case = _load(session, case_id)
    player = _player(session, case, body.token)
    post = BoardPost(case_id=case.id, player_idx=player.idx, text=body.text.strip())
    session.add(post)
    session.commit()
    return {"author": player.name, "text": post.text, "ts": _iso(post.created_at)}


@router.post("/cases/{case_id}/vote")
def vote(case_id: str, body: VoteIn, session: SessionDep) -> dict:
    case = _load(session, case_id)
    player = _player(session, case, body.token)
    if not 0 <= body.suspect < len(case.data["suspects"]):
        raise HTTPException(422, "unknown suspect")
    snap = _Snapshot(session, case)
    if snap.phase != "vote":
        raise HTTPException(409, f"voting is not open (phase: {snap.phase})")
    existing = session.get(Vote, (case.id, player.idx))
    if existing:
        existing.suspect = body.suspect
        session.add(existing)
    else:
        session.add(Vote(case_id=case.id, player_idx=player.idx, suspect=body.suspect))
    session.commit()
    log_event(session, "voted", case.id, actor=player.name, suspect=body.suspect)
    snap.votes[player.idx] = body.suspect
    phase = phase_of(snap.day, snap.days, snap.joined, snap.votes)
    if phase == "reveal":
        log_event(session, "revealed", case.id, actor=player.name)
    return {"ok": True, "phase": phase}


@router.post("/cases/{case_id}/advance")
def advance(case_id: str, body: HostAction, session: SessionDep) -> dict:
    """Demo mode: jump to the next day (after the last day: vote, then reveal)."""
    case = _load(session, case_id)
    _host(case, body.host_token)
    if not case.demo:
        raise HTTPException(409, "advance is only available in demo mode")
    if virtual_day(case) < case.data["days"] + 2:
        case.day_offset += 1
        session.add(case)
        session.commit()
    return host(case_id, body.host_token, session)


@router.post("/cases/{case_id}/hint")
def hint(case_id: str, body: HostAction, session: SessionDep) -> dict:
    """Share one key clue from an unlocked day with everyone (for a stuck group)."""
    case = _load(session, case_id)
    _host(case, body.host_token)
    snap = _Snapshot(session, case)
    shared = set(case.shared)
    candidates = [c for c in snap.data["clues"]
                  if c["key"] and c["day"] <= snap.clue_day and c["id"] not in shared]
    if not candidates:
        raise HTTPException(409, "no hint available yet")
    pick = min(candidates, key=lambda c: (c["day"], c["player"]))
    case.shared = sorted(shared | {pick["id"]})
    session.add(case)
    session.commit()
    return {"shared": snap.clue(pick)}


@router.get("/cases/{case_id}/reveal")
def reveal(case_id: str, session: SessionDep) -> dict:
    case = _load(session, case_id)
    snap = _Snapshot(session, case)
    if snap.phase != "reveal":
        raise HTTPException(409, f"not revealed yet (phase: {snap.phase})")
    data = snap.data
    sus = data["suspects"]
    culprit = data["solution"]["culprit"]
    truth = data["solution"]["truth"]
    labels = data["labels"]
    chain = [{
        **step,
        "from": snap.names[step["player"]],
        "eliminated": [sus[s]["name"] for s in step["eliminated"]],
        "remaining": [sus[s]["name"] for s in step["remaining"]],
    } for step in explain(data)]
    return {
        "case_id": case.id,
        "title": data["title"],
        "intro": data["intro"],
        "culprit": sus[culprit],
        "truth": [{"suspect": s["name"], "room": labels["room"][truth["room"][i]],
                   "time": labels["time"][truth["time"][i]],
                   "item": labels["item"][truth["item"][i]]} for i, s in enumerate(sus)],
        "chain": chain,
        "votes": [{"player": snap.names[p], "suspect": sus[s]["name"], "correct": s == culprit}
                  for p, s in sorted(snap.votes.items())],
        "stats": {
            "worlds_total": data["report"]["worlds_total"],
            "worlds_public": data["report"]["worlds_public"],
            "worlds_left": data["report"]["worlds_left"],
            "candidates_by_day": data["report"]["candidates_by_day"],
            "seed": data["seed"],
        },
    }
