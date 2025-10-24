# Tests Module

## Overview

Comprehensive test suite for Agent Squad backend covering unit tests, integration tests, API tests, and end-to-end workflows.

## Test Structure

```
tests/
├── conftest.py                  # Global test fixtures
├── test_security.py             # Security tests
│
├── test_agents/                 # Agent module tests
│   ├── test_message_bus.py
│   ├── test_history_manager.py
│   ├── test_context_manager.py
│   ├── test_rag_service.py
│   ├── test_memory_store.py
│   ├── test_routing_engine.py
│   ├── test_conversation_manager.py
│   ├── test_escalation_service.py
│   └── test_workflow_engine.py
│
├── test_api/                    # API endpoint tests
│   ├── test_auth.py
│   ├── test_squads.py
│   ├── test_tasks.py
│   └── test_executions.py
│
├── test_models/                 # Database model tests
│   ├── test_user.py
│   ├── test_squad.py
│   ├── test_conversation.py
│   └── test_task_execution.py
│
├── test_services/               # Service layer tests
│   ├── test_agent_service.py
│   ├── test_squad_service.py
│   ├── test_auth_service.py
│   └── test_task_execution_service.py
│
├── test_integration/            # Integration tests
│   ├── test_full_workflow.py
│   ├── test_ticket_to_pr.py
│   └── test_real_atlassian.py
│
└── test_mcp/                    # MCP integration tests
    └── test_mcp_client.py
```

## Test Categories

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (<1s per test)
- Isolated from database/network

### Integration Tests
- Test component interactions
- Use test database
- Real message bus (in-memory)
- Medium execution time (1-5s)

### API Tests
- Test FastAPI endpoints
- Use TestClient
- Authentication/authorization
- Request/response validation

### End-to-End Tests
- Test complete workflows
- Real database interactions
- Agent message flows
- Slow execution (10-60s)

## Running Tests

### All Tests
```bash
pytest backend/tests -v
```

### Specific Category
```bash
pytest backend/tests/test_agents -v           # Agent tests
pytest backend/tests/test_api -v              # API tests
pytest backend/tests/test_integration -v      # Integration tests
```

### With Coverage
```bash
pytest backend/tests --cov=backend --cov-report=html
```

### Single Test
```bash
pytest backend/tests/test_agents/test_message_bus.py::test_send_message -v
```

## Key Test Fixtures

### Database Fixtures (`conftest.py`)
```python
@pytest.fixture
async def db_session():
    """Async database session for tests"""
    # Creates test database
    # Yields session
    # Cleans up after test

@pytest.fixture
async def squad(db_session):
    """Create test squad"""

@pytest.fixture
async def squad_member(db_session, squad):
    """Create test squad member"""
```

### Agent Fixtures
```python
@pytest.fixture
def mock_llm_response():
    """Mock LLM API response"""

@pytest.fixture
def agno_agent(squad_member):
    """Create Agno agent for testing"""
```

## Writing Tests

### Example Unit Test
```python
@pytest.mark.asyncio
async def test_create_squad_member(db_session, squad):
    member = await AgentService.create_squad_member(
        db=db_session,
        squad_id=squad.id,
        role="backend_developer"
    )

    assert member.id is not None
    assert member.role == "backend_developer"
```

### Example Integration Test
```python
@pytest.mark.asyncio
async def test_agent_question_answer_flow(db_session, squad):
    # Create agents
    backend_dev = await create_squad_member(role="backend_developer")
    tech_lead = await create_squad_member(role="tech_lead")

    # Setup routing
    await setup_routing_rules(squad.id)

    # Backend dev asks question
    conversation = await initiate_question(
        asker_id=backend_dev.id,
        question="How to implement caching?"
    )

    # Verify routing
    assert conversation.current_responder_id == tech_lead.id
```

## Test Configuration

### Environment Variables
```bash
TEST_DATABASE_URL=postgresql://localhost/agent_squad_test
PYTHONPATH=/path/to/agent-squad
```

### Pytest Configuration (`pytest.ini`)
```ini
[pytest]
asyncio_mode = auto
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Test Coverage

Target: 80%+ coverage

Current coverage by module:
- Core: 85%
- Services: 80%
- Agents: 75%
- API: 90%
- Models: 85%

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Commits to main
- Nightly builds

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pytest backend/tests --cov=backend --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

1. **Arrange-Act-Assert** pattern
2. **One assertion per test** (when possible)
3. **Clear test names** (describe what is tested)
4. **Use fixtures** for setup
5. **Mock external services** (LLM APIs, external APIs)
6. **Clean up after tests**
7. **Test edge cases** and error conditions

## Related Documentation

- See `../core/CLAUDE.md` for core module
- See `../services/CLAUDE.md` for services
- See `../agents/CLAUDE.md` for agent architecture
