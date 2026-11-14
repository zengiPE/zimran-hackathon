"""Simple product event log (spec: created, joined, clue_opened, voted, paid).

    from app.events import log_event
    log_event(session, "joined", case_id, actor=player_name)

Feeds the demo/pitch numbers (funnel: created -> joined -> clue_opened -> voted -> paid).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, func, select

EventType = Literal[
    "created", "joined", "clue_opened", "voted", "revealed", "checkout_started", "paid"
]
EVENT_TYPES: tuple[str, ...] = EventType.__args__


def _now() -> datetime:
    return datetime.now(UTC)


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=_now, index=True)
    type: str = Field(index=True)
    case_id: str = Field(index=True)
    actor: str | None = None  # player name / "host" / "stripe"
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


def log_event(
    session: Session, type: EventType, case_id: str, *, actor: str | None = None, **data: Any
) -> Event:
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type {type!r}")
    event = Event(type=type, case_id=case_id, actor=actor, data=data)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def funnel(session: Session) -> dict[str, int]:
    """Distinct cases that reached each step (for the 'what we measured' slide)."""
    rows = session.exec(
        select(Event.type, func.count(func.distinct(Event.case_id))).group_by(Event.type)
    ).all()
    counts = dict(rows)
    return {t: counts.get(t, 0) for t in EVENT_TYPES}
