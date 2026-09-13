"""Run support cases through the full AI pipeline for evaluation."""
import csv
import time
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import SupportCase
from app.services import (
    decision_service,
    evidence_service,
    guardrail_service,
    llm_service,
    retrieval_service,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_CSV = PROJECT_ROOT / "data" / "evaluation_expected.csv"


def load_expected() -> Dict[str, str]:
    """Load expected decisions from the golden dataset CSV."""
    expected: Dict[str, str] = {}
    with open(EXPECTED_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            expected[row["case_id"]] = row["expected_decision"]
    return expected


def run_one_case(db: Session, case_id: str, expected: str) -> dict:
    """Run a single case through the full pipeline."""
    start = time.time()

    case = db.query(SupportCase).filter(SupportCase.case_id == case_id).first()
    if not case:
        return {"case_id": case_id, "expected": expected, "actual": None, "error": "case not found"}

    try:
        claim = llm_service.extract_claim(case.message)

        retrieved = retrieval_service.search(db, case.message, top_k=3)
        policy_texts = [r.chunk_text for r in retrieved]
        policy_labels = [f"{r.source_file}#{r.section_title}" for r in retrieved]

        evidence = evidence_service.gather_evidence(db, case)
        evidence.policy_chunks = policy_labels

        decision = decision_service.decide(claim, policy_texts, evidence)
        decision = guardrail_service.apply_guardrails(decision, claim)

        latency_ms = int((time.time() - start) * 1000)

        return {
            "case_id": case_id,
            "expected": expected,
            "actual": decision.decision,
            "confidence": decision.confidence,
            "requires_human_approval": decision.requires_human_approval,
            "reason": decision.reason,
            "evidence_payments": decision.evidence.payments,
            "policy_chunks": decision.evidence.policy_chunks,
            "latency_ms": latency_ms,
            "claim_type": claim.claim_type,
        }

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "case_id": case_id,
            "expected": expected,
            "actual": None,
            "error": str(e),
            "latency_ms": latency_ms,
        }


def run_all(case_ids: List[str] = None) -> List[dict]:
    """Run all cases (or a subset) through the pipeline."""
    expected_map = load_expected()

    if case_ids is None:
        case_ids = list(expected_map.keys())

    db = SessionLocal()
    results: List[dict] = []
    try:
        for case_id in case_ids:
            expected = expected_map.get(case_id, "UNKNOWN")
            result = run_one_case(db, case_id, expected)
            print(f"  {case_id}: expected={expected} actual={result.get('actual')}")
            results.append(result)
    finally:
        db.close()

    return results