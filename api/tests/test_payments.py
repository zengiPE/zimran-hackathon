import hashlib
import hmac
import json
import time
from types import SimpleNamespace

import pytest
import stripe
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # registers every table on SQLModel.metadata
from app.config import Settings
from app.db import _normalize, get_session
from app.events import Event, funnel, log_event
from app.main import app
from app.payments import service
from app.payments.models import Payment

WEBHOOK_SECRET = "whsec_test_secret"
SETTINGS = Settings(
    stripe_secret_key="sk_test_123",
    stripe_webhook_secret=WEBHOOK_SECRET,
    public_web_url="https://web.example/",
)


class FakeStripe:
    """Stands in for stripe.StripeClient: records create() params, serves retrieve()."""

    def __init__(self):
        self.created: list[dict] = []
        self.sessions: dict[str, dict] = {}
        sessions = SimpleNamespace(create=self._create, retrieve=self._retrieve)
        self.v1 = SimpleNamespace(checkout=SimpleNamespace(sessions=sessions))

    def _create(self, params):
        self.created.append(params)
        sid = f"cs_test_{len(self.created)}"
        data = {
            "id": sid, "url": f"https://checkout.stripe.test/{sid}", "status": "open",
            "payment_status": "unpaid", "metadata": params["metadata"],
            "client_reference_id": params["client_reference_id"],
        }
        self.sessions[sid] = data
        return stripe.checkout.Session.construct_from(data, "sk_test_123")

    def _retrieve(self, sid):
        if sid not in self.sessions:
            raise stripe.InvalidRequestError("No such checkout.session", "id")
        return stripe.checkout.Session.construct_from(self.sessions[sid], "sk_test_123")

    def complete(self, sid):
        self.sessions[sid].update(status="complete", payment_status="paid", amount_total=1200)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def fake_stripe(monkeypatch):
    fake = FakeStripe()
    monkeypatch.setattr(service, "get_settings", lambda: SETTINGS)
    monkeypatch.setattr(service, "stripe_client", lambda: fake)
    return fake


@pytest.fixture
def client(engine):
    def _session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    yield TestClient(app)
    app.dependency_overrides.clear()


def signed(payload: dict, secret: str = WEBHOOK_SECRET) -> tuple[bytes, str]:
    body = json.dumps(payload).encode()
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return body, f"t={ts},v1={sig}"


def webhook_event(cs: dict, type_: str = "checkout.session.completed") -> dict:
    return {"id": "evt_1", "object": "event", "type": type_,
            "data": {"object": {"object": "checkout.session", **cs}}}


def paid_events(db: Session) -> list[Event]:
    return list(db.exec(select(Event).where(Event.type == "paid")).all())


# --- plans & checkout --------------------------------------------------------------------


def test_plans_endpoint(client):
    plans = {p["key"]: p for p in client.get("/api/plans").json()}
    assert plans["case"]["amount_cents"] == 1200 and plans["case"]["interval"] is None
    assert plans["monthly"]["amount_cents"] == 799 and plans["monthly"]["interval"] == "month"


def test_checkout_one_case(client, fake_stripe, db):
    r = client.post("/api/checkout", json={"case_id": "case 42"})
    assert r.status_code == 200
    assert r.json() == {"url": "https://checkout.stripe.test/cs_test_1", "session_id": "cs_test_1"}

    params = fake_stripe.created[0]
    assert params["mode"] == "payment"
    price = params["line_items"][0]["price_data"]
    assert price["unit_amount"] == 1200 and price["currency"] == "usd" and "recurring" not in price
    assert params["metadata"] == {"case_id": "case 42", "plan": "case"}
    assert params["success_url"] == (
        "https://web.example/paywall?case_id=case%2042&checkout=success"
        "&session_id={CHECKOUT_SESSION_ID}"
    )
    assert params["cancel_url"].endswith("checkout=canceled")

    payment = db.get(Payment, "cs_test_1")
    assert payment.status == "pending" and payment.case_id == "case 42"
    assert db.exec(select(Event).where(Event.type == "checkout_started")).one().case_id == "case 42"


def test_checkout_monthly_is_subscription(client, fake_stripe):
    client.post("/api/checkout", json={"case_id": "c1", "plan": "monthly"})
    params = fake_stripe.created[0]
    assert params["mode"] == "subscription"
    price = params["line_items"][0]["price_data"]
    assert price["unit_amount"] == 799 and price["recurring"] == {"interval": "month"}
    assert params["subscription_data"]["metadata"]["plan"] == "monthly"


def test_checkout_rejects_unknown_plan(client, fake_stripe):
    assert client.post("/api/checkout", json={"case_id": "c1", "plan": "lifetime"}).status_code == 422


@pytest.mark.parametrize("key", ["", "sk_live_123"])
def test_checkout_unavailable_without_test_key(client, monkeypatch, key):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(stripe_secret_key=key))
    r = client.post("/api/checkout", json={"case_id": "c1"})
    assert r.status_code == 503


# --- confirmation: redirect fallback ---------------------------------------------------------


def test_redirect_confirms_payment_once(client, fake_stripe, db):
    client.post("/api/checkout", json={"case_id": "c1"})
    assert client.get("/api/checkout/cs_test_1").json()["paid"] is False

    fake_stripe.complete("cs_test_1")
    for _ in range(2):  # the success page may poll; must not double-count
        body = client.get("/api/checkout/cs_test_1").json()
        assert body == {"case_id": "c1", "paid": True, "plan": "case", "status": "paid"}
    assert len(paid_events(db)) == 1
    assert client.get("/api/cases/c1/payment").json()["paid"] is True


def test_redirect_unknown_session(client, fake_stripe):
    assert client.get("/api/checkout/cs_test_nope").status_code == 404


# --- confirmation: webhook -------------------------------------------------------------------


def test_webhook_marks_paid_and_is_idempotent(client, fake_stripe, db):
    client.post("/api/checkout", json={"case_id": "c1"})
    cs = {"id": "cs_test_1", "status": "complete", "payment_status": "paid",
          "metadata": {"case_id": "c1", "plan": "case"}}
    body, sig = signed(webhook_event(cs))
    for _ in range(2):  # Stripe retries deliveries
        r = client.post("/api/stripe/webhook", content=body, headers={"stripe-signature": sig})
        assert r.status_code == 200
    assert db.get(Payment, "cs_test_1").status == "paid"
    assert len(paid_events(db)) == 1
    assert paid_events(db)[0].data["via"] == "webhook"


def test_webhook_rejects_bad_signature(client, fake_stripe, db):
    body, sig = signed(webhook_event({"id": "cs_x"}), secret="whsec_wrong")
    r = client.post("/api/stripe/webhook", content=body, headers={"stripe-signature": sig})
    assert r.status_code == 400
    assert db.exec(select(Payment)).first() is None


def test_webhook_without_signature_header(client, fake_stripe):
    body, _ = signed(webhook_event({"id": "cs_x"}))
    assert client.post("/api/stripe/webhook", content=body).status_code == 400


def test_webhook_for_session_missing_in_db(client, fake_stripe, db):
    # e.g. the DB was reset between checkout and webhook: trust Stripe's record
    cs = {"id": "cs_test_9", "status": "complete", "payment_status": "paid",
          "amount_total": 799, "metadata": {"case_id": "c9", "plan": "monthly"}}
    body, sig = signed(webhook_event(cs))
    client.post("/api/stripe/webhook", content=body, headers={"stripe-signature": sig})
    p = db.get(Payment, "cs_test_9")
    assert (p.status, p.case_id, p.plan, p.amount_cents) == ("paid", "c9", "monthly", 799)


def test_webhook_expired_session(client, fake_stripe, db):
    client.post("/api/checkout", json={"case_id": "c1"})
    cs = {"id": "cs_test_1", "status": "expired", "payment_status": "unpaid",
          "metadata": {"case_id": "c1", "plan": "case"}}
    body, sig = signed(webhook_event(cs, "checkout.session.expired"))
    client.post("/api/stripe/webhook", content=body, headers={"stripe-signature": sig})
    assert db.get(Payment, "cs_test_1").status == "expired"
    assert client.get("/api/cases/c1/payment").json()["paid"] is False


# --- events & db ---------------------------------------------------------------------------


def test_event_log_and_funnel(db):
    for case in ("a", "b"):
        log_event(db, "created", case, actor="host")
        log_event(db, "joined", case, actor="Maya")
        log_event(db, "joined", case, actor="Leo")
    log_event(db, "voted", "a", actor="Maya", suspect="Jordan")
    f = funnel(db)
    assert (f["created"], f["joined"], f["voted"], f["paid"]) == (2, 2, 1, 0)


def test_unknown_event_type_rejected(db):
    with pytest.raises(ValueError):
        log_event(db, "hacked", "a")


@pytest.mark.parametrize(
    "url, expected",
    [
        ("postgres://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///./casefile.db", "sqlite:///./casefile.db"),
    ],
)
def test_database_url_normalized(url, expected):
    assert _normalize(url) == expected
