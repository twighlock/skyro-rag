# SLA & Escalations (Payouts)
**SLA:** 99.5% of payouts complete within 2 hours (rolling 24h).  
**Escalate:** if delay > 3 hours OR backlog age > 25 minutes OR provider 5xx > 8% (10-min).

## Runbook
1) Check provider status page; if 429/5xx > 3% (5-min), throttle to 80% baseline.
2) If fail rate > 8% (10-min), switch to secondary provider.
3) Update status page; notify Support with ETA.
4) If backlog age > 25 min, add burst workers capped at +200 RPS.
