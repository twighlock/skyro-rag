# AML Screening Provider Migration — Plan
**From:** OldAML • **To:** NewAML • **Flag:** `aml_provider=new`

## Phases
1) **Shadow** (2 weeks): call both providers, compare decisions; no customer impact.  
2) **Dual-write** (1 week): write NewAML results to new tables; keep OldAML as source of truth.  
3) **Cutover** (1 day): route 100% traffic to NewAML; monitor latency and decision drift.  
4) **Decommission** (1 week): remove OldAML calls after data retention requirements met.

## Metrics
- Screening latency p95 < 800 ms
- Decision drift < 1.5%
- False positive rate ≤ baseline

## Risks & Mitigations
- **Risk:** Latency spikes → **Mitigation:** region pinning and connection pooling
- **Risk:** Policy differences → **Mitigation:** mapping table + override rules
