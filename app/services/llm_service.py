import json
import time
from typing import Optional

from groq import Groq

from app.config import settings
from app.logger import logger
from app.schemas import ClaimExtraction

_client: Optional[Groq] = None

EXTRACTION_PROMPT_VERSION = "extract_v1"
MODEL_NAME = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a claim extraction system for a SaaS customer support team.

Given a customer support message, extract the following fields:

- claim_type: one of
    duplicate_charge,
    unauthorized_transaction,
    refund_request,
    cancellation_dispute,
    payment_failure,
    invoice_mismatch,
    other
- claimed_amount: numeric value in USD if mentioned, otherwise null
- urgency: low, medium, or high
- key_details: one sentence summarizing what the customer wants

Return ONLY valid JSON matching this schema:
{
  "claim_type": "string",
  "claimed_amount": number or null,
  "urgency": "string",
  "key_details": "string"
}

Do not include markdown. Do not include commentary. Only JSON."""


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def extract_claim(message: str) -> ClaimExtraction:
    start = time.time()
    try:
        response = _get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        result = ClaimExtraction(**parsed)

        latency_ms = int((time.time() - start) * 1000)
        usage = getattr(response, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", None) if usage else None
        tokens_out = getattr(usage, "completion_tokens", None) if usage else None

        logger.info(
            "llm_extract_success",
            extra={
                "prompt_version": EXTRACTION_PROMPT_VERSION,
                "model": MODEL_NAME,
                "latency_ms": latency_ms,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "claim_type": result.claim_type,
                "urgency": result.urgency,
            },
        )
        return result

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        logger.error(
            "llm_extract_failure",
            extra={
                "prompt_version": EXTRACTION_PROMPT_VERSION,
                "model": MODEL_NAME,
                "latency_ms": latency_ms,
                "error": str(e),
            },
        )
        raise
