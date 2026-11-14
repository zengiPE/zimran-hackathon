"""Database tables and session. Postgres in production, SQLite locally and in tests."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import JSON, Column
from sqlalchemy.pool import NullPool
from sqlmodel import Field, Session, SQLModel, create_engine

from app.config import get_settings


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


def database_url() -> str:
    url = get_settings().database_url
    if not url:
        # Vercel functions can only write to /tmp, and it is per instance: fine for a
        # smoke test, not for real games. Set DATABASE_URL to Postgres in production.
        url = "sqlite:////tmp/casefile.db" if os.environ.get("VERCEL") else "sqlite:///./casefile.db"
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


@lru_cache
def get_engine():
    url = database_url()
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(url, poolclass=NullPool)  # serverless: no idle pools
    SQLModel.metadata.create_all(engine)
    return engine


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
