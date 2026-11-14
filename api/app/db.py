"""Shared database setup (SQLModel). Every module puts its tables on SQLModel.metadata.

Usage in routes:   def handler(session: SessionDep): ...
Tables are created on first use (fine for a hackathon; no migrations).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

log = logging.getLogger(__name__)

def _normalize(url: str) -> str:
    # Neon/Supabase/Heroku hand out postgres:// URLs; SQLAlchemy wants a driver name.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


@lru_cache
def get_engine() -> Engine:
    url = _normalize(get_settings().database_url)
    if url.startswith("sqlite:///./") and os.environ.get("VERCEL"):
        # Vercel functions can only write to /tmp, and it is wiped between cold starts.
        # Set DATABASE_URL to Postgres there; this only keeps the API from crashing.
        log.warning("DATABASE_URL not set on Vercel: using ephemeral SQLite in /tmp")
        url = "sqlite:////tmp/" + url.removeprefix("sqlite:///./")
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    import app.models  # noqa: F401  (registers every table before create_all)

    SQLModel.metadata.create_all(engine)
    return engine


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
