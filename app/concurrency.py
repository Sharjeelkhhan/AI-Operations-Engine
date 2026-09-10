from sqlalchemy.orm import Session

from app.models import Payment, Subscription


class ConcurrencyConflictError(RuntimeError):
    pass


def apply_payment_update(db: Session, payment_id: str, new_status: str, expected_version: int) -> Payment:
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).one_or_none()
    if payment is None:
        raise ValueError("Payment not found")
    if payment.version != expected_version:
        raise ConcurrencyConflictError("Payment has changed since it was last read")

    payment.status = new_status
    payment.version = payment.version + 1
    db.commit()
    db.refresh(payment)
    return payment


def apply_subscription_update(db: Session, subscription_id: str, new_status: str, expected_version: int) -> Subscription:
    subscription = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).one_or_none()
    if subscription is None:
        raise ValueError("Subscription not found")
    if subscription.version != expected_version:
        raise ConcurrencyConflictError("Subscription has changed since it was last read")

    subscription.status = new_status
    subscription.version = subscription.version + 1
    db.commit()
    db.refresh(subscription)
    return subscription
