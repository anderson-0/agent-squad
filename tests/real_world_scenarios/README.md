# Real-World Scenario Test Suite

Comprehensive test suite for validating agent capabilities and identifying tool gaps through realistic software development scenarios.

## Overview

This test suite contains 10 real-world scenarios that simulate actual software development workflows. Each scenario tests specific agent capabilities and helps identify which tools agents need to complete real work.

## Scenarios

### 1. Bug Fix with Root Cause Analysis
**Duration:** ~30 minutes
**Tests:** Investigation, debugging, fixing race conditions
**Key Tools:** Log analysis, debugger, Redis inspection, code editing

### 2. REST API Endpoint Implementation
**Duration:** ~45 minutes
**Tests:** API development, validation, testing, frontend integration
**Key Tools:** File operations, API testing, schema validation, test runner

### 3. Third-Party API Integration
**Duration:** ~60 minutes
**Tests:** External API integration, webhooks, secrets management
**Key Tools:** HTTP requests, package installation, webhook testing, secret management

### 4. Database Schema Migration
**Duration:** ~40 minutes
**Tests:** Schema design, data migration, rollback
**Key Tools:** Database operations, Alembic, SQL queries, schema inspection

### 5. Performance Optimization
**Duration:** ~90 minutes
**Tests:** Profiling, query optimization, caching, bundle analysis
**Key Tools:** Profiler, query analyzer, benchmarking, load testing

### 6. Security Vulnerability Remediation
**Duration:** ~60 minutes
**Tests:** Security scanning, vulnerability fixes, penetration testing
**Key Tools:** Security scanners (bandit, safety), SAST, penetration testing

### 7. Legacy Code Refactoring
**Duration:** ~120 minutes
**Tests:** Code analysis, refactoring, dependency management
**Key Tools:** Code metrics, dependency graphs, refactoring tools

### 8. CI/CD Pipeline Setup
**Duration:** ~90 minutes
**Tests:** GitHub Actions, testing in CI, deployment automation
**Key Tools:** YAML editing, CI configuration, Docker build, secrets management

### 9. Documentation Generation
**Duration:** ~150 minutes
**Tests:** OpenAPI generation, guide writing, diagram creation
**Key Tools:** OpenAPI generator, Markdown editing, diagram tools, doc hosting

### 10. Multi-Service Feature Implementation
**Duration:** ~240 minutes
**Tests:** Microservices, message queues, service orchestration
**Key Tools:** Service creation, NATS configuration, distributed tracing

## Quick Start

### Prerequisites

1. **Agent-Squad running:**
   ```bash
   ./scripts/setup.sh
   ```

2. **All services healthy:**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000
   - PostgreSQL, Redis, NATS all running

### Run All Scenarios

```bash
# From project root
python run_real_world_scenarios.py
```

### Run Specific Scenarios

```bash
# Run scenarios 1, 2, and 3
python run_real_world_scenarios.py --scenarios 1 2 3
```

### Generate Reports

```bash
# Save JSON report
python run_real_world_scenarios.py --json-output results.json

# Generate HTML report
python run_real_world_scenarios.py --html-report

# Both
python run_real_world_scenarios.py --json-output results.json --html-report
```

## Test Architecture

### Base Framework

**`base_scenario.py`** - Base class for all scenarios

Key features:
- Scenario lifecycle management (setup → run → validate → teardown)
- Metrics tracking (timing, quality score, tool usage)
- Step-by-step execution with error handling
- Tool usage monitoring
- Success criteria validation

### Scenario Structure

Each scenario implements:

```python
class MyScenario(BaseScenario):
    async def setup_scenario(self):
        # Create squad, define success criteria
        pass

    async def run_scenario(self):
        # Execute workflow steps
        # Track tool usage
        # Monitor progress
        pass

    async def validate_results(self) -> bool:
        # Check if scenario succeeded
        return success

    def get_expected_tools(self) -> List[str]:
        # List tools needed for this scenario
        return ["tool1", "tool2", ...]
```

### Metrics Collected

For each scenario:
- **Timing:** Start, end, duration
- **Status:** Completed, partial, failed, timeout
- **Quality Score:** 0-100 based on success criteria and completion
- **Steps:** Completed vs total
- **Tool Usage:** Which tools used, which missing
- **Errors:** All errors encountered
- **Agent Activity:** Which agents involved, messages sent

### Tool Gap Identification

The test suite automatically identifies:
- **Available tools:** Tools that exist and were used successfully
- **Missing tools:** Tools needed but not available
- **Failed tools:** Tools that exist but failed
- **Unused tools:** Tools available but not used

## Understanding Reports

### Console Output

Real-time progress with color-coded status:
- 🔵 **Blue (→):** Information
- 🟢 **Green (✓):** Success
- 🟡 **Yellow (◐):** Partial completion
- 🔴 **Red (✗):** Failure

### JSON Report

Detailed machine-readable results:
```json
{
  "test_run": {
    "started_at": "...",
    "completed_at": "...",
    "scenarios_run": 10
  },
  "results_summary": {
    "completed": 7,
    "partial": 2,
    "failed": 1,
    "completion_rate": 70,
    "avg_quality_score": 75.3
  },
  "tool_analysis": {
    "total_tools_needed": 85,
    "total_tools_used": 20,
    "total_tools_missing": 65,
    "most_missing_tools": [...]
  },
  "scenarios": [...]
}
```

### HTML Report

Visual report with:
- Results overview (metrics cards)
- Scenario results table
- Missing tools analysis with priority
- Color-coded for quick scanning

## Success Criteria

### Overall Suite

- **Target Completion Rate:** >80% of scenarios complete
- **Target Quality Score:** >75/100 average
- **Target Tool Availability:** >60% of needed tools available

### Individual Scenarios

Each scenario defines specific success criteria:
- Root cause identified
- Fix implemented
- Tests pass
- Feature works end-to-end

## Tool Priority Classification

Based on test results:

### Critical (Needed in 5+ scenarios)
Tools absolutely required for most workflows.
**Priority:** Implement immediately

### High (Needed in 3-4 scenarios)
Tools needed for common tasks.
**Priority:** Implement within 2 weeks

### Medium (Needed in 1-2 scenarios)
Specialized tools for specific use cases.
**Priority:** Implement as needed

## Development Workflow

### Adding New Scenarios

1. Create new scenario file in `tests/real_world_scenarios/`
2. Extend `BaseScenario` class
3. Implement required methods
4. Add to runner in `run_real_world_scenarios.py`

Example:
```python
from .base_scenario import BaseScenario

class MyNewScenario(BaseScenario):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "My New Scenario"
        self.expected_duration_minutes = 60

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "My Squad",
            ["project_manager", "backend_developer"]
        )
        self.add_success_criterion("Task completed")

    async def run_scenario(self):
        # Implement workflow
        pass

    async def validate_results(self) -> bool:
        return True

    def get_expected_tools(self) -> List[str]:
        return ["tool1", "tool2"]
```

### Running During Development

```bash
# Run just your new scenario
python run_real_world_scenarios.py --scenarios 11

# Run with verbose output
python run_real_world_scenarios.py --scenarios 11 -v
```

## Troubleshooting

### Scenarios Timeout

**Problem:** Scenarios don't complete within timeout

**Solutions:**
- Increase timeout in scenario constructor
- Check if API is responding
- Verify all services are healthy
- Check agent execution logs

### High Tool Missing Rate

**Problem:** Many tools marked as missing

**Expected:** This is normal! The test suite is designed to identify tool gaps.

**Next Steps:**
1. Review "most_missing_tools" in report
2. Prioritize by frequency
3. Implement high-priority tools first
4. Re-run tests to validate

### Tests Fail to Start

**Problem:** Scenarios fail during setup

**Solutions:**
- Verify API is accessible: `curl http://localhost:8000/api/v1/health`
- Check database is running: `docker-compose ps postgres`
- Ensure migrations ran: `docker-compose logs backend`
- Verify environment variables set correctly

## Best Practices

### When Running Tests

1. **Clean State:** Run on fresh deployment
2. **No Manual Changes:** Don't modify data during test run
3. **Full Suite:** Run all scenarios together for accurate tool analysis
4. **Regular Cadence:** Run weekly to track improvements

### When Adding Tools

1. **High Impact First:** Implement tools needed in 5+ scenarios
2. **Test Immediately:** Re-run scenarios after adding tool
3. **Document:** Update tool documentation
4. **Track Progress:** Save reports to compare before/after

### When Debugging

1. **Check Logs:** Review agent execution logs
2. **Isolate:** Run single scenario to debug
3. **Step Through:** Review step-by-step execution
4. **Validate Setup:** Ensure test environment is correct

## Metrics Guide

### Quality Score Calculation

Quality score (0-100) is calculated as:
- **60%** - Success criteria met
- **30%** - Completion percentage
- **10%** - Error penalty

Example:
- 4/5 success criteria met = 48 points
- 90% steps completed = 27 points
- 1 error = -2 points
- **Total: 73/100**

### Completion Rate

Percentage of scenarios that fully completed:
- **>80%:** Excellent - Ready for production
- **60-80%:** Good - Most workflows work
- **40-60%:** Fair - Core functionality works
- **<40%:** Poor - Many tool gaps

### Tool Availability Rate

Percentage of needed tools that are available:
- **>80%:** Excellent - Few tool gaps
- **60-80%:** Good - Some gaps but workable
- **40-60%:** Fair - Many gaps, limited capability
- **<40%:** Poor - Major tool gaps

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Real-World Scenario Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:  # Manual trigger

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for healthy
        run: ./scripts/wait-for-healthy.sh

      - name: Run scenarios
        run: |
          python run_real_world_scenarios.py \
            --json-output results.json \
            --html-report

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: scenario-results
          path: |
            results.json
            scenario_report.html

      - name: Check success rate
        run: |
          RATE=$(jq -r '.results_summary.completion_rate' results.json)
          if [ $(echo "$RATE < 80" | bc) -eq 1 ]; then
            echo "Completion rate below 80%: $RATE%"
            exit 1
          fi
```

## Roadmap

### Phase 1: Core Tools (Week 1-2)
- Code execution (Python, JS)
- Git operations (clone, commit, push)
- Database queries (SQL, migrations)
- HTTP requests (API testing)

### Phase 2: Testing & Performance (Week 3-4)
- Test runner (pytest, jest)
- Code coverage
- Profiling & benchmarking
- Load testing

### Phase 3: Advanced Tools (Week 5-6)
- Security scanning
- Documentation generation
- CI/CD configuration
- Docker operations

## Contributing

To improve the test suite:

1. Add more realistic scenarios
2. Improve metrics collection
3. Add more detailed validation
4. Enhance reporting
5. Add CI/CD integration

## Support

For questions or issues:
- Review scenario code in `tests/real_world_scenarios/`
- Check base framework in `base_scenario.py`
- Review runner code in `run_real_world_scenarios.py`
- Open GitHub issue with scenario results attached

---

**Last Updated:** November 7, 2025
**Version:** 1.0.0
**Status:** Production Ready
