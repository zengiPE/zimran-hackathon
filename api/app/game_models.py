"""Tables for live games: cases, players, opened clues, theory board, votes."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class Case(SQLModel, table=True):
    __tablename__ = "cases"  # type: ignore[assignment]

    id: str = Field(primary_key=True)
    host_token: str = Field(index=True)
    data: dict = Field(sa_column=Column(JSON, nullable=False))  # engine output incl. solution
    demo: bool = False
    day_seconds: int = 86400
    day_offset: int = 0  # days skipped by the host in demo mode
    shared: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    started_at: datetime = Field(default_factory=utcnow)


class Player(SQLModel, table=True):
    __tablename__ = "players"  # type: ignore[assignment]

    token: str = Field(primary_key=True)
    case_id: str = Field(foreign_key="cases.id", index=True)
    idx: int
    name: str
    joined_at: datetime | None = None
    # AI teammate seat (new columns are nullable so existing databases can be migrated)
    is_ai: bool | None = None
    persona: str | None = None


class ClueOpen(SQLModel, table=True):
    __tablename__ = "clue_opens"  # type: ignore[assignment]

    case_id: str = Field(primary_key=True)
    clue_id: str = Field(primary_key=True)
    opened_at: datetime = Field(default_factory=utcnow)


class BoardPost(SQLModel, table=True):
    __tablename__ = "board_posts"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    case_id: str = Field(index=True)
    player_idx: int
    text: str
    created_at: datetime = Field(default_factory=utcnow)
    fact_clue_id: str | None = None  # a clue the author attached ("Share this clue")
    is_ai: bool | None = None
    visible_at: datetime | None = None  # AI posts appear after a short "typing" delay


class AiAction(SQLModel, table=True):
    """Idempotency key for AI moves (one share per clue, one vote per seat), so
    concurrent polls never duplicate a post."""

    __tablename__ = "ai_actions"  # type: ignore[assignment]

    case_id: str = Field(primary_key=True)
    key: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)


class Vote(SQLModel, table=True):
    __tablename__ = "votes"  # type: ignore[assignment]

    case_id: str = Field(primary_key=True)
    player_idx: int = Field(primary_key=True)
    suspect: int
    created_at: datetime = Field(default_factory=utcnow)
