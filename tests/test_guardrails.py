from app.schemas import ClaimExtraction, DecisionOutput, EvidenceBundle
from app.services.guardrail_service import apply_guardrails


def _claim(**overrides):
    defaults = dict(
        claim_type="duplicate_charge",
        claimed_amount=99.0,
        urgency="medium",
        key_details="test",
    )
    defaults.update(overrides)
    return ClaimExtraction(**defaults)


def _decision(**overrides):
    defaults = dict(
        decision="REFUND_RECOMMENDED",
        confidence=0.95,
        reason="test",
        evidence=EvidenceBundle(payments=["P1", "P2"], total_amount=198.0),
        requires_human_approval=False,
    )
    defaults.update(overrides)
    return DecisionOutput(**defaults)


def test_unauthorized_claim_forces_security_review():
    d = apply_guardrails(_decision(), _claim(claim_type="unauthorized_transaction"))
    assert d.decision == "SECURITY_REVIEW"
    assert d.requires_human_approval is True


def test_high_value_refund_needs_approval():
    d = apply_guardrails(
        _decision(decision="REFUND_RECOMMENDED"),
        _claim(claimed_amount=600.0),
    )
    assert d.decision == "REFUND_WITH_APPROVAL"
    assert d.requires_human_approval is True


def test_low_confidence_forces_human_review():
    d = apply_guardrails(_decision(confidence=0.5), _claim())
    assert d.decision == "HUMAN_REVIEW"


def test_duplicate_claim_without_evidence_forces_review():
    d = apply_guardrails(
        _decision(evidence=EvidenceBundle(payments=["P1"], total_amount=99.0)),
        _claim(claim_type="duplicate_charge"),
    )
    assert d.decision == "HUMAN_REVIEW"


def test_normal_case_passes_through():
    d = apply_guardrails(_decision(), _claim())
    assert d.decision == "REFUND_RECOMMENDED"
    assert d.requires_human_approval is False