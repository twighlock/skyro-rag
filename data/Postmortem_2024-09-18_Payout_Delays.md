# Postmortem: Payout Delays — 2024-09-18
**Impact:** 09:12–11:47 UTC, 7.8% payouts delayed > 2 hours; no data loss.  
**Severity:** SEV-2 • **Reported by:** Support on call

## Root Cause
Settlement queue overload coincided with provider retry storms (HTTP 429), causing compounding delays. Our retry jitter was too narrow, leading to synchronized bursts.

## Timeline
- 09:10 — increase in 429s from provider
- 09:12 — queue age alert triggered
- 10:05 — manual throttle to 60% baseline; requeue rate drops
- 11:47 — backlog drained

## Mitigation
- Reduced concurrency from 1,200 → 600
- Widened retry jitter; applied exponential backoff
- Drained backlog with controlled bursts

## Action Items
- Token bucket per merchant (owner: Eng) — due 2024-10-01
- Provider contract: burst caps (owner: BizOps) — due 2024-10-07
- Alert: queue age > 25 min (owner: SRE) — **done**
