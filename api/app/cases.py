"""Case API: create a case, play it day by day, vote, reveal.

Players have no accounts: each one gets a private token in their invite link.
The organizer gets a separate host token for the host screen (and demo controls).
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app import crew
from app.ai import friends
from app.clock import aware, iso, next_unlock_at, phase_of, virtual_day
from app.config import get_settings
from app.db import SessionDep
from app.engine import GenerationError, explain, generate_case
from app.events import log_event
from app.game_models import BoardPost, Case, ClueOpen, Player, Vote, utcnow
from app.story import THEMES, ClueFact, get_theme, narrate_case

router = APIRouter(prefix="/api", tags=["cases"])


_aware, _iso = aware, iso


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


class NextIn(BaseModel):
    token: str | None = None  # any player of the finished case
    host_token: str | None = None
    theme: str | None = None  # default: the next theme in rotation


class VoteIn(BaseModel):
    token: str
    suspect: int


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


Seat = tuple[str, bool, str | None]  # name, is_ai, persona key


def _build_case(session: Session, seats: list[Seat], *, demo: bool, days: int, theme: str,
                suspects: int, seed: int | None, group_id: str | None = None,
                prev_case_id: str | None = None) -> tuple[Case, list[Player]]:
    """Generate, narrate and store a case with its seats."""
    seed = seed if seed is not None else secrets.randbelow(10**9)
    data = None
    for attempt in range(5):
        try:
            data = generate_case(seed + attempt, len(seats), days, suspects, theme)
            break
        except GenerationError:
            continue
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
    if data is None:
        raise HTTPException(500, "could not build a case, try again")
    _narrate(data)

    case = Case(id=secrets.token_urlsafe(6), host_token=secrets.token_urlsafe(12),
                data=data, demo=demo, group_id=group_id, prev_case_id=prev_case_id)
    session.add(case)
    players = [Player(token=secrets.token_urlsafe(9), case_id=case.id, idx=i, name=name,
                      is_ai=ai, persona=persona, joined_at=utcnow() if ai else None)
               for i, (name, ai, persona) in enumerate(seats)]
    session.add_all(players)
    session.commit()
    return case, players


def _case_out(case: Case, players: list[Player]) -> dict:
    return {
        "case_id": case.id,
        "host_token": case.host_token,
        "host_url": _url(f"/host/{case.id}?token={case.host_token}"),
        "days": case.data["days"],
        "theme": case.data["theme"],
        "invites": [{"idx": p.idx, "name": p.name, "token": p.token, "ai": bool(p.is_ai),
                     "url": _url(f"/play/{case.id}?token={p.token}")} for p in players],
    }


@router.post("/cases", status_code=201)
def create_case(body: CreateCase, session: SessionDep) -> dict:
    seats, demo, days = _seats(body)
    if any(not n for n, _ in seats):
        raise HTTPException(422, "player names must be non-empty")
    if body.theme not in THEMES:
        raise HTTPException(422, f"unknown theme {body.theme}")
    # A player called Leo in a story with a suspect Leo makes every clue ambiguous.
    # Only checked here: a crew's next case may switch stories, and that must not fail.
    suspects = {s.lower() for s in THEMES[body.theme].suspect_names}
    clash = next((n for n, ai in seats if not ai and n.lower() in suspects), None)
    if clash:
        raise HTTPException(422, f"{clash} is a suspect in this story. Add an initial, like {clash} K.")
    personas = iter(friends.personas_for(sum(ai for _, ai in seats)))
    full: list[Seat] = [(n, ai, next(personas).key if ai else None) for n, ai in seats]
    case, players = _build_case(session, full, demo=demo, days=days, theme=body.theme,
                                suspects=body.suspects, seed=body.seed)
    log_event(session, "created", case.id, actor="host", players=len(seats), days=days,
              theme=body.theme, demo=demo, ai_seats=sum(ai for _, ai in seats),
              solo=body.solo is not None)
    return _case_out(case, players)


def _crew_view(session: Session, case: Case, phase: str, idx: int | None) -> dict:
    """Crew stats, plus (after the reveal) how to get to the next case."""
    out: dict = {"crew": crew.summary(session, case)}
    if phase == "reveal":
        nxt = None
        if case.next_case_id:
            seat = session.exec(select(Player).where(Player.case_id == case.next_case_id,
                                                     Player.idx == idx)).first() \
                if idx is not None else None
            nxt = {"case_id": case.next_case_id,
                   "url": _url(f"/play/{case.next_case_id}?token={seat.token}") if seat else None}
        out["next_case"] = nxt
        out["next_access"] = crew.access(session, case)
    return out


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
        **_crew_view(session, case, snap.phase, player.idx),
    }


@router.get("/cases/{case_id}/host")
def host(case_id: str, token: str, session: SessionDep) -> dict:
    case = _load(session, case_id)
    _host(case, token)
    snap = _Snapshot(session, case)
    view = _crew_view(session, case, snap.phase, None)
    if view.get("next_case"):
        nxt = session.get(Case, case.next_case_id)
        view["next_case"]["host_url"] = _url(f"/host/{nxt.id}?token={nxt.host_token}")
    return {**snap.common(), "players": snap.player_rows(with_tokens=True),
            "votes_count": len(snap.votes), **view}


@router.post("/cases/{case_id}/next", status_code=201)
def next_case(case_id: str, body: NextIn, session: SessionDep) -> dict:
    """After the reveal: open the crew's next case. Same seats, new mystery, next theme.

    Idempotent: if someone already opened it, everyone gets the same case back.
    Needs a paid case or a Club subscription in the crew when Stripe is configured (402).
    """
    case = _load(session, case_id)
    me_idx = None
    if body.token:
        me_idx = _player(session, case, body.token).idx
    elif body.host_token:
        _host(case, body.host_token)
    else:
        raise HTTPException(403, "token or host_token required")
    snap = _Snapshot(session, case)
    if snap.phase != "reveal":
        raise HTTPException(409, f"finish this case first (phase: {snap.phase})")

    if not case.next_case_id:
        if crew.access(session, case)["requires_payment"]:
            raise HTTPException(402, "the next case needs a paid plan")
        theme = body.theme or crew.next_theme(snap.data["theme"])
        if theme not in THEMES:
            raise HTTPException(422, f"unknown theme {theme}")
        group = case.group_id or case.id
        seats: list[Seat] = [(p.name, bool(p.is_ai), p.persona) for p in snap.players]
        new, _ = _build_case(session, seats, demo=case.demo, days=snap.days, theme=theme,
                             suspects=len(snap.data["suspects"]), seed=None, group_id=group,
                             prev_case_id=case.id)
        case.group_id = group
        case.next_case_id = new.id
        session.add(case)
        session.commit()
        log_event(session, "created", new.id, actor="crew", players=len(seats),
                  days=snap.days, theme=theme, demo=case.demo, next_of=case.id)

    new = session.get(Case, case.next_case_id)
    players = session.exec(select(Player).where(Player.case_id == new.id)
                           .order_by(Player.idx)).all()
    out = _case_out(new, players)
    out["you"] = next((i for i in out["invites"] if i["idx"] == me_idx), None)
    return out


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
        "crew": crew.summary(session, case),
        "next_case_id": case.next_case_id,
        "next_access": crew.access(session, case),
        "stats": {
            "worlds_total": data["report"]["worlds_total"],
            "worlds_public": data["report"]["worlds_public"],
            "worlds_left": data["report"]["worlds_left"],
            "candidates_by_day": data["report"]["candidates_by_day"],
            "seed": data["seed"],
        },
    }
