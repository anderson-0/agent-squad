# Async Database Guide - SQLAlchemy + asyncpg

Agent Squad uses **async SQLAlchemy with asyncpg** for high-performance database operations.

## Why Async + asyncpg?

- ⚡ **10x faster** than psycopg2 for async operations
- 🚀 **Non-blocking** - handles concurrent requests efficiently
- 🎯 **Native FastAPI support** - works seamlessly with async routes
- 💪 **Production-ready** - used by major companies at scale

## Quick Start

### Basic Async Query

```python
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models import User


@app.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    # Async query
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
```

## Core Concepts

### 1. Async Session Dependency

```python
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

# In your route
async def my_route(db: AsyncSession = Depends(get_db)):
    # db is an async session
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### 2. Execute + Scalars Pattern

Async SQLAlchemy uses `execute()` + result processing:

```python
# Single object
result = await db.execute(select(User).filter(User.id == user_id))
user = result.scalar_one_or_none()  # Returns User or None

# Multiple objects
result = await db.execute(select(User).filter(User.is_active == True))
users = result.scalars().all()  # Returns list of Users

# First object
result = await db.execute(select(User).order_by(User.created_at.desc()))
user = result.scalars().first()  # Returns first User or None
```

### 3. Select Statements

Use `select()` instead of `.query()`:

```python
from sqlalchemy import select, and_, or_

# Simple select
stmt = select(User)
result = await db.execute(stmt)
users = result.scalars().all()

# With filters
stmt = select(User).filter(User.email == "user@example.com")
result = await db.execute(stmt)
user = result.scalar_one_or_none()

# Multiple filters
stmt = select(User).filter(
    and_(
        User.is_active == True,
        User.email_verified == True
    )
)
result = await db.execute(stmt)
users = result.scalars().all()
```

## CRUD Operations

### Create

```python
async def create_user(db: AsyncSession, email: str, name: str):
    user = User(
        email=email,
        name=name,
        password_hash="hashed_password",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # Load the ID and defaults
    return user
```

### Read

```python
# Get by ID
async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

# Get all
async def get_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

# Get with filter
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()
```

### Update

```python
async def update_user(db: AsyncSession, user_id: str, name: str):
    # Fetch user
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Update
    user.name = name
    await db.commit()
    await db.refresh(user)
    return user
```

### Delete

```python
async def delete_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    await db.delete(user)
    await db.commit()
    return True
```

## Advanced Queries

### Joins and Relationships

```python
from sqlalchemy.orm import selectinload

# Eager load relationships
async def get_squad_with_members(db: AsyncSession, squad_id: str):
    stmt = (
        select(Squad)
        .filter(Squad.id == squad_id)
        .options(selectinload(Squad.members))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Multiple relationships
stmt = (
    select(Squad)
    .options(
        selectinload(Squad.members),
        selectinload(Squad.projects)
    )
)
result = await db.execute(stmt)
squads = result.scalars().all()
```

### Filtering and Ordering

```python
from sqlalchemy import desc, asc

# Order by
stmt = select(User).order_by(desc(User.created_at))
result = await db.execute(stmt)
users = result.scalars().all()

# Multiple conditions
stmt = (
    select(Task)
    .filter(
        and_(
            Task.status == "pending",
            Task.priority == "high"
        )
    )
    .order_by(desc(Task.created_at))
)
result = await db.execute(stmt)
tasks = result.scalars().all()

# OR conditions
stmt = select(User).filter(
    or_(
        User.plan_tier == "pro",
        User.plan_tier == "enterprise"
    )
)
result = await db.execute(stmt)
users = result.scalars().all()
```

### Pagination

```python
async def get_users_paginated(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20
):
    offset = (page - 1) * per_page

    # Get total count
    count_stmt = select(func.count(User.id))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get paginated results
    stmt = select(User).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    users = result.scalars().all()

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
async def count_users(db: AsyncSession):
    result = await db.execute(select(func.count(User.id)))
    return result.scalar()

# Average
async def average_feedback_rating(db: AsyncSession):
    result = await db.execute(select(func.avg(Feedback.rating)))
    return result.scalar()

# Group by
async def squad_member_counts(db: AsyncSession):
    stmt = (
        select(Squad.id, func.count(SquadMember.id))
        .join(SquadMember)
        .group_by(Squad.id)
    )
    result = await db.execute(stmt)
    return result.all()
```

## Transactions

### Basic Transaction

```python
async def transfer_squad(
    db: AsyncSession,
    squad_id: str,
    new_owner_id: str
):
    try:
        # Everything in this function is in one transaction
        result = await db.execute(select(Squad).filter(Squad.id == squad_id))
        squad = result.scalar_one_or_none()

        if not squad:
            raise ValueError("Squad not found")

        squad.user_id = new_owner_id
        await db.commit()

        return squad
    except Exception as e:
        await db.rollback()
        raise
```

### Manual Transaction Control

```python
async def complex_operation(db: AsyncSession):
    async with db.begin():
        # Create user
        user = User(email="test@example.com", name="Test")
        db.add(user)
        await db.flush()  # Get user.id without committing

        # Create squad for user
        squad = Squad(user_id=user.id, name="Test Squad")
        db.add(squad)
        await db.flush()

        # Create squad members
        member = SquadMember(squad_id=squad.id, role="developer")
        db.add(member)

        # Commit happens automatically at end of 'async with' block
        # Or rollback if exception occurs
```

### Savepoints (Nested Transactions)

```python
async def operation_with_savepoint(db: AsyncSession):
    # Outer transaction
    user = User(email="test@example.com", name="Test")
    db.add(user)

    # Savepoint
    async with db.begin_nested():
        squad = Squad(user_id=user.id, name="Test Squad")
        db.add(squad)
        # If this fails, only squad creation is rolled back

    await db.commit()  # Commits user even if squad failed
```

## Context Manager Usage

For use outside of FastAPI routes:

```python
from backend.core.database import get_db_context

async def some_background_task():
    async with get_db_context() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            # Process user
            pass
```

## FastAPI Route Examples

### Complete CRUD API

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: str
    name: str


class UserUpdate(BaseModel):
    name: str


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if exists
    result = await db.execute(
        select(User).filter(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user = User(**user_data.dict(), password_hash="hashed")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = user_data.name
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}
```

## Performance Tips

### 1. Use Eager Loading

```python
# ❌ Bad - N+1 queries
stmt = select(Squad)
result = await db.execute(stmt)
squads = result.scalars().all()

for squad in squads:
    # Each iteration makes a new query!
    members = await squad.members

# ✅ Good - Single query with join
stmt = select(Squad).options(selectinload(Squad.members))
result = await db.execute(stmt)
squads = result.scalars().all()

for squad in squads:
    members = squad.members  # Already loaded!
```

### 2. Use Bulk Operations

```python
# ✅ Good - Bulk insert
members = [
    SquadMember(squad_id=squad_id, role=role)
    for role in roles
]
db.add_all(members)
await db.commit()

# ❌ Bad - Individual inserts
for role in roles:
    member = SquadMember(squad_id=squad_id, role=role)
    db.add(member)
    await db.commit()  # Commit for each!
```

### 3. Use execute_many for Batch Updates

```python
from sqlalchemy import update

# Update multiple rows efficiently
stmt = (
    update(Task)
    .where(Task.project_id == project_id)
    .values(status="completed")
)
await db.execute(stmt)
await db.commit()
```

### 4. Index Your Queries

Ensure foreign keys and frequently queried columns have indexes (already done in models).

## Sync Fallback

For rare cases where sync is needed (like Alembic migrations):

```python
from backend.core.database import get_sync_db, SyncSessionLocal

# Sync dependency
@app.get("/sync-route")
def sync_route(db: Session = Depends(get_sync_db)):
    users = db.query(User).all()
    return users

# Sync context manager
with get_sync_db_context() as db:
    user = db.query(User).filter(User.email == email).first()
```

## Common Patterns

### Check and Create

```python
async def get_or_create_user(db: AsyncSession, email: str):
    # Try to get
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return user, False

    # Create if not exists
    user = User(email=email, name="New User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True
```

### Conditional Updates

```python
from sqlalchemy import update

async def increment_usage(db: AsyncSession, squad_id: str):
    stmt = (
        update(UsageMetrics)
        .where(UsageMetrics.squad_id == squad_id)
        .values(value=UsageMetrics.value + 1)
    )
    await db.execute(stmt)
    await db.commit()
```

### Soft Deletes

```python
from datetime import datetime

async def soft_delete_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deleted_at = datetime.utcnow()
    user.is_active = False
    await db.commit()
    return True
```

## Testing

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.models.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"


@pytest.fixture
async def async_db():
    # Create engine
    engine = create_async_engine(TEST_DATABASE_URL)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user(async_db):
    user = User(email="test@example.com", name="Test User")
    async_db.add(user)
    await async_db.commit()

    result = await async_db.execute(select(User).filter(User.email == "test@example.com"))
    retrieved = result.scalar_one_or_none()

    assert retrieved is not None
    assert retrieved.name == "Test User"
```

## Resources

- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)
- [FastAPI with Async SQLAlchemy](https://fastapi.tiangolo.com/advanced/async-sql-databases/)

## Summary

Agent Squad uses **async SQLAlchemy with asyncpg** for maximum performance:

- ✅ Use `async/await` for all database operations
- ✅ Use `select()` instead of `.query()`
- ✅ Use `await db.execute()` + `result.scalars()`
- ✅ Use eager loading to avoid N+1 queries
- ✅ Use bulk operations for batch inserts
- ✅ Always use `AsyncSession` dependency in routes

This provides excellent performance for concurrent FastAPI requests!
