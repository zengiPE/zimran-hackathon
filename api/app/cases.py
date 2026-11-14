"""Case API: create a case, play it day by day, vote, reveal.

Players have no accounts: each one gets a private token in their invite link.
The organizer gets a separate host token for the host screen (and demo controls).
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.ai import friends
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

class PlayerIn(BaseModel):
    name: str = Field(max_length=40)
    ai: bool = False  # an AI teammate takes this seat


class SoloIn(BaseModel):
    me: str = Field(min_length=1, max_length=40)


class CreateCase(BaseModel):
    theme: str = "lake-house"
    # Names, or {name, ai} objects to seat AI teammates. Not needed with `solo`.
    players: list[str | PlayerIn] | None = Field(default=None, max_length=6)
    # Solo: you + 3 AI teammates, 3 days, demo controls on.
    solo: SoloIn | None = None
    demo: bool = False
    days: int | None = Field(default=None, ge=2, le=5)
    suspects: int = Field(default=5, ge=4, le=5)
    seed: int | None = None


class HostAction(BaseModel):
    host_token: str


class BoardIn(BaseModel):
    token: str
    text: str = Field(default="", max_length=280)
    fact_id: str | None = None  # attach one of your own unlocked clues ("Share this clue")


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
        self.has_ai = friends.enabled() and any(p.is_ai for p in self.players)
        self._open_ai_clues(session)
        self.phase = phase_of(self.day, self.days, self.joined, self.votes)
        self._auto_share(session)
        if self.has_ai and friends.tick(session, self):
            self.phase = phase_of(self.day, self.days, self.joined, self.votes)

    def _open_ai_clues(self, session: Session) -> None:
        """AI seats read their clue the moment it unlocks, so it never counts as unopened.
        With AI turned off, their clues auto-share like a dropout's: the case stays solvable."""
        if not self.has_ai:
            return
        ai = {p.idx for p in self.players if p.is_ai}
        new = [c["id"] for c in self.data["clues"]
               if c["player"] in ai and c["day"] <= self.clue_day and c["id"] not in self.opened]
        if not new:
            return
        for cid in new:
            session.add(ClueOpen(case_id=self.case.id, clue_id=cid))
        try:
            session.commit()
        except IntegrityError:  # a concurrent request opened them first
            session.rollback()
        self.opened |= set(new)

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
                "is_ai": bool(p.is_ai),
                "joined": p.joined_at is not None,
                "opened_today": today in self.opened,
                "voted": p.idx in self.votes,
            }
            if with_tokens:
                row["token"] = p.token
                row["url"] = _url(f"/play/{self.case.id}?token={p.token}")
            rows.append(row)
        return rows

    def board(self, session: Session) -> tuple[list[dict], list[str]]:
        """Visible posts (oldest first, last 100) and names of AI seats still 'typing'."""
        now = utcnow()
        clues = {c["id"]: c for c in self.data["clues"]}
        posts = session.exec(select(BoardPost).where(BoardPost.case_id == self.case.id)
                             .order_by(BoardPost.id.desc()).limit(150)).all()
        visible, typing = [], set()
        for b in posts:
            if b.visible_at is not None and _aware(b.visible_at) > now:
                typing.add(self.names[b.player_idx])
            else:
                visible.append(b)
        visible.sort(key=lambda b: (_aware(b.visible_at or b.created_at), b.id or 0))
        rows = [{
            "author": self.names[b.player_idx],
            "text": b.text,
            "ts": _iso(b.visible_at or b.created_at),
            "is_ai": bool(b.is_ai),
            "fact": self.clue(clues[b.fact_clue_id]) if b.fact_clue_id in clues else None,
        } for b in visible[-100:]]
        return rows, sorted(typing)

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


def _seats(body: CreateCase) -> tuple[list[tuple[str, bool]], bool, int]:
    """(name, is_ai) per seat, demo flag, days."""
    if body.solo is not None:
        if not friends.enabled():
            raise HTTPException(409, "AI teammates are turned off")
        seats = [(body.solo.me, False)] + [(p.name, True) for p in friends.personas_for(3)]
        return [(n.strip()[:40], ai) for n, ai in seats], True, 3
    if not body.players or not 3 <= len(body.players) <= 6:
        raise HTTPException(422, "players must list 3 to 6 people (or use solo)")
    seats = [(p, False) if isinstance(p, str) else (p.name, p.ai) for p in body.players]
    seats = [(n.strip()[:40], ai) for n, ai in seats]
    if any(ai for _, ai in seats) and not friends.enabled():
        raise HTTPException(409, "AI teammates are turned off")
    if all(ai for _, ai in seats):
        raise HTTPException(422, "at least one seat must be a person")
    return seats, body.demo, body.days or (3 if body.demo else 5)


@router.post("/cases", status_code=201)
def create_case(body: CreateCase, session: SessionDep) -> dict:
    seats, demo, days = _seats(body)
    names = [n for n, _ in seats]
    if any(not n for n in names):
        raise HTTPException(422, "player names must be non-empty")
    if body.theme not in THEMES:
        raise HTTPException(422, f"unknown theme {body.theme}")
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
                data=data, demo=demo)
    session.add(case)
    personas = iter(friends.personas_for(sum(ai for _, ai in seats)))
    players = []
    for i, (name, ai) in enumerate(seats):
        persona = next(personas) if ai else None
        players.append(Player(token=secrets.token_urlsafe(9), case_id=case.id, idx=i, name=name,
                              is_ai=ai, persona=persona.key if persona else None,
                              joined_at=utcnow() if ai else None))
    session.add_all(players)
    session.commit()
    log_event(session, "created", case.id, actor="host", players=len(names), days=days,
              theme=body.theme, demo=demo, ai_seats=sum(ai for _, ai in seats),
              solo=body.solo is not None)
    return {
        "case_id": case.id,
        "host_token": case.host_token,
        "host_url": _url(f"/host/{case.id}?token={case.host_token}"),
        "days": days,
        "invites": [{"idx": p.idx, "name": p.name, "token": p.token, "ai": bool(p.is_ai),
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
    board, typing = snap.board(session)
    return {
        **snap.common(),
        "me": {"idx": player.idx, "name": player.name, "is_ai": bool(player.is_ai)},
        "my_clues": [snap.clue(c) for c in mine],
        "shared_clues": [snap.clue(c) for c in shared],
        "board": board,
        "typing": typing,
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
    text = body.text.strip()
    if not text and not body.fact_id:
        raise HTTPException(422, "write something or attach a clue")
    snap = _Snapshot(session, case)
    clue = None
    if body.fact_id:
        clue = next((c for c in snap.data["clues"] if c["id"] == body.fact_id), None)
        if clue is None or clue["player"] != player.idx or clue["day"] > snap.clue_day:
            raise HTTPException(403, "you can only share your own unlocked clue")
    post = BoardPost(case_id=case.id, player_idx=player.idx, text=text,
                     fact_clue_id=body.fact_id, is_ai=False)
    session.add(post)
    session.commit()
    session.refresh(post)
    out = {"author": player.name, "text": post.text, "ts": _iso(post.created_at),
           "is_ai": False, "fact": snap.clue(clue) if clue else None}
    if snap.has_ai and not player.is_ai:
        board, _ = snap.board(session)
        recent = [f"{b['author']}: {b['text']}"
                  + (f" [shared clue: {b['fact']['text']}]" if b["fact"] else "")
                  for b in board[-6:]]
        friends.respond(session, snap, player, post, recent)
    return out


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
