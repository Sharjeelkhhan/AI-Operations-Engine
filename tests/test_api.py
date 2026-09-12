import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, Base, engine
from app.concurrency import ConcurrencyConflictError, apply_payment_update
from app.main import app, reset_rate_limit_history
from app.models import Customer, Payment, Subscription, SupportCase
from app.services.idempotency_service import clear_idempotency_store, remember_request_key

client = TestClient(app)
HEADERS = {"X-API-Key": "dev-api-key", "X-User-Role": "admin"}
VIEWER_HEADERS = {"X-API-Key": "dev-api-key", "X-User-Role": "viewer"}


def _fake_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=40),
    )


def setup_module():
    reset_rate_limit_history()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Customer).count() == 0:
        db.add_all(
            [
                Customer(
                    customer_id="C1001",
                    name="Emily Miller",
                    email="emily.miller@gmail.com",
                    country="Canada",
                    plan="Pro",
                ),
                Customer(
                    customer_id="C1002",
                    name="Noah Weber",
                    email="noah.weber@gmail.com",
                    country="UK",
                    plan="Starter",
                ),
            ]
        )
        db.commit()
    db.close()


def setup_function():
    reset_rate_limit_history()
    clear_idempotency_store()


def test_root():
    response = client.get("/", headers=HEADERS)
    assert response.status_code == 200
    assert "running" in response.json()["message"].lower()


def test_list_customers():
    response = client.get("/customers/", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_customer_by_id():
    response = client.get("/customers/C1001", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["customer_id"] == "C1001"


def test_get_nonexistent_customer():
    response = client.get("/customers/C9999", headers=HEADERS)
    assert response.status_code == 404


def test_health_check():
    response = client.get("/health", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "unhealthy"}


def test_list_payments():
    response = client.get("/payments/", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_missing_api_key_is_rejected():
    response = client.get("/customers/", headers={})
    assert response.status_code == 401


def test_viewer_role_cannot_access_admin_endpoints():
    response = client.get("/customers/", headers=VIEWER_HEADERS)
    assert response.status_code == 403


def test_admin_role_can_access_endpoints():
    response = client.get("/customers/", headers=HEADERS)
    assert response.status_code == 200


def test_rate_limiter_blocks_excess_requests():
    for _ in range(5):
        response = client.get("/health", headers=HEADERS)
        assert response.status_code == 200

    response = client.get("/health", headers=HEADERS)
    assert response.status_code == 429


def test_request_logging_records_method_path_and_status(caplog):
    with caplog.at_level("INFO", logger="novadesk"):
        response = client.get("/health", headers=HEADERS)

    assert response.status_code == 200
    assert "request" in caplog.text.lower()
    assert "/health" in caplog.text
    assert "status=200" in caplog.text


def test_production_requires_nonempty_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "")

    from app.config import Settings

    try:
        Settings().validate_environment()
        assert False, "Expected missing production secrets to raise a ValueError"
    except ValueError:
        pass


def test_idempotency_service_blocks_duplicate_request_keys():
    key = "payment-123"

    first = remember_request_key(key, "response-1")
    second = remember_request_key(key, "response-2")

    assert first is True
    assert second is False


def test_concurrent_updates_are_not_double_applied():
    first = remember_request_key("payment-update-123", "response-1")
    second = remember_request_key("payment-update-123", "response-2")

    assert first is True
    assert second is False


def test_stale_version_update_is_rejected():
    db = SessionLocal()
    try:
        subscription_id = f"SUB-{uuid.uuid4().hex[:8]}"
        payment_id = f"PAY-{uuid.uuid4().hex[:8]}"

        subscription = Subscription(
            subscription_id=subscription_id,
            customer_id="C1001",
            plan="Pro",
            monthly_price=100,
            status="active",
            start_date="2026-01-01",
            renewal_date="2026-02-01",
            version=1,
        )
        db.add(subscription)
        db.flush()

        payment = Payment(
            payment_id=payment_id,
            customer_id="C1001",
            subscription_id=subscription_id,
            amount=100,
            currency="USD",
            status="pending",
            payment_date="2026-01-01",
            version=1,
        )
        db.add(payment)
        db.commit()

        with pytest.raises(ConcurrencyConflictError):
            apply_payment_update(db, payment.payment_id, "successful", 0)
    finally:
        db.close()


@patch("app.services.llm_service._get_client")
def test_extract_endpoint_returns_structured_claim(mock_get_client):
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    db = SessionLocal()
    try:
        db.add(
            SupportCase(
                case_id=case_id,
                customer_id="C1001",
                message="I was charged twice this month.",
                submitted_at="2026-09-12",
            )
        )
        db.commit()
    finally:
        db.close()

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "claim_type": "duplicate_charge",
        "claimed_amount": 99.0,
        "urgency": "medium",
        "key_details": "Customer reports duplicate charge.",
    })
    mock_get_client.return_value = mock_client

    response = client.post(f"/support-cases/{case_id}/extract", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["claim_type"] == "duplicate_charge"
    assert body["urgency"] == "medium"
    assert body["claimed_amount"] == 99.0


def test_extract_nonexistent_case_returns_404():
    response = client.post("/support-cases/CASE9999/extract", headers=HEADERS)
    assert response.status_code == 404


def test_extract_requires_admin_role():
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    db = SessionLocal()
    try:
        db.add(
            SupportCase(
                case_id=case_id,
                customer_id="C1001",
                message="Customer wants a refund.",
                submitted_at="2026-09-12",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.post(f"/support-cases/{case_id}/extract", headers=VIEWER_HEADERS)
    assert response.status_code == 403


def test_extract_requires_api_key():
    response = client.post("/support-cases/CASE5001/extract", headers={})
    assert response.status_code == 401
