# OKR Q3 — Payments
**Team:** Payments • **Period:** 2024-07-01 → 2024-09-30

## Objectives & Key Results
**O1: Make payouts reliably fast**
- KR1: Reduce average payout time p50 ≤ 20 min, p95 ≤ 90 min
- KR2: Reduce requeue rate ≤ 1.5% (rolling 7d)

**O2: Keep fraud losses within budget**
- KR3: Duplicate-detection precision ≥ 0.95; recall ≥ 0.80
- KR4: Chargebacks per 1k transactions ≤ 2.8 (p90 weekly)

**O3: Improve developer ergonomics**
- KR5: SDK coverage Python & JS with ≥ 90% sample parity
- KR6: Time-to-first-payout in sandbox < 15 minutes

## Notes
- Halfway health check (Aug 15): KR1 at risk due to provider throttling.
- Dependencies: SRE queue tuning, Risk device graph rollout.
