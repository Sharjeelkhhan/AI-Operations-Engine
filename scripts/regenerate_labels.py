"""
Regenerate evaluation_expected.csv from actual DB data + policy rules.
Uses the same LLM extractor the system uses.
"""
import csv
import time
from pathlib import Path

from app.database import SessionLocal
from app.models import Payment, Subscription, SupportCase
from app.services import llm_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CSV = PROJECT_ROOT / "data" / "evaluation_expected.csv"

HIGH_VALUE_THRESHOLD = 500.0


def extract_with_retry(message: str, retries: int = 3) -> str:
    """Extract claim type with retry on timeout."""
    for attempt in range(retries):
        try:
            claim = llm_service.extract_claim(message)
            return claim.claim_type
        except Exception as e:
            if attempt == retries - 1:
                print(f"  FAILED after {retries} attempts: {e}")
                raise
            wait = 2 ** attempt
            print(f"  Retry in {wait}s... ({e})")
            time.sleep(wait)
    return "other"


def expected_decision_for(db, case, claim_type: str) -> str:
    """Derive expected decision from actual data + policy rules."""
    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == case.customer_id)
        .all()
    )
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.customer_id == case.customer_id)
        .all()
    )

    successful = [p for p in payments if p.status == "successful"]
    failed = [p for p in payments if p.status == "failed"]
    total = sum(p.amount for p in successful)

    if claim_type == "unauthorized_transaction":
        return "SECURITY_REVIEW"

    if claim_type == "duplicate_charge":
        if len(successful) >= 2 and len(set(p.amount for p in successful)) == 1:
            if total > HIGH_VALUE_THRESHOLD:
                return "REFUND_WITH_APPROVAL"
            return "REFUND_RECOMMENDED"
        return "HUMAN_REVIEW"

    if claim_type == "payment_failure":
        if failed:
            return "PAYMENT_INVESTIGATION"
        return "HUMAN_REVIEW"

    if claim_type == "cancellation_dispute":
        cancelled = [s for s in subscriptions if s.status == "cancelled"]
        if cancelled and successful:
            return "REFUND_RECOMMENDED"
        return "HUMAN_REVIEW"

    if claim_type == "refund_request":
        if len(successful) >= 2 and len(set(p.amount for p in successful)) == 1:
            if total > HIGH_VALUE_THRESHOLD:
                return "REFUND_WITH_APPROVAL"
            return "REFUND_RECOMMENDED"
        return "HUMAN_REVIEW"

    return "HUMAN_REVIEW"


def main():
    db = SessionLocal()
    rows = []
    try:
        cases = (
            db.query(SupportCase)
            .filter(SupportCase.case_id.like("CASE5%"))
            .order_by(SupportCase.case_id)
            .all()
        )
        for case in cases:
            claim_type = extract_with_retry(case.message)
            expected = expected_decision_for(db, case, claim_type)
            successful_count = len([
                p for p in db.query(Payment).filter(Payment.customer_id == case.customer_id).all()
                if p.status == "successful"
            ])
            rows.append({
                "case_id": case.case_id,
                "expected_decision": expected,
                "expected_reason": f"claim_type={claim_type}; successful_payments={successful_count}",
            })
            print(f"{case.case_id}: {claim_type} -> {expected}")
    finally:
        db.close()

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "expected_decision", "expected_reason"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} expected labels to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()