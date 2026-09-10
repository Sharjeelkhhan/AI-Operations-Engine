from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_admin_role
from app.database import get_db
from app.exceptions import NotFoundError
from app.schemas import PaymentOut
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/", response_model=List[PaymentOut])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    return payment_service.get_all_payments(db)[skip : skip + limit]


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    payment = payment_service.get_payment_by_id(db, payment_id)
    if not payment:
        raise NotFoundError("Payment", payment_id)
    return payment