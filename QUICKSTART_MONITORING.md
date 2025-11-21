# Quick Start: Git Operations Monitoring

Complete setup for E2B-based git operations with Prometheus and Grafana monitoring.

---

## 🚀 Quick Start (5 Minutes)

### 1. Set Environment Variables

```bash
# Required for E2B sandbox execution
export E2B_API_KEY=your-e2b-api-key

# Required for GitHub operations
export GITHUB_TOKEN=your-github-token

# Optional: Add to your ~/.bashrc or ~/.zshrc
echo 'export E2B_API_KEY=your-e2b-api-key' >> ~/.bashrc
echo 'export GITHUB_TOKEN=your-github-token' >> ~/.bashrc
```

**Get API Keys:**
- E2B API Key: https://e2b.dev (sign up, free tier available)
- GitHub Token: https://github.com/settings/tokens (create with `repo` scope)

### 2. Start All Services

```bash
# Start backend, database, Redis, NATS, Prometheus, and Grafana
docker-compose up -d

# Check service health
docker-compose ps

# Watch logs (optional)
docker-compose logs -f backend prometheus grafana
```

### 3. Access Dashboards

Open in your browser:

- **Grafana Dashboard**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`
  - Navigate to: Dashboards → "Git Operations - E2B Sandbox Monitoring"

- **Prometheus**: http://localhost:9090
  - Query metrics directly
  - View targets: http://localhost:9090/targets

- **Backend API**: http://localhost:8000
  - API docs: http://localhost:8000/docs
  - Metrics endpoint: http://localhost:8000/metrics

### 4. Verify Setup

```bash
# Check metrics endpoint is working
curl http://localhost:8000/metrics | grep git_operation

# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="backend-api")'

# Check Grafana health
curl http://localhost:3001/api/health
```

---

## 📊 What You Get

### Grafana Dashboard (12 Panels)

1. **Operation Success Rate** - Current success rate (green > 95%)
2. **P95 Latency by Operation** - 95th percentile latency per git operation
3. **Active Sandboxes** - Number of cached sandboxes
4. **Cache Hit Ratio** - Efficiency of sandbox reuse (green > 70%)
5. **Operations per Minute** - Throughput by operation type
6. **Error Rate by Type** - Errors categorized (timeout, auth, conflict, etc.)
7. **Sandbox Creation Time** - Heatmap of creation times
8. **Estimated Monthly Cost** - Current spending (alert at $75)
9. **Daily Cost Trend** - Cost over time
10. **Operations Distribution** - Pie chart of operation types
11. **Push Retry Attempts** - Retry patterns
12. **Conflicts Detected** - Git conflicts over time

### Metrics Collected

- `sandbox_creation_seconds` - Sandbox creation time
- `active_sandboxes_total` - Active sandbox count
- `sandbox_cache_hits_total` / `sandbox_cache_misses_total` - Cache performance
- `git_operation_total{operation, status}` - Operation counts
- `git_operation_duration_seconds{operation}` - Operation latency
- `git_errors_total{operation, error_type}` - Error tracking
- `git_push_retry_count_total{attempt}` - Retry attempts
- `git_conflicts_detected_total{operation}` - Conflict detection
- `estimated_cost_dollars{period}` - Cost tracking

---

## 🧪 Test the System

### Execute a Test Git Operation

```python
# backend/scripts/test_git_operations.py
import asyncio
from backend.integrations.mcp.client import MCPClientManager

async def test_git_clone():
    mcp = MCPClientManager()

    # Clone a test repository
    result = await mcp.call_tool(
        server="git_operations",
        tool="git_clone",
        arguments={
            "repo_url": "https://github.com/octocat/Hello-World.git",
            "branch": "master",
            "agent_id": "test-agent-001",
            "task_id": "test-task-001"
        }
    )

    print("Clone result:", result)

    # Get sandbox ID from result
    sandbox_id = result.get("sandbox_id")

    # Test git status
    status = await mcp.call_tool(
        server="git_operations",
        tool="git_status",
        arguments={"sandbox_id": sandbox_id}
    )

    print("Status result:", status)

# Run test
asyncio.run(test_git_clone())
```

### Watch Metrics Update

1. Open Grafana: http://localhost:3001
2. Go to "Git Operations" dashboard
3. Execute test git operations (above script)
4. Watch panels update in real-time (15s refresh)

---

## 🎯 What to Monitor

### During Validation Period (2-4 weeks)

**Week 1-2: Establish Baseline**
- Average latency per operation
- Peak concurrent sandboxes
- Error rate by type
- Cache hit ratio
- Daily cost

**Week 2-4: Identify Patterns**
- Latency trends (improving/degrading?)
- Error spikes (what causes them?)
- Cost trajectory (staying under budget?)
- Cache effectiveness (hit ratio stable?)

### Decision Criteria for Approach 2 Migration

Migrate if ANY threshold exceeded:
- ✗ P95 latency > 5 seconds (consistently)
- ✗ Error rate > 10%
- ✗ Monthly cost > $75 (75% of $100 budget)
- ✗ Cache miss ratio > 50%
- ✗ Active sandboxes > 10 simultaneously

**Current Expected Performance:**
- ✅ P95 latency: ~2-8 seconds (E2B sandbox creation)
- ✅ Error rate: < 5%
- ✅ Monthly cost: ~$1.50 (10 agents, 20 ops/day)
- ✅ Cache hit ratio: > 70% (1-hour TTL effective)
- ✅ Peak sandboxes: 3-5 concurrent

---

## 🔧 Troubleshooting

### No Metrics in Grafana

**Check Prometheus targets:**
```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

**Expected output:**
```json
{"job": "backend-api", "health": "up"}
{"job": "prometheus", "health": "up"}
{"job": "nats", "health": "up"}
```

### Backend Not Exposing Metrics

**Check metrics endpoint:**
```bash
curl http://localhost:8000/metrics
```

**Should return:**
```
# HELP git_operation_total Total git operations executed
# TYPE git_operation_total counter
git_operation_total{operation="clone",status="success"} 10.0
...
```

### Grafana Dashboard Empty

**Verify datasource:**
1. Grafana → Configuration → Data Sources → Prometheus
2. Click "Test"
3. Should show: "Data source is working"

**Reimport dashboard:**
```bash
# Copy dashboard JSON
cat monitoring/grafana/dashboards/git_operations.json

# Grafana → Dashboards → Import → Paste JSON
```

### Services Not Starting

**Check logs:**
```bash
docker-compose logs prometheus
docker-compose logs grafana
docker-compose logs backend
```

**Common issues:**
- Port conflicts (9090, 3001, 8000 already in use)
- Missing environment variables (E2B_API_KEY, GITHUB_TOKEN)
- Volume permission issues

---

## 📚 Documentation

- **Comprehensive Guide**: [monitoring/README.md](monitoring/README.md)
- **Implementation Summary**: [plans/251120-2018-hybrid-e2b-git-implementation/IMPLEMENTATION_SUMMARY.md](plans/251120-2018-hybrid-e2b-git-implementation/IMPLEMENTATION_SUMMARY.md)
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **E2B Docs**: https://e2b.dev/docs

---

## 🎉 Success Checklist

- [ ] E2B_API_KEY and GITHUB_TOKEN set
- [ ] `docker-compose up -d` successful
- [ ] All services healthy (`docker-compose ps`)
- [ ] Grafana dashboard accessible at http://localhost:3001
- [ ] Prometheus showing backend target as "UP"
- [ ] Backend metrics endpoint returning data
- [ ] Test git operation executed successfully
- [ ] Metrics visible in Grafana dashboard

**You're ready!** Start using the system and monitor performance over the next 2-4 weeks.

---

**Questions?** Check the comprehensive guide at `monitoring/README.md`
