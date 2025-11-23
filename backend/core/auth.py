"""
Authentication dependencies for FastAPI routes
"""
from typing import Optional
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import verify_token
from backend.models.user import User

logger = logging.getLogger(__name__)


# HTTP Bearer token scheme
security = HTTPBearer()


# Plan tier hierarchy for access control
TIER_HIERARCHY = {
    "free": 0,
    "starter": 1,
    "pro": 2,
    "enterprise": 3
}


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
    except (ValueError, AttributeError) as e:
        logger.warning(
            "Invalid user ID format in JWT token",
            extra={
                "user_id_prefix": user_id_str[:8] if user_id_str and len(user_id_str) > 8 else user_id_str,
                "token_prefix": token[:16] + "..." if len(token) > 16 else token,
                "error_type": type(e).__name__,
                "error": str(e)
            },
            exc_info=False  # Don't need full stack trace for invalid UUIDs
        )
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
        required_tier: Minimum plan tier required (free, starter, pro, enterprise)

    Returns:
        Dependency function that checks user's plan tier

    Raises:
        ValueError: If required_tier is not a valid tier
    """
    # Validate required tier at dependency creation time
    if required_tier not in TIER_HIERARCHY:
        raise ValueError(
            f"Unknown plan tier: '{required_tier}'. "
            f"Valid tiers: {', '.join(TIER_HIERARCHY.keys())}"
        )

    async def check_plan_tier(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user's plan tier meets the requirement"""
        # Default to free tier if user has no tier set
        user_tier = current_user.plan_tier or "free"

        # Validate user tier from database
        if user_tier not in TIER_HIERARCHY:
            logger.error(
                f"Invalid user plan tier in database: {user_tier}",
                extra={
                    "user_id": str(current_user.id),
                    "invalid_tier": user_tier,
                    "valid_tiers": list(TIER_HIERARCHY.keys())
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid user plan configuration. Please contact support."
            )

        user_tier_level = TIER_HIERARCHY[user_tier]
        required_tier_level = TIER_HIERARCHY[required_tier]

        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} plan or higher. "
                       f"Your current plan: {user_tier}"
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
            logger.debug(
                "Optional auth failed: Invalid or non-access token",
                extra={"reason": "invalid_token_type"}
            )
            return None

        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.debug(
                "Optional auth failed: Missing user ID in token",
                extra={"reason": "missing_sub"}
            )
            return None

        user_id = UUID(user_id_str)
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(
                f"Optional auth failed: User not found for ID {user_id}",
                extra={"user_id": str(user_id), "reason": "user_not_found"}
            )
            return None

        if not user.is_active:
            logger.warning(
                f"Optional auth failed: User {user_id} is inactive",
                extra={"user_id": str(user_id), "reason": "user_inactive"}
            )
            return None

        return user

    except (ValueError, AttributeError) as e:
        logger.debug(
            f"Optional auth failed: Invalid token format - {e}",
            extra={"error": str(e), "reason": "invalid_format"}
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in optional auth: {e}",
            extra={"error": str(e), "reason": "unexpected_error"},
            exc_info=True
        )

    return None
