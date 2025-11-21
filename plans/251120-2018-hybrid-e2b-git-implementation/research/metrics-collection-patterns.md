# Metrics Collection Patterns & Migration Decision Criteria

Research Date: 2025-11-20

## Executive Summary

Migration from simple MCP server to full FastAPI service requires data-driven decisions. Prometheus-based observability provides the foundation; migration triggers based on cost/performance/concurrency thresholds prevent premature over-engineering.

---

## 1. Key Metrics to Collect (Priority Order)

### Phase 1: Foundation (Week 1-2)
- **Sandbox Creation Time**: P50/P95/P99 latency (histogram: `sandbox_creation_duration_seconds`)
- **Operation Success Rate**: Percentage of successful operations vs failures by operation type
- **Concurrent Active Sandboxes**: Gauge tracking active sandbox instances
- **Request Volume**: Counter tracking requests per endpoint/operation type

### Phase 2: Cost Analysis (Week 2-4)
- **Cost Per Operation**: Track compute resources consumed (CPU minutes, memory GB-seconds)
- **Cost Per Concurrent User**: Aggregate cost divided by concurrent user count
- **Failure Recovery Cost**: Additional compute spent retrying failed operations
- **Resource Utilization**: CPU%, memory%, disk I/O (Prometheus node exporter metrics)

### Phase 3: Performance Signals (Week 3-4)
- **Operation Throughput**: Requests per second by operation type (counter: `operations_total`)
- **Latency Percentiles**: P50/P95/P99 for critical paths (histogram buckets: 50ms, 100ms, 200ms, 500ms, 1s, 2s, 5s)
- **Queue Depth**: Operations waiting for sandbox resources (gauge)
- **Sandbox Reuse Ratio**: Cache hits vs cache misses (counter: `sandbox_cache_hits`, `sandbox_cache_misses`)

### Phase 4: System Health (Continuous)
- **Error Rate by Category**: Network errors, timeout errors, resource exhaustion, validation errors
- **API Availability**: Uptime percentage and incident duration
- **Dependency Health**: E2b API response times, rate limit status

---

## 2. Prometheus Integration Pattern for FastAPI

### Minimal Setup (Start Here)
```python
# 1. Install: prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

Exposes `/metrics` endpoint with default HTTP metrics (request count, duration, size).

### Custom Metrics for Sandbox Operations
```python
from prometheus_client import Counter, Histogram, Gauge

# Core metrics
sandbox_creation = Histogram(
    'sandbox_creation_seconds',
    'Time to create sandbox',
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
    labelnames=['region', 'size']
)

operation_success = Counter(
    'operations_success_total',
    'Successful operations',
    labelnames=['operation', 'status']
)

active_sandboxes = Gauge(
    'active_sandboxes',
    'Currently active sandboxes',
    labelnames=['region']
)

# In endpoint handlers:
with sandbox_creation.labels(region='us-east', size='small').time():
    sandbox = await create_sandbox()
```

### Prometheus Scrape Config
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi-service'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard Queries
- `rate(operations_success_total[5m])` - Request rate by operation type
- `histogram_quantile(0.95, sandbox_creation_seconds_bucket)` - P95 sandbox creation time
- `active_sandboxes` - Real-time active sandbox count

---

## 3. Migration Trigger Thresholds (Decision Criteria)

### Trigger Conditions (Any ONE satisfied = Candidate for Migration)

| Metric | Threshold | Signal |
|--------|-----------|--------|
| **Concurrency** | >10 simultaneous sandbox operations | Resource contention evident |
| **Cost/Op** | >$0.05 per operation after failures | Efficiency optimization needed |
| **P95 Latency** | >2 seconds for creation operations | Performance bottleneck |
| **Error Rate** | >5% of operations failing | Reliability concern |
| **Cost/Month** | >$500 for sandbox operations | Scale makes service cost-effective |
| **Throughput** | >100 operations/minute sustained | MCP single-process limitation reached |

### Pre-Migration Validation (2-week period minimum)

Before migration, collect baseline data:
1. **Cost baseline**: Calculate `total_compute_cost / total_operations` with 95% confidence interval
2. **Performance baseline**: P50/P95/P99 latencies for all critical operations
3. **Failure analysis**: Root cause breakdown of failures (e2b API, timeouts, resource limits)
4. **Concurrency pattern**: Peak concurrent users, typical session duration, operation distribution
5. **Growth trajectory**: Trend analysis to forecast when thresholds will be exceeded

---

## 4. Migration Strategies

### Strategy A: Gradual Canary (Recommended for >$500/month)
1. **Week 1**: Deploy FastAPI service alongside MCP server (10% traffic)
2. **Week 2**: Increase FastAPI traffic to 50%, monitor error rates
3. **Week 3**: Reach 100% FastAPI, keep MCP as fallback (read-only)
4. **Week 4**: Decommission MCP if no critical issues

**Advantages**: Zero downtime, easy rollback, production validation
**Timeline**: 3-4 weeks, minimal risk

### Strategy B: Big Bang (For urgent scaling, >1000 ops/min)
1. **Day 1**: Deploy FastAPI with feature parity + 2x safety margin
2. **Day 1**: Run parallel testing (mock MCP vs real FastAPI)
3. **Day 2**: Switch 100% traffic with instant fallback to MCP
4. **Week 1**: Monitor for regressions, optimize

**Advantages**: Faster, decisive
**Disadvantages**: Higher risk, requires robust testing

### Strategy C: Feature-Based (When MCP bottleneck is specific operation)
1. **Phase 1**: Move only high-volume operations to FastAPI (e.g., sandbox creation)
2. **Phase 2**: Move support operations as they hit thresholds
3. **Full migration**: Timeline extends but risk per phase is isolated

**Advantages**: Minimal blast radius, easy to manage
**Disadvantages**: Operational complexity (dual systems longer)

---

## 5. Validation Period Data Collection (Weeks 1-4)

### Daily Metrics Review Checklist

**Week 1 (Baseline Stability)**
- [ ] Consistent cost per operation ±10%
- [ ] P50/P95/P99 latencies stable
- [ ] Error rate <2% (exclude known transient issues)
- [ ] No resource exhaustion events

**Week 2 (Load Pattern Analysis)**
- [ ] Peak concurrency identified
- [ ] Operation distribution mapped (% create vs read vs delete)
- [ ] E2b API rate limit headroom confirmed (>50% capacity available)
- [ ] Cache hit ratio established (baseline)

**Week 3 (Failure Mode Assessment)**
- [ ] All failures categorized and documented
- [ ] Transient failures recovery time measured
- [ ] Cascade failures identified (if any)
- [ ] Timeout thresholds validated against e2b latency

**Week 4 (Migration Readiness)**
- [ ] Trend analysis: cost trajectory, concurrency growth rate
- [ ] Decision: meet any trigger threshold?
- [ ] Resource requirement forecast for 3 months ahead
- [ ] Architectural gaps identified (caching, retry logic, rate limiting)

### Key Success Metrics (Must be Stable)
```
Cost per operation:     < ±10% variance
P95 latency:           < ±20% variance
Error rate:            < ±2% absolute change
Concurrent peak:       Identified and consistent
```

---

## 6. Architecture Decision Framework

### Decide STAY with MCP If:
- Cost per operation < $0.01 (already efficient)
- Peak concurrency < 3 simultaneous operations
- P95 latency < 500ms consistently
- Error rate < 1%
- Monthly cost < $100

→ **Recommendation**: Optimize current MCP (caching, connection pooling), revisit quarterly

### Decide MIGRATE If:
- Any trigger threshold exceeded + stable for 2 weeks
- Cost trajectory shows >2x growth in 3 months
- Error rate trending upward
- Single MCP process causing visible request queuing

→ **Recommendation**: Execute canary migration to FastAPI + Postgres

### Decide HYBRID If:
- Some operations meet migration criteria, others don't
- Cost per operation varies wildly by operation type (e.g., create=expensive, read=cheap)
- Specific concurrency bottleneck identified

→ **Recommendation**: Migrate high-cost/high-volume operations; keep MCP for others

---

## 7. Prometheus Setup Quick Reference

**Installation**:
```bash
pip install prometheus-fastapi-instrumentator prometheus-client
```

**Minimal handler decorator**:
```python
@app.post("/create-sandbox")
async def create_sandbox():
    with sandbox_creation.labels(region="us").time():
        # Your code here
        pass
```

**Quick dashboard**: Use Grafana ID `16110` (FastAPI Observability) as template

---

## Unresolved Questions

1. What's your current e2b API cost per operation? (Affects cost threshold)
2. Peak concurrent users in production currently? (Calibrates threshold)
3. Acceptable error rate for production? (SLA target)
4. Timeline flexibility: can you wait 4 weeks for full validation, or urgent?

---

**Next Step**: Instrument MCP server with these metrics this week, establish baseline by 2025-11-27.
