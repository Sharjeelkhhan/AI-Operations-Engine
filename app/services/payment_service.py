from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Payment


def get_all_payments(db: Session) -> List[Payment]:
    return db.query(Payment).all()


def get_payment_by_id(db: Session, payment_id: str) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.payment_id == payment_id).first()


def get_payments_for_customer(db: Session, customer_id: str) -> List[Payment]:
    return db.query(Payment).filter(Payment.customer_id == customer_id).all()


def get_successful_payments_for_subscription(db: Session, subscription_id: str) -> List[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.subscription_id == subscription_id, Payment.status == "successful")
        .all()
    )
