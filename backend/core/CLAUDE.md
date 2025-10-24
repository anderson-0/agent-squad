# Core Module

## Overview

The `core/` module contains foundational infrastructure and configuration for the entire Agent Squad application. It provides essential services like application setup, database management, configuration, authentication, security, and logging.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Core Module                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application (app.py)              │  │
│  │  - Application lifecycle                               │  │
│  │  - Middleware setup                                    │  │
│  │  - Health checks                                       │  │
│  └───────┬──────────────────────┬─────────────────────────┘  │
│          │                      │                             │
│          ▼                      ▼                             │
│  ┌──────────────┐      ┌────────────────────┐               │
│  │ Config       │      │    Database        │               │
│  │ (Settings)   │─────▶│  (SQLAlchemy)      │               │
│  │              │      │  - Async + Sync    │               │
│  └───────┬──────┘      │  - PostgreSQL      │               │
│          │             └────────────────────┘               │
│          │                                                   │
│          ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             Supporting Services                       │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  - Agno Config (agno_config.py)                      │   │
│  │  - Auth (auth.py)                                    │   │
│  │  - Security (security.py)                            │   │
│  │  - Logging (logging.py)                              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `config.py` - Application Configuration

**Purpose**: Centralized configuration management using Pydantic Settings

**Key Components**:
- `Settings`: Main configuration class
- Environment variable loading
- Type validation
- Default values

**Configuration Categories**:

#### Application Settings
```python
ENV: str = "development"
DEBUG: bool = True
APP_NAME: str = "Agent Squad"
API_V1_PREFIX: str = "/api/v1"
```

#### Database Settings
```python
DATABASE_URL: str  # Required
REDIS_URL: str = "redis://localhost:6379/0"
```

#### Security Settings
```python
SECRET_KEY: str  # Required
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

#### LLM Provider API Keys
```python
OPENAI_API_KEY: str = ""  # Optional
ANTHROPIC_API_KEY: str = ""  # Optional
```

#### Vector Database (Pinecone)
```python
PINECONE_API_KEY: str = ""  # Optional
PINECONE_ENVIRONMENT: str = ""
PINECONE_INDEX_NAME: str = "agent-squad"
```

#### Message Bus (NATS)
```python
MESSAGE_BUS: str = "nats"  # Default: NATS (production)
NATS_URL: str = "nats://localhost:4222"
NATS_STREAM_NAME: str = "agent-messages"
NATS_MAX_MSGS: int = 1_000_000  # 1M messages
NATS_MAX_AGE_DAYS: int = 7  # 7 days retention
NATS_CONSUMER_NAME: str = "agent-processor"
```

#### Feature Flags
```python
USE_AGNO_AGENTS: bool = True  # Deprecated: Agno is now the only implementation
ENABLE_WEBHOOKS: bool = True
ENABLE_METRICS: bool = True
```

**Usage**:
```python
from backend.core.config import settings

# Access configuration
database_url = settings.DATABASE_URL
is_debug = settings.DEBUG
allowed_origins = settings.get_allowed_origins()
```

**Environment Variables**:
Configuration loaded from `.env` file:
```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_squad
SECRET_KEY=your-secret-key-here

# Optional (with defaults)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
REDIS_URL=redis://localhost:6379/0
NATS_URL=nats://localhost:4222
```

**Location**: `backend/core/config.py:1`

---

### 2. `agno_config.py` - Agno Framework Configuration ⭐ NEW

**Purpose**: Configuration and initialization for the Agno framework (enterprise-grade multi-agent system)

**Key Components**:
- `AgnoConfig`: Singleton configuration manager
- `get_agno_config()`: Dependency injection function
- `get_agno_db()`: Database accessor
- `AgnoContext`: Context manager for resource cleanup
- `initialize_agno()`: Application startup hook
- `shutdown_agno()`: Application shutdown hook

**Design Patterns**:
- Singleton Pattern: Single config instance
- Factory Pattern: Database creation
- Lazy Initialization: Database created on first use
- Dependency Injection: Service locator pattern
- Context Manager: Resource lifecycle management

**Database Configuration**:
```python
db = PostgresDb(
    db_url=settings.DATABASE_URL,
    # Custom table names for namespacing
    session_table="agno_sessions",    # Agent session storage
    culture_table="agno_culture",     # Agent culture/configuration
    memory_table="agno_memory",       # Agent memory storage
    metrics_table="agno_metrics",     # Performance metrics
    eval_table="agno_eval",           # Evaluation results
    knowledge_table="agno_knowledge", # Knowledge base
)
```

**Usage Patterns**:

#### Basic Usage
```python
from backend.core.agno_config import get_agno_db

# Get database instance
db = get_agno_db()

# Create agent with Agno database
agent = Agent(
    agent_id="agent-123",
    role="backend_developer",
    db=db
)
```

#### Context Manager (Recommended)
```python
from backend.core.agno_config import AgnoContext

async with AgnoContext() as db:
    agent = Agent(agent_id="...", db=db)
    response = await agent.process_message("Hello")
```

#### Application Lifecycle
```python
from backend.core.agno_config import initialize_agno, shutdown_agno

# In FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_agno()  # Initialize Agno framework
    yield
    # Shutdown
    shutdown_agno()  # Clean up connections
```

**Health Check**:
```python
from backend.core.agno_config import get_agno_config

config = get_agno_config()
is_healthy = config.health_check()  # Returns True/False
```

**Key Features**:
- ✅ Automatic table creation (Agno creates tables on first use)
- ✅ Connection pooling (handled by SQLAlchemy)
- ✅ Singleton pattern (one database instance)
- ✅ Health checks (database connectivity)
- ✅ Proper cleanup (connection disposal)

**Agno Tables**:
| Table | Purpose |
|-------|---------|
| `agno_sessions` | Agent session state and history |
| `agno_memory` | Agent memory and context |
| `agno_culture` | Agent configuration and culture |
| `agno_metrics` | Performance metrics |
| `agno_eval` | Evaluation results |
| `agno_knowledge` | Knowledge base |

**Location**: `backend/core/agno_config.py:1`

---

### 3. `database.py` - Database Connection Management

**Purpose**: SQLAlchemy database connection with async and sync support

**Architecture**:
- **Primary**: Async (asyncpg driver) for FastAPI endpoints
- **Secondary**: Sync (psycopg2 driver) for migrations and scripts

**Async Database** (Primary):

```python
from backend.core.database import get_db, AsyncSession
from fastapi import Depends

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

**Async Context Manager**:
```python
from backend.core.database import get_db_context

async with get_db_context() as db:
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
```

**Sync Database** (Compatibility):

```python
from backend.core.database import get_sync_db_context

# For Alembic migrations and scripts
with get_sync_db_context() as db:
    user = db.query(User).filter(User.email == email).first()
```

**Configuration**:
- Connection pool: 5 connections
- Max overflow: 10 additional connections
- Pool pre-ping: Verify connections before use
- Echo SQL: Enabled in DEBUG mode

**Lifecycle Functions**:
```python
# Application startup
await init_db()  # Create all tables

# Application shutdown
await close_db()  # Dispose connections
```

**Location**: `backend/core/database.py:1`

---

### 4. `app.py` - FastAPI Application

**Purpose**: Main FastAPI application setup and configuration

**Key Components**:
- FastAPI app instance
- Lifespan management (startup/shutdown)
- Middleware configuration
- Health checks
- Metrics endpoint

**Application Lifecycle**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await init_db()
    print(f"🚀 {settings.APP_NAME} started")

    yield

    # Shutdown
    await close_db()
    print("👋 Application shutdown complete")
```

**Middleware Stack**:
1. **CORS**: Cross-origin resource sharing
   - Configurable origins
   - Credentials support
   - All methods/headers allowed
2. **GZip**: Response compression
   - Minimum size: 1000 bytes
3. **Prometheus**: Metrics collection (if enabled)
   - Endpoint: `/metrics`

**Key Endpoints**:
- `/` - Root endpoint (welcome message)
- `/health` - Health check
- `/docs` - OpenAPI docs (DEBUG only)
- `/redoc` - ReDoc documentation (DEBUG only)
- `/metrics` - Prometheus metrics (if enabled)
- `/api/v1/*` - API routes

**Usage**:
```bash
# Run application
uvicorn backend.core.app:app --reload

# Access
http://localhost:8000/docs       # OpenAPI docs
http://localhost:8000/health     # Health check
http://localhost:8000/metrics    # Prometheus metrics
```

**Location**: `backend/core/app.py:1`

---

### 5. `auth.py` - Authentication

**Purpose**: JWT-based authentication for API endpoints

**Key Functions**:
- Token generation (access + refresh)
- Token verification
- Password hashing (bcrypt)
- User authentication

**Usage**:
```python
from backend.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password
)

# Generate tokens
access_token = create_access_token(data={"sub": user.email})
refresh_token = create_refresh_token(data={"sub": user.email})

# Verify token
payload = verify_token(token)

# Password management
hashed = hash_password("password123")
is_valid = verify_password("password123", hashed)
```

**Security Features**:
- JWT with HS256 algorithm
- Configurable token expiration
- Bcrypt password hashing (cost factor: 12)
- Secure token validation

**Configuration**:
- Access token: 30 minutes (configurable)
- Refresh token: 7 days (configurable)
- Algorithm: HS256
- Secret key: From environment

**Location**: `backend/core/auth.py:1`

---

### 6. `security.py` - Security Utilities

**Purpose**: Security helper functions and middleware

**Key Functions**:
- API key validation
- Rate limiting helpers
- CORS configuration
- Input sanitization
- Security headers

**Usage**:
```python
from backend.core.security import (
    validate_api_key,
    sanitize_input,
    get_security_headers
)

# Validate API key
is_valid = validate_api_key(api_key)

# Sanitize user input
safe_input = sanitize_input(user_input)

# Security headers
headers = get_security_headers()
```

**Security Best Practices**:
- HTTPS in production
- Secure cookies (httponly, secure, samesite)
- Content Security Policy (CSP)
- XSS protection
- CSRF protection for state-changing operations

**Location**: `backend/core/security.py:1`

---

### 7. `logging.py` - Logging Configuration

**Purpose**: Structured logging configuration

**Features**:
- JSON logging in production
- Pretty logging in development
- Configurable log levels
- Request/response logging
- Performance metrics logging

**Setup**:
```python
from backend.core.logging import setup_logging

# Called at application startup
setup_logging()
```

**Log Levels** (from `settings.LOG_LEVEL`):
- `DEBUG`: Detailed development information
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical failures

**Log Format**:
- **Production** (JSON): Structured logs for aggregation
- **Development** (Pretty): Human-readable colored logs

**Usage**:
```python
import logging

logger = logging.getLogger(__name__)

logger.info("User logged in", extra={"user_id": user.id})
logger.error("Failed to process request", extra={"error": str(e)})
```

**Integration**:
- FastAPI request logging
- SQLAlchemy query logging (DEBUG mode)
- Uvicorn access logs
- Custom application logs

**Location**: `backend/core/logging.py:1`

---

## Module Dependencies

### Internal Dependencies
```python
# Core depends on:
- backend.models.base      # Database models
- backend.api.v1.router    # API routes
```

### External Dependencies
```python
# Main libraries:
- fastapi                  # Web framework
- pydantic-settings        # Configuration
- sqlalchemy[asyncio]      # Database ORM
- asyncpg                  # Async PostgreSQL driver
- psycopg2-binary         # Sync PostgreSQL driver
- python-jose[cryptography] # JWT tokens
- passlib[bcrypt]         # Password hashing
- prometheus-client       # Metrics
- agno                    # Multi-agent framework ⭐
```

---

## Configuration Checklist

### Required Environment Variables
```bash
✅ DATABASE_URL=postgresql://user:pass@localhost:5432/agent_squad
✅ SECRET_KEY=your-secret-key-minimum-32-chars
```

### Optional (Production)
```bash
⚪ OPENAI_API_KEY=sk-...
⚪ ANTHROPIC_API_KEY=...
⚪ PINECONE_API_KEY=...
⚪ REDIS_URL=redis://localhost:6379/0
⚪ NATS_URL=nats://localhost:4222
⚪ SENTRY_DSN=https://...
⚪ STRIPE_SECRET_KEY=sk_...
```

### Feature Flags
```bash
ENV=production
DEBUG=false
ENABLE_METRICS=true
ENABLE_WEBHOOKS=true
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Application Startup Flow

```
1. Load Environment Variables (.env)
   └─ settings = Settings()

2. Setup Logging
   └─ setup_logging()

3. Initialize Agno Framework ⭐
   └─ initialize_agno()
   └─ Create Agno database instance
   └─ Auto-create Agno tables

4. Initialize Database (Application)
   └─ await init_db()
   └─ Create application tables

5. Start FastAPI Application
   └─ Load middleware (CORS, GZip)
   └─ Load API routes
   └─ Start metrics endpoint

6. Application Ready 🚀
```

---

## Application Shutdown Flow

```
1. Shutdown Signal Received

2. Shutdown Agno Framework ⭐
   └─ shutdown_agno()
   └─ Close Agno database connections

3. Close Application Database
   └─ await close_db()
   └─ Dispose connection pool

4. Cleanup Complete 👋
```

---

## Testing

### Configuration Testing
```python
def test_settings_load():
    """Test settings load from environment"""
    from backend.core.config import settings

    assert settings.APP_NAME == "Agent Squad"
    assert settings.DATABASE_URL is not None
    assert settings.SECRET_KEY is not None
```

### Database Testing
```python
@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection"""
    from backend.core.database import get_db_context

    async with get_db_context() as db:
        result = await db.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

### Agno Testing
```python
def test_agno_initialization():
    """Test Agno framework initialization"""
    from backend.core.agno_config import get_agno_config

    config = get_agno_config()
    assert config.health_check() == True
```

---

## Production Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY backend /app/backend

# Environment variables
ENV DATABASE_URL=postgresql://...
ENV SECRET_KEY=...
ENV ENV=production
ENV DEBUG=false

# Run application
CMD ["uvicorn", "backend.core.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
```bash
# Production environment variables
export ENV=production
export DEBUG=false
export DATABASE_URL=postgresql://prod-user:pass@db-host:5432/agent_squad
export SECRET_KEY=$(openssl rand -hex 32)
export NATS_URL=nats://nats-cluster:4222
export REDIS_URL=redis://redis-cluster:6379
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

### Health Checks
```yaml
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

# Readiness probe
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Performance Considerations

### Database Connection Pool
- Default pool size: 5
- Max overflow: 10
- Total max connections: 15
- Pre-ping enabled (verify before use)

### Recommendations for Scale:
- **< 100 users**: Default settings (5 + 10)
- **100-1000 users**: Increase to 10 + 20
- **> 1000 users**: Consider connection proxy (PgBouncer)

### Async Performance
- Async database: ~10x faster than sync for I/O operations
- Use async endpoints for all user-facing APIs
- Use sync only for migrations and scripts

---

## Troubleshooting

**Q: Application fails to start?**
- Check `DATABASE_URL` is correct
- Check `SECRET_KEY` is set
- Verify PostgreSQL is running
- Check logs for specific errors

**Q: Database connection errors?**
- Verify PostgreSQL is accessible
- Check firewall rules
- Verify credentials
- Test connection: `psql $DATABASE_URL`

**Q: Agno framework errors?**
- Check `DATABASE_URL` is accessible from Agno
- Verify PostgreSQL version >= 12
- Check Agno tables created: `\dt agno_*`
- Review Agno health check results

**Q: CORS errors in frontend?**
- Check `ALLOWED_ORIGINS` includes frontend URL
- Verify credentials are enabled
- Check browser console for specific error

**Q: Authentication not working?**
- Verify `SECRET_KEY` is set correctly
- Check token expiration settings
- Validate JWT format
- Review auth logs

---

## Related Documentation

- See `../agents/CLAUDE.md` for agent architecture
- See `../agents/agno_base.py` for Agno agent implementation
- See `../services/CLAUDE.md` for service layer
- See `../api/` for API endpoint documentation
- See `../models/` for database model documentation
- See Agno docs: https://docs.agno.com
