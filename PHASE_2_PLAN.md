# Phase 2: Authentication & Payments - Implementation Plan

**Status**: Ready to Start
**Estimated Time**: 2-3 weeks
**Prerequisites**: ✅ Phase 1 Complete

## Overview

Phase 2 will implement:
1. **Authentication System** - JWT-based auth with secure password handling
2. **User Management** - Registration, login, profile, organizations
3. **Stripe Integration** - Subscription plans and payment processing
4. **Authorization** - Role-based access control

## Architecture

### Authentication Flow

```
1. User registers → Hash password → Create user in DB → Generate JWT
2. User logs in → Verify password → Generate JWT token
3. Protected routes → Verify JWT → Load user from DB → Allow access
```

### Subscription Flow

```
1. User selects plan → Create Stripe checkout session
2. User completes payment → Stripe webhook fires
3. Webhook handler → Create subscription in DB → Update user plan
4. User accesses features → Check subscription tier → Allow/deny
```

## Implementation Order

### Week 1: Authentication Foundation

#### Day 1-2: Password & JWT Utils
- [ ] Password hashing with bcrypt
- [ ] JWT token generation and validation
- [ ] Auth utilities and dependencies

**Files to create**:
- `backend/core/security.py` - Password hashing, JWT utils
- `backend/core/auth.py` - Auth dependencies
- `backend/schemas/auth.py` - Pydantic schemas

#### Day 3-4: User Registration & Login
- [ ] User registration endpoint
- [ ] User login endpoint
- [ ] Token refresh endpoint
- [ ] User profile endpoint

**Files to create**:
- `backend/api/v1/endpoints/auth.py` - Auth routes
- `backend/services/auth_service.py` - Auth business logic
- `backend/repositories/user_repository.py` - User data access

#### Day 5: Email Verification (Optional for MVP)
- [ ] Generate verification tokens
- [ ] Email verification endpoint
- [ ] Email service integration (SendGrid/SES)

### Week 2: Stripe Integration

#### Day 1-2: Stripe Setup
- [ ] Stripe customer creation
- [ ] Checkout session creation
- [ ] Subscription plans configuration

**Files to create**:
- `backend/integrations/stripe/client.py` - Stripe client
- `backend/integrations/stripe/models.py` - Stripe models
- `backend/services/subscription_service.py` - Subscription logic

#### Day 3-4: Webhook Handling
- [ ] Webhook endpoint
- [ ] Signature verification
- [ ] Event handlers (checkout, subscription events)
- [ ] Database updates

**Files to create**:
- `backend/api/v1/endpoints/webhooks.py` - Webhook routes
- `backend/integrations/stripe/webhooks.py` - Webhook handlers

#### Day 5: Subscription Management
- [ ] Get current subscription
- [ ] Upgrade/downgrade plan
- [ ] Cancel subscription
- [ ] Billing portal link

### Week 3: Organization & Authorization

#### Day 1-2: Organization Management
- [ ] Create organization
- [ ] List organizations
- [ ] Update organization
- [ ] Delete organization

**Files to create**:
- `backend/api/v1/endpoints/organizations.py`
- `backend/services/organization_service.py`
- `backend/repositories/organization_repository.py`

#### Day 3-4: Authorization & Permissions
- [ ] Role-based access control
- [ ] Organization ownership checks
- [ ] Squad access control
- [ ] Permission decorators

**Files to create**:
- `backend/core/permissions.py` - Permission checks
- `backend/core/rbac.py` - Role definitions

#### Day 5: Testing & Documentation
- [ ] Unit tests for auth
- [ ] Integration tests
- [ ] API documentation
- [ ] Postman/Thunder Client collection

## Detailed Implementation

### 1. Security Module

```python
# backend/core/security.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from backend.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 2. Auth Schemas

```python
# backend/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    plan_tier: str
    is_active: bool
    email_verified: bool

    class Config:
        from_attributes = True
```

### 3. Auth Service

```python
# backend/services/auth_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models import User
from backend.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from backend.schemas.auth import UserRegister, UserLogin

class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> User:
        # Check if user exists
        result = await db.execute(select(User).filter(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=hash_password(user_data.password),
            plan_tier="starter",
            is_active=True,
            email_verified=False
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> User:
        # Get user by email
        result = await db.execute(select(User).filter(User.email == credentials.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        return user

    @staticmethod
    def create_tokens(user: User) -> dict:
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
```

### 4. Auth Endpoints

```python
# backend/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.services.auth_service import AuthService
from backend.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from backend.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    user = await AuthService.register_user(db, user_data)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return JWT tokens"""
    user = await AuthService.authenticate_user(db, credentials)
    tokens = AuthService.create_tokens(user)
    return tokens

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user"""
    return current_user

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Verify refresh token and create new tokens
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).filter(User.id == payload["sub"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return AuthService.create_tokens(user)
```

### 5. Stripe Service

```python
# backend/services/subscription_service.py
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models import User, Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionService:
    PLANS = {
        "starter": settings.STRIPE_STARTER_PRICE_ID,
        "pro": settings.STRIPE_PRO_PRICE_ID,
        "enterprise": settings.STRIPE_ENTERPRISE_PRICE_ID,
    }

    @staticmethod
    async def create_checkout_session(
        db: AsyncSession,
        user: User,
        plan: str,
        success_url: str,
        cancel_url: str
    ):
        # Get or create Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={"user_id": str(user.id)}
            )
            user.stripe_customer_id = customer.id
            await db.commit()

        # Create checkout session
        price_id = SubscriptionService.PLANS.get(plan)
        if not price_id:
            raise ValueError(f"Invalid plan: {plan}")

        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user.id),
        )

        return session

    @staticmethod
    async def handle_checkout_complete(db: AsyncSession, session):
        user_id = session.client_reference_id
        subscription_id = session.subscription

        # Get user
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return

        # Get subscription from Stripe
        stripe_sub = stripe.Subscription.retrieve(subscription_id)

        # Create subscription in database
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=subscription_id,
            stripe_price_id=stripe_sub.items.data[0].price.id,
            plan_tier=user.plan_tier,  # Map from price_id
            status=stripe_sub.status,
            current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end),
        )

        db.add(subscription)
        await db.commit()
```

## Testing Checklist

### Authentication
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login with wrong credentials fails
- [ ] Access protected route without token fails
- [ ] Access protected route with valid token succeeds
- [ ] Token refresh works
- [ ] Expired token rejected

### Stripe
- [ ] Create checkout session
- [ ] Complete checkout (use Stripe test cards)
- [ ] Webhook receives event
- [ ] Subscription created in DB
- [ ] User plan updated
- [ ] Cancel subscription

## Environment Variables

Add to `.env`:
```env
# JWT
SECRET_KEY=your-super-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...

# Email (Optional for Phase 2)
SENDGRID_API_KEY=...
SENDGRID_FROM_EMAIL=...
```

## Success Criteria

Phase 2 is complete when:
- [x] Users can register and login
- [x] JWT authentication works
- [x] Protected routes require authentication
- [x] Stripe checkout flow works end-to-end
- [x] Webhooks are processed correctly
- [x] Subscriptions are tracked in database
- [x] Users can view their subscription
- [x] All tests pass

## Next: Phase 3

After Phase 2, we'll move to **Phase 3: Agent Framework Integration** where we'll implement the AI agents that power the squads.

---

**Ready to start Phase 2? Let's build the authentication system!** 🚀
