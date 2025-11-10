# Ledger Reconciliation Runbook
**Cadence:** nightly at 02:00 UTC • **Owner:** FinOps

## Steps
1. Export settlements for T-1 from provider (CSV).
2. Join with internal payouts ledger by `payout_id` and `provider_ref`.
3. Compute deltas; flag mismatches > $0.01 or missing rows.
4. Create Jira ticket `FINOPS-RECON-*` for mismatches; attach diff.
5. Post summary to `#finops` with totals: matched, missing, mismatched.

## Alerts
- If mismatches > 0.5% of rows, page on-call (Payments).

## Notes
- FX rounding differences must be within provider tolerance table.
