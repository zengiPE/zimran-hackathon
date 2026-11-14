"""Stripe Checkout (test mode) for the paywall: $12 per case or $7.99/month.

Payment is confirmed two ways, both idempotent:
1. Webhook ``checkout.session.completed`` (the normal path).
2. Success-redirect fallback: the web app calls GET /api/checkout/{session_id}, and we ask
   Stripe directly. The spec's plan B for "the webhook doesn't arrive" during the demo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import quote

import stripe
from sqlmodel import Session

from app.config import get_settings
from app.events import log_event
from app.payments.models import Payment


@dataclass(frozen=True)
class Plan:
    key: str
    mode: Literal["payment", "subscription"]
    amount_cents: int
    name: str
    description: str
    interval: Literal["month"] | None = None


PLANS: dict[str, Plan] = {
    "case": Plan(
        "case", "payment", 1200, "Casefile: your next case", "One new case for your whole group"
    ),
    "monthly": Plan(
        "monthly",
        "subscription",
        799,
        "Casefile Club",
        "A new case every week for your group",
        interval="month",
    ),
}


class PaymentsNotConfigured(RuntimeError):
    pass


def stripe_client() -> stripe.StripeClient:
    key = get_settings().stripe_secret_key
    if not key:
        raise PaymentsNotConfigured("STRIPE_SECRET_KEY is not set")
    if not key.startswith(("sk_test_", "rk_test_")):
        # Hackathon: never charge a real card by accident.
        raise PaymentsNotConfigured("only Stripe test-mode keys are allowed")
    return stripe.StripeClient(key)


def _obj(o: Any) -> dict[str, Any]:
    return o.to_dict() if hasattr(o, "to_dict") else dict(o)


def create_checkout(
    db: Session, client: stripe.StripeClient, case_id: str, plan_key: str
) -> tuple[str, str]:
    """Create a Checkout session. Returns (checkout_url, session_id)."""
    plan = PLANS[plan_key]
    web = get_settings().public_web_url.rstrip("/")
    cid = quote(case_id, safe="")
    price_data: dict[str, Any] = {
        "currency": "usd",
        "unit_amount": plan.amount_cents,
        "product_data": {"name": plan.name, "description": plan.description},
    }
    if plan.interval:
        price_data["recurring"] = {"interval": plan.interval}
    metadata = {"case_id": case_id, "plan": plan.key}
    params: dict[str, Any] = {
        "mode": plan.mode,
        "line_items": [{"price_data": price_data, "quantity": 1}],
        "client_reference_id": case_id,
        "metadata": metadata,
        # {CHECKOUT_SESSION_ID} is filled in by Stripe
        "success_url": f"{web}/paywall?case_id={cid}&checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{web}/paywall?case_id={cid}&checkout=canceled",
    }
    if plan.mode == "subscription":
        params["subscription_data"] = {"metadata": metadata}

    cs = _obj(client.v1.checkout.sessions.create(params=params))
    db.add(
        Payment(id=cs["id"], case_id=case_id, plan=plan.key, amount_cents=plan.amount_cents)
    )
    db.commit()
    log_event(db, "checkout_started", case_id, plan=plan.key, session_id=cs["id"])
    return cs["url"], cs["id"]


def apply_checkout_session(db: Session, cs: dict[str, Any], *, source: str) -> Payment:
    """Record the state of a Stripe checkout session. Safe to call many times."""
    meta = cs.get("metadata") or {}
    case_id = meta.get("case_id") or cs.get("client_reference_id") or ""
    plan_key = meta.get("plan", "case")
    payment = db.get(Payment, cs["id"])
    if payment is None:  # e.g. created before a DB reset; trust Stripe's record
        amount = cs.get("amount_total") or PLANS.get(plan_key, PLANS["case"]).amount_cents
        payment = Payment(id=cs["id"], case_id=case_id, plan=plan_key, amount_cents=amount)
        db.add(payment)

    is_paid = cs.get("status") == "complete" and cs.get("payment_status") in (
        "paid",
        "no_payment_required",
    )
    if is_paid and payment.status != "paid":
        payment.status = "paid"
        payment.paid_at = datetime.now(UTC)
        db.commit()
        log_event(
            db, "paid", payment.case_id, actor="stripe",
            plan=payment.plan, amount_cents=payment.amount_cents, via=source,
        )
    elif cs.get("status") == "expired" and payment.status == "pending":
        payment.status = "expired"
        db.commit()
    else:
        db.commit()
    db.refresh(payment)
    return payment


def sync_checkout(db: Session, client: stripe.StripeClient, session_id: str) -> Payment:
    """Success-redirect fallback: ask Stripe for the session's current state."""
    cs = _obj(client.v1.checkout.sessions.retrieve(session_id))
    return apply_checkout_session(db, cs, source="redirect")


HANDLED_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "checkout.session.expired",
}


def handle_webhook(db: Session, payload: bytes, signature: str | None) -> str:
    """Verify and apply a Stripe webhook. Raises ValueError / SignatureVerificationError."""
    secret = get_settings().stripe_webhook_secret
    if not secret:
        raise PaymentsNotConfigured("STRIPE_WEBHOOK_SECRET is not set")
    event = stripe.Webhook.construct_event(payload, signature, secret)
    if event.type in HANDLED_EVENTS:
        apply_checkout_session(db, _obj(event.data.object), source="webhook")
    return event.type


def case_is_paid(db: Session, case_id: str) -> Payment | None:
    from sqlmodel import select

    return db.exec(
        select(Payment).where(Payment.case_id == case_id, Payment.status == "paid")
    ).first()
