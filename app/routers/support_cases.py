from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_admin_role
from app.database import get_db
from app.exceptions import NotFoundError
from app.models import SupportCase
from app.schemas import ClaimExtraction, SupportCaseOut
from app.services import case_service, llm_service
from app.schemas import AnalyzeResponse
from app.services import decision_service, evidence_service, guardrail_service, llm_service, retrieval_service
router = APIRouter(prefix="/support-cases", tags=["support-cases"])


@router.get("/", response_model=List[SupportCaseOut])
def list_support_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    return case_service.get_all_cases(db)[skip : skip + limit]


@router.get("/{case_id}", response_model=SupportCaseOut)
def get_support_case(
    case_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    case = case_service.get_case_by_id(db, case_id)
    if not case:
        raise NotFoundError("Support case", case_id)
    return case


@router.post("/{case_id}/extract", response_model=ClaimExtraction)
def extract_case(
    case_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    case = db.query(SupportCase).filter(SupportCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    return llm_service.extract_claim(case.message)

@router.post("/{case_id}/analyze", response_model=AnalyzeResponse)
def analyze_case(
    case_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    case = db.query(SupportCase).filter(SupportCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    claim = llm_service.extract_claim(case.message)

    retrieved = retrieval_service.search(db, case.message, top_k=3)
    policy_texts = [r.chunk_text for r in retrieved]
    policy_labels = [f"{r.source_file}#{r.section_title}" for r in retrieved]

    evidence = evidence_service.gather_evidence(db, case)
    evidence.policy_chunks = policy_labels


    decision = decision_service.decide(claim, policy_texts, evidence)

    decision = guardrail_service.apply_guardrails(decision, claim)

    return AnalyzeResponse(
        case_id=case.case_id,
        claim=claim,
        decision=decision.decision,
        confidence=decision.confidence,
        reason=decision.reason,
        evidence=decision.evidence,
        requires_human_approval=decision.requires_human_approval,
        llm_metadata={
            "model": decision_service.MODEL_NAME,
            "prompt_version": decision_service.DECISION_PROMPT_VERSION,
        },
    )