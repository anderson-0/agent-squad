"""
Authentication dependencies for FastAPI routes
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import verify_token
from backend.models.user import User


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id_str: Optional[str] = payload.get("sub")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert to UUID
    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user for clarity).

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User object if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user with verified email.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User object if email is verified

    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email address."
        )
    return current_user


def require_plan_tier(required_tier: str):
    """
    Dependency factory to require a specific plan tier or higher.

    Usage:
        @app.get("/premium-feature")
        async def premium_feature(
            user: User = Depends(require_plan_tier("pro"))
        ):
            ...

    Args:
        required_tier: Minimum plan tier required (starter, pro, enterprise)

    Returns:
        Dependency function that checks user's plan tier
    """
    tier_hierarchy = {
        "starter": 0,
        "pro": 1,
        "enterprise": 2
    }

    async def check_plan_tier(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user's plan tier meets the requirement"""
        user_tier_level = tier_hierarchy.get(current_user.plan_tier, -1)
        required_tier_level = tier_hierarchy.get(required_tier, 999)

        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} plan or higher. "
                       f"Your current plan: {current_user.plan_tier}"
            )

        return current_user

    return check_plan_tier


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    Useful for endpoints that work both with and without authentication.

    Args:
        credentials: Optional HTTP Bearer token credentials
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)

        if not payload or payload.get("type") != "access":
            return None

        user_id_str = payload.get("sub")
        if not user_id_str:
            return None

        user_id = UUID(user_id_str)
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user and user.is_active:
            return user

    except (ValueError, AttributeError):
        pass

    return None
