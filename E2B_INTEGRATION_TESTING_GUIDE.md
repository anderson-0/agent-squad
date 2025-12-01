# E2B Integration - End-to-End Testing Guide

Complete guide for testing the E2B Sandbox + GitHub Webhooks integration.

## Overview

This guide covers testing the complete integration:
- **Phase 1:** Frontend E2B Visualization
- **Phase 2:** Backend SSE Integration
- **Phase 3:** GitHub Webhooks for PR Status
- **Phase 4:** Sandbox Model Enhancement

---

## Prerequisites

### 1. Environment Variables

**Backend** (`backend/.env`):
```bash
# E2B Configuration
E2B_API_KEY=your_e2b_api_key_here
E2B_TEMPLATE_ID=your_template_id  # Optional

# GitHub Configuration
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agentsquad

# SSE Configuration (optional)
SSE_HEARTBEAT_INTERVAL=15  # seconds
```

**Frontend** (`frontend/.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Database Setup

```bash
# Run migrations
cd backend
alembic upgrade head

# Verify pr_number column exists
psql -d agentsquad -c "\d sandboxes"
# Should show: pr_number | integer | | nullable
```

### 3. Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
bun install
```

---

## Test Plan

### Level 1: Unit Tests (5 minutes)

Test individual components without external dependencies.

```bash
cd backend

# Test webhook signature validation
pytest tests/test_e2b_integration_e2e.py::test_webhook_signature_validation -v

# Test webhook sandbox lookup
pytest tests/test_e2b_integration_e2e.py::test_webhook_sandbox_lookup -v

# Test sandbox model
python3 -m pytest tests/test_models/ -k sandbox -v
```

**Expected:** All tests pass ✅

---

### Level 2: Backend API Tests (10 minutes)

Test API endpoints without E2B/GitHub integration.

#### Start Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

#### Test Webhook Endpoint

```bash
# Test webhook endpoint is accessible
curl http://localhost:8000/api/v1/webhooks/github/test

# Expected response:
# {
#   "status": "ok",
#   "endpoint": "/api/v1/webhooks/github",
#   "webhook_secret_configured": true,
#   "supported_events": [...]
# }
```

#### Test Invalid Webhook (Should Reject)

```bash
# Missing signature header
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{"action": "opened"}'

# Expected: 400 Bad Request - "Missing X-Hub-Signature-256 header"
```

**Expected:** Endpoint accessible, signature validation works ✅

---

### Level 3: E2B Integration Tests (20 minutes)

Test with real E2B API (requires E2B_API_KEY).

```bash
cd backend

# Run full E2E test
pytest tests/test_e2b_integration_e2e.py::test_complete_sandbox_workflow -v -s

# What this tests:
# 1. Create E2B sandbox
# 2. Clone repository
# 3. Create branch
# 4. Commit changes
# 5. Push to remote
# 6. Create PR on GitHub
# 7. Store PR number in database
# 8. Simulate webhook event
# 9. Terminate sandbox
```

**Expected Output:**
```
[1/8] Creating E2B sandbox...
✓ Sandbox created: e2b-abc123

[2/8] Cloning repository...
✓ Repository cloned to: /code/test-repo

[3/8] Creating branch: test-feature-xyz
✓ Branch created: test-feature-xyz

[4/8] Making test changes...
✓ Test file created

[5/8] Committing changes...
✓ Changes committed: test: add test file for E2E test

[6/8] Pushing to remote: test-feature-xyz
✓ Changes pushed to remote

[7/8] Creating Pull Request...
✓ PR created: #123 - https://github.com/test-org/test-repo/pull/123
✓ PR number stored in sandbox: #123

[8/8] Simulating GitHub webhook (PR approved)...
✓ Webhook processed: pr_approved event
  Reviewer: test-reviewer

[9/9] Terminating sandbox...
✓ Sandbox terminated: True
✓ Runtime: 45.3s

============================================================
✅ E2E TEST PASSED - All steps completed successfully!
============================================================
```

**If test fails:**
- Check E2B_API_KEY is valid
- Check GITHUB_TOKEN has repo access
- Check network connectivity
- Check test repository exists and is accessible

---

### Level 4: Frontend Integration (15 minutes)

Test real-time UI updates with SSE.

#### Start Services

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bun run dev
```

#### Test UI Flow

1. **Open Browser:**
   ```
   http://localhost:3000/agent-work
   ```

2. **Open Browser DevTools:**
   - Network tab → Filter by "EventStream"
   - Should see SSE connection to `/squads/{id}/stream`

3. **Trigger Sandbox Workflow:**
   ```bash
   # In Terminal 3
   curl -X POST http://localhost:8000/api/v1/sandboxes \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "task_id": "test-task-id",
       "agent_id": "test-agent-id",
       "repo_url": "https://github.com/owner/repo"
     }'
   ```

4. **Verify UI Updates:**
   - ✅ "Sandboxes" tab badge shows count
   - ✅ SandboxProgressCard appears
   - ✅ Status badge shows "Created" → "Running"
   - ✅ Git workflow stepper appears
   - ✅ Steps animate as they progress

5. **Trigger PR Creation:**
   ```bash
   # Create PR (replace sandbox_id with actual ID)
   curl -X POST http://localhost:8000/api/v1/sandboxes/{sandbox_id}/pr \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test PR",
       "body": "Test",
       "head": "feature-branch",
       "base": "main"
     }'
   ```

6. **Verify PR Badge:**
   - ✅ PR link badge appears
   - ✅ Shows "Open" status
   - ✅ Confetti animation plays
   - ✅ Clickable link to GitHub

**Expected:** UI updates in real-time without refresh ✅

---

### Level 5: GitHub Webhook Integration (30 minutes)

Test real GitHub webhooks with ngrok/tunnel.

#### Setup Tunnel

**Option A: ngrok**
```bash
ngrok http 8000
# Note the HTTPS URL: https://abc123.ngrok.io
```

**Option B: Cloudflare Tunnel**
```bash
cloudflared tunnel --url http://localhost:8000
```

#### Configure GitHub Webhook

1. **Go to Repository Settings:**
   ```
   https://github.com/your-org/your-repo/settings/hooks
   ```

2. **Add Webhook:**
   - **Payload URL:** `https://abc123.ngrok.io/api/v1/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** Your `GITHUB_WEBHOOK_SECRET` value
   - **Events:**
     - ✅ Pull requests
     - ✅ Pull request reviews
   - **Active:** ✅

3. **Save Webhook**

#### Test Webhook Flow

1. **Create PR via Backend API** (from Level 4)

2. **On GitHub, Review the PR:**
   - Click "Add review"
   - Select "Approve"
   - Submit review

3. **Check Backend Logs:**
   ```
   [INFO] Received GitHub webhook: pull_request_review - submitted
   [INFO] Found sandbox abc-123 by exact PR match #42
   [INFO] Broadcasted pr_approved to execution xyz-789
   [INFO] Broadcasted pr_approved to squad def-456
   ```

4. **Check Frontend UI:**
   - PR badge should update from "Open" → "Approved"
   - Reviewer name should appear
   - No page refresh needed

5. **Merge the PR on GitHub:**
   - Click "Merge pull request"
   - Confirm merge

6. **Check Frontend UI:**
   - PR badge should update to "Merged"
   - Confetti animation plays
   - Badge shows purple color

**Expected:** Webhook received → SSE broadcast → UI updates ✅

---

## Troubleshooting

### Issue: SSE Connection Fails

**Symptoms:**
- Network tab shows SSE connection failed
- No real-time updates in UI

**Solutions:**
1. Check backend is running on port 8000
2. Check CORS configuration allows frontend origin
3. Check SSE endpoint exists: `GET /squads/{id}/stream`
4. Open browser console for error messages

---

### Issue: Webhook Signature Validation Fails

**Symptoms:**
- Backend logs: "Invalid webhook signature"
- GitHub shows webhook delivery as failed

**Solutions:**
1. Verify `GITHUB_WEBHOOK_SECRET` matches GitHub settings
2. Check webhook secret in GitHub is exactly the same
3. Restart backend after changing secret
4. Test with: `curl -X POST ... -H "X-Hub-Signature-256: sha256=..."`

---

### Issue: Sandbox Not Found for Webhook

**Symptoms:**
- Backend logs: "No sandbox found for PR #123"
- Webhook processed but no UI update

**Solutions:**
1. Check PR number is stored: `SELECT pr_number FROM sandboxes WHERE pr_number = 123;`
2. Verify sandbox was created via API (not manually)
3. Check `create_pr()` method is saving PR number
4. Run migration: `alembic upgrade head`

---

### Issue: E2B Sandbox Creation Fails

**Symptoms:**
- Error: "E2B_API_KEY not configured"
- Error: "Failed to create sandbox"

**Solutions:**
1. Verify E2B_API_KEY is valid: https://e2b.dev/docs
2. Check E2B quota/limits haven't been exceeded
3. Test E2B API directly:
   ```python
   from e2b import Sandbox
   sb = Sandbox()  # Should not throw error
   ```

---

## Monitoring & Metrics

### SSE Connection Statistics

```bash
# Get SSE stats
curl http://localhost:8000/api/v1/sse/stats

# Expected:
# {
#   "total_connections": 5,
#   "execution_streams": 3,
#   "squad_streams": 2
# }
```

### Webhook Delivery Status

Check GitHub webhook delivery logs:
```
https://github.com/your-org/your-repo/settings/hooks/{hook_id}
```

Look for:
- ✅ Green checkmark = Successful delivery
- ❌ Red X = Failed delivery
- Click on delivery to see request/response details

### Database Verification

```sql
-- Check sandboxes with PR numbers
SELECT id, e2b_id, pr_number, status, created_at
FROM sandboxes
WHERE pr_number IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;

-- Check sandbox lifecycle
SELECT
  status,
  COUNT(*) as count,
  AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_runtime_seconds
FROM sandboxes
GROUP BY status;
```

---

## Performance Benchmarks

Expected performance metrics:

| Operation | Time | Notes |
|-----------|------|-------|
| Create Sandbox | 3-5s | E2B API call |
| Clone Repo | 2-10s | Depends on repo size |
| Create Branch | <1s | Git operation |
| Commit Changes | <1s | Git operation |
| Push Changes | 2-5s | Network upload |
| Create PR | 1-2s | GitHub API call |
| SSE Broadcast | <100ms | Non-blocking |
| Webhook Processing | <500ms | Database lookup + broadcast |
| UI Update (SSE) | <100ms | Real-time |

**Total Workflow:** 10-30 seconds (depending on repository size)

---

## Success Criteria

### ✅ All Tests Pass

- [ ] Unit tests pass (webhook validation, sandbox lookup)
- [ ] Backend API accessible (webhook endpoint responds)
- [ ] E2E test completes successfully (9/9 steps)
- [ ] Frontend displays real-time updates
- [ ] GitHub webhooks deliver successfully
- [ ] PR status updates in UI without refresh

### ✅ No Errors in Logs

- [ ] No SSE connection errors
- [ ] No webhook signature validation failures
- [ ] No "sandbox not found" errors
- [ ] No database errors

### ✅ Performance Acceptable

- [ ] Sandbox creation < 5s
- [ ] SSE broadcast < 100ms
- [ ] Webhook processing < 500ms
- [ ] UI updates < 100ms after event

---

## Next Steps After Testing

Once all tests pass:

1. **Documentation:**
   - Update deployment guide
   - Document webhook setup for production
   - Create user guide for monitoring

2. **Production Deployment:**
   - Set production webhook URL
   - Configure production secrets
   - Set up monitoring/alerting

3. **Phase 4: Cost Tracking** (Optional)
   - Implement sandbox cost calculation
   - Add cost analytics dashboard
   - Set up budget alerts

---

## Support

If you encounter issues not covered in this guide:

1. Check backend logs: `tail -f logs/app.log`
2. Check frontend console: Browser DevTools → Console
3. Check GitHub webhook deliveries
4. Review SSE connection in Network tab
5. Verify database state with SQL queries

For E2B-specific issues:
- E2B Documentation: https://e2b.dev/docs
- E2B Discord: https://discord.gg/U7KEcGErtQ

For GitHub webhook issues:
- GitHub Webhooks Guide: https://docs.github.com/webhooks
