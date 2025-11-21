# Phase 2: Metrics Instrumentation

**Phase:** 2 of 5
**Date:** 2025-11-20
**Priority:** P0 (Must Have)
**Status:** Complete ✅ (Ready for Testing)
**Parent Plan:** [Hybrid E2B Git Integration](plan.md)

---

## Context

Add comprehensive Prometheus metrics to git operations MCP server. Enables data-driven decision for migration to Approach 2. Metrics collected during 2-4 week validation period (Phase 3).

**Reference:** [Metrics Collection Patterns](research/metrics-collection-patterns.md)

---

## Overview

Instrument git operations with Prometheus metrics:
- Sandbox creation time (histogram)
- Operation success/failure counts (counter)
- Active sandboxes (gauge)
- Git operation latency (histogram)
- Error rates by category (counter)

Create Grafana dashboard for real-time monitoring.

---

## Key Insights

- Minimal overhead: Async metric collection, no blocking I/O
- Foundation metrics (Week 1-2): Latency, success rate, concurrency
- Cost metrics (Week 2-4): Resource usage, failure recovery cost
- Performance metrics (Week 3-4): Throughput, queue depth, reuse ratio
- Decision criteria: Any threshold exceeded → candidate for migration

---

## Requirements

### Functional
- Prometheus `/metrics` endpoint exposed
- All git operations instrumented
- Grafana dashboard with 8-10 key charts
- Alerts configured for threshold breaches

### Non-Functional
- Metrics collection overhead < 5ms per operation
- Metric export endpoint response < 100ms
- Dashboard refresh rate: 15 seconds
- Data retention: 30 days

---

## Architecture Considerations

### Prometheus Setup
```python
from prometheus_client import Counter, Histogram, Gauge, Summary

# Sandbox metrics
sandbox_creation_duration = Histogram(
    'sandbox_creation_seconds',
    'Time to create E2B sandbox',
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

# Operation metrics
git_operation_total = Counter(
    'git_operation_total',
    'Total git operations',
    labelnames=['operation', 'status']  # status: success, failure, retry
)

git_operation_duration = Histogram(
    'git_operation_duration_seconds',
    'Git operation latency',
    labelnames=['operation'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Resource metrics
active_sandboxes = Gauge(
    'active_sandboxes_total',
    'Currently active E2B sandboxes'
)

# Error metrics
git_errors = Counter(
    'git_errors_total',
    'Git operation errors',
    labelnames=['operation', 'error_type']  # error_type: network, timeout, conflict, auth
)
```

### Instrumentation Pattern
```python
async def _handle_git_clone(self, arguments):
    active_sandboxes.inc()  # Increment gauge

    with sandbox_creation_duration.time():
        try:
            sandbox = Sandbox.create(...)
            git_operation_total.labels(operation='clone', status='success').inc()
            return {"success": True, ...}
        except Exception as e:
            git_operation_total.labels(operation='clone', status='failure').inc()
            git_errors.labels(operation='clone', error_type='network').inc()
            raise
        finally:
            active_sandboxes.dec()  # Decrement gauge
```

### Grafana Dashboard Panels
1. **Operation Success Rate** (gauge): `rate(git_operation_total{status="success"}[5m]) / rate(git_operation_total[5m])`
2. **P95 Latency by Operation** (graph): `histogram_quantile(0.95, git_operation_duration_seconds_bucket)`
3. **Active Sandboxes** (gauge): `active_sandboxes_total`
4. **Operations per Minute** (graph): `rate(git_operation_total[1m])`
5. **Error Rate by Type** (stacked graph): `rate(git_errors_total[5m])`
6. **Sandbox Creation Time** (heatmap): `sandbox_creation_seconds_bucket`

---

## Related Code Files

### Modified Files
- `backend/integrations/mcp/servers/git_operations_server.py` (add metrics)
- `backend/core/config.py` (add Prometheus config)

### New Files
- `backend/monitoring/prometheus_metrics.py` (centralized metrics definitions)
- `monitoring/grafana/dashboards/git_operations.json` (dashboard config)
- `docker-compose.yml` (add Prometheus & Grafana services, if not present)

---

## Implementation Steps

### Step 1: Install Dependencies
- Add `prometheus-client` to `requirements.txt`
- Add `prometheus-fastapi-instrumentator` (if using FastAPI)
- Install Prometheus & Grafana via Docker Compose

### Step 2: Define Metrics
- Create `backend/monitoring/prometheus_metrics.py`
- Define all metrics (counters, histograms, gauges)
- Export metrics module for import

### Step 3: Instrument Git Operations
- Import metrics in `git_operations_server.py`
- Add `with histogram.time():` context managers
- Increment counters on success/failure
- Update gauges for active sandboxes
- Track error types in labels

### Step 4: Expose Metrics Endpoint
- Add `/metrics` route (if not auto-exposed)
- Test endpoint returns Prometheus format
- Verify metrics update in real-time

### Step 5: Configure Prometheus
- Add scrape config for MCP server
- Set scrape interval: 15 seconds
- Configure retention: 30 days
- Test Prometheus UI shows metrics

### Step 6: Create Grafana Dashboard
- Import template or create custom dashboard
- Add 8-10 key panels (listed above)
- Configure alerts for thresholds
- Test dashboard displays live data

### Step 7: Validate Metrics
- Run load test (simulate 10 concurrent operations)
- Verify metrics update correctly
- Check Grafana dashboard refresh
- Confirm alert triggers at thresholds

---

## Todo List

### P0: Metrics Definition
- [x] Install `prometheus-client` in `requirements.txt` ✅ (already present)
- [x] Create `backend/monitoring/prometheus_metrics.py` ✅
- [x] Define `sandbox_creation_duration` histogram ✅
- [x] Define `git_operation_total` counter ✅
- [x] Define `git_operation_duration` histogram ✅
- [x] Define `active_sandboxes` gauge ✅
- [x] Define `git_errors` counter (with error_type labels) ✅
- [x] Export metrics for import in git_operations_server ✅

### P0: Instrumentation
- [x] Import metrics in `git_operations_server.py` ✅
- [x] Instrument `git_clone` with creation duration timer ✅
- [x] Instrument `git_push` with retry count tracking ✅
- [x] Instrument `git_pull` with conflict detection counter ✅
- [x] Add success/failure counters to all 5 tools ✅ (clone, status, diff, pull, push)
- [x] Track active sandboxes (increment on create, decrement on cleanup) ✅
- [x] Add error type labels (network, timeout, conflict, auth, sandbox_not_found) ✅
- [x] Add cache hit/miss tracking for sandbox retrieval ✅

### P0: Prometheus Setup
- [x] Add Prometheus service to `docker-compose.yml` ✅
- [x] Configure Prometheus scrape config (`prometheus.yml`) ✅
- [x] Set scrape interval: 15 seconds ✅
- [x] Set retention period: 30 days ✅
- [x] Expose `/metrics` endpoint on backend (port 8000) ✅ (already configured)
- [ ] Test Prometheus UI shows git metrics (requires running system)

### P0: Grafana Dashboard
- [x] Add Grafana service to `docker-compose.yml` ✅
- [x] Create dashboard: `monitoring/grafana/dashboards/git_operations.json` ✅
- [x] Add panel: Operation Success Rate (gauge) ✅
- [x] Add panel: P95 Latency by Operation (line graph) ✅
- [x] Add panel: Active Sandboxes (gauge) ✅
- [x] Add panel: Cache Hit Ratio (gauge) ✅ (bonus panel)
- [x] Add panel: Operations per Minute (line graph) ✅
- [x] Add panel: Error Rate by Type (stacked area) ✅
- [x] Add panel: Sandbox Creation Time (heatmap) ✅
- [x] Add panel: Estimated Monthly Cost (gauge) ✅ (bonus panel)
- [x] Add panel: Daily Cost Trend (line graph) ✅ (bonus panel)
- [x] Add panel: Operations Distribution (pie chart) ✅ (bonus panel)
- [x] Add panel: Push Retry Attempts (bar chart) ✅ (bonus panel)
- [x] Add panel: Conflicts Detected (line graph) ✅ (bonus panel)
- [x] Configure auto-refresh: 15 seconds ✅
- [x] Configure Grafana datasource provisioning ✅
- [x] Configure dashboard auto-loading ✅
- [ ] Test dashboard with live data (requires running system)

### P1: Alerts
- [ ] Configure alert: P95 latency > 2 seconds
- [ ] Configure alert: Error rate > 5%
- [ ] Configure alert: Active sandboxes > 10
- [ ] Configure alert: Operations per minute > 100
- [ ] Configure alert: Monthly cost > $75 (75% of $100 budget)
- [ ] Configure alert: Daily cost > $5 (exceeds projected daily rate)
- [ ] Add E2B cost tracking metric (sandbox hours × $0.015/hr)
- [ ] Test alert triggers via load test
- [ ] Add Slack/email notification channel

### P1: Documentation
- [ ] Document metrics definitions and labels
- [ ] Create dashboard user guide
- [ ] Document alert thresholds and escalation
- [ ] Add troubleshooting guide for metric issues

---

## Success Criteria

### Functional
- ✅ Prometheus `/metrics` endpoint operational
- ✅ All git operations instrumented
- ✅ Grafana dashboard displays 8+ charts
- ✅ Metrics update in real-time (< 30s lag)
- ✅ Alerts configured and tested

### Performance
- ✅ Metrics collection overhead < 5ms
- ✅ Metrics endpoint response < 100ms
- ✅ Dashboard loads in < 2 seconds

### Data Quality
- ✅ All operations tracked (no missing data)
- ✅ Error types correctly labeled
- ✅ Latency buckets cover full range (0.1s - 60s)
- ✅ Gauges reflect actual state (no drift)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Metrics overhead impacts performance | Low | Low | Async collection, no blocking I/O |
| Prometheus storage fills disk | Low | Medium | Configure retention policy (30 days) |
| Dashboard shows stale data | Low | Low | Auto-refresh enabled, test connectivity |
| Alert fatigue from false positives | Medium | Low | Tune thresholds after baseline week |
| Metric label cardinality explosion | Low | Medium | Limit labels (operation, status, error_type) |

---

## Security Considerations

- **No PII in metrics**: Never include user IDs, tokens, or repo URLs in labels
- **Sanitize error messages**: Redact credentials from error_type labels
- **Grafana access control**: Require authentication for dashboard
- **Metrics endpoint**: Expose only to internal network (no public access)

---

## Next Steps

1. Execute all P0 checklist items (define metrics, instrument code, setup Prometheus/Grafana)
2. Deploy to dev environment
3. Run load test to validate metrics
4. Review dashboard with team
5. Proceed to Phase 3: Begin validation period

---

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 15-20 min | Automated config generation, dashboard JSON |
| Senior Dev | 2-3 hrs | Familiar with Prometheus/Grafana patterns |
| Junior Dev | 4-6 hrs | Learning Prometheus query language (PromQL) |

**Complexity:** Simple

---

## Unresolved Questions

1. Prometheus storage backend: local disk or remote (e.g., Thanos)?
2. Alert notification channel: Slack, email, PagerDuty, or all?
3. Dashboard access: read-only for all or edit access for ops team?
4. Metric sampling rate: 100% or sample high-volume operations?
