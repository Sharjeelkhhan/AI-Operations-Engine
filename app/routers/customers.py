from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_admin_role
from app.database import get_db
from app.exceptions import NotFoundError
from app.schemas import CustomerOut
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerOut])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    return customer_service.get_all_customers(db)[skip : skip + limit]


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    customer = customer_service.get_customer_by_id(db, customer_id)
    if not customer:
        raise NotFoundError("Customer", customer_id)
    return customer