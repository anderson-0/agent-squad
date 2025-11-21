# Phase 3: Validation Period (2-4 Weeks)

**Phase:** 3 of 5
**Date:** 2025-11-20
**Priority:** P1 (Observational)
**Status:** Pending
**Parent Plan:** [Hybrid E2B Git Integration](plan.md)

---

## Context

Collect production metrics for 2-4 weeks to make data-driven migration decision. No code changes—purely observational. Weekly checkpoints evaluate if migration thresholds exceeded.

**Reference:** [Metrics Collection Patterns](research/metrics-collection-patterns.md)

---

## Overview

Monitor git operations in production:
- **Week 1**: Baseline stability (cost, latency, error rate)
- **Week 2**: Load pattern analysis (concurrency, operation distribution)
- **Week 3**: Failure mode assessment (error categories, recovery time)
- **Week 4**: Migration readiness decision

---

## Key Insights

- No intervention during validation (let system run naturally)
- Daily metric reviews catch regressions early
- Weekly checkpoints assess migration triggers
- 2-week minimum before migration decision
- Extend to 4 weeks if metrics unstable or inconclusive

---

## Requirements

### Observational Goals
- Establish baseline metrics with ±10% variance
- Identify peak concurrency patterns
- Categorize all failure modes
- Forecast cost trajectory for 3 months
- Validate decision criteria weekly

### Data Collection
- Daily snapshots of key metrics
- Weekly aggregated reports
- Incident logs for all failures
- Cost tracking per operation

---

## Architecture Considerations

### Metric Stability Thresholds
```
Cost per operation:     < ±10% variance
P95 latency:           < ±20% variance
Error rate:            < ±2% absolute change
Concurrent peak:       Identified and consistent
```

### Migration Trigger Review (Weekly)
| Metric | Threshold | Status |
|--------|-----------|--------|
| Concurrency | >10 simultaneous operations | Check weekly |
| Cost/Op | >$0.05 per operation | Check weekly |
| P95 Latency | >2 seconds | Check weekly |
| Error Rate | >5% of operations | Check weekly |
| Monthly Cost | >$500 | Check weekly |
| Throughput | >100 operations/minute | Check weekly |

---

## Related Code Files

### No Code Changes
This phase is purely observational. No files modified.

### Review Files
- Grafana dashboard: `monitoring/grafana/dashboards/git_operations.json`
- Prometheus queries: Review key metrics
- Alert logs: Check for threshold breaches

---

## Implementation Steps

### Week 1: Baseline Stability
**Goal:** Establish stable baseline metrics

**Daily Tasks:**
1. Review Grafana dashboard (morning checkpoint)
2. Export snapshot of key metrics
3. Log any anomalies or incidents
4. Verify metrics consistency

**Success Criteria:**
- Cost per operation stable (±10%)
- P50/P95/P99 latencies stable (±20%)
- Error rate < 2%
- No resource exhaustion events

### Week 2: Load Pattern Analysis
**Goal:** Understand usage patterns and concurrency

**Daily Tasks:**
1. Record peak concurrency times
2. Map operation distribution (% clone vs pull vs push)
3. Analyze E2B API rate limit headroom
4. Measure cache hit ratio (if sandboxes reused)

**Success Criteria:**
- Peak concurrency identified
- Operation distribution mapped
- E2B rate limit headroom > 50%
- Cache hit ratio baseline established

### Week 3: Failure Mode Assessment
**Goal:** Categorize all failures and assess recovery

**Daily Tasks:**
1. Review error logs and categorize failures
2. Measure transient failure recovery time
3. Identify cascade failures (if any)
4. Validate timeout configs vs actual E2B latency

**Success Criteria:**
- All failures categorized (network, timeout, conflict, auth)
- Transient failure recovery time measured
- Cascade failures identified or ruled out
- Timeout thresholds validated

### Week 4: Migration Readiness Decision
**Goal:** Decide if migration to Approach 2 needed

**Weekly Checkpoint:**
1. **Trend analysis**: Cost trajectory, concurrency growth rate
2. **Threshold check**: Any trigger exceeded for 2+ weeks?
3. **Forecast**: Resource requirements for 3 months ahead
4. **Gap analysis**: Architectural gaps (caching, retry, rate limiting)

**Decision Criteria:**
- **STAY** with Approach 1 if all thresholds met
- **MIGRATE** to Approach 2 if any threshold exceeded
- **EXTEND** validation if metrics unstable

---

## Todo List

### P1: Week 1 - Baseline Stability
- [ ] Day 1: Review Grafana dashboard, export metrics snapshot
- [ ] Day 2: Verify cost per operation stability (±10%)
- [ ] Day 3: Verify P95 latency stability (±20%)
- [ ] Day 4: Verify error rate < 2%
- [ ] Day 5: Check for resource exhaustion events
- [ ] Day 6-7: Weekend monitoring (passive, alert-based)
- [ ] Week 1 Summary: Document baseline metrics

### P1: Week 2 - Load Pattern Analysis
- [ ] Day 8: Identify peak concurrency times
- [ ] Day 9: Map operation distribution (% by type)
- [ ] Day 10: Check E2B API rate limit headroom
- [ ] Day 11: Measure cache hit ratio (sandbox reuse)
- [ ] Day 12: Analyze concurrent user patterns
- [ ] Day 13-14: Weekend monitoring
- [ ] Week 2 Summary: Document load patterns

### P1: Week 3 - Failure Mode Assessment
- [ ] Day 15: Review error logs, categorize failures
- [ ] Day 16: Measure transient failure recovery time
- [ ] Day 17: Identify cascade failures (if any)
- [ ] Day 18: Validate timeout configs vs E2B latency
- [ ] Day 19: Document all failure modes
- [ ] Day 20-21: Weekend monitoring
- [ ] Week 3 Summary: Failure analysis report

### P1: Week 4 - Migration Decision
- [ ] Day 22: Run trend analysis (cost, concurrency growth)
- [ ] Day 23: Check migration triggers (all thresholds)
- [ ] Day 24: Forecast resource needs (3 months ahead)
- [ ] Day 25: Identify architectural gaps
- [ ] Day 26: **DECISION**: Stay, Migrate, or Extend validation
- [ ] Day 27-28: Prepare Phase 4 plan if migrating
- [ ] Week 4 Summary: Migration readiness report

### P2: Extended Validation (If Needed)
- [ ] Week 5-6: Repeat pattern analysis if metrics unstable
- [ ] Week 5-6: Re-evaluate decision criteria
- [ ] Week 5-6: Final decision by end of Week 6

---

## Success Criteria

### Week 1 Success
- ✅ Baseline metrics established
- ✅ Cost/latency/error rate stable
- ✅ No major incidents

### Week 2 Success
- ✅ Peak concurrency identified
- ✅ Operation distribution mapped
- ✅ E2B rate limit headroom confirmed

### Week 3 Success
- ✅ All failures categorized
- ✅ Recovery times measured
- ✅ Timeout configs validated

### Week 4 Success
- ✅ Clear migration decision made
- ✅ Forecast complete (3 months)
- ✅ Plan ready for next phase

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Metrics unstable (no clear baseline) | Medium | Medium | Extend validation to 6 weeks |
| Threshold exceeded but transient spike | Low | Low | Require 2+ weeks sustained breach |
| E2B pricing changes mid-validation | Low | Medium | Monitor E2B announcements, adjust thresholds |
| Validation period extends indefinitely | Low | Medium | Max 6 weeks, make decision with incomplete data |

---

## Security Considerations

- **No production changes**: Read-only monitoring, no risk
- **Data export**: Sanitize metrics (no PII, tokens, repo URLs)
- **Dashboard access**: Limit to ops team during validation

---

## Next Steps

### If STAY with Approach 1
1. Document optimization opportunities
2. Schedule quarterly re-evaluation
3. Close Phase 4-5 as not needed

### If MIGRATE to Approach 2
1. Proceed to Phase 4: Migration planning
2. Prepare canary rollout strategy
3. Allocate team resources for 2-3 week migration

### If EXTEND Validation
1. Document reasons for extension
2. Set new decision deadline (Week 6)
3. Adjust monitoring focus based on gaps

---

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | N/A | Automated metric collection |
| Senior Dev | 1-2 hrs/week | Daily dashboard reviews, weekly reports |
| Junior Dev | 2-3 hrs/week | Learning metrics analysis, report writing |

**Total Effort:** 4-12 hours spread over 2-4 weeks (passive monitoring)

**Complexity:** Simple (observational only)

---

## Unresolved Questions

1. Who reviews daily metrics? (DevOps, Backend team, or automated?)
2. Alert escalation path if threshold breached mid-validation?
3. Decision authority: Who makes final call to migrate or stay?
4. Budget approval needed if migration recommended?
