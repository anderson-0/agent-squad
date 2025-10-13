"""
Authentication service - Business logic for user authentication
"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token,
    verify_email_verification_token,
)
from backend.models.user import User
from backend.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    PasswordChange,
    PasswordReset,
    PasswordResetRequest,
)


class AuthService:
    """Service for handling authentication operations"""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: UserRegister
    ) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        result = await db.execute(
            select(User).filter(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
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
    async def authenticate_user(
        db: AsyncSession,
        credentials: UserLogin
    ) -> User:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            credentials: User login credentials

        Returns:
            Authenticated user object

        Raises:
            HTTPException: If credentials are invalid or user is inactive
        """
        # Get user by email
        result = await db.execute(
            select(User).filter(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        # Verify user exists and password is correct
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        return user

    @staticmethod
    def create_tokens(user: User) -> TokenResponse:
        """
        Create access and refresh tokens for a user.

        Args:
            user: User object

        Returns:
            TokenResponse with access and refresh tokens
        """
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes in seconds
        )

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str
    ) -> TokenResponse:
        """
        Create a new access token using a refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token string

        Returns:
            New TokenResponse with access and refresh tokens

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Get user from database
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token"
            )

        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Create new tokens
        return AuthService.create_tokens(user)

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        password_data: PasswordChange
    ) -> None:
        """
        Change user's password.

        Args:
            db: Database session
            user: Current user
            password_data: Password change data

        Raises:
            HTTPException: If current password is incorrect
        """
        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )

        # Update password
        user.password_hash = hash_password(password_data.new_password)
        await db.commit()

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        email: str
    ) -> str:
        """
        Generate a password reset token for a user.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Password reset token

        Note:
            Returns token even if user doesn't exist (for security)
        """
        # Check if user exists
        result = await db.execute(
            select(User).filter(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Always return a token (don't reveal if user exists)
        # In production, send email only if user exists
        if user:
            return create_password_reset_token(email)

        # Return a dummy token for non-existent users
        return create_password_reset_token(email)

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        reset_data: PasswordReset
    ) -> None:
        """
        Reset user's password using reset token.

        Args:
            db: Database session
            reset_data: Password reset data with token

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify reset token
        email = verify_password_reset_token(reset_data.token)

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Get user by email
        result = await db.execute(
            select(User).filter(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password
        user.password_hash = hash_password(reset_data.new_password)
        await db.commit()

    @staticmethod
    async def verify_email(
        db: AsyncSession,
        token: str
    ) -> User:
        """
        Verify user's email address using verification token.

        Args:
            db: Database session
            token: Email verification token

        Returns:
            User with verified email

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify email token
        email = verify_email_verification_token(token)

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

        # Get user by email
        result = await db.execute(
            select(User).filter(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Mark email as verified
        user.email_verified = True
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    def create_email_verification_token_for_user(email: str) -> str:
        """
        Create an email verification token.

        Args:
            email: User's email address

        Returns:
            Email verification token
        """
        return create_email_verification_token(email)

    @staticmethod
    async def get_user_by_email(
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """
        Get user by email address.

        Args:
            db: Database session
            email: Email address

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(
            select(User).filter(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user: User,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """
        Update user profile.

        Args:
            db: Database session
            user: User to update
            name: New name (optional)
            email: New email (optional)

        Returns:
            Updated user

        Raises:
            HTTPException: If email is already taken
        """
        if name:
            user.name = name

        if email and email != user.email:
            # Check if email is already taken
            result = await db.execute(
                select(User).filter(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )

            user.email = email
            user.email_verified = False  # Require re-verification

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        user: User
    ) -> None:
        """
        Deactivate a user account.

        Args:
            db: Database session
            user: User to deactivate
        """
        user.is_active = False
        await db.commit()

    @staticmethod
    async def reactivate_user(
        db: AsyncSession,
        user: User
    ) -> None:
        """
        Reactivate a user account.

        Args:
            db: Database session
            user: User to reactivate
        """
        user.is_active = True
        await db.commit()
