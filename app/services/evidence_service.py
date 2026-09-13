from sqlalchemy.orm import Session

from app.models import Customer, Payment, Subscription, SupportCase
from app.schemas import EvidenceBundle


def gather_evidence(db: Session, case: SupportCase) -> EvidenceBundle:
    """
    Gather all DB evidence relevant to a support case.
    Returns IDs (not full records) plus a summary, so the LLM has a compact view.
    """
    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == case.customer_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )

    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.customer_id == case.customer_id)
        .all()
    )

    successful_payments = [p for p in payments if p.status == "successful"]
    total = sum(p.amount for p in successful_payments)

    summary_lines = [
        f"Customer has {len(payments)} payment record(s) total, "
        f"{len(successful_payments)} successful.",
        f"Total successful amount: ${total:.2f}.",
    ]

    if subscriptions:
        for sub in subscriptions:
            summary_lines.append(
                f"Subscription {sub.subscription_id}: plan={sub.plan}, "
                f"status={sub.status}, renewal={sub.renewal_date}."
            )

    # Flag obvious duplicate pattern for the LLM's context
    if len(successful_payments) >= 2:
        amounts = [p.amount for p in successful_payments]
        if len(set(amounts)) == 1 and len(amounts) >= 2:
            summary_lines.append(
                f"NOTE: {len(successful_payments)} successful payments "
                f"of the same amount (${amounts[0]:.2f}) detected — potential duplicate."
            )

    return EvidenceBundle(
        payments=[p.payment_id for p in successful_payments],
        subscriptions=[s.subscription_id for s in subscriptions],
        total_amount=float(total),
        policy_chunks=[],  # filled in by decision_service
        summary=" ".join(summary_lines),
    )