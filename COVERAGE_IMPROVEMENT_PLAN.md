# Test Coverage Improvement Plan: 85% → 95%+

**Current Coverage**: ~85%
**Target Coverage**: 90-95%
**Stretch Goal**: 95-100%

**Generated**: 2025-11-22

---

## Strategy Overview

To reach 90-95% coverage, we need to:

1. **Measure current coverage** - Get exact baseline
2. **Identify untested code** - Find coverage gaps
3. **Prioritize by risk** - Test critical paths first
4. **Add missing tests** - Fill coverage gaps systematically
5. **Maintain coverage** - CI/CD enforcement

---

## Phase 1: Measure Current Coverage (Day 1)

### Step 1.1: Run Coverage Analysis

```bash
cd backend

# Generate coverage report
pytest tests/ \
  --cov=backend \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-report=json

# Open HTML report
open htmlcov/index.html
```

### Step 1.2: Analyze Coverage by Module

**Expected Output**:
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend/agents/communication/           450     45    90%     L45-67, L120-135
backend/agents/orchestration/           380     60    84%     L78-92, L156-178
backend/services/                       520     80    85%     ...
backend/api/v1/endpoints/               680     50    93%     ...
backend/models/                         340     20    94%     ...
---------------------------------------------------------------------
TOTAL                                   3500    350   90%
```

### Step 1.3: Generate Missing Lines Report

```bash
# Get detailed missing lines
pytest tests/ \
  --cov=backend \
  --cov-report=term-missing \
  > coverage_report.txt

# Analyze which files have lowest coverage
grep -E "^backend.*py" coverage_report.txt | \
  awk '{print $4, $1}' | \
  sort -n | \
  head -20
```

**Action Item**: Identify the 20 files with lowest coverage percentages.

---

## Phase 2: Identify Untested Code (Day 1-2)

### 2.1 Modules Likely Under-Tested

Based on codebase structure, these areas likely need more tests:

#### **API Endpoints** - Missing Tests
- ✅ `auth.py` - Has tests
- ✅ `squads.py` - Has tests
- ❓ `health.py` - Likely missing
- ❓ `cache_metrics.py` - Likely missing
- ❓ `costs.py` - Likely missing
- ❓ `intelligence.py` - Likely missing
- ❓ `mcp.py` - Partial coverage
- ❓ `ml_detection.py` - Partial coverage
- ❓ `pm_guardian.py` - Partial coverage
- ❓ `routing_rules.py` - Partial coverage
- ❓ `webhooks.py` - NEW (needs tests)
- ❓ `multi_turn_conversations.py` - Partial coverage

**Estimated Missing**: 8-10 endpoint test files needed

#### **Services** - Missing Tests
- ✅ `agent_service.py` - Has tests
- ✅ `squad_service.py` - Has tests
- ✅ `analytics_service.py` - Has tests
- ✅ `cache_service.py` - Has tests
- ✅ `sandbox_service.py` - Has tests
- ❓ `webhook_service.py` - NEW (battle-tested but not unit tested)
- ❓ `sse_service.py` - Partial coverage
- ❓ `github_integration.py` - Partial coverage
- ❓ `inngest_service.py` - Likely missing
- ❓ `cost_tracking_service.py` - Likely missing

**Estimated Missing**: 5-7 service test files needed

#### **Models** - Missing Tests
Currently only 2 model test files exist:
- ✅ `test_conversation.py`
- ✅ `test_routing_rule.py`

**Missing model tests** (need at least smoke tests):
- ❌ `user.py`
- ❌ `squad.py`
- ❌ `squad_member.py`
- ❌ `task_execution.py`
- ❌ `agent_message.py`
- ❌ `workflow_state.py`
- ❌ `branching_decision.py`
- ❌ `pm_checkpoint.py`
- ❌ `llm_cost.py`
- ❌ `sandbox.py` (has service tests but not model tests)

**Estimated Missing**: 10+ model test files needed

#### **Collaboration Patterns** - Missing Tests
- ❌ `collaboration/patterns.py`
- ❌ `collaboration/standup.py`
- ❌ `collaboration/code_review.py`
- ❌ `collaboration/problem_solving.py`

**Estimated Missing**: 4 collaboration test files needed

#### **Guardian System** - Partial Coverage
- ✅ `test_advanced_guardian.py` exists
- ✅ `test_pm_guardian.py` exists
- ❌ `workflow_health_monitor.py` - Likely partial
- ❌ `recommendations_engine.py` - Likely partial
- ❌ `coherence_scorer.py` - Likely partial
- ❌ `advanced_anomaly_detector.py` - Likely partial

**Estimated Missing**: 4 guardian component tests needed

#### **Configuration** - Missing Tests
- ❌ `configuration/mcp_tool_mapper.py`
- ❌ `configuration/interaction_config.py`

**Estimated Missing**: 2 configuration test files needed

#### **Specialized Agents** - Missing Tests
Only 2 test files exist in `agents/specialized/`:
- ✅ `test_agno_project_manager.py`
- ✅ `test_agno_message_bus_integration.py`

**Missing specialized agent tests**:
- ❌ `agno_backend_developer.py`
- ❌ `agno_frontend_developer.py`
- ❌ `agno_tech_lead.py`
- ❌ `agno_qa_tester.py`
- ❌ `agno_devops_engineer.py`
- ❌ `agno_designer.py`
- ❌ `agno_data_scientist.py`
- ❌ `agno_ml_engineer.py`
- ❌ `agno_ai_engineer.py`
- ❌ `agno_solution_architect.py`
- ❌ `agno_data_engineer.py`

**Estimated Missing**: 11 specialized agent test files needed

#### **Orchestration** - Partial Coverage
- ✅ `workflow_engine.py` - Has tests
- ❌ `orchestrator.py` - Likely partial
- ❌ `phase_based_engine.py` - Likely partial
- ❌ `delegation_engine.py` - Likely partial

**Estimated Missing**: 3 orchestration test files needed

#### **ML/Intelligence** - Partial Coverage
- ❌ `ml/opportunity_detector.py`
- ✅ `intelligence/workflow_intelligence.py` - Has tests
- ✅ `discovery/ml_enhanced_discovery.py` - Has tests

**Estimated Missing**: 1 ML test file needed

#### **Interaction** - Partial Coverage
- ✅ `conversation_manager.py` - Has tests
- ✅ `escalation_service.py` - Has tests
- ✅ `routing_engine.py` - Has tests
- ❌ `celery_tasks.py` - Likely missing
- ❌ `celery_config.py` - Likely missing
- ❌ `timeout_monitor.py` - Likely missing
- ❌ `agent_message_handler.py` - Likely partial
- ❌ `seed_routing_templates.py` - Utility (skip)

**Estimated Missing**: 4 interaction test files needed

---

## Phase 3: Prioritized Test Creation (Days 2-5)

### Priority P0: Critical Path (90% → 92%)

**Must have 100% coverage** - these affect production:

#### 3.1 API Endpoints (2 days)
```bash
# Create missing endpoint tests
tests/test_api/test_health_endpoints.py          # Health checks
tests/test_api/test_costs_endpoints.py           # Cost tracking API
tests/test_api/test_mcp_endpoints.py             # MCP API (enhance existing)
tests/test_api/test_cache_metrics_endpoints.py   # Cache metrics API
tests/test_api/test_webhook_endpoints.py         # Webhook API (NEW)
```

**Test Count**: ~50 new tests
**Coverage Gain**: +2-3%

#### 3.2 Core Services (1 day)
```bash
# Create missing service tests
tests/test_services/test_sse_service.py          # SSE manager
tests/test_services/test_inngest_service.py      # Inngest workflows
tests/test_services/test_cost_tracking_service.py # Cost tracking
```

**Test Count**: ~30 new tests
**Coverage Gain**: +1-2%

#### 3.3 Authentication & Security (1 day)
```bash
# Enhance existing security tests
tests/test_security.py                           # Enhance existing
tests/test_api/test_auth_endpoints.py            # Enhance existing
tests/test_auth_middleware.py                    # NEW - middleware tests
```

**Test Count**: ~20 new tests
**Coverage Gain**: +1%

---

### Priority P1: High Value (92% → 94%)

**Important for reliability** - business logic:

#### 3.4 Database Models (2 days)
```bash
# Create model tests (basic CRUD + validation)
tests/test_models/test_user.py
tests/test_models/test_squad.py
tests/test_models/test_squad_member.py
tests/test_models/test_task_execution.py
tests/test_models/test_agent_message.py
tests/test_models/test_workflow_state.py
tests/test_models/test_branching_decision.py
tests/test_models/test_pm_checkpoint.py
tests/test_models/test_llm_cost.py
tests/test_models/test_sandbox.py
```

**Test Count**: ~100 new tests (10 per model)
**Coverage Gain**: +2-3%

#### 3.5 Collaboration Patterns (1 day)
```bash
tests/test_agents/test_collaboration_patterns.py
tests/test_agents/test_standup.py
tests/test_agents/test_code_review.py
tests/test_agents/test_problem_solving.py
```

**Test Count**: ~40 new tests
**Coverage Gain**: +1%

---

### Priority P2: Nice to Have (94% → 95%+)

**Completeness** - edge cases and specialized components:

#### 3.6 Specialized Agents (2 days)
```bash
# Test each specialized agent's unique capabilities
tests/test_agents/test_specialized_backend_dev.py
tests/test_agents/test_specialized_frontend_dev.py
tests/test_agents/test_specialized_tech_lead.py
tests/test_agents/test_specialized_qa.py
tests/test_agents/test_specialized_devops.py
# ... (11 total)
```

**Test Count**: ~110 new tests (10 per agent)
**Coverage Gain**: +1-2%

#### 3.7 Guardian Components (1 day)
```bash
tests/test_agents/test_workflow_health_monitor.py
tests/test_agents/test_recommendations_engine.py
tests/test_agents/test_coherence_scorer.py
tests/test_agents/test_anomaly_detector.py
```

**Test Count**: ~40 new tests
**Coverage Gain**: +1%

#### 3.8 Orchestration (1 day)
```bash
tests/test_agents/test_orchestrator.py
tests/test_agents/test_phase_based_engine.py
tests/test_agents/test_delegation_engine.py
```

**Test Count**: ~30 new tests
**Coverage Gain**: +0.5%

#### 3.9 Configuration & Utilities (0.5 days)
```bash
tests/test_agents/test_mcp_tool_mapper.py
tests/test_agents/test_interaction_config.py
```

**Test Count**: ~20 new tests
**Coverage Gain**: +0.5%

---

## Phase 4: Edge Cases & Error Paths (95% → 98%+)

### 4.1 Error Handling Tests (1 day)

**For each major service**, add tests for:
- Invalid input validation
- Database connection failures
- External API failures (GitHub, E2B, etc.)
- Timeout scenarios
- Race conditions
- Concurrent operations

**Example**:
```python
# tests/test_services/test_agent_service_errors.py
@pytest.mark.asyncio
async def test_create_agent_database_failure(db_session):
    """Test agent creation when database fails"""
    # Mock database failure
    # Verify graceful error handling

@pytest.mark.asyncio
async def test_create_agent_invalid_role(db_session):
    """Test agent creation with invalid role"""
    # Verify validation error raised
```

**Test Count**: ~80 new tests
**Coverage Gain**: +2-3%

### 4.2 Boundary & Edge Cases (1 day)

Test boundary conditions:
- Empty inputs
- Maximum length inputs
- Null/None values
- Large payloads
- Zero/negative numbers
- Concurrent modifications

**Test Count**: ~60 new tests
**Coverage Gain**: +1-2%

---

## Coverage Target Breakdown

| Phase | Priority | Tests Added | Coverage Gain | Cumulative |
|-------|----------|-------------|---------------|------------|
| Current | - | 300+ | - | ~85% |
| Phase 3.1-3.3 | P0 | 100 | +4-6% | 89-91% |
| Phase 3.4-3.5 | P1 | 140 | +3-4% | 92-95% |
| Phase 3.6-3.9 | P2 | 200 | +2-3% | 94-98% |
| Phase 4 | Edge | 140 | +3-5% | 97-100% |
| **TOTAL** | - | **580** | **+12-18%** | **97-100%** ✅

---

## Implementation Plan

### Week 1: P0 Tests (90%)
**Days 1-3**: Measure coverage, create P0 endpoint and service tests
- Run coverage analysis
- Create 5 endpoint test files
- Create 3 service test files
- Add 100+ tests
- Target: 90% coverage

### Week 2: P1 Tests (94%)
**Days 4-6**: Model and collaboration tests
- Create 10 model test files
- Create 4 collaboration test files
- Add 140+ tests
- Target: 94% coverage

### Week 3: P2 Tests (95%+)
**Days 7-10**: Specialized agents, guardians, orchestration
- Create 11 specialized agent tests
- Create 4 guardian component tests
- Create 3 orchestration tests
- Add 200+ tests
- Target: 95%+ coverage

### Week 4: Edge Cases (98%+)
**Days 11-12**: Error handling and edge cases
- Add error path tests to all services
- Add boundary condition tests
- Add 140+ tests
- Target: 98%+ coverage

---

## Test Templates

### Template: Model Test

```python
# tests/test_models/test_<model_name>.py
import pytest
from uuid import uuid4
from backend.models.<model_name> import <ModelName>

class Test<ModelName>Model:
    @pytest.mark.asyncio
    async def test_create(self, db_session):
        """Test model creation"""
        model = <ModelName>(field1="value1")
        db_session.add(model)
        await db_session.commit()
        assert model.id is not None

    @pytest.mark.asyncio
    async def test_field_validation(self, db_session):
        """Test field validation"""
        with pytest.raises(ValueError):
            model = <ModelName>(invalid_field="bad")

    @pytest.mark.asyncio
    async def test_relationships(self, db_session):
        """Test model relationships"""
        # Test foreign key relationships
```

### Template: Service Test

```python
# tests/test_services/test_<service_name>.py
import pytest
from backend.services.<service_name> import <ServiceName>

class Test<ServiceName>:
    @pytest.mark.asyncio
    async def test_happy_path(self, db_session):
        """Test main functionality"""
        service = <ServiceName>(db_session)
        result = await service.main_method()
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, db_session):
        """Test error handling"""
        service = <ServiceName>(db_session)
        with pytest.raises(ExpectedError):
            await service.method_with_invalid_input()

    @pytest.mark.asyncio
    async def test_edge_case(self, db_session):
        """Test edge case"""
        # Test boundary conditions
```

### Template: API Endpoint Test

```python
# tests/test_api/test_<endpoint_name>_endpoints.py
import pytest

class Test<Endpoint>API:
    @pytest.mark.asyncio
    async def test_get_endpoint(self, client, auth_headers):
        """Test GET endpoint"""
        response = await client.get(
            "/api/v1/<endpoint>",
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_post_endpoint(self, client, auth_headers):
        """Test POST endpoint"""
        payload = {"field": "value"}
        response = await client.post(
            "/api/v1/<endpoint>",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Test endpoint without auth"""
        response = await client.get("/api/v1/<endpoint>")
        assert response.status_code == 401
```

---

## CI/CD Enforcement

### Step 1: Add Coverage Threshold

**File**: `.github/workflows/test.yml`

```yaml
- name: Run tests with coverage
  run: |
    pytest tests/ \
      --cov=backend \
      --cov-report=xml \
      --cov-report=term \
      --cov-fail-under=90  # Fail if coverage < 90%
```

### Step 2: Add Pre-commit Hook

**File**: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Run tests before commit
pytest tests/ --cov=backend --cov-fail-under=90 -x

if [ $? -ne 0 ]; then
    echo "❌ Tests failed or coverage below 90%"
    exit 1
fi

echo "✅ Tests passed and coverage ≥ 90%"
```

### Step 3: Add Pull Request Check

Require coverage report in PRs:
- Coverage must not decrease
- New code must have tests
- Critical paths must have 100% coverage

---

## Monitoring Coverage Over Time

### Daily Coverage Report

```bash
# Generate coverage badge
coverage-badge -o coverage.svg -f

# Commit to repo
git add coverage.svg
git commit -m "Update coverage badge"
```

### Weekly Coverage Review

1. Run full coverage analysis
2. Identify modules below 90%
3. Create tickets for missing tests
4. Prioritize by criticality

### Coverage Dashboard

Use tools like:
- **Codecov** - Automated coverage tracking
- **Coveralls** - Coverage history graphs
- **SonarQube** - Code quality + coverage

---

## Success Metrics

### Week 1 Goals
- ✅ Coverage baseline measured
- ✅ P0 endpoint tests created
- ✅ Coverage ≥ 90%

### Week 2 Goals
- ✅ Model tests complete
- ✅ Collaboration tests complete
- ✅ Coverage ≥ 94%

### Week 3 Goals
- ✅ Specialized agent tests complete
- ✅ Guardian tests complete
- ✅ Coverage ≥ 95%

### Week 4 Goals
- ✅ Error handling tests complete
- ✅ Edge case tests complete
- ✅ Coverage ≥ 98%
- ✅ CI/CD enforcement enabled

---

## Estimated Effort

| Phase | Tests | Developer Days | Calendar Days |
|-------|-------|---------------|---------------|
| P0 Critical | 100 | 3 days | 3 days |
| P1 High Value | 140 | 3 days | 3 days |
| P2 Nice to Have | 200 | 4 days | 4 days |
| Edge Cases | 140 | 2 days | 2 days |
| **TOTAL** | **580** | **12 days** | **2-3 weeks** |

**With 2 developers**: 1-1.5 weeks
**With automation/AI**: 3-5 days

---

## Quick Wins (Day 1)

To quickly boost coverage by 3-5%:

1. **Add health endpoint tests** (30 min)
   ```bash
   tests/test_api/test_health_endpoints.py
   ```

2. **Add webhook endpoint tests** (1 hour)
   ```bash
   tests/test_api/test_webhook_endpoints.py
   ```

3. **Add 5 model smoke tests** (2 hours)
   ```bash
   tests/test_models/test_user.py
   tests/test_models/test_squad.py
   tests/test_models/test_squad_member.py
   tests/test_models/test_task_execution.py
   tests/test_models/test_agent_message.py
   ```

4. **Add SSE service tests** (1 hour)
   ```bash
   tests/test_services/test_sse_service.py
   ```

**Total Time**: 4.5 hours
**Coverage Gain**: +3-5%
**New Coverage**: 88-90%

---

## Summary

### To reach 90%:
- Add P0 tests (100 tests, 3 days)
- Focus: API endpoints, core services, security

### To reach 95%:
- Add P0 + P1 tests (240 tests, 6 days)
- Focus: + models, collaboration patterns

### To reach 98%+:
- Add P0 + P1 + P2 + Edge (580 tests, 12 days)
- Focus: + specialized agents, error paths, edge cases

### To reach 100%:
- Add exhaustive edge cases, every error path
- Test generated code, utilities, config
- Not recommended (diminishing returns after 98%)

**Recommended Target**: **95%** (best balance of effort vs. quality)

---

## Next Steps

1. **Run coverage analysis** (today)
   ```bash
   pytest tests/ --cov=backend --cov-report=html
   ```

2. **Review HTML report** (today)
   ```bash
   open htmlcov/index.html
   ```

3. **Create P0 tests** (this week)
   - Start with quick wins
   - Focus on critical endpoints

4. **Implement CI enforcement** (next week)
   - Add coverage threshold
   - Enable PR checks

**Let me know if you want me to start creating the missing tests!** 🚀
