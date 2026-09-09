# NovaDesk Escalation Policy

## 1. Cases That Require Human Review
- Customer claims that cannot be fully verified with database records.
- Potential unauthorized transactions.
- Refund requests above $500 (unless manager approval already exists).
- Any case where the AI’s confidence is below 0.85.
- Cases involving legal threats or regulatory complaints.

## 2. Cases That Can Be Automated
- Duplicate charges with clear evidence of two successful payments for the same period and total amount ≤ $500.
- Cancellation refunds where cancellation date is before payment date and amount ≤ $500.
- Simple payment status inquiries where records are unambiguous.

## 3. Escalation Procedure
- The AI must set `decision = 'HUMAN_REVIEW'` and `requires_human_approval = true`.
- The reason must explain what is missing or uncertain.
- The support team is notified via the case management system.