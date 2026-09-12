import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.schemas import ClaimExtraction
from app.services import llm_service


def _fake_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=40),
    )


@patch("app.services.llm_service._get_client")
def test_extract_claim_success(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "claim_type": "duplicate_charge",
        "claimed_amount": 99.0,
        "urgency": "medium",
        "key_details": "Customer reports duplicate charge.",
    })
    mock_get_client.return_value = mock_client

    result = llm_service.extract_claim("I was charged twice this month.")
    assert isinstance(result, ClaimExtraction)
    assert result.claim_type == "duplicate_charge"
    assert result.claimed_amount == 99.0
    assert result.urgency == "medium"


@patch("app.services.llm_service._get_client")
def test_extract_claim_invalid_json_raises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="not json at all"))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )
    mock_get_client.return_value = mock_client

    with pytest.raises(json.JSONDecodeError):
        llm_service.extract_claim("test")


@patch("app.services.llm_service._get_client")
def test_extract_claim_invalid_claim_type_raises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "claim_type": "made_up_type",
        "claimed_amount": 10,
        "urgency": "medium",
        "key_details": "x",
    })
    mock_get_client.return_value = mock_client

    with pytest.raises(ValidationError):
        llm_service.extract_claim("test")


@patch("app.services.llm_service._get_client")
def test_extract_claim_missing_field_raises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "claim_type": "duplicate_charge",
        "claimed_amount": 55.0,
    })
    mock_get_client.return_value = mock_client

    with pytest.raises(ValidationError):
        llm_service.extract_claim("test")


@patch("app.services.llm_service._get_client")
def test_extract_claim_groq_api_error_reraises(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("groq down")
    mock_get_client.return_value = mock_client

    with pytest.raises(RuntimeError, match="groq down"):
        llm_service.extract_claim("test")


@patch("app.services.llm_service.logger")
@patch("app.services.llm_service._get_client")
def test_extract_claim_logs_metrics(mock_get_client, mock_logger):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "claim_type": "duplicate_charge",
        "claimed_amount": 99.0,
        "urgency": "medium",
        "key_details": "x",
    })
    mock_get_client.return_value = mock_client

    llm_service.extract_claim("test")

    mock_logger.info.assert_called_once()
    _, kwargs = mock_logger.info.call_args
    extra = kwargs.get("extra", {})
    assert extra["tokens_in"] == 100
    assert extra["tokens_out"] == 40
    assert "latency_ms" in extra
    assert extra["prompt_version"] == "extract_v1"


@patch("app.services.llm_service._get_client")
def test_extract_claim_amount_null_when_absent(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response({
        "claim_type": "refund_request",
        "urgency": "low",
        "key_details": "Customer wants a refund.",
    })
    mock_get_client.return_value = mock_client

    result = llm_service.extract_claim("Can I get my money back?")
    assert result.claimed_amount is None
    assert result.claim_type == "refund_request"
