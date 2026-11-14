"""Game clock: which day a case is on and which phase it is in."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.game_models import Case, utcnow


def aware(dt: datetime) -> datetime:
    """SQLite hands datetimes back without a timezone; they are stored as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def iso(dt: datetime) -> str:
    return aware(dt).isoformat()


def virtual_day(case: Case) -> int:
    """1-based day of the case: real days elapsed since start plus days skipped in demo."""
    elapsed = (utcnow() - aware(case.started_at)).total_seconds()
    return 1 + int(elapsed // case.day_seconds) + case.day_offset


def next_unlock_at(case: Case) -> str:
    start = aware(case.started_at)
    real_days = int((utcnow() - start).total_seconds() // case.day_seconds)
    return iso(start + timedelta(seconds=(real_days + 1) * case.day_seconds))


def phase_of(day: int, days: int, joined: set[int], votes: dict[int, int]) -> str:
    if day <= days:
        return "play"
    if day >= days + 2:
        return "reveal"
    if joined and joined <= votes.keys():
        return "reveal"
    return "vote"
