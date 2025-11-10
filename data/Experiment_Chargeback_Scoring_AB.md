# Experiment: Chargeback Scoring (A/B)
**Hypothesis:** A gradient-boosted model (GBDT v7) with device-graph and merchant-tier features will reduce chargebacks without hurting approvals.

## Design
- **Arm A:** legacy rules engine
- **Arm B:** GBDT v7, threshold 0.62, features: card velocity, device pairing, merchant risk tier, BIN country match.

## Sample & Duration
- 14 days, 2.1M transactions randomized 50/50
- Guardrails: approvals ±0.5% from baseline; manual reviews ≤ +0.5 / 1k

## Results
- Approvals: A 92.10% vs **B 92.38%** (Δ +0.28pp, ns)
- Chargebacks per 1k: A 3.2 vs **B 2.5** (p<0.05)
- Manual reviews per 1k: A 4.1 vs B 4.0 (ns)

## Decision
Ship **B** to 100% with 7-day watch. Auto-rollback if >3.0/1k for 3 consecutive days.

## Implementation Notes
- Threshold tunable via `fraud.threshold.chargeback_v7`.
- Export features logged under `features.chargeback_v7.*`.
