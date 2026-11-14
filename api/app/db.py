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
from sqlalchemy import Engine, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

log = logging.getLogger(__name__)

def _normalize(url: str) -> str:
    # Neon/Supabase/Heroku hand out postgres:// URLs; SQLAlchemy wants a driver name.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def engine_kwargs(url: str) -> dict:
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    elif url.startswith("postgresql"):
        # Neon/Supabase poolers (PgBouncer, transaction mode) break server-side prepared
        # statements ("prepared statement ... does not exist"); psycopg must not create them.
        # Small pool: each serverless instance needs only a couple of connections.
        kwargs["connect_args"] = {"prepare_threshold": None}
        kwargs.update(pool_size=2, max_overflow=3, pool_recycle=300)
    return kwargs


@lru_cache
def get_engine() -> Engine:
    url = _normalize(get_settings().database_url)
    if url.startswith("sqlite:///./") and os.environ.get("VERCEL"):
        # Vercel functions can only write to /tmp, and it is wiped between cold starts.
        # Set DATABASE_URL to Postgres there; this only keeps the API from crashing.
        log.warning("DATABASE_URL not set on Vercel: using ephemeral SQLite in /tmp")
        url = "sqlite:////tmp/" + url.removeprefix("sqlite:///./")
    engine = create_engine(url, **engine_kwargs(url))
    import app.models  # noqa: F401  (registers every table before create_all)

    SQLModel.metadata.create_all(engine)
    add_missing_columns(engine)
    return engine


def add_missing_columns(engine: Engine) -> list[str]:
    """create_all never alters existing tables. Add new nullable columns to tables that
    already exist (enough for a hackathon; no Alembic). Returns the columns it added."""
    insp = inspect(engine)
    added = []
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                if col.primary_key or not col.nullable:
                    log.warning("cannot auto-add non-nullable column %s.%s", table.name, col.name)
                    continue
                ddl = col.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {ddl}'))
                added.append(f"{table.name}.{col.name}")
    if added:
        log.info("added columns: %s", ", ".join(added))
    return added


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
