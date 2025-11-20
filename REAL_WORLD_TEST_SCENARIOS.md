# Real-World Test Scenarios for Agent-Squad

**Purpose:** Identify tool gaps and validate agent capabilities through realistic scenarios
**Created:** November 7, 2025
**Status:** Proposed - Ready for implementation

---

## Overview

These 10 scenarios simulate actual software development workflows that teams encounter daily. By testing these scenarios, we can:

1. **Validate** that agents can complete real work
2. **Identify** missing tools agents need
3. **Discover** workflow bottlenecks
4. **Improve** agent collaboration patterns
5. **Measure** end-to-end completion rates

Each scenario includes:
- Real-world context
- Expected agent workflow
- Success criteria
- Potential tool gaps to discover

---

## Scenario 1: Bug Fix with Root Cause Analysis

### Context
A production bug reported: "User login fails intermittently with 500 error"

### Real-World Workflow
1. **PM** triages bug, assigns to Backend Dev
2. **Backend Dev** investigates:
   - Reads error logs
   - Analyzes stack traces
   - Reviews authentication code
   - Identifies root cause (race condition in Redis cache)
3. **Backend Dev** implements fix:
   - Adds Redis lock mechanism
   - Updates error handling
   - Adds logging for diagnostics
4. **QA Tester** validates:
   - Tests login flow (normal case)
   - Tests under load (race condition scenario)
   - Verifies error handling
   - Checks logs are informative

### Success Criteria
- [ ] Root cause identified correctly
- [ ] Fix implemented and documented
- [ ] Tests added to prevent regression
- [ ] No new bugs introduced

### Expected Tool Needs
**Likely to discover need for:**
- ✅ File reading (view source code)
- ✅ File editing (make code changes)
- ✅ Log analysis tools (grep logs, parse stack traces)
- ✅ Code search tools (find all usages of auth function)
- ⚠️ **Debugger tool** (set breakpoints, inspect variables)
- ⚠️ **Load testing tool** (simulate race conditions)
- ⚠️ **Redis inspection tool** (view cache contents, monitor locks)

### Estimated Time
- Manual: 2-4 hours
- With Agents: 30-60 minutes (if tools available)

---

## Scenario 2: REST API Endpoint Implementation

### Context
Feature request: "Add user profile update endpoint with validation"

### Real-World Workflow
1. **PM** defines requirements:
   - Endpoint: PATCH /users/{id}/profile
   - Fields: name, email, bio, avatar_url
   - Validation: email format, max lengths
   - Authentication: JWT required

2. **Backend Dev** implements:
   - Creates Pydantic schema with validation
   - Implements endpoint in FastAPI
   - Adds database update logic
   - Handles edge cases (user not found, email taken)

3. **Backend Dev** adds tests:
   - Unit tests for validation
   - Integration tests for endpoint
   - Tests for edge cases

4. **Frontend Dev** integrates:
   - Creates profile update form
   - Adds API client function
   - Handles success/error states

5. **QA Tester** validates:
   - Tests all fields update correctly
   - Tests validation works (invalid email, too long text)
   - Tests authentication (no token = 401)
   - Tests edge cases

### Success Criteria
- [ ] Endpoint works correctly
- [ ] Validation prevents invalid data
- [ ] Frontend form functional
- [ ] All tests pass
- [ ] API documented

### Expected Tool Needs
**Likely to discover need for:**
- ✅ File creation/editing (create files, write code)
- ✅ Code execution (run tests)
- ✅ Database query tool (check data was updated)
- ⚠️ **API testing tool** (curl/httpie for manual testing)
- ⚠️ **API documentation generator** (OpenAPI/Swagger)
- ⚠️ **Schema validation tool** (test Pydantic schemas)
- ⚠️ **Database migration tool** (alembic commands)

### Estimated Time
- Manual: 3-5 hours
- With Agents: 45-90 minutes

---

## Scenario 3: Third-Party API Integration

### Context
Integrate Stripe payment processing into checkout flow

### Real-World Workflow
1. **PM** researches:
   - Reviews Stripe documentation
   - Identifies required endpoints (create payment intent, confirm payment)
   - Plans error handling strategy

2. **Backend Dev** implements:
   - Installs stripe SDK
   - Creates Stripe service class
   - Implements payment intent creation
   - Implements webhook handler for events
   - Adds error handling (network issues, card declined)

3. **Frontend Dev** integrates:
   - Installs Stripe.js
   - Creates checkout form with Stripe Elements
   - Handles payment submission
   - Shows success/error messages

4. **DevOps** configures:
   - Adds Stripe API keys to environment
   - Configures webhook endpoint in Stripe dashboard
   - Sets up webhook signature verification

5. **QA Tester** validates:
   - Tests successful payment flow
   - Tests card decline scenarios
   - Tests network error handling
   - Verifies webhook events processed

### Success Criteria
- [ ] Payment flow works end-to-end
- [ ] Webhooks processed correctly
- [ ] Errors handled gracefully
- [ ] Secure (API keys not exposed)

### Expected Tool Needs
**Likely to discover need for:**
- ✅ Package installation (pip install, npm install)
- ✅ File reading (read Stripe docs)
- ✅ Environment variable management
- ⚠️ **HTTP request tool** (test API calls to Stripe)
- ⚠️ **Webhook testing tool** (simulate webhook events)
- ⚠️ **Secret management tool** (securely store API keys)
- ⚠️ **External API documentation reader** (fetch Stripe API docs)

### Estimated Time
- Manual: 4-6 hours
- With Agents: 1-2 hours

---

## Scenario 4: Database Schema Migration

### Context
Add user preferences table with JSON column for settings

### Real-World Workflow
1. **Backend Dev** plans migration:
   - Designs schema (user_preferences table)
   - Plans data migration (migrate existing settings from user table)
   - Considers rollback strategy

2. **Backend Dev** implements migration:
   - Creates Alembic migration file
   - Adds upgrade() function (create table, migrate data)
   - Adds downgrade() function (rollback)
   - Tests migration on dev database

3. **Backend Dev** updates code:
   - Creates UserPreferences model
   - Updates user model relationship
   - Updates queries to use new table
   - Updates tests

4. **DevOps** reviews:
   - Checks migration is idempotent
   - Verifies rollback works
   - Plans deployment strategy (run migration before code deploy)

5. **QA Tester** validates:
   - Tests migration runs successfully
   - Tests data migrated correctly
   - Tests new code works with migrated data
   - Tests rollback works

### Success Criteria
- [ ] Migration runs without errors
- [ ] Data migrated correctly (no data loss)
- [ ] Rollback works
- [ ] Performance acceptable (if large dataset)

### Expected Tool Needs
**Likely to discover need for:**
- ✅ File creation (create migration file)
- ✅ Database query tool (check data)
- ✅ Command execution (alembic upgrade, alembic downgrade)
- ⚠️ **Database inspection tool** (view schema, table structure)
- ⚠️ **Data validation tool** (compare before/after data)
- ⚠️ **Query performance analyzer** (EXPLAIN ANALYZE)
- ⚠️ **Backup/restore tool** (test rollback safety)

### Estimated Time
- Manual: 2-3 hours
- With Agents: 45-60 minutes

---

## Scenario 5: Performance Optimization Investigation

### Context
Dashboard page is slow (loading takes 5+ seconds, should be <1 second)

### Real-World Workflow
1. **PM** creates performance task:
   - Describes issue: "Dashboard loads in 5s, users complaining"
   - Target: <1 second load time
   - Priority: high

2. **Backend Dev** investigates:
   - Profiles endpoint (/api/dashboard)
   - Identifies slow query (N+1 problem in user stats)
   - Measures baseline performance

3. **Backend Dev** optimizes:
   - Fixes N+1 query (add selectinload)
   - Adds database index on frequently queried column
   - Adds Redis caching for expensive aggregations
   - Measures improvement

4. **Frontend Dev** optimizes:
   - Identifies large bundle size
   - Adds code splitting
   - Lazy loads dashboard widgets
   - Optimizes images (compress, use WebP)

5. **QA Tester** validates:
   - Measures actual load time
   - Tests with realistic data volumes
   - Verifies functionality unchanged
   - Tests cache invalidation works

### Success Criteria
- [ ] Dashboard loads in <1 second
- [ ] Optimizations don't break functionality
- [ ] Solution scales with data growth

### Expected Tool Needs
**Likely to discover need for:**
- ✅ Code profiling (identify slow code)
- ✅ Database query analysis (EXPLAIN)
- ⚠️ **Performance benchmarking tool** (measure response times)
- ⚠️ **Database query profiler** (pg_stat_statements, slow query log)
- ⚠️ **Frontend performance tool** (Lighthouse, bundle analyzer)
- ⚠️ **Load testing tool** (simulate realistic load)
- ⚠️ **Monitoring dashboard** (track metrics over time)

### Estimated Time
- Manual: 3-6 hours
- With Agents: 1-2 hours

---

## Scenario 6: Security Vulnerability Remediation

### Context
Security scan reports: "SQL Injection vulnerability in search endpoint"

### Real-World Workflow
1. **PM** escalates security issue:
   - Creates high-priority task
   - Describes vulnerability (search param not sanitized)
   - Assigns to Backend Dev + Security review

2. **Backend Dev** analyzes:
   - Reviews vulnerable code (raw SQL string concatenation)
   - Identifies all similar patterns in codebase
   - Researches proper fix (parameterized queries)

3. **Backend Dev** fixes:
   - Replaces raw SQL with SQLAlchemy parameterized query
   - Adds input validation
   - Adds automated security tests
   - Scans codebase for similar vulnerabilities

4. **Solution Architect** reviews:
   - Validates fix is correct
   - Checks for edge cases
   - Recommends additional hardening (rate limiting, WAF rules)

5. **QA Tester** validates:
   - Tests fix works
   - Tests SQL injection attempts blocked
   - Runs security scan again (verify vulnerability gone)
   - Tests functionality unchanged

### Success Criteria
- [ ] Vulnerability fixed
- [ ] No similar vulnerabilities exist
- [ ] Automated tests prevent regression
- [ ] Documented in security log

### Expected Tool Needs
**Likely to discover need for:**
- ✅ Code search (find similar patterns)
- ✅ Code editing (fix vulnerabilities)
- ⚠️ **Security scanning tool** (bandit, safety, npm audit)
- ⚠️ **SAST tool** (static analysis security testing)
- ⚠️ **Dependency vulnerability scanner** (check for CVEs)
- ⚠️ **Penetration testing tool** (test security fixes)
- ⚠️ **Code review tool** (flag security issues)

### Estimated Time
- Manual: 2-4 hours
- With Agents: 45-90 minutes

---

## Scenario 7: Legacy Code Refactoring

### Context
Refactor 500-line God class into smaller, testable modules

### Real-World Workflow
1. **Tech Lead** identifies technical debt:
   - 500-line UserService class does too much
   - Hard to test, hard to maintain
   - Plan: Split into AuthService, ProfileService, NotificationService

2. **Backend Dev** analyzes:
   - Reads existing UserService code
   - Maps out dependencies
   - Identifies which methods belong to which service
   - Plans refactoring steps (incremental, safe)

3. **Backend Dev** refactors:
   - Creates AuthService with auth methods
   - Creates ProfileService with profile methods
   - Creates NotificationService with notification methods
   - Updates UserService to delegate to new services
   - Updates all callers

4. **Backend Dev** adds tests:
   - Unit tests for each new service
   - Integration tests unchanged (behavior same)
   - Achieves >80% coverage

5. **QA Tester** validates:
   - Runs full regression test suite
   - Verifies no behavior changed
   - Tests edge cases still work

### Success Criteria
- [ ] Code split into logical services
- [ ] All tests pass (no behavior change)
- [ ] Code coverage improved
- [ ] Code more maintainable (smaller classes)

### Expected Tool Needs
**Likely to discover need for:**
- ✅ Code reading (understand existing code)
- ✅ Code editing (refactor)
- ✅ Code search (find all usages)
- ⚠️ **Code analysis tool** (complexity metrics, coupling analysis)
- ⚠️ **Refactoring tool** (automated safe refactorings)
- ⚠️ **Code coverage tool** (pytest-cov)
- ⚠️ **Dependency graph tool** (visualize dependencies)
- ⚠️ **Code metrics dashboard** (track improvements)

### Estimated Time
- Manual: 4-8 hours
- With Agents: 2-3 hours

---

## Scenario 8: CI/CD Pipeline Setup

### Context
Set up GitHub Actions pipeline for automated testing and deployment

### Real-World Workflow
1. **DevOps** plans pipeline:
   - Triggers: on push to main, on PR
   - Steps: lint, test, build, deploy (staging on PR, prod on merge)
   - Environments: staging, production
   - Secrets: database URL, API keys

2. **DevOps** implements:
   - Creates .github/workflows/ci.yml
   - Configures linting step (ruff, black)
   - Configures test step (pytest with coverage)
   - Configures build step (Docker build)
   - Configures deploy step (deploy to staging/prod)

3. **DevOps** configures secrets:
   - Adds secrets to GitHub repo settings
   - Configures environment protection rules
   - Sets up deploy approvals for prod

4. **Backend Dev** adds tests:
   - Ensures tests run in CI
   - Fixes any CI-specific issues
   - Adds coverage reporting

5. **QA Tester** validates:
   - Creates test PR
   - Verifies CI runs
   - Checks tests run correctly
   - Verifies deployment to staging works

### Success Criteria
- [ ] Pipeline runs on every push/PR
- [ ] Tests run and report results
- [ ] Failed tests block merge
- [ ] Successful merges deploy to staging
- [ ] Production deploys require approval

### Expected Tool Needs
**Likely to discover need for:**
- ✅ File creation (create workflow file)
- ✅ YAML editing
- ⚠️ **CI/CD configuration tool** (validate workflow syntax)
- ⚠️ **Secret management tool** (manage GitHub secrets)
- ⚠️ **Docker build tool** (build images in CI)
- ⚠️ **Deployment tool** (deploy to staging/prod)
- ⚠️ **Notification tool** (Slack/email on CI failure)

### Estimated Time
- Manual: 3-5 hours
- With Agents: 1-2 hours

---

## Scenario 9: Comprehensive Documentation Generation

### Context
Generate complete API documentation for all endpoints

### Real-World Workflow
1. **PM** requests documentation:
   - All API endpoints need documentation
   - Include: endpoint, method, parameters, responses, examples
   - Format: OpenAPI/Swagger + Markdown guides

2. **Backend Dev** generates OpenAPI:
   - Reviews FastAPI routes (auto-generates OpenAPI)
   - Adds missing docstrings
   - Adds response examples
   - Validates schema is complete

3. **Backend Dev** writes guides:
   - Authentication guide (how to get JWT token)
   - Common workflows (create squad, execute task)
   - Error handling guide (error codes, retry strategies)
   - Rate limiting guide

4. **Frontend Dev** adds examples:
   - JavaScript/TypeScript examples for each endpoint
   - React component examples
   - Error handling examples

5. **QA Tester** reviews:
   - Tests all examples work
   - Verifies documentation accurate
   - Checks for clarity (can a new dev understand?)

### Success Criteria
- [ ] All endpoints documented
- [ ] Examples for common workflows
- [ ] Hosted documentation accessible
- [ ] Kept up-to-date (CI checks)

### Expected Tool Needs
**Likely to discover need for:**
- ✅ Code reading (extract docstrings, schemas)
- ✅ Markdown generation
- ⚠️ **OpenAPI schema generator** (from FastAPI app)
- ⚠️ **Documentation hosting tool** (Swagger UI, ReDoc, MkDocs)
- ⚠️ **Code example generator** (generate curl, JS examples)
- ⚠️ **Documentation validator** (check links, examples work)
- ⚠️ **Diagram generator** (architecture diagrams, sequence diagrams)
- ⚠️ **Screenshot tool** (capture UI for docs)

### Estimated Time
- Manual: 6-10 hours
- With Agents: 2-4 hours

---

## Scenario 10: Multi-Service Feature Implementation

### Context
Implement "notification system" requiring changes across multiple services

### Real-World Workflow
1. **Solution Architect** designs system:
   - Components: notification service, queue (NATS), email service
   - Flow: event occurs → publish to NATS → notification service → email service
   - Technologies: NATS JetStream, SendGrid

2. **Backend Dev** implements notification service:
   - Creates notification service (FastAPI microservice)
   - Subscribes to NATS topics (user.created, task.completed)
   - Stores notifications in database
   - Exposes REST API (GET /notifications)

3. **Backend Dev** integrates email service:
   - Creates email service (separate microservice)
   - Subscribes to notification events
   - Sends emails via SendGrid
   - Handles email templates

4. **Backend Dev** updates main API:
   - Publishes events to NATS when actions occur
   - Adds notification preferences to user model
   - Adds endpoints to manage preferences

5. **Frontend Dev** adds UI:
   - Notification bell icon with unread count
   - Notification dropdown
   - Notification preferences page

6. **DevOps** deploys:
   - Adds notification service to docker-compose
   - Adds email service to docker-compose
   - Configures NATS topics
   - Adds SendGrid API key

7. **QA Tester** validates:
   - Tests notifications created on events
   - Tests emails sent correctly
   - Tests notification preferences work
   - Tests unread count accurate

### Success Criteria
- [ ] Notifications created on events
- [ ] Emails sent reliably
- [ ] Preferences respected
- [ ] System scales (queues handle load)
- [ ] Services are loosely coupled

### Expected Tool Needs
**Likely to discover need for:**
- ✅ File creation (multiple services)
- ✅ Docker configuration (docker-compose updates)
- ✅ Message bus operations (NATS publish/subscribe)
- ⚠️ **Service orchestration tool** (start multiple services)
- ⚠️ **Message queue inspector** (view NATS messages)
- ⚠️ **Email testing tool** (test emails without sending)
- ⚠️ **Service dependency graph** (visualize service calls)
- ⚠️ **Distributed tracing** (track requests across services)
- ⚠️ **API gateway tool** (route requests to services)

### Estimated Time
- Manual: 10-15 hours
- With Agents: 4-6 hours

---

## Summary: Potential Tool Gaps Discovered

### High Priority (Likely Needed for Most Scenarios)

**File Operations:**
- ✅ Read files (HAVE)
- ✅ Write files (HAVE)
- ✅ Edit files (HAVE)
- ⚠️ Multi-file editing (edit multiple files atomically)

**Code Operations:**
- ✅ Search code (HAVE - via grep)
- ⚠️ **Code execution tool** (run scripts, tests)
- ⚠️ **Package installation** (pip, npm, bun)
- ⚠️ **Syntax validation** (lint, format)

**Git Operations:**
- ⚠️ **Clone repository**
- ⚠️ **Create branch**
- ⚠️ **Commit changes**
- ⚠️ **Push to remote**
- ⚠️ **Create pull request**
- ⚠️ **View git history**

**Database Operations:**
- ⚠️ **Run SQL queries** (SELECT, UPDATE)
- ⚠️ **Run migrations** (alembic)
- ⚠️ **Inspect schema** (view tables, columns)
- ⚠️ **View query performance** (EXPLAIN)

**HTTP/API Operations:**
- ⚠️ **Make HTTP requests** (GET, POST, etc.)
- ⚠️ **Test API endpoints**
- ⚠️ **Parse API responses**

### Medium Priority (Useful for 3-5 Scenarios)

**Testing Tools:**
- ⚠️ **Run tests** (pytest, jest)
- ⚠️ **Code coverage** (pytest-cov)
- ⚠️ **Load testing** (locust, k6)

**Performance Tools:**
- ⚠️ **Profiling** (cProfile, py-spy)
- ⚠️ **Benchmarking** (measure execution time)
- ⚠️ **Metrics collection** (track performance)

**Security Tools:**
- ⚠️ **Security scanning** (bandit, safety)
- ⚠️ **Dependency auditing** (npm audit)
- ⚠️ **SAST** (static analysis)

**Documentation Tools:**
- ⚠️ **Generate OpenAPI schema**
- ⚠️ **Generate Markdown docs**
- ⚠️ **Create diagrams** (architecture, sequence)

### Low Priority (Nice to Have for 1-2 Scenarios)

**DevOps Tools:**
- ⚠️ **Docker build/run**
- ⚠️ **CI/CD configuration**
- ⚠️ **Secret management**
- ⚠️ **Deployment automation**

**Advanced Analysis:**
- ⚠️ **Dependency graphs**
- ⚠️ **Code metrics** (complexity, coupling)
- ⚠️ **Distributed tracing**

---

## Implementation Plan

### Phase 1: Core Tools (Week 1)
Implement tools needed for 8+ scenarios:
1. ✅ File operations (DONE - have Read, Write, Edit)
2. ⚠️ **Code execution** - Run Python/JS scripts
3. ⚠️ **Git operations** - Basic git commands
4. ⚠️ **Database queries** - SQL execution
5. ⚠️ **HTTP requests** - API testing

### Phase 2: Testing & Performance (Week 2)
Implement tools needed for 5+ scenarios:
1. ⚠️ **Test runner** - pytest, jest
2. ⚠️ **Code coverage** - Track test coverage
3. ⚠️ **Profiling** - Identify bottlenecks
4. ⚠️ **Benchmarking** - Measure performance

### Phase 3: Advanced Tools (Week 3)
Implement tools needed for 2-3 scenarios:
1. ⚠️ **Security scanning** - Find vulnerabilities
2. ⚠️ **Documentation generation** - Auto-generate docs
3. ⚠️ **CI/CD configuration** - GitHub Actions
4. ⚠️ **Docker operations** - Build, run containers

---

## Testing Strategy

### For Each Scenario:

**Step 1: Manual Baseline**
- Complete scenario manually
- Document tools used
- Record time taken
- Note pain points

**Step 2: Agent Attempt (Current Tools)**
- Run agents on scenario
- Document what works
- Document what fails
- Identify missing tools

**Step 3: Implement Missing Tools**
- Prioritize by frequency (how many scenarios need it?)
- Implement tool as MCP server or Agno tool
- Test tool works correctly

**Step 4: Re-test Scenario**
- Run agents again with new tools
- Measure improvement
- Document success rate

**Step 5: Iterate**
- Fix issues discovered
- Add more tools if needed
- Achieve >80% success rate

### Success Metrics

For each scenario, measure:
- **Completion rate** - Did agents finish?
- **Time to completion** - How long did it take?
- **Quality score** - Was output correct?
- **Tool usage** - Which tools were used?
- **Error rate** - How many failures?

**Target:**
- Completion rate: >80%
- Time: 2-3x faster than manual
- Quality: >90% correct
- Errors: <10% of attempts

---

## Next Steps

1. **Prioritize scenarios** - Which 3-5 should we test first?
2. **Set up test infrastructure** - Create test harness for scenarios
3. **Run baseline tests** - Establish current capability
4. **Identify tool gaps** - Document what's missing
5. **Implement top tools** - Start with high-priority tools
6. **Re-test scenarios** - Measure improvement
7. **Iterate** - Continue until targets met

---

## Proposed Testing Order

**Week 1: Core Workflows**
1. ✅ Scenario 2: REST API Endpoint (validates basic coding)
2. ✅ Scenario 1: Bug Fix (validates investigation + fix)
3. ✅ Scenario 4: Database Migration (validates database ops)

**Week 2: Integration & Performance**
4. ✅ Scenario 3: Third-Party API (validates external integration)
5. ✅ Scenario 5: Performance Optimization (validates profiling)

**Week 3: Advanced Scenarios**
6. ✅ Scenario 6: Security Vulnerability (validates security)
7. ✅ Scenario 7: Legacy Refactoring (validates code analysis)
8. ✅ Scenario 8: CI/CD Setup (validates DevOps)

**Week 4: Complex Multi-Service**
9. ✅ Scenario 9: Documentation (validates doc generation)
10. ✅ Scenario 10: Multi-Service Feature (validates orchestration)

---

**Document Created:** November 7, 2025
**Status:** Proposed - Ready for discussion and prioritization
**Next:** Select 3-5 scenarios to test first
