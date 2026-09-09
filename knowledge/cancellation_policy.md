# NovaDesk Cancellation Policy

## 1. Subscription Cancellation
- Customers may cancel their subscription at any time.
- Cancellation takes effect at the end of the current billing period.
- The cancellation date is recorded in the `subscriptions` table as `status = 'cancelled'` and `end_date`.

## 2. Refunds After Cancellation
- If a payment is processed after the cancellation date, it is considered erroneous and should be refunded.
- If the payment occurred before cancellation, no refund is due.

## 3. Prorated Refunds
- NovaDesk does not offer prorated refunds for partial months.
- Exception: Duplicate charges (see Refund Policy).