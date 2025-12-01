# Git Operations Monitoring Guide

Comprehensive monitoring setup for E2B-based git operations using Prometheus and Grafana.

---

## Quick Start

### 1. Start All Services

```bash
# Start all services including Prometheus and Grafana
docker-compose up -d

# Check service health
docker-compose ps
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`
  - Dashboard: "Git Operations - E2B Sandbox Monitoring"

- **Prometheus**: http://localhost:9090
  - Query metrics directly
  - View targets: http://localhost:9090/targets

- **Backend API**: http://localhost:8000
  - Metrics endpoint: http://localhost:8000/metrics
  - API docs: http://localhost:8000/docs

---

## Architecture

```
┌─────────────────┐
│  Backend API    │
│  (port 8000)    │
│  /metrics       │
└────────┬────────┘
         │ scrapes every 15s
         ▼
┌─────────────────┐      ┌─────────────────┐
│   Prometheus    │─────▶│    Grafana      │
│   (port 9090)   │      │   (port 3001)   │
│  - Stores 30d   │      │  - Visualizes   │
│  - Alerts       │      │  - Dashboards   │
└─────────────────┘      └─────────────────┘
```

---

## Metrics Collected

### Sandbox Metrics
- `sandbox_creation_seconds` - Time to create E2B sandbox (histogram)
- `active_sandboxes_total` - Currently active sandboxes (gauge)
- `sandbox_cache_hits_total` - Cache hit count (counter)
- `sandbox_cache_misses_total` - Cache miss count (counter)

### Git Operation Metrics
- `git_operation_total{operation, status}` - Total operations (counter)
  - Operations: `clone`, `status`, `diff`, `pull`, `push`
  - Status: `started`, `success`, `failure`, `retry`

- `git_operation_duration_seconds{operation}` - Operation latency (histogram)
  - Buckets: 0.1s, 0.5s, 1s, 2s, 5s, 10s, 30s, 60s, 120s, 300s

- `git_errors_total{operation, error_type}` - Error counts (counter)
  - Error types: `timeout`, `auth`, `conflict`, `network`, `sandbox_not_found`, `other`

- `git_push_retry_count_total{attempt}` - Push retry attempts (counter)
- `git_conflicts_detected_total{operation}` - Conflicts detected (counter)

### Cost Tracking
- `sandbox_hours_total{project}` - Total sandbox hours consumed (counter)
- `estimated_cost_dollars{period}` - Estimated cost (gauge)
  - Periods: `hourly`, `daily`, `monthly`

---

## Dashboard Panels

The Grafana dashboard includes 12 panels:

1. **Operation Success Rate** (Gauge)
   - Shows success rate over last 5 minutes
   - Red < 90%, Yellow 90-95%, Green > 95%

2. **P95 Latency by Operation** (Line Graph)
   - 95th percentile latency per operation
   - Alert threshold: 5 seconds

3. **Active Sandboxes** (Gauge)
   - Current number of active sandboxes
   - Alert threshold: 10 sandboxes

4. **Cache Hit Ratio** (Gauge)
   - Percentage of cache hits
   - Red < 50%, Yellow 50-70%, Green > 70%

5. **Operations per Minute** (Line Graph)
   - Operations rate by type
   - Alert threshold: 100 ops/minute

6. **Error Rate by Type** (Stacked Area)
   - Errors per minute by error type
   - Helps identify common failure patterns

7. **Sandbox Creation Time Heatmap** (Heatmap)
   - Distribution of sandbox creation times
   - Identifies performance patterns

8. **Estimated Monthly Cost** (Gauge)
   - Current monthly cost estimate
   - Alert threshold: $75 (75% of budget)

9. **Daily Cost Trend** (Line Graph)
   - Daily spending over time
   - Helps track cost trends

10. **Operations Distribution** (Pie Chart)
    - Breakdown of operations by type
    - Shows usage patterns

11. **Push Retry Attempts** (Bar Chart)
    - Number of retries per push operation
    - Indicates conflict frequency

12. **Conflicts Detected** (Line Graph)
    - Git conflicts over time
    - Helps identify problematic repos

---

## PromQL Query Examples

### Success Rate
```promql
# Overall success rate (last 5 minutes)
100 * (
  rate(git_operation_total{status="success"}[5m])
  /
  rate(git_operation_total[5m])
)
```

### P95 Latency
```promql
# 95th percentile latency by operation
histogram_quantile(0.95,
  rate(git_operation_duration_seconds_bucket[5m])
)
```

### Cache Hit Ratio
```promql
# Cache hit percentage
100 * (
  sandbox_cache_hits_total
  /
  (sandbox_cache_hits_total + sandbox_cache_misses_total)
)
```

### Operations per Minute
```promql
# Operations rate (per minute)
rate(git_operation_total[1m]) * 60
```

### Error Rate
```promql
# Errors per minute by type
rate(git_errors_total[5m]) * 60
```

### Monthly Cost Estimate
```promql
# Current monthly cost estimate
estimated_cost_dollars{period="monthly"}
```

---

## Alert Configuration

### Recommended Alerts

Create alert rules in `monitoring/prometheus/alert_rules.yml`:

```yaml
groups:
  - name: git_operations
    interval: 30s
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(git_operation_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency detected"
          description: "P95 latency is {{ $value }}s (threshold: 5s)"

      - alert: HighErrorRate
        expr: 100 * (rate(git_operation_total{status="failure"}[5m]) / rate(git_operation_total[5m])) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% (threshold: 10%)"

      - alert: TooManySandboxes
        expr: active_sandboxes_total > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Too many active sandboxes"
          description: "{{ $value }} active sandboxes (threshold: 10)"

      - alert: HighMonthlyCost
        expr: estimated_cost_dollars{period="monthly"} > 75
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Monthly cost exceeds 75% of budget"
          description: "Estimated cost: ${{ $value }} (budget: $100)"

      - alert: LowCacheHitRatio
        expr: 100 * (sandbox_cache_hits_total / (sandbox_cache_hits_total + sandbox_cache_misses_total)) < 50
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Low cache hit ratio"
          description: "Cache hit ratio: {{ $value }}% (threshold: 50%)"
```

---

## Troubleshooting

### Metrics Not Showing Up

**Problem**: Grafana shows "No data"

**Solutions**:
1. Check Prometheus is scraping the backend:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```
   - Look for `backend-api` target
   - Status should be "UP"

2. Check backend metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```
   - Should return Prometheus format metrics
   - Look for `git_operation_total` metrics

3. Verify Prometheus configuration:
   ```bash
   docker-compose logs prometheus | grep error
   ```

4. Check Grafana datasource:
   - Grafana → Configuration → Data Sources → Prometheus
   - Click "Test" button
   - Should show "Data source is working"

### No Git Operations Metrics

**Problem**: Backend metrics work but no git operations metrics

**Cause**: No git operations have been executed yet

**Solution**: Execute a test git operation:
```python
# Use MCP client to call git_clone
from backend.integrations.mcp.client import MCPClientManager

mcp = MCPClientManager()
result = await mcp.call_tool(
    server="git_operations",
    tool="git_clone",
    arguments={
        "repo_url": "https://github.com/user/test-repo.git",
        "branch": "main",
        "agent_id": "test-agent",
        "task_id": "test-task"
    }
)
```

### High Memory Usage

**Problem**: Prometheus consuming too much memory

**Cause**: Long retention period or high cardinality

**Solutions**:
1. Reduce retention period:
   ```yaml
   # docker-compose.yml
   command:
     - '--storage.tsdb.retention.time=7d'  # Reduce from 30d
   ```

2. Check metric cardinality:
   ```bash
   curl http://localhost:9090/api/v1/status/tsdb | jq '.data.seriesCountByMetricName'
   ```

### Dashboard Not Loading

**Problem**: Grafana dashboard shows errors

**Solutions**:
1. Verify dashboard JSON is valid:
   ```bash
   cat monitoring/grafana/dashboards/git_operations.json | jq .
   ```

2. Reimport dashboard:
   - Grafana → Dashboards → Import
   - Upload `git_operations.json`

3. Check Grafana logs:
   ```bash
   docker-compose logs grafana | grep error
   ```

---

## Maintenance

### Backup Prometheus Data

```bash
# Stop Prometheus
docker-compose stop prometheus

# Backup data
docker run --rm -v agent-squad_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Restart Prometheus
docker-compose start prometheus
```

### Reset Prometheus Data

```bash
# Stop and remove Prometheus
docker-compose stop prometheus
docker-compose rm prometheus

# Delete volume
docker volume rm agent-squad_prometheus_data

# Restart
docker-compose up -d prometheus
```

### Grafana Password Reset

```bash
# Reset to default (admin/admin)
docker-compose exec grafana grafana-cli admin reset-admin-password admin
```

---

## Performance Tuning

### Optimize Scrape Interval

Edit `prometheus.yml`:
```yaml
global:
  scrape_interval: 30s  # Increase from 15s to reduce load
```

### Reduce Metric Cardinality

Limit labels in metrics code:
```python
# Avoid high cardinality labels
git_operation_total.labels(
    operation='clone',
    status='success'
    # Don't add: repo_url, user_id, task_id
)
```

### Dashboard Auto-Refresh

Edit dashboard settings:
```json
{
  "refresh": "30s"  # Increase from 15s to reduce load
}
```

---

## Cost Analysis

### E2B Sandbox Costs

**Rate**: $0.015/sandbox-hour
**Budget**: $100/month
**Threshold**: 6,666 sandbox-hours/month

### Query Cost Metrics

```promql
# Total sandbox hours consumed
sum(sandbox_hours_total)

# Cost per operation
estimated_cost_dollars{period="monthly"} / sum(git_operation_total)

# Average sandbox duration
rate(sandbox_creation_seconds_sum[5m]) / rate(sandbox_creation_seconds_count[5m])
```

---

## Production Checklist

Before deploying to production:

- [ ] Change Grafana admin password
- [ ] Set up Alertmanager for notifications
- [ ] Configure Prometheus remote write (optional)
- [ ] Enable HTTPS for Grafana
- [ ] Restrict Prometheus/Grafana to internal network
- [ ] Set up log aggregation (optional)
- [ ] Configure automated backups
- [ ] Test alert rules
- [ ] Document on-call procedures
- [ ] Set up status page (optional)

---

## Resources

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **E2B Docs**: https://e2b.dev/docs
- **Dashboard JSON**: `monitoring/grafana/dashboards/git_operations.json`

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs <service>`
2. Review metrics endpoint: http://localhost:8000/metrics
3. Test Prometheus targets: http://localhost:9090/targets
4. Verify Grafana datasource connectivity

---

**Last Updated**: 2025-11-21
**Version**: 1.0.0
