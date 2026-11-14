from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Field, SQLModel

PaymentStatus = Literal["pending", "paid", "expired"]


class Payment(SQLModel, table=True):
    """One Stripe Checkout session. id = Stripe checkout session id (cs_test_...)."""

    id: str = Field(primary_key=True)
    case_id: str = Field(index=True)
    plan: str
    amount_cents: int
    status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    paid_at: datetime | None = None
