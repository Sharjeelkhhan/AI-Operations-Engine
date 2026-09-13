import json
import time
from typing import List, Optional

from groq import Groq

from app.config import settings
from app.logger import logger
from app.schemas import ClaimExtraction, DecisionOutput, EvidenceBundle

_client: Optional[Groq] = None

MODEL_NAME = "openai/gpt-oss-20b"
DECISION_PROMPT_VERSION = "decision_v1"


SYSTEM_PROMPT = """You are a decision engine for NovaDesk's customer dispute system.

You receive:
1. A customer CLAIM (structured).
2. Relevant COMPANY POLICY chunks (retrieved).
3. EVIDENCE from the database (payments, subscriptions).

You must produce a DECISION recommending what should happen next.

Allowed decisions (choose exactly one):
- REFUND_RECOMMENDED: refund is clearly supported by policy + evidence
- REFUND_WITH_APPROVAL: refund is supported but exceeds $500 (needs manager)
- CANCELLATION_REFUND: refund due to a valid cancellation
- PAYMENT_INVESTIGATION: customer and DB disagree about a payment
- SECURITY_REVIEW: possible unauthorized transaction
- HUMAN_REVIEW: evidence missing, ambiguous, or policy unclear
- INFO_ONLY: no action needed

Rules:
- You MUST cite specific evidence (payment IDs, policy chunks) in your reason.
- If evidence does not support the claim, choose HUMAN_REVIEW.
- If claim_type is "unauthorized_transaction", you MUST choose SECURITY_REVIEW.
- If claimed_amount > 500 and refund is warranted, choose REFUND_WITH_APPROVAL.
- Confidence must be a number between 0 and 1.
- Never invent payment IDs or policy sections that are not in the input.

Return ONLY valid JSON:
{
  "decision": "one of the allowed decisions",
  "confidence": 0.0-1.0,
  "reason": "short explanation citing evidence",
  "requires_human_approval": true|false
}
"""


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _build_user_message(
    claim: ClaimExtraction,
    policy_chunks: List[str],
    evidence: EvidenceBundle,
) -> str:
    policy_block = "\n\n---\n\n".join(policy_chunks) if policy_chunks else "(no policy chunks retrieved)"

    return f"""CUSTOMER CLAIM
- claim_type: {claim.claim_type}
- claimed_amount: {claim.claimed_amount}
- urgency: {claim.urgency}
- key_details: {claim.key_details}

DATABASE EVIDENCE
- successful payment IDs: {evidence.payments}
- subscriptions: {evidence.subscriptions}
- total successful amount: ${evidence.total_amount:.2f}
- summary: {evidence.summary}

RELEVANT POLICY CHUNKS
{policy_block}

Produce the decision JSON now."""


def decide(
    claim: ClaimExtraction,
    policy_chunks: List[str],
    evidence: EvidenceBundle,
) -> DecisionOutput:
    start = time.time()
    try:
        response = _get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(claim, policy_chunks, evidence)},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        decision = DecisionOutput(
            decision=parsed["decision"],
            confidence=float(parsed["confidence"]),
            reason=parsed["reason"],
            evidence=evidence,
            requires_human_approval=bool(parsed.get("requires_human_approval", False)),
        )

        latency_ms = int((time.time() - start) * 1000)
        usage = getattr(response, "usage", None)
        logger.info(
            "decision_success",
            extra={
                "prompt_version": DECISION_PROMPT_VERSION,
                "model": MODEL_NAME,
                "decision": decision.decision,
                "confidence": decision.confidence,
                "latency_ms": latency_ms,
                "tokens_in": getattr(usage, "prompt_tokens", None) if usage else None,
                "tokens_out": getattr(usage, "completion_tokens", None) if usage else None,
            },
        )
        return decision

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        logger.error(
            "decision_failure",
            extra={
                "prompt_version": DECISION_PROMPT_VERSION,
                "model": MODEL_NAME,
                "latency_ms": latency_ms,
                "error": str(e),
            },
        )
        raise