# Agent Squad Test Suite

Comprehensive test suite for the Agent Squad AI agent system.

## Test Structure

```
backend/tests/
├── test_agents/              # Agent system tests
│   └── test_message_bus.py   # MessageBus communication tests
├── test_services/            # Service layer tests
│   └── test_squad_service.py # Squad service tests
├── test_api/                 # API endpoint tests
│   └── test_squads_endpoints.py # Squad API tests
├── test_integration/         # Integration tests
│   └── test_full_workflow.py # End-to-end workflow tests
├── conftest.py              # Pytest fixtures and configuration
└── README.md                # This file
```

## Running Tests

### Prerequisites

1. **Docker Compose** - Tests run against a test database in Docker
2. **Python 3.11+** with pytest and dependencies installed

### Run All Tests

```bash
# From project root
pytest backend/tests/

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Verbose output
pytest backend/tests/ -v

# Stop on first failure
pytest backend/tests/ -x
```

### Run Specific Test Suites

```bash
# Agent communication tests
pytest backend/tests/test_agents/

# Service layer tests
pytest backend/tests/test_services/

# API endpoint tests
pytest backend/tests/test_api/

# Integration tests
pytest backend/tests/test_integration/
```

### Run Specific Test Files

```bash
# MessageBus tests
pytest backend/tests/test_agents/test_message_bus.py

# Squad service tests
pytest backend/tests/test_services/test_squad_service.py

# Squad API tests
pytest backend/tests/test_api/test_squads_endpoints.py

# Full workflow tests
pytest backend/tests/test_integration/test_full_workflow.py
```

### Run Specific Test Functions

```bash
# Run a single test
pytest backend/tests/test_agents/test_message_bus.py::test_send_message_point_to_point

# Run tests matching a pattern
pytest backend/tests/ -k "squad"
pytest backend/tests/ -k "message"
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage of core logic
- **Integration Tests**: Cover critical workflows
- **API Tests**: All endpoints tested with auth/validation

## Test Categories

### Unit Tests

Test individual components in isolation:
- MessageBus communication
- Service layer logic
- Agent capabilities
- Workflow state machine
- Delegation engine

### Integration Tests

Test multiple components working together:
- Full squad setup workflow
- Squad member lifecycle
- Multi-squad management
- Task execution flow
- Agent collaboration patterns

### API Tests

Test REST API endpoints:
- Authentication and authorization
- CRUD operations
- Filtering and pagination
- Error handling
- Access control

## Fixtures

Common test fixtures available in `conftest.py`:

- `test_db` - Fresh database for each test
- `client` - Async HTTP test client
- `test_user_data` - Test user credentials
- `test_user_data_2` - Second test user credentials

## Writing New Tests

### Example Unit Test

```python
import pytest
from uuid import uuid4

@pytest.mark.asyncio
async def test_my_feature(test_db):
    """Test my feature"""
    # Arrange
    user_id = uuid4()

    # Act
    result = await my_function(test_db, user_id)

    # Assert
    assert result is not None
    assert result.status == "success"
```

### Example API Test

```python
import pytest

@pytest.mark.asyncio
async def test_my_endpoint(client, test_user_data):
    """Test my API endpoint"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]

    # Test endpoint
    response = await client.get(
        "/api/v1/my-endpoint",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "expected_field" in response.json()
```

### Example Integration Test

```python
import pytest

@pytest.mark.asyncio
async def test_complete_workflow(client, test_user_data):
    """Test complete end-to-end workflow"""
    # Step 1: Setup
    # ... register, login, create squad

    # Step 2: Add agents
    # ... create agents with different roles

    # Step 3: Execute task
    # ... start task execution

    # Step 4: Verify results
    # ... check execution completed successfully
```

## Test Database

Tests use a separate test database to avoid affecting development data:

- **URL**: `postgresql+asyncpg://postgres:postgres@postgres:5432/agent_squad_test`
- **Lifecycle**: Fresh database for each test function
- **Cleanup**: Automatic rollback after each test

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Manual workflow dispatch

CI configuration: `.github/workflows/test.yml`

## Troubleshooting

### Database Connection Issues

```bash
# Ensure Docker containers are running
docker-compose up -d

# Check database is accessible
docker-compose ps
```

### Import Errors

```bash
# Ensure PYTHONPATH includes backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run tests from project root
cd /path/to/agent-squad
pytest backend/tests/
```

### Slow Tests

```bash
# Run in parallel with pytest-xdist
pytest backend/tests/ -n auto

# Run only fast tests
pytest backend/tests/ -m "not slow"
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_expensive_operation():
    """Test that takes a long time"""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Integration test"""
    pass

@pytest.mark.unit
def test_isolated_component():
    """Unit test"""
    pass
```

Run specific markers:
```bash
pytest backend/tests/ -m "unit"
pytest backend/tests/ -m "integration"
pytest backend/tests/ -m "not slow"
```

## Code Coverage

Generate coverage reports:

```bash
# HTML report
pytest backend/tests/ --cov=backend --cov-report=html
open htmlcov/index.html

# Terminal report
pytest backend/tests/ --cov=backend --cov-report=term

# XML report (for CI)
pytest backend/tests/ --cov=backend --cov-report=xml
```

## Test Statistics

Current test suite stats:

- **Total Tests**: 30+
- **Unit Tests**: 15+
- **Integration Tests**: 10+
- **API Tests**: 10+
- **Coverage**: ~80%

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures for setup and teardown
3. **Assertions**: Be specific with assertions
4. **Documentation**: Write clear docstrings
5. **Speed**: Keep tests fast (< 1s per test)
6. **Reliability**: Tests should not be flaky
7. **Coverage**: Aim for 80%+ coverage of critical paths

## Contributing

When adding new features, please:
1. Write tests for new functionality
2. Ensure all existing tests pass
3. Maintain or improve code coverage
4. Document test scenarios in docstrings
5. Follow existing test patterns and structure
