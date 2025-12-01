# Phase 08 - Testing & Deployment

**Date:** 2025-11-21
**Priority:** P0 (Critical)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** All previous phases (01-07)
- **Related Docs:** [System Architecture](../../docs/system-architecture.md)

## Overview

Comprehensive testing strategy covering unit tests, integration tests, E2E tests. Error scenario validation (sandbox crashes, git failures, network issues). Deployment guide for production (Docker, env vars, monitoring).

**Testing Levels:**
- **Unit Tests:** Services, utilities (backend)
- **Integration Tests:** API endpoints, database operations
- **E2E Tests:** Full workflow (task assignment → PR creation)
- **Error Tests:** Failure scenarios, recovery logic

## Key Insights

Critical paths to test:
1. Task assignment → Sandbox creation → Clone repo → Create branch
2. Code commit → Push → PR creation
3. Sandbox crash → Cleanup → Error notification
4. Network failure → Retry → Success/Failure handling
5. Multiple agents working simultaneously (concurrency)

## Requirements

### Functional
- Unit tests for all services (>80% coverage)
- Integration tests for API endpoints
- E2E tests for critical workflows
- Error scenario tests (crashes, timeouts, auth failures)
- Load tests for concurrent operations
- SSE connection stability tests
- Database migration tests

### Non-Functional
- Test execution <5 minutes (CI pipeline)
- Coverage reports generated automatically
- Tests run in isolated environments
- Reproducible test failures
- Clear error messages for failures
- Performance benchmarks tracked

## Architecture

### Testing Pyramid

```
        ╱╲
       ╱E2E╲          10% (Critical workflows)
      ╱──────╲
     ╱ Integ. ╲        30% (API + DB integration)
    ╱──────────╲
   ╱   Unit     ╲      60% (Services, utilities)
  ╱──────────────╲
```

### Test Environment

```
┌─────────────────────────────────────────┐
│ Docker Compose Test Environment         │
├─────────────────────────────────────────┤
│ - PostgreSQL (test database)            │
│ - FastAPI backend (test mode)           │
│ - Next.js frontend (test mode)          │
│ - Mock E2B API (test doubles)           │
│ - Mock GitHub API (test doubles)        │
└─────────────────────────────────────────┘
```

## Related Code Files

### New Files to Create
- `backend/tests/unit/test_e2b_service.py`
- `backend/tests/unit/test_git_service.py`
- `backend/tests/unit/test_github_service.py`
- `backend/tests/integration/test_api_endpoints.py`
- `backend/tests/integration/test_sse.py`
- `backend/tests/e2e/test_full_workflow.py`
- `backend/tests/conftest.py` - Pytest fixtures
- `backend/tests/mocks/e2b_mock.py` - E2B API mock
- `backend/tests/mocks/github_mock.py` - GitHub API mock
- `frontend/tests/e2e/task-assignment.spec.ts` - Playwright E2E
- `docker-compose.test.yml` - Test environment
- `DEPLOYMENT.md` - Deployment guide
- `.github/workflows/ci.yml` - CI pipeline

### Files to Modify
- `backend/pytest.ini` - Pytest configuration
- `backend/requirements-dev.txt` - Add pytest, pytest-asyncio, httpx, faker
- `package.json` - Add Playwright scripts

## Implementation Steps

### Backend Testing

1. **Setup Pytest Infrastructure**
   - Install pytest, pytest-asyncio, pytest-cov, httpx, faker
   - Create pytest.ini with async config
   - Create conftest.py with fixtures:
     - `test_db` - Isolated test database
     - `test_client` - FastAPI test client
     - `mock_e2b` - Mocked E2B service
     - `mock_github` - Mocked GitHub API

2. **Unit Tests - E2B Service**
   - Test sandbox creation (success, quota error, timeout)
   - Test command execution (stdout, stderr, exit codes)
   - Test sandbox destruction (success, already destroyed)
   - Test retry logic (transient failures)
   - Mock E2B SDK responses

3. **Unit Tests - Git Service**
   - Test clone_repo (success, auth failure, network timeout)
   - Test create_branch (success, branch exists, main not found)
   - Test commit (success, nothing to commit, invalid message)
   - Test push (success, auth failure, push rejected)
   - Mock E2BSandboxService.execute_command

4. **Unit Tests - GitHub Service**
   - Test create_pull_request (success, duplicate, validation error)
   - Test check_existing_pr (found, not found)
   - Test rate limit handling
   - Mock GitHub API responses

5. **Integration Tests - API Endpoints**
   - Test POST /api/v1/sandboxes (creates sandbox, stores in DB)
   - Test POST /api/v1/git/clone (clones repo in sandbox)
   - Test POST /api/v1/git/push (pushes branch)
   - Test POST /api/v1/github/pull-requests (creates PR, updates task)
   - Test error responses (404, 422, 500)

6. **Integration Tests - SSE**
   - Test SSE connection and event streaming
   - Test event filtering by agent_id
   - Test reconnection with Last-Event-ID
   - Test heartbeat delivery
   - Test concurrent connections

7. **E2E Tests - Full Workflow**
   - Test complete flow:
     1. Create task
     2. Assign to agent
     3. Create sandbox
     4. Clone repo
     5. Create branch
     6. Commit changes
     7. Push branch
     8. Create PR
     9. Verify PR URL in task
   - Use real test database, mocked E2B/GitHub

8. **Error Scenario Tests**
   - Test sandbox creation failure → cleanup
   - Test git clone timeout → retry → failure
   - Test push rejected → error notification
   - Test PR creation with 403 → error message
   - Test SSE disconnect → reconnect
   - Test database connection loss → recovery

9. **Load Tests**
   - Test 10 concurrent sandbox creations
   - Test 50 concurrent SSE connections
   - Test 100 rapid API calls
   - Monitor response times, error rates

10. **Database Migration Tests**
    - Test alembic upgrade → downgrade → upgrade
    - Test migrations with existing data
    - Verify schema matches models

### Frontend Testing

11. **Setup Playwright**
    - Install Playwright: `npm install -D @playwright/test`
    - Create playwright.config.ts
    - Setup test fixtures (authenticated user)

12. **E2E Tests - Task Assignment**
    - Navigate to squad page
    - Drag task to "In Progress"
    - Verify sandbox creation API called
    - Verify SSE connection established
    - Verify status updates in UI

13. **E2E Tests - Real-Time Updates**
    - Trigger sandbox creation
    - Verify status badge updates
    - Verify terminal output appears
    - Verify PR notification shows

14. **Component Tests**
    - Test TerminalOutput rendering
    - Test ProgressBar animations
    - Test SandboxStatus badge states
    - Test error toast displays

### Deployment

15. **Create Docker Compose**
    - Backend service (FastAPI + Uvicorn)
    - Frontend service (Next.js)
    - PostgreSQL service
    - Nginx reverse proxy (optional)
    - Environment variable injection

16. **Create Deployment Guide**
    - Environment variables checklist
    - Database migration steps
    - E2B API key setup
    - GitHub PAT configuration
    - Health check verification
    - Monitoring setup (optional)

17. **CI/CD Pipeline**
    - GitHub Actions workflow:
      - Lint (ruff, eslint)
      - Type check (mypy, tsc)
      - Unit tests
      - Integration tests
      - Build Docker images
      - Push to registry (optional)
    - Run on PR and main branch

18. **Monitoring Setup**
    - Add health check endpoint: GET /health
    - Add metrics endpoint: GET /metrics (Prometheus)
    - Log aggregation setup (stdout → CloudWatch/Datadog)
    - Error tracking (Sentry integration)

## Todo List

### P0 - Critical

- [ ] Install pytest, pytest-asyncio, pytest-cov, httpx
- [ ] Create conftest.py with test_db, test_client fixtures
- [ ] Create mocks/e2b_mock.py for E2B service
- [ ] Create mocks/github_mock.py for GitHub API
- [ ] Write unit tests for E2BSandboxService (5+ test cases)
- [ ] Write unit tests for GitService (5+ test cases)
- [ ] Write unit tests for GitHubService (5+ test cases)
- [ ] Write integration tests for API endpoints (10+ test cases)
- [ ] Write E2E test for full workflow (task → PR)
- [ ] Write error scenario tests (5+ scenarios)
- [ ] Run all tests, verify >80% coverage
- [ ] Fix any failing tests
- [ ] Create docker-compose.yml for deployment
- [ ] Create DEPLOYMENT.md with setup instructions
- [ ] Create .github/workflows/ci.yml for CI pipeline
- [ ] Test deployment locally with Docker
- [ ] Verify health checks work in Docker

### P1 - Important

- [ ] Install Playwright for frontend E2E tests
- [ ] Write E2E test for task assignment flow
- [ ] Write E2E test for SSE real-time updates
- [ ] Write integration tests for SSE endpoint
- [ ] Write load tests for concurrent operations
- [ ] Test database migrations (upgrade/downgrade)
- [ ] Add code coverage reporting to CI
- [ ] Setup Sentry for error tracking
- [ ] Add Prometheus metrics endpoint
- [ ] Document monitoring setup in DEPLOYMENT.md
- [ ] Create docker-compose.test.yml for test environment
- [ ] Test CI pipeline with PR

### P2 - Nice to Have

- [ ] Add visual regression tests (Percy, Chromatic)
- [ ] Add performance benchmarks (Lighthouse CI)
- [ ] Create load test suite (Locust, k6)
- [ ] Add mutation testing (mutmut)
- [ ] Setup test coverage badges (Codecov)
- [ ] Add security scanning (Snyk, Dependabot)
- [ ] Create staging environment
- [ ] Add blue-green deployment strategy

## Success Criteria

- [ ] All unit tests pass (>80% coverage)
- [ ] All integration tests pass
- [ ] E2E workflow test passes (task → PR)
- [ ] Error scenarios handled correctly
- [ ] Load tests show acceptable performance (<1s response time)
- [ ] CI pipeline runs successfully on PR
- [ ] Docker deployment works locally
- [ ] Health checks return 200 OK
- [ ] Monitoring captures errors and metrics
- [ ] Documentation complete and accurate

## Risk Assessment

**High Risks:**
- Tests depending on external services (E2B, GitHub) - flaky tests
- Database state pollution between tests
- Race conditions in concurrent tests
- E2E tests timing out on CI (slow environment)

**Medium Risks:**
- Mock drift from real API behavior
- Test data cleanup failures
- CI pipeline costs (GitHub Actions minutes)

**Mitigation:**
- Use test doubles for E2B/GitHub (no real API calls)
- Isolate database per test (transactions, rollback)
- Use locks/semaphores for concurrent test coordination
- Increase E2E timeouts on CI, use retry logic
- Regularly validate mocks against real APIs
- Cleanup test data in fixtures teardown
- Optimize test parallelization to reduce CI time

## Security Considerations

- **Test Secrets:** Store test API keys in GitHub Secrets (not .env files)
- **Database Isolation:** Use separate test database (never production)
- **Mock Data:** Avoid using real user data in tests (GDPR compliance)
- **Token Rotation:** Use short-lived tokens for tests, rotate regularly
- **Audit Logs:** Don't log sensitive data in test outputs

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 60 min | Test generation, fixture setup, CI config |
| Senior Dev | 8-10 hrs | Test strategy, mocking, E2E tests |
| Junior Dev | 16-20 hrs | Learning pytest, Playwright, debugging failures |

**Complexity:** High (testing strategy, mocking, deployment)

## Next Steps

After completion:
- Deploy to staging environment
- Monitor error rates and performance
- Iterate based on production feedback
- Add more tests as bugs discovered

## Unresolved Questions

1. **Test Database:** Use SQLite for speed or PostgreSQL for accuracy?
2. **E2B Mocking:** Mock at SDK level or HTTP level?
3. **GitHub Mocking:** Use VCR.py for recording real responses?
4. **E2E Frequency:** Run E2E tests on every commit or nightly only?
5. **Load Test Targets:** What are acceptable response times? (1s? 500ms?)
6. **Deployment Platform:** Render, Railway, AWS, GCP, or self-hosted?
7. **Database Backups:** Automated backups strategy? (daily, hourly?)
8. **Monitoring Tool:** Prometheus + Grafana or SaaS (Datadog, New Relic)?
