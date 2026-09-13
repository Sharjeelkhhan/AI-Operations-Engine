import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.schemas import ClaimExtraction, EvidenceBundle
from app.services import decision_service


def _fake_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))],
        usage=SimpleNamespace(prompt_tokens=500, completion_tokens=100),
    )


def _claim():
    return ClaimExtraction(
        claim_type="duplicate_charge",
        claimed_amount=99.0,
        urgency="medium",
        key_details="charged twice",
    )


def _evidence():
    return EvidenceBundle(
        payments=["P3001", "P3002"],
        subscriptions=["S2001"],
        total_amount=198.0,
        summary="2 successful payments found.",
    )


@patch("app.services.decision_service._get_client")
def test_decide_success(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "decision": "REFUND_RECOMMENDED",
        "confidence": 0.94,
        "reason": "Two successful payments found.",
        "requires_human_approval": False,
    })
    mock_get_client.return_value = mock_client

    result = decision_service.decide(_claim(), ["policy text"], _evidence())
    assert result.decision == "REFUND_RECOMMENDED"
    assert result.confidence == 0.94
    assert result.evidence.payments == ["P3001", "P3002"]


@patch("app.services.decision_service._get_client")
def test_decide_invalid_decision_raises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "decision": "MADE_UP_DECISION",
        "confidence": 0.9,
        "reason": "x",
        "requires_human_approval": False,
    })
    mock_get_client.return_value = mock_client

    with pytest.raises(ValidationError):
        decision_service.decide(_claim(), [], _evidence())


@patch("app.services.decision_service._get_client")
def test_decide_invalid_json_raises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )
    mock_get_client.return_value = mock_client

    with pytest.raises(json.JSONDecodeError):
        decision_service.decide(_claim(), [], _evidence())


@patch("app.services.decision_service._get_client")
def test_decide_api_error_reraises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("groq down")
    mock_get_client.return_value = mock_client

    with pytest.raises(RuntimeError, match="groq down"):
        decision_service.decide(_claim(), [], _evidence())