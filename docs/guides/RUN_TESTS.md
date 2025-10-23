# Running Tests - Quick Guide

## Prerequisites

1. **Docker Compose Running**: Ensure your Docker containers are up
   ```bash
   docker-compose ps
   ```
   You should see `postgres`, `redis`, and `backend` running.

2. **Test Database**: Tests use `agent_squad_test` database (automatically created)

---

## Quick Start - Run All Tests

```bash
# From project root - run all tests
docker exec agent-squad-backend pytest backend/tests/ -v

# With coverage report
docker exec agent-squad-backend pytest backend/tests/ --cov=backend --cov-report=term-missing
```

---

## Run Specific Test Suites

### 1. MessageBus Communication Tests (11 tests)
```bash
docker exec agent-squad-backend pytest backend/tests/test_agents/test_message_bus.py -v
```

**Tests**:
- Point-to-point messaging
- Broadcast messages
- Message metadata and task execution tracking
- Conversation history
- Subscriptions and real-time updates
- Message statistics
- Unread messages

### 2. Squad Service Tests (13 tests)
```bash
docker exec agent-squad-backend pytest backend/tests/test_services/test_squad_service.py -v
```

**Tests**:
- Squad CRUD operations
- Plan tier validation (starter: 3, pro: 10, enterprise: 50)
- Cost calculation by LLM model
- Squad ownership verification
- Squad with agents

### 3. Squad API Endpoint Tests (10 tests)
```bash
docker exec agent-squad-backend pytest backend/tests/test_api/test_squads_endpoints.py -v
```

**Tests**:
- REST API endpoints (GET, POST, PUT, DELETE)
- Authentication and authorization
- Access control (users can't access other users' squads)
- Cost estimation endpoint

### 4. Integration Tests (4 tests)
```bash
docker exec agent-squad-backend pytest backend/tests/test_integration/test_full_workflow.py -v
```

**Tests**:
- Complete squad setup workflow (register → squad → agents → verify)
- Squad member lifecycle (create → update → deactivate → reactivate → delete)
- Multi-squad management (3 teams with different compositions)
- Squad filtering by status

---

## Run Tests by Pattern

```bash
# Run tests matching "squad"
docker exec agent-squad-backend pytest backend/tests/ -k "squad" -v

# Run tests matching "message"
docker exec agent-squad-backend pytest backend/tests/ -k "message" -v

# Run tests matching "workflow"
docker exec agent-squad-backend pytest backend/tests/ -k "workflow" -v
```

---

## Run Single Test

```bash
# Run a specific test function
docker exec agent-squad-backend pytest backend/tests/test_agents/test_message_bus.py::test_send_message_point_to_point -v

# Another example
docker exec agent-squad-backend pytest backend/tests/test_api/test_squads_endpoints.py::test_create_squad -v
```

---

## Useful Options

### Stop on First Failure
```bash
docker exec agent-squad-backend pytest backend/tests/ -x
```

### Show Test Output (print statements)
```bash
docker exec agent-squad-backend pytest backend/tests/ -v -s
```

### Run with Coverage HTML Report
```bash
docker exec agent-squad-backend pytest backend/tests/ --cov=backend --cov-report=html

# View report (generated in htmlcov/ directory)
open htmlcov/index.html
```

### Show Slowest Tests
```bash
docker exec agent-squad-backend pytest backend/tests/ --durations=10
```

### Verbose Output with Test Details
```bash
docker exec agent-squad-backend pytest backend/tests/ -vv
```

---

## Test Output Examples

### Successful Test Run
```
backend/tests/test_agents/test_message_bus.py::test_send_message_point_to_point PASSED [  9%]
backend/tests/test_agents/test_message_bus.py::test_broadcast_message PASSED [ 18%]
...
================================ 30 passed in 12.34s ================================
```

### With Coverage
```
---------- coverage: platform darwin, python 3.11.7 -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend/agents/communication/message_bus.py    120      8    93%   45-47, 89
backend/services/squad_service.py              150     12    92%   67-69, 123-125
...
---------------------------------------------------------------------
TOTAL                                         2450    185    92%
```

---

## Troubleshooting

### Database Connection Errors
```bash
# Ensure PostgreSQL is running
docker-compose ps postgres

# Check if test database exists
docker exec agent-squad-postgres psql -U postgres -c "\l" | grep agent_squad_test

# If needed, create test database manually
docker exec agent-squad-postgres psql -U postgres -c "CREATE DATABASE agent_squad_test;"
```

### Import Errors
```bash
# Ensure backend container has all dependencies
docker exec agent-squad-backend pip list | grep pytest

# If needed, rebuild containers
docker-compose down
docker-compose up --build -d
```

### Test Database Not Cleaned Up
Tests automatically create and drop tables for each test function. If you encounter issues:
```bash
# Drop and recreate test database
docker exec agent-squad-postgres psql -U postgres -c "DROP DATABASE IF EXISTS agent_squad_test;"
docker exec agent-squad-postgres psql -U postgres -c "CREATE DATABASE agent_squad_test;"
```

---

## Running Tests Locally (Outside Docker)

If you want to run tests on your local machine instead of inside Docker:

1. **Set Test Database URL**:
   ```bash
   export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/agent_squad_test"
   ```

2. **Install Test Dependencies**:
   ```bash
   pip install pytest pytest-asyncio httpx
   ```

3. **Run Tests**:
   ```bash
   pytest backend/tests/ -v
   ```

---

## Test Statistics

- **Total Tests**: 30+
- **Unit Tests**: 15+ (MessageBus, services)
- **API Tests**: 10+ (REST endpoints with auth)
- **Integration Tests**: 4 (end-to-end workflows)
- **Coverage Goal**: 80%+ of critical paths

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `pytest backend/tests/` | Run all tests |
| `pytest backend/tests/ -v` | Run with verbose output |
| `pytest backend/tests/ -x` | Stop on first failure |
| `pytest backend/tests/ -k "squad"` | Run tests matching pattern |
| `pytest backend/tests/ --cov=backend` | Run with coverage |
| `pytest backend/tests/test_agents/` | Run specific test directory |
| `pytest backend/tests/test_api/test_squads_endpoints.py::test_create_squad` | Run single test |

---

## Next Steps

After running tests successfully:
1. Review coverage report to identify gaps
2. Add tests for any uncovered critical paths
3. Run tests in CI/CD pipeline
4. Keep tests passing as you add new features

For more details, see: `backend/tests/README.md`
