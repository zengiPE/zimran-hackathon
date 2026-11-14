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


class Vote(SQLModel, table=True):
    __tablename__ = "votes"  # type: ignore[assignment]

    case_id: str = Field(primary_key=True)
    player_idx: int = Field(primary_key=True)
    suspect: int
    created_at: datetime = Field(default_factory=utcnow)
