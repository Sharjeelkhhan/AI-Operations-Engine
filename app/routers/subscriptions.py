from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_admin_role
from app.database import get_db
from app.exceptions import NotFoundError
from app.schemas import SubscriptionOut
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/", response_model=List[SubscriptionOut])
def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    return subscription_service.get_all_subscriptions(db)[skip : skip + limit]


@router.get("/{subscription_id}", response_model=SubscriptionOut)
def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_role),
):
    sub = subscription_service.get_subscription_by_id(db, subscription_id)
    if not sub:
        raise NotFoundError("Subscription", subscription_id)
    return sub