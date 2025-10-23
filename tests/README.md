# Integration Tests

This folder contains integration and end-to-end (E2E) tests for the Agent Squad project.

## Test Organization

### End-to-End Tests
- **test_mvp_e2e.py** - MVP end-to-end workflow tests
- **test_multi_turn_conversations_e2e.py** - Multi-turn conversation E2E tests
- **test_sse_streaming_e2e.py** - Server-Sent Events streaming E2E tests
- **test_analytics_e2e.py** - Analytics feature E2E tests

### Integration Tests

#### Message Bus & NATS
- **test_nats_integration.py** - NATS message bus integration tests
- **test_nats_demo.py** - NATS demonstration tests

#### Agent Features
- **test_agent_streaming.py** - Agent streaming functionality tests
- **test_demo_simple.py** - Simple agent demo tests

#### External Integrations
- **test_jira_direct.py** - Direct Jira API integration tests
- **test_jira_simple.py** - Simplified Jira integration tests
- **test_mcp_agent_integration.py** - MCP agent integration tests
- **test_mcp_tools_simple.py** - MCP tools simple tests

#### Streaming & SSE
- **test_sse_direct.py** - Direct SSE tests
- **test_phase2_context.py** - Phase 2 context management tests

#### Performance & Edge Cases
- **test_celery_timeout.py** - Celery task timeout tests

## Additional Test Suites

### Backend Unit Tests
Located in `/backend/tests/`:
- Unit tests for models, services, and agents
- API endpoint tests
- Security tests

See [backend/tests/README.md](../backend/tests/README.md) for details.

## Running Tests

### Run All Integration Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
# Example: Run multi-turn conversation tests
pytest tests/test_multi_turn_conversations_e2e.py -v

# Example: Run analytics tests
pytest tests/test_analytics_e2e.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

### Run Specific Test Function
```bash
pytest tests/test_mvp_e2e.py::test_create_squad -v
```

## Test Environment

### Prerequisites
1. **Database**: PostgreSQL running with test database
2. **Message Bus**: NATS server running (for NATS tests)
3. **Redis**: Redis server running (for caching tests)
4. **Environment**: `.env` file configured

### Environment Variables
```bash
# Test database
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agent_squad_test

# NATS
NATS_URL=nats://localhost:4222

# Redis
REDIS_URL=redis://localhost:6379
```

## Test Data

Tests use:
- Fixtures in test files
- Mock data generators
- Test database with isolated transactions
- In-memory message bus for unit tests

## CI/CD Integration

These tests are run in the CI/CD pipeline:
- On every pull request
- Before deployment to staging/production
- Nightly regression testing

## Writing New Tests

### Guidelines
1. Use descriptive test names (test_should_do_something_when_condition)
2. Follow AAA pattern: Arrange, Act, Assert
3. Clean up resources (use fixtures with cleanup)
4. Mock external services when appropriate
5. Add docstrings explaining complex test scenarios

### Example
```python
import pytest

@pytest.mark.asyncio
async def test_agent_should_stream_responses_when_enabled():
    """Test that agent streams responses when streaming is enabled."""
    # Arrange
    agent = create_test_agent(streaming=True)

    # Act
    responses = []
    async for chunk in agent.process("test message"):
        responses.append(chunk)

    # Assert
    assert len(responses) > 0
    assert responses[-1].is_final
```

## Troubleshooting

### Tests Failing?
1. Check services are running: `docker-compose ps`
2. Verify database migrations: `alembic current`
3. Check environment variables: `env | grep TEST_`
4. Run single test with verbose output: `pytest tests/test_name.py -vv`

### Slow Tests?
- Use `pytest -x` to stop on first failure
- Run specific test suites: `pytest tests/test_analytics_e2e.py`
- Check for database connection issues

## Documentation

- [RUN_TESTS.md](../RUN_TESTS.md) - Comprehensive testing guide
- [TEST_STATUS.md](../TEST_STATUS.md) - Current test status
- [Implementation Phases](../docs/implementation_phases/) - Phase-specific test requirements
