from __future__ import annotations

from typing import Literal

import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.db import SessionDep
from app.payments import service

router = APIRouter(prefix="/api", tags=["payments"])


class CheckoutIn(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    plan: Literal["case", "monthly"] = "case"


class CheckoutOut(BaseModel):
    url: str
    session_id: str


class PaymentOut(BaseModel):
    case_id: str
    paid: bool
    plan: str | None = None
    status: str | None = None


class PlanOut(BaseModel):
    key: str
    name: str
    description: str
    amount_cents: int
    interval: str | None


def _client() -> stripe.StripeClient:
    try:
        return service.stripe_client()
    except service.PaymentsNotConfigured as e:
        raise HTTPException(503, f"payments unavailable: {e}") from e


@router.get("/plans", response_model=list[PlanOut])
def list_plans() -> list[PlanOut]:
    """Prices for the paywall screen, so the UI never hardcodes them."""
    return [
        PlanOut(key=p.key, name=p.name, description=p.description,
                amount_cents=p.amount_cents, interval=p.interval)
        for p in service.PLANS.values()
    ]


@router.post("/checkout", response_model=CheckoutOut)
def create_checkout(body: CheckoutIn, db: SessionDep) -> CheckoutOut:
    client = _client()
    try:
        url, session_id = service.create_checkout(db, client, body.case_id, body.plan)
    except stripe.StripeError as e:
        raise HTTPException(502, f"stripe error: {e.user_message or e}") from e
    return CheckoutOut(url=url, session_id=session_id)


@router.get("/checkout/{session_id}", response_model=PaymentOut)
def checkout_status(session_id: str, db: SessionDep) -> PaymentOut:
    """Called by the success page; confirms the payment even if the webhook is late."""
    client = _client()
    try:
        p = service.sync_checkout(db, client, session_id)
    except stripe.InvalidRequestError as e:
        raise HTTPException(404, "unknown checkout session") from e
    except stripe.StripeError as e:
        raise HTTPException(502, f"stripe error: {e.user_message or e}") from e
    return PaymentOut(case_id=p.case_id, paid=p.status == "paid", plan=p.plan, status=p.status)


@router.get("/cases/{case_id}/payment", response_model=PaymentOut)
def case_payment(case_id: str, db: SessionDep) -> PaymentOut:
    p = service.case_is_paid(db, case_id)
    return PaymentOut(case_id=case_id, paid=p is not None, plan=p and p.plan,
                      status=p and p.status)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: SessionDep) -> dict[str, str]:
    payload = await request.body()
    try:
        event_type = service.handle_webhook(db, payload, request.headers.get("stripe-signature"))
    except service.PaymentsNotConfigured as e:
        raise HTTPException(503, str(e)) from e
    except (ValueError, stripe.SignatureVerificationError) as e:
        raise HTTPException(400, "invalid webhook") from e
    return {"received": event_type}
