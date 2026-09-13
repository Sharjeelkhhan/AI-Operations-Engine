"""
Rebuild evaluation_expected.csv using actual DB data + known claim types.
No LLM calls. Fast, deterministic, quota-free.
"""
import csv
from pathlib import Path

from app.database import SessionLocal
from app.models import Payment, Subscription, SupportCase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CSV = PROJECT_ROOT / "data" / "evaluation_expected.csv"

HIGH_VALUE_THRESHOLD = 500.0

# Known claim types per case (from earlier LLM extraction)
CLAIM_TYPES = {
    "CASE5000": "duplicate_charge",
    "CASE5001": "duplicate_charge",
    "CASE5002": "payment_failure",
    "CASE5003": "duplicate_charge",
    "CASE5004": "unauthorized_transaction",
    "CASE5005": "duplicate_charge",
    "CASE5006": "cancellation_dispute",
    "CASE5007": "duplicate_charge",
    "CASE5008": "duplicate_charge",
    "CASE5009": "payment_failure",
    "CASE5010": "refund_request",
    "CASE5011": "cancellation_dispute",
    "CASE5012": "cancellation_dispute",
    "CASE5013": "unauthorized_transaction",
    "CASE5014": "refund_request",
    "CASE5015": "invoice_mismatch",
    "CASE5016": "unauthorized_transaction",
    "CASE5017": "unauthorized_transaction",
    "CASE5018": "refund_request",
    "CASE5019": "other",
    "CASE5020": "cancellation_dispute",
    "CASE5021": "duplicate_charge",
    "CASE5022": "duplicate_charge",
    "CASE5023": "invoice_mismatch",
    "CASE5024": "refund_request",
    "CASE5025": "unauthorized_transaction",
    "CASE5026": "duplicate_charge",
    "CASE5027": "other",
    "CASE5028": "other",
    "CASE5029": "other",
    "CASE5030": "other",
    "CASE5031": "other",
    "CASE5032": "other",
    "CASE5033": "other",
    "CASE5034": "other",
    "CASE5035": "other",
    "CASE5036": "other",
    "CASE5037": "other",
    "CASE5038": "other",
    "CASE5039": "other",
    "CASE5040": "other",
    "CASE5041": "other",
    "CASE5042": "other",
    "CASE5043": "other",
    "CASE5044": "other",
    "CASE5045": "other",
    "CASE5046": "other",
    "CASE5047": "other",
    "CASE5048": "other",
    "CASE5049": "other",
}


def expected_decision_for(db, case, claim_type: str) -> str:
    payments = db.query(Payment).filter(Payment.customer_id == case.customer_id).all()
    subscriptions = db.query(Subscription).filter(Subscription.customer_id == case.customer_id).all()

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
            claim_type = CLAIM_TYPES.get(case.case_id, "other")
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

    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()