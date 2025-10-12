# Agent Squad Backend

FastAPI-based backend for Agent Squad - AI-Powered Software Development SaaS.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Poetry (recommended) or pip

## Quick Start with Docker

```bash
# From project root
docker-compose up backend postgres redis
```

## Local Development Setup

### 1. Install Dependencies

Using Poetry (recommended):
```bash
poetry install
```

Using pip:
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Generate Prisma Client

```bash
prisma generate
```

### 4. Run Database Migrations

```bash
prisma db push
```

### 5. Start Development Server

```bash
# Using Poetry
poetry run python main.py

# Or directly
python main.py

# With uvicorn directly
uvicorn backend.core.app:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Project Structure

```
backend/
├── api/                  # API routes
│   └── v1/              # API version 1
│       └── endpoints/   # Route handlers
├── core/                 # Core functionality
│   ├── app.py           # FastAPI app
│   ├── config.py        # Configuration
│   ├── database.py      # DB connection
│   └── logging.py       # Logging setup
├── services/             # Business logic
├── repositories/         # Data access layer
├── agents/               # AI agents
│   ├── communication/   # A2A protocol
│   └── specialized/     # Specialized agents
├── workflows/            # Inngest workflows
├── integrations/         # External integrations
│   ├── mcp/             # MCP servers
│   ├── stripe/          # Payment processing
│   └── llm/             # LLM providers
├── models/               # Database models
├── schemas/              # Pydantic schemas
├── utils/                # Utilities
└── tests/                # Test suite
```

## Database Commands

```bash
# Generate Prisma client
prisma generate

# Push schema changes to database
prisma db push

# Create a migration
prisma migrate dev --name migration_name

# Apply migrations
prisma migrate deploy

# Open Prisma Studio (DB GUI)
prisma studio
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_specific.py

# Run with output
pytest -v -s
```

## Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy backend/
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `OPENAI_API_KEY`: OpenAI API key
- `STRIPE_SECRET_KEY`: Stripe secret key

## Common Issues

### Prisma Client Not Found

```bash
prisma generate
```

### Database Connection Issues

Ensure PostgreSQL is running:
```bash
docker-compose up postgres -d
```

### Port Already in Use

Change the port in `.env`:
```
PORT=8001
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](../LICENSE) file.
