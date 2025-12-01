# Hybrid Strategy: E2B Sandbox Git Integration

**Plan Date:** 2025-11-20
**Plan ID:** 251120-2018
**Strategy:** Hybrid (Start Approach 1, Validate, Migrate to Approach 2 if needed)
**Parent Plan:** [251120-1909-e2b-sandbox-git-integration](../251120-1909-e2b-sandbox-git-integration/plan.md)

---

## Executive Summary

Implement git operations in E2B sandboxes using phased strategy:
1. **Week 1**: Deploy Approach 1 (simple MCP server) - fast implementation, low risk
2. **Weeks 2-5**: Collect comprehensive metrics, validate performance/cost/concurrency
3. **Weeks 6-9** (conditional): Migrate to Approach 2 (service layer with pooling) if metrics exceed thresholds

**Key Decision Criteria:** Migrate only if ANY threshold exceeded:
- Concurrency > 10 simultaneous operations
- Cost per operation > $0.05
- P95 latency > 2 seconds
- Error rate > 5%
- Monthly cost > $500

---

## Phase Overview

| Phase | Description | Status | Timeline | Priority |
|-------|-------------|--------|----------|----------|
| [Phase 1](phase-01-approach-1-implementation.md) | Implement Approach 1 (Quick Win) | Pending | Week 1 (4-6 hrs) | P0 |
| [Phase 2](phase-02-metrics-instrumentation.md) | Add Prometheus metrics & Grafana dashboard | Pending | Week 1 (2-3 hrs) | P0 |
| [Phase 3](phase-03-validation-period.md) | 2-4 week monitoring & data collection | Pending | Weeks 2-5 | P1 |
| [Phase 4](phase-04-migration-planning.md) | Create migration plan (if needed) | Pending | Week 6 (conditional) | P2 |
| [Phase 5](phase-05-approach-2-migration.md) | Execute Approach 2 migration | Pending | Weeks 6-9 (conditional) | P2 |

---

## Decision Framework

### Stay with Approach 1 If:
- Peak concurrency < 10 operations
- P95 latency < 2s consistently
- Error rate < 5%
- Monthly cost < $500
- Cost per operation < $0.05

**Action:** Optimize MCP server, revisit quarterly

### Migrate to Approach 2 If:
- **ANY** threshold exceeded for 2+ weeks
- Cost trajectory shows 2x growth in 3 months
- Error rate trending upward
- Request queuing visible in metrics

**Action:** Execute canary migration (Phase 4-5)

---

## Time Estimates

### Total Timeline
| Executor | Approach 1 Only | Full Hybrid (with migration) |
|----------|----------------|------------------------------|
| Claude | 1-2 hrs | 4-5 hrs |
| Senior Dev | 1 day | 4-5 days |
| Junior Dev | 2 days | 8-10 days |

### Phase Breakdown
- **Phase 1** (Approach 1): 30-45 min (Claude), 4-6 hrs (Senior), 8-12 hrs (Junior)
- **Phase 2** (Metrics): 15-20 min (Claude), 2-3 hrs (Senior), 4-6 hrs (Junior)
- **Phase 3** (Validation): Observational (weekly checkpoints)
- **Phase 4** (Planning): 20-30 min (Claude), 3-4 hrs (Senior), 6-8 hrs (Junior)
- **Phase 5** (Migration): 90-120 min (Claude), 2-3 days (Senior), 4-6 days (Junior)

---

## Key Metrics to Track

### Foundation (Week 1-2)
- Sandbox creation time: P50/P95/P99 latency
- Operation success rate by type
- Concurrent active sandboxes
- Request volume per endpoint

### Cost Analysis (Week 2-4)
- Cost per operation (compute resources)
- Cost per concurrent user
- Failure recovery cost
- Resource utilization (CPU%, memory%)

### Performance Signals (Week 3-4)
- Operation throughput (requests/sec)
- Latency percentiles for critical paths
- Queue depth (operations waiting)
- Sandbox reuse ratio

### System Health (Continuous)
- Error rate by category
- API availability
- E2B dependency health

---

## Migration Strategy (If Triggered)

### Canary Rollout (Recommended)
1. **Week 6**: Deploy Approach 2 alongside MCP (10% traffic)
2. **Week 7**: Increase to 50%, monitor error rates
3. **Week 8**: Reach 100%, keep MCP as fallback
4. **Week 9**: Decommission MCP if no issues

### Dual-Write Pattern
- **Phase 1**: Write to both systems, read from Approach 1
- **Phase 2**: Write to Approach 2 (primary), validate against Approach 1
- **Phase 3**: Full cutover to Approach 2

### Rollback Strategy
- Feature flags per operation (instant revert)
- Approach 1 remains hot backup for 2 weeks
- Data consistency via dual-write
- Kill-switch tested weekly

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Premature migration (over-engineering) | Medium | Medium | Data-driven thresholds, 2-week validation |
| Metrics overhead impacts performance | Low | Low | Async metric collection, sampling |
| E2B sandbox costs accumulate | Medium | Medium | Timeout cleanup, cost alerts |
| Migration introduces bugs | Low | High | Canary rollout, dual-write validation |
| Lock state inconsistency during migration | Low | Medium | Abstract lock interface, chaos testing |

---

## Security Considerations

### Approach 1
- GitHub tokens injected via env vars only
- Never log tokens or credentials
- Sandbox isolation per agent

### Approach 2 (if migrated)
- Redis locks with TTL (prevent deadlocks)
- Distributed lock audit logs
- Secrets management via Vault/AWS Secrets Manager

---

## Success Criteria

### Phase 1-2 (Foundation)
- ✅ Git operations (clone, pull, push) functional
- ✅ Metrics exported to Prometheus
- ✅ Grafana dashboard operational
- ✅ Baseline data collected (1 week)

### Phase 3 (Validation)
- ✅ Stable metrics for 2+ weeks
- ✅ Decision criteria evaluated weekly
- ✅ Cost projection validated
- ✅ Migration readiness assessed

### Phase 4-5 (Migration, if triggered)
- ✅ Zero-downtime migration
- ✅ Data consistency > 99.99%
- ✅ Performance parity or better vs Approach 1
- ✅ Rollback tested successfully

---

## Dependencies

### Existing Infrastructure
- E2B API key configured
- GitHub token with repo access
- PostgreSQL database (for Approach 2)
- Redis instance (for Approach 2 distributed locks)

### Code Dependencies
- Existing `python_executor_server.py` pattern
- `backend/agents/configuration/mcp_tool_mapping.yaml`
- `backend/core/config.py`

---

## Related Files

- [Approach 1 Details](../251120-1909-e2b-sandbox-git-integration/approach-01-quick-win.md)
- [Approach 2 Details](../251120-1909-e2b-sandbox-git-integration/approach-02-enterprise-grade.md)
- [Metrics Patterns](research/metrics-collection-patterns.md)
- [Migration Strategies](research/migration-strategies.md)

---

## Next Steps

1. Review this plan with stakeholders
2. Confirm E2B API access and GitHub token setup
3. Execute Phase 1: Implement Approach 1
4. Execute Phase 2: Add metrics instrumentation
5. Begin Phase 3: Validation period

---

## Configuration Decisions

1. ✅ **GitHub token scope:** Per-project (shared across agents in same project)
2. ✅ **Sandbox TTL:** 1 hour (balance cost vs reuse)
3. ✅ **Branch cleanup:** Automatic (reduce repo clutter)
4. ✅ **Redis setup:** Single instance (upgrade if needed)
5. ✅ **Budget cap:** $100/month initial, $500/month production (with 75% alerts)
6. ⏳ **Error rate SLA:** TBD (establish baseline during validation period)

**Rationale:**
- Per-project tokens enable sandbox reuse across agents on same project
- 1-hour TTL optimizes cost (60-70% savings vs per-operation sandboxes)
- Automatic branch cleanup prevents repo pollution
- Single Redis sufficient for <100 concurrent operations
- Budget tiered: validation phase ($100) → production ($500) if migrating
- Error rate target determined after 2 weeks of baseline data
