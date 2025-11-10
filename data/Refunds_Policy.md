# Refunds Policy
**Eligibility:** card-present and card-not-present; refund window 60 days.  
**Flow:** request → validate → hold funds → issue refund → notify customer.

## Edge Cases
- **Partial refunds:** pro-rate fees; respect FX rate at original capture time.
- **Duplicate refunds:** enforce idempotency key `refund_idem_key` (24h TTL).
- **Chargeback coexistence:** if chargeback opened, block refunds to avoid double credits.

## Audit
- Log `refund.created`, `refund.failed`, `refund.succeeded` with `actor`, `reason`, `source_txn`.
