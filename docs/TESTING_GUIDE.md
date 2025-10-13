# Testing Guide

This guide explains how to test the Agent Squad application at various levels.

## Phase 1 Foundation Testing

Phase 1 testing focuses on verifying that the infrastructure and foundation are working correctly.

### Manual Verification Steps

#### 1. Start All Services

```bash
cd agent-squad
docker-compose up
```

**Expected Result**: All 4 services should start successfully:
- `agent-squad-postgres` - PostgreSQL database
- `agent-squad-redis` - Redis cache
- `agent-squad-backend` - FastAPI backend
- `agent-squad-frontend` - Next.js frontend

Look for these log messages:
```
agent-squad-backend   | 🚀 Agent Squad started in development mode
agent-squad-frontend  | ✓ Ready in 3s
```

#### 2. Verify Service Health

Run the verification script:
```bash
./scripts/verify-setup.sh
```

**Expected Output**:
```
✓ docker is installed
✓ node is installed
✓ python3 is installed
✓ PostgreSQL container is running
✓ Redis container is running
✓ Backend container is running
✓ Frontend container is running
✓ Backend Health Check is running at http://localhost:8000/health
✓ Backend API Docs is running at http://localhost:8000/docs
✓ Frontend is running at http://localhost:3000
✓ PostgreSQL is accepting connections
✓ Redis is responding to PING
```

#### 3. Test Backend Endpoints

Open a browser or use curl:

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "0.1.0"
}
```

**API Documentation:**
```bash
open http://localhost:8000/docs
```

Should display interactive Swagger UI.

**Root Endpoint:**
```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Welcome to Agent Squad",
  "docs": "/docs",
  "health": "/health"
}
```

#### 4. Test Frontend

Open in browser:
```bash
open http://localhost:3000
```

**Expected Result**: Landing page should display with:
- "Agent Squad" heading
- Three feature cards
- "Get Started" and "API Documentation" buttons
- Proper Tailwind CSS styling

#### 5. Test Database Connection

```bash
cd backend
prisma studio
```

**Expected Result**: Prisma Studio should open at http://localhost:5555 showing the database schema with empty tables.

#### 6. Test Redis Connection

```bash
docker exec agent-squad-redis redis-cli ping
```

**Expected Output:**
```
PONG
```

#### 7. Check Service Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f backend
```

**Look for**:
- No error messages
- Successful database connections
- Successful Redis connections
- Hot reload messages when you change files

#### 8. Test Hot Reload

**Backend:**
1. Edit `backend/core/app.py`
2. Add a comment or change a string
3. Watch backend logs for "Application startup complete" message

**Frontend:**
1. Edit `frontend/app/page.tsx`
2. Change the heading text
3. Browser should automatically refresh

### Automated Testing

Currently, Phase 1 has no business logic to test, but the testing infrastructure is in place.

#### Backend Tests (when written)

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run with output
pytest -v -s
```

#### Frontend Tests (when written)

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm test -- --coverage
```

### CI/CD Testing

GitHub Actions will automatically run tests on every push and pull request.

#### Trigger CI Locally

You can validate the GitHub Actions workflows locally using `act`:

```bash
# Install act
brew install act

# Run backend CI
act -W .github/workflows/backend-ci.yml

# Run frontend CI
act -W .github/workflows/frontend-ci.yml
```

### Integration Testing (Future)

Phase 2+ will include integration tests:

- API endpoint tests
- Database transaction tests
- Authentication flow tests
- Payment flow tests
- Agent communication tests

### Performance Testing (Future)

Phase 8 will include:

- Load testing with Locust
- Database query optimization
- API response time benchmarks
- Frontend performance metrics

## Common Issues & Solutions

### Services Won't Start

```bash
# Check for port conflicts
lsof -i :3000
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Stop and remove all containers
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up
```

### Backend Database Error

```bash
# Ensure PostgreSQL is ready
docker-compose logs postgres

# Regenerate Prisma client
cd backend
prisma generate
prisma db push
```

### Frontend Build Error

```bash
# Clear caches and reinstall
cd frontend
rm -rf node_modules .next
npm install
```

### Docker Out of Space

```bash
# Clean up Docker
docker system prune -a --volumes
```

## Test Coverage Goals

Phase 2+ will aim for:
- **Backend**: 80%+ code coverage
- **Frontend**: 70%+ code coverage
- **Integration**: All critical paths covered
- **E2E**: All user flows covered

## Next Steps

Once Phase 1 verification passes, you're ready to:

1. Move to Phase 2: Authentication & Payments
2. Start writing actual business logic tests
3. Implement first API endpoints
4. Create first UI components

See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for Phase 2 details.
