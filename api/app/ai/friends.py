"""AI teammates: deterministic moves decided by the engine, worded by templates or the LLM.

What an AI seat knows (and nothing else):
  its own clues up to today + clues shared with the group (dropouts, hints)
  + clues anyone attached to a board post ("Share this clue").
What it believes = engine.candidates(those facts): exhaustive, never a guess.

Moves:
  each day      every AI posts its new clue (template line + the clue attached)
  human posts   1 AI replies (2 if the post changed two AIs' suspects): a hypothesis,
                a question about a suspect it can't rule out, or a reaction.
                A post that names an AI ("Nora, ...") is answered by that AI; a post that
                names a suspect gets an answer about that suspect (possible, or ruled out
                and by which of its clues), decided by the engine
  voting opens  every AI votes: its only candidate, else a seeded pick among candidates

Serverless-friendly: no background tasks. Posts are written right away with a future
`visible_at` (the 2-6 s "typing" delay); /me hides them until then and lists their authors
in `typing`. AiAction rows make every move idempotent across concurrent polls.
"""

from __future__ import annotations

import random
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.ai import llm
from app.ai.personas import BY_KEY, PERSONAS, Persona
from app.config import get_settings
from app.engine import candidates
from app.engine.facts import Fact
from app.game_models import AiAction, BoardPost, Player, Vote, utcnow
from app.story.narrative import _contains, _core
from app.story.themes import get_theme


def enabled() -> bool:
    return get_settings().ai_friends_enabled


def aware(dt: datetime) -> datetime:
    """SQLite hands datetimes back without a timezone; they are stored as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _delay(seconds: float) -> timedelta:
    return timedelta(seconds=seconds * get_settings().ai_delay_scale)


def personas_for(count: int) -> list[Persona]:
    return [PERSONAS[i % len(PERSONAS)] for i in range(count)]


def join_names(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " or " + names[-1]


# ---------- knowledge ----------

def board_fact_ids(session: Session, case_id: str, exclude_post: int | None = None) -> set[str]:
    rows = session.exec(select(BoardPost.id, BoardPost.fact_clue_id).where(
        BoardPost.case_id == case_id, BoardPost.fact_clue_id.is_not(None))).all()
    return {fid for pid, fid in rows if pid != exclude_post}


def known_clues(data: dict, idx: int, clue_day: int, shared_ids: set[str],
                board_ids: set[str]) -> list[dict]:
    """Clues an AI seat may use. Other players' private clues never get in here."""
    return [c for c in data["clues"]
            if (c["player"] == idx and c["day"] <= clue_day)
            or c["id"] in shared_ids or c["id"] in board_ids]


def possible(data: dict, clues: list[dict]) -> list[int]:
    return candidates(data, [Fact.from_dict(c["fact"]) for c in clues])


def suspect_names(data: dict, ids: list[int]) -> list[str]:
    return [data["suspects"][i]["name"] for i in ids]


# ---------- wording ----------

def validate_reply(theme_id: str, text: str, allowed_suspects: set[str],
                   allowed_terms: set[str]) -> str | None:
    """None if the line is acceptable; otherwise why it is not."""
    if not text or len(text) > llm.MAX_CHARS:
        return "empty or too long"
    if llm.LEAK_RE.search(text):
        return "quotes the prompt's field names"
    theme = get_theme(theme_id)
    for name in theme.suspect_names:
        if name not in allowed_suspects and _contains(text, name):
            return f"names {name!r}, who is not possible for this AI"
    allowed = {_core(t).lower() for t in allowed_terms}
    for term in (*theme.rooms, *theme.times, *theme.items):
        if _core(term).lower() not in allowed and _contains(text, term):
            return f"mentions {term!r}, which is not in its clues"
    return None


def answer_line(poss: list[str], x: str, reason: str | None) -> str:
    """Engine-true answer to "anything about X?": X is possible, the one left, or ruled out."""
    if poss == [x]:
        return f"It's {x}. My notes leave nobody else."
    if x in poss:
        return f"{x}? Still possible on my side. I can't rule {x} out: it's {join_names(poss)}."
    if reason:
        return f"{x} is out for me. My clue says: {reason} Still open: {join_names(poss)}."
    return f"{x} is out for me. Still open: {join_names(poss)}."


def template_line(persona: Persona, intent: str, rng: random.Random, poss: list[str],
                  who: str, x: str, reason: str | None = None) -> str:
    if intent == "answer":
        return answer_line(poss, x, reason)
    if intent == "hypothesis":
        options = persona.hypothesis_one if len(poss) == 1 else persona.hypothesis
    else:
        options = getattr(persona, intent)
    return rng.choice(options).format(cands=join_names(poss), one=poss[0], who=who, x=x)


def write_line(data: dict, persona: Persona, intent: str, rng: random.Random,
               clues: list[dict], poss: list[str], recent: list[str], who: str,
               x: str, reason: str | None = None) -> tuple[str, str]:
    """(text, source). The LLM if configured and the line passes validation, else a template."""
    mentioned = {m for c in clues for m in c.get("mentions", [])}
    labels = data["labels"]
    public_terms = {labels["room"][data["crime_room"]], labels["time"][data["crime_time"]]}
    if intent == "hypothesis":
        allowed_suspects = set(poss)
    else:
        allowed_suspects = set(poss) | (mentioned & set(suspect_names(data, range(len(
            data["suspects"])))))
    if intent == "answer":
        allowed_suspects.add(x)  # the suspect the human asked about
    ctx = llm.ReplyContext(
        persona_name=persona.name, persona_style=persona.style, intent=intent,
        intro=data["intro"], my_clues=[c["text"] for c in clues], possible=poss,
        recent=recent, who=who, x=x)
    text = llm.chat_line(ctx)
    if text and validate_reply(data["theme"], text, allowed_suspects,
                               mentioned | public_terms | set(poss)) is None:
        return text, "llm"
    return template_line(persona, intent, rng, poss, who, x, reason), "template"


def first_named(text: str, names: list[str]) -> str | None:
    """The name that appears first in the text (whole word, any case), or None."""
    hits = []
    for name in names:
        m = re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.IGNORECASE)
        if m:
            hits.append((m.start(), name))
    return min(hits)[1] if hits else None


def ruling_out_clue(data: dict, clues: list[dict], suspect_id: int) -> str | None:
    """A clue this AI knows without which the suspect would be possible again (its 'why')."""
    for c in clues:
        rest = [o for o in clues if o is not c]
        if suspect_id in possible(data, rest):
            return c["text"]
    return None


# ---------- moves ----------

def _once(session: Session, case_id: str, key: str, *rows) -> bool:
    session.add(AiAction(case_id=case_id, key=key))
    for row in rows:
        session.add(row)
    try:
        session.commit()
        return True
    except IntegrityError:  # another request made this move first
        session.rollback()
        return False


def tick(session: Session, snap) -> bool:
    """Daily clue posts and votes for AI seats. Returns True if any vote was cast."""
    ais = [p for p in snap.players if p.is_ai]
    if not ais or not enabled():
        return False
    case, data = snap.case, snap.data
    seed = data["seed"]
    done = set(session.exec(select(AiAction.key).where(AiAction.case_id == case.id)).all())
    now = utcnow()

    for k, p in enumerate(ais):
        persona = BY_KEY[p.persona]
        for d in range(1, snap.clue_day + 1):
            cid = f"d{d}p{p.idx}"
            key = f"share:{cid}"
            if key in done:
                continue
            rng = random.Random(f"{seed}:{key}")
            post = BoardPost(case_id=case.id, player_idx=p.idx, text=rng.choice(persona.share),
                             fact_clue_id=cid, is_ai=True,
                             visible_at=now + _delay(2 + 1.5 * k + 0.5 * (d - 1)))
            _once(session, case.id, key, post)

    voted = False
    if snap.phase == "vote":
        shared = set(case.shared)
        board_ids = board_fact_ids(session, case.id)
        for k, p in enumerate(ais):
            key = f"vote:{p.idx}"
            if p.idx in snap.votes or key in done:
                continue
            persona = BY_KEY[p.persona]
            poss = possible(data, known_clues(data, p.idx, snap.clue_day, shared, board_ids))
            rng = random.Random(f"{seed}:{key}")
            pick = poss[0] if len(poss) == 1 else rng.choice(poss)
            name = data["suspects"][pick]["name"]
            post = BoardPost(case_id=case.id, player_idx=p.idx, is_ai=True,
                             text=rng.choice(persona.vote).format(one=name),
                             visible_at=now + _delay(2 + 1.5 * k))
            if _once(session, case.id, key, Vote(case_id=case.id, player_idx=p.idx,
                                                 suspect=pick), post):
                snap.votes[p.idx] = pick
                voted = True
    return voted


def respond(session: Session, snap, author: Player, post: BoardPost,
            recent: list[str]) -> list[BoardPost]:
    """AI replies to a human post: whoever's suspects changed (max 2), else one seeded pick."""
    ais = [p for p in snap.players if p.is_ai]
    if not ais or not enabled() or author.is_ai:
        return []
    data = snap.data
    shared = set(snap.case.shared)
    before_ids = board_fact_ids(session, snap.case.id, exclude_post=post.id)
    after_ids = before_ids | ({post.fact_clue_id} if post.fact_clue_id else set())
    rng = random.Random(f"{data['seed']}:reply:{post.id}")

    beliefs: dict[int, tuple[list[dict], list[int]]] = {}
    changed: list[Player] = []
    for p in ais:
        after = known_clues(data, p.idx, snap.clue_day, shared, after_ids)
        poss_after = possible(data, after)
        if after_ids != before_ids:
            before = known_clues(data, p.idx, snap.clue_day, shared, before_ids)
            if possible(data, before) != poss_after:
                changed.append(p)
        beliefs[p.idx] = (after, poss_after)

    # "Nora, anything about Leo?": the AI named in the post answers, about the suspect named.
    text_in = post.text or ""
    by_name = {p.name: p for p in ais}
    addressed = by_name.get(first_named(text_in, list(by_name)))
    all_suspects = suspect_names(data, range(len(data["suspects"])))
    asked = first_named(text_in, all_suspects)

    if addressed is not None:
        responders = [addressed] + [p for p in changed if p is not addressed][:1]
    else:
        responders = changed[:2] or [rng.choice(ais)]
    started = aware(post.created_at)
    replies = []
    for k, p in enumerate(responders):
        clues, poss_ids = beliefs[p.idx]
        poss = suspect_names(data, poss_ids)
        reason = None
        if asked is not None and (p is addressed or (addressed is None and k == 0)):
            intent, x = "answer", asked
            asked_id = all_suspects.index(asked)
            if asked_id not in poss_ids:
                reason = ruling_out_clue(data, clues, asked_id)
        elif p in changed or p is addressed:
            intent, x = "hypothesis", rng.choice(poss)
        else:
            intent = rng.choice(["hypothesis", "ask", "react"])
            if intent == "ask" and len(poss) < 2:
                intent = "hypothesis"
            x = rng.choice(poss)
        text, _source = write_line(data, BY_KEY[p.persona], intent, rng, clues, poss, recent,
                                   author.name, x, reason)
        reply = BoardPost(case_id=snap.case.id, player_idx=p.idx, text=text, is_ai=True,
                          visible_at=started + _delay(rng.uniform(2, 6) + 2.5 * k))
        session.add(reply)
        replies.append(reply)
    session.commit()
    return replies
