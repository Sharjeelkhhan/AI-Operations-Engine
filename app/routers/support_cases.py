from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SupportCase
from app.schemas import SupportCaseOut
from typing import List

router = APIRouter(prefix="/support-cases", tags=["support-cases"])

@router.get("/", response_model=List[SupportCaseOut])
def list_support_cases(db: Session = Depends(get_db)):
    return db.query(SupportCase).all()

@router.get("/{case_id}", response_model=SupportCaseOut)
def get_support_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(SupportCase).filter(SupportCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Support case not found")
    return case