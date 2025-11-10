# Feature Spec: P2P Limits v2
**Team:** Payments • **Owner:** A. Novak (PM) • **Status:** Draft → In Review  
**Reviewers:** Risk, Support, Legal  
**Last updated:** 2024-09-10

## 1. Summary
We are revising peer-to-peer (P2P) transfer limits by customer tier and clarifying exactly when KYC re-verification is required. The current limit rules frequently result in opaque failures at checkout and unnecessary escalations to Support.

**Objectives**
- Reduce limit-related declines by 30% (p90 over 28 days)
- Maintain or improve fraud loss rate (≤ +2 bps to baseline)
- Improve “limit clarity” CSAT from 4.1 → 4.6

## 2. Background & Problem
- Legacy rules were implemented in 2021 and don’t reflect the current risk posture or device graph coverage.
- “Repeat KYC” is triggered on profile edits even if they are non-sensitive (e.g., marketing preferences), causing drop-offs.

## 3. Proposed Limits
| Tier     | Daily Limit | Monthly Limit | Required KYC | Re-verification |
|----------|-------------|---------------|--------------|-----------------|
| Bronze   | $1,000      | $5,000        | L0           | If profile edited + any sanctions hit |
| Silver   | $2,500      | $12,000       | L1           | If legal name, DOB, or address changes |
| **Gold** | **$5,000**  | **$25,000**   | L1           | **Not required if profile unchanged** |
| Platinum | $15,000     | $75,000       | L2           | Annual refresh or on AML trigger      |

**Manual Review Thresholds**
- Bronze: $800/day
- Silver: $2,000/day
- Gold: $4,000/day
- Platinum: $12,000/day

## 4. UX & Error Copy
- `LIMIT_EXCEEDED_DAILY`: “You’ve reached today’s limit for your tier.”
- `KYC_RECHECK_REQUIRED`: “Please confirm your identity to increase your limit.”  
- “View my limits” link opens `/settings/limits` with tier breakdown and eligibility.

## 5. API & Events
- `POST /v1/p2p/send` will include `limit_context { tier, daily_remaining, monthly_remaining }`.
- Emit `limits.violation` event with payload: `user_id`, `tier`, `attempt_amount`, `rule_id`.

## 6. Rollout Plan
1. Phase 1 — 10% users (1 week), guard by feature flag `limits_v2_enabled`.
2. Phase 2 — 50% users (1 week) if chargeback rate ≤ baseline + 2 bps.
3. Phase 3 — 100% users and remove legacy code path.

## 7. Metrics & Alerts
- Decline rate tagged `LIMIT_*` (by tier)
- Fraud loss rate (bps) by tier and device score
- Dashboard alert: if `LIMIT_*` declines > 10% WoW

## 8. Risks & Mitigations
- **Risk:** Gold tier increase could shift fraud.  
  **Mitigation:** device graph threshold +2 for new devices during ramp.

## 9. Open Questions
- Should legal address edits always trigger L1 re-verification? (Legal to confirm)
