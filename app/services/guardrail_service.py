from app.logger import logger
from app.schemas import ClaimExtraction, DecisionOutput

CONFIDENCE_FLOOR = 0.85
HIGH_VALUE_THRESHOLD = 500.0


def apply_guardrails(
    decision: DecisionOutput,
    claim: ClaimExtraction,
) -> DecisionOutput:
    """
    Apply rule-based guardrails on top of the LLM's decision.
    The LLM suggests; these rules enforce policy. Never the other way around.
    """
    original = decision.decision

    # Rule 1: Unauthorized transactions always go to security
    if claim.claim_type == "unauthorized_transaction" and decision.decision != "SECURITY_REVIEW":
        decision.decision = "SECURITY_REVIEW"
        decision.requires_human_approval = True
        decision.reason = (
            "Guardrail: unauthorized transaction claims must be routed to security. "
            f"LLM originally suggested {original}. " + decision.reason
        )

    # Rule 2: High-value refunds need manager approval
    if (
        decision.decision == "REFUND_RECOMMENDED"
        and claim.claimed_amount is not None
        and claim.claimed_amount > HIGH_VALUE_THRESHOLD
    ):
        decision.decision = "REFUND_WITH_APPROVAL"
        decision.requires_human_approval = True
        decision.reason = (
            f"Guardrail: refund amount ${claim.claimed_amount:.2f} exceeds "
            f"${HIGH_VALUE_THRESHOLD:.0f}; manager approval required. " + decision.reason
        )

    # Rule 3: Low confidence forces human review
    if decision.confidence < CONFIDENCE_FLOOR and decision.decision not in (
        "HUMAN_REVIEW",
        "SECURITY_REVIEW",
    ):
        decision.decision = "HUMAN_REVIEW"
        decision.requires_human_approval = True
        decision.reason = (
            f"Guardrail: confidence {decision.confidence:.2f} below threshold "
            f"{CONFIDENCE_FLOOR}. " + decision.reason
        )

    # Rule 4: Duplicate charge claim without payment evidence → human review
    if (
        claim.claim_type == "duplicate_charge"
        and len(decision.evidence.payments) < 2
        and decision.decision in ("REFUND_RECOMMENDED", "REFUND_WITH_APPROVAL")
    ):
        decision.decision = "HUMAN_REVIEW"
        decision.requires_human_approval = True
        decision.reason = (
            "Guardrail: duplicate charge claim lacks supporting payment evidence. "
            + decision.reason
        )

    if decision.decision != original:
        logger.info(
            "guardrail_override",
            extra={
                "original": original,
                "final": decision.decision,
                "claim_type": claim.claim_type,
            },
        )

    return decision