# E2B Integration - Quick Test Checklist

Fast reference for testing E2B + GitHub Webhooks integration.

## Pre-Flight Check ✈️

```bash
# 1. Environment variables set?
grep -E "(E2B_API_KEY|GITHUB_TOKEN|GITHUB_WEBHOOK_SECRET)" backend/.env

# 2. Database migrated?
cd backend && alembic current

# 3. Dependencies installed?
cd backend && pip list | grep -E "(e2b|fastapi|sqlalchemy)"
cd frontend && bun list | grep -E "(framer-motion|react-confetti-boom)"
```

---

## Level 1: Smoke Tests (2 min) 🔥

**Backend Compilation:**
```bash
cd backend
python3 -m py_compile models/sandbox.py services/sandbox_service.py services/webhook_service.py
# No errors = ✅
```

**Webhook Endpoint:**
```bash
# Start backend first: uvicorn main:app --reload
curl http://localhost:8000/api/v1/webhooks/github/test
# {"status": "ok"} = ✅
```

---

## Level 2: Unit Tests (5 min) 🧪

```bash
cd backend

# Webhook signature validation
pytest tests/test_e2b_integration_e2e.py::test_webhook_signature_validation -v
# PASSED = ✅

# Sandbox lookup by PR number
pytest tests/test_e2b_integration_e2e.py::test_webhook_sandbox_lookup -v
# PASSED = ✅
```

---

## Level 3: E2E Flow (15 min) 🚀

**Requires: E2B_API_KEY, GITHUB_TOKEN**

```bash
cd backend
pytest tests/test_e2b_integration_e2e.py::test_complete_sandbox_workflow -v -s

# Watch for:
# [1/8] Creating E2B sandbox... ✓
# [2/8] Cloning repository... ✓
# [3/8] Creating branch... ✓
# [4/8] Making test changes... ✓
# [5/8] Committing changes... ✓
# [6/8] Pushing to remote... ✓
# [7/8] Creating Pull Request... ✓
# [8/8] Simulating GitHub webhook... ✓
# [9/9] Terminating sandbox... ✓
# ✅ E2E TEST PASSED
```

---

## Level 4: Frontend UI (10 min) 🎨

**Terminal 1 - Backend:**
```bash
cd backend && uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend && bun run dev
```

**Browser:**
1. Open http://localhost:3000/agent-work
2. Click "Sandboxes" tab
3. Trigger workflow via API or Inngest
4. Watch for:
   - ✅ Sandbox card appears
   - ✅ Status updates in real-time
   - ✅ Git workflow stepper animates
   - ✅ PR badge appears with confetti
   - ✅ No page refresh needed

---

## Level 5: GitHub Webhooks (15 min) 🪝

**Setup Tunnel:**
```bash
ngrok http 8000
# Copy HTTPS URL: https://abc123.ngrok.io
```

**GitHub Webhook:**
1. Repo → Settings → Webhooks → Add webhook
2. URL: `https://abc123.ngrok.io/api/v1/webhooks/github`
3. Secret: Your GITHUB_WEBHOOK_SECRET
4. Events: Pull requests, Pull request reviews

**Test:**
1. Create PR via backend API
2. Approve PR on GitHub
3. Check UI updates to "Approved" (no refresh!)
4. Merge PR on GitHub
5. Check UI updates to "Merged" + confetti

---

## Quick Troubleshooting 🔧

**SSE not working?**
```bash
# Check connection
curl http://localhost:8000/api/v1/squads/{squad_id}/stream

# Check stats
curl http://localhost:8000/api/v1/sse/stats
```

**Webhook failing?**
```bash
# Check signature
echo $GITHUB_WEBHOOK_SECRET

# Test invalid request (should reject)
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
# Expected: 400 Bad Request
```

**Sandbox not found?**
```sql
-- Check PR numbers stored
SELECT id, e2b_id, pr_number FROM sandboxes WHERE pr_number IS NOT NULL;
```

---

## Success Criteria ✅

- [ ] Smoke tests pass (compilation + webhook endpoint)
- [ ] Unit tests pass (2/2)
- [ ] E2E test passes (9/9 steps)
- [ ] Frontend updates in real-time
- [ ] GitHub webhooks deliver successfully
- [ ] PR status updates without refresh
- [ ] No errors in backend/frontend logs

---

## Performance Check ⏱️

Expected timings:
- Create sandbox: < 5s
- Clone repo: < 10s
- Git operations: < 1s each
- Create PR: < 2s
- SSE broadcast: < 100ms
- Webhook processing: < 500ms
- UI update: < 100ms

**Total workflow:** 10-30 seconds

---

## Done! 🎉

If all checks pass, you have a fully functional E2B + GitHub Webhooks integration with real-time UI updates!

**Next:** See `E2B_INTEGRATION_TESTING_GUIDE.md` for detailed troubleshooting and advanced testing scenarios.
