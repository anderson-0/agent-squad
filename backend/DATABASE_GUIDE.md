# Database Guide - SQLAlchemy

This guide explains how to work with the database using SQLAlchemy in Agent Squad.

## Overview

Agent Squad uses:
- **ORM**: SQLAlchemy 2.0 with **async support**
- **Driver**: **asyncpg** (10x faster than psycopg2)
- **Database**: PostgreSQL 15
- **Migrations**: Alembic
- **Connection Pool**: SQLAlchemy built-in pooling

## 🚀 Async Database (Primary)

**Agent Squad uses async SQLAlchemy with asyncpg for better performance!**

For detailed async usage examples, see **[ASYNC_DATABASE_GUIDE.md](./ASYNC_DATABASE_GUIDE.md)**

Quick async example:
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

@app.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    return user
```

**Note**: This guide shows both async and sync patterns. For production code, prefer async. See [ASYNC_DATABASE_GUIDE.md](./ASYNC_DATABASE_GUIDE.md) for comprehensive async examples.

## Models

All models are located in `backend/models/`:

```
models/
├── __init__.py         # All models exported
├── base.py            # Base class and TimestampMixin
├── user.py            # User, Organization
├── squad.py           # Squad, SquadMember
├── project.py         # Project, Task, TaskExecution
├── message.py         # AgentMessage
├── feedback.py        # Feedback, LearningInsight
├── integration.py     # Integration, Webhook
└── billing.py         # Subscription, UsageMetrics
```

## Creating a New Model

### 1. Define the Model

```python
# backend/models/example.py
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class Example(Base, TimestampMixin):
    """Example model"""

    __tablename__ = "examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="examples")

    # Indexes
    __table_args__ = (Index("ix_examples_user_id", "user_id"),)
```

### 2. Add to __init__.py

```python
# backend/models/__init__.py
from backend.models.example import Example

__all__ = [
    # ... existing models
    "Example",
]
```

### 3. Create Migration

```bash
cd backend
alembic revision --autogenerate -m "add example model"
alembic upgrade head
```

## Using the Database

### In FastAPI Routes

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models import User


@app.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### In Services

```python
from backend.core.database import get_db_context
from backend.models import Squad, SquadMember


def create_squad(user_id: str, name: str, member_roles: list[str]):
    with get_db_context() as db:
        # Create squad
        squad = Squad(user_id=user_id, name=name, status="active")
        db.add(squad)
        db.flush()  # Get the squad ID

        # Create members
        for role in member_roles:
            member = SquadMember(
                squad_id=squad.id,
                role=role,
                system_prompt=load_prompt(role),
            )
            db.add(member)

        db.commit()
        db.refresh(squad)
        return squad
```

## Common Queries

### Basic CRUD Operations

```python
from backend.models import User

# Create
user = User(email="user@example.com", name="John Doe", password_hash="...")
db.add(user)
db.commit()
db.refresh(user)

# Read
user = db.query(User).filter(User.email == "user@example.com").first()
users = db.query(User).filter(User.is_active == True).all()

# Update
user.name = "Jane Doe"
db.commit()

# Delete
db.delete(user)
db.commit()
```

### Filtering and Ordering

```python
from sqlalchemy import and_, or_, desc

# Multiple filters
active_users = db.query(User).filter(
    and_(User.is_active == True, User.email_verified == True)
).all()

# OR condition
users = db.query(User).filter(
    or_(User.plan_tier == "pro", User.plan_tier == "enterprise")
).all()

# Ordering
users = db.query(User).order_by(desc(User.created_at)).limit(10).all()
```

### Relationships and Joins

```python
from backend.models import Squad, SquadMember

# Eager loading
squad = (
    db.query(Squad)
    .filter(Squad.id == squad_id)
    .options(joinedload(Squad.members))
    .first()
)

# Access relationships
for member in squad.members:
    print(member.role)

# Query with join
squads_with_pm = (
    db.query(Squad)
    .join(SquadMember)
    .filter(SquadMember.role == "project_manager")
    .all()
)
```

### Pagination

```python
def get_paginated_users(db: Session, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    users = db.query(User).offset(offset).limit(per_page).all()
    total = db.query(User).count()

    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }
```

### Aggregations

```python
from sqlalchemy import func

# Count
user_count = db.query(func.count(User.id)).scalar()

# Group by
squad_member_counts = (
    db.query(Squad.id, func.count(SquadMember.id))
    .join(SquadMember)
    .group_by(Squad.id)
    .all()
)

# Average
avg_rating = db.query(func.avg(Feedback.rating)).scalar()
```

## Transactions

### Automatic Transaction Management

FastAPI's `Depends(get_db)` handles transactions automatically:
- Commits on successful response
- Rolls back on exceptions

### Manual Transaction Control

```python
def transfer_squad(db: Session, squad_id: str, new_owner_id: str):
    try:
        squad = db.query(Squad).filter(Squad.id == squad_id).with_for_update().first()
        if not squad:
            raise ValueError("Squad not found")

        squad.user_id = new_owner_id
        db.commit()
    except Exception as e:
        db.rollback()
        raise
```

### Nested Transactions (Savepoints)

```python
with db.begin_nested():  # Creates a savepoint
    # Do some work
    squad.name = "New Name"
    # If an exception occurs here, only this nested transaction rolls back
```

## Migrations with Alembic

### Creating Migrations

```bash
# Autogenerate from model changes
alembic revision --autogenerate -m "description"

# Manual migration
alembic revision -m "description"
```

### Migration File Structure

```python
"""add user email verification

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

### Viewing Migration Status

```bash
# Current version
alembic current

# Migration history
alembic history

# Show SQL without running
alembic upgrade head --sql
```

## Best Practices

### 1. Always Use Sessions Properly

```python
# ✅ Good - using FastAPI dependency
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ✅ Good - using context manager
with get_db_context() as db:
    user = db.query(User).first()

# ❌ Bad - session not closed
db = SessionLocal()
user = db.query(User).first()
```

### 2. Use Relationships for Efficient Queries

```python
# ✅ Good - single query with join
squad = db.query(Squad).options(joinedload(Squad.members)).first()

# ❌ Bad - N+1 queries
squad = db.query(Squad).first()
for member in squad.members:  # Triggers separate query for each member
    print(member.role)
```

### 3. Index Foreign Keys and Query Columns

```python
class Squad(Base, TimestampMixin):
    # ...
    __table_args__ = (
        Index("ix_squads_user_id", "user_id"),  # For FK lookups
        Index("ix_squads_status", "status"),     # For status filtering
    )
```

### 4. Use Bulk Operations for Performance

```python
# ✅ Good - bulk insert
members = [SquadMember(squad_id=squad_id, role=role) for role in roles]
db.bulk_save_objects(members)
db.commit()

# ❌ Bad - individual inserts
for role in roles:
    member = SquadMember(squad_id=squad_id, role=role)
    db.add(member)
    db.commit()  # Separate commit for each!
```

### 5. Handle Exceptions Properly

```python
try:
    user = User(email=email, name=name)
    db.add(user)
    db.commit()
except IntegrityError as e:
    db.rollback()
    if "unique constraint" in str(e):
        raise HTTPException(status_code=400, detail="Email already exists")
    raise
except Exception as e:
    db.rollback()
    raise
```

## Testing with Database

### Test Database Setup

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/agent_squad_test"

@pytest.fixture(scope="function")
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(engine)
```

### Example Test

```python
# tests/test_user.py
from backend.models import User

def test_create_user(db):
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()

    retrieved = db.query(User).filter(User.email == "test@example.com").first()
    assert retrieved is not None
    assert retrieved.name == "Test User"
```

## Async Support ✅ ENABLED

**Async SQLAlchemy with asyncpg is now enabled!**

Agent Squad uses async operations by default for better performance. See [ASYNC_DATABASE_GUIDE.md](./ASYNC_DATABASE_GUIDE.md) for:
- Complete async examples
- CRUD operations
- Transactions
- Performance tips
- Testing with async

Basic async usage:
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

Sync operations are still available via `get_sync_db()` for migrations and special cases.

## Troubleshooting

### Connection Pool Exhausted

```python
# Check pool status
from backend.core.database import engine
print(engine.pool.status())

# Increase pool size in database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Default is 5
    max_overflow=40,  # Default is 10
)
```

### Detached Instance Error

```python
# ❌ Error: accessing relationship after session closed
user = db.query(User).first()
db.close()
squads = user.squads  # DetachedInstanceError

# ✅ Fix: eager load or refresh
user = db.query(User).options(joinedload(User.squads)).first()
db.close()
squads = user.squads  # Works!
```

### Migration Conflicts

```bash
# Multiple heads
alembic merge heads -m "merge branches"

# Stamp database without running migrations
alembic stamp head
```

## Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI with SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)
