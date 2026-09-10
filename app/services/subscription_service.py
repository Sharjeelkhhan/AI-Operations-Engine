from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Subscription


def get_all_subscriptions(db: Session) -> List[Subscription]:
    return db.query(Subscription).all()


def get_subscription_by_id(db: Session, subscription_id: str) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
