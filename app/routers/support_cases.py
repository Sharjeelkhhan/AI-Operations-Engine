from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_admin_role
from app.database import get_db
from app.exceptions import NotFoundError
from app.schemas import SupportCaseOut
from app.services import case_service

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