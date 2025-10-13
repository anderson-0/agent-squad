"""
Authentication API endpoints
"""
from typing import Dict

from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import (
    get_current_user,
    get_current_active_user,
)
from backend.models.user import User
from backend.services.auth_service import AuthService
from backend.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PasswordResetRequest,
    PasswordReset,
    EmailVerificationRequest,
    EmailVerificationResend,
    AuthStatus,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Register a new user.

    - **email**: Valid email address (will be verified)
    - **name**: Full name (2-100 characters)
    - **password**: Strong password (min 8 chars, must contain letter and digit)

    Returns the created user object (without password).
    """
    user = await AuthService.register_user(db, user_data)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return access and refresh tokens"
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Login with email and password.

    - **email**: User's email address
    - **password**: User's password

    Returns JWT access token and refresh token.
    Use the access token in the Authorization header: `Bearer <token>`
    """
    user = await AuthService.authenticate_user(db, credentials)
    tokens = AuthService.create_tokens(user)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token"
)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token using a refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token and refresh token.
    """
    tokens = await AuthService.refresh_access_token(db, token_data.refresh_token)
    return tokens


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current authenticated user's profile.

    Requires authentication (Bearer token in Authorization header).
    """
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the currently authenticated user's profile"
)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Update current user's profile.

    - **name**: New name (optional)
    - **email**: New email (optional, will require re-verification)

    Requires authentication.
    """
    updated_user = await AuthService.update_user(
        db,
        current_user,
        name=user_update.name,
        email=user_update.email
    )
    return updated_user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change the current user's password"
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Change password for current user.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, must contain letter and digit)

    Requires authentication.
    """
    await AuthService.change_password(db, current_user, password_data)


@router.post(
    "/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description="Request a password reset email"
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Request password reset email.

    - **email**: Email address of the account

    An email with reset instructions will be sent if the account exists.
    Returns success message regardless of whether account exists (security).
    """
    token = await AuthService.request_password_reset(db, reset_request.email)

    # In production, send email with token here
    # For now, return token in response (development only)
    return {
        "message": "If the email exists, a password reset link has been sent",
        "token": token  # TODO: Remove in production, send via email instead
    }


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password",
    description="Reset password using reset token"
)
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Reset password using token from email.

    - **token**: Password reset token from email
    - **new_password**: New password (min 8 chars, must contain letter and digit)
    """
    await AuthService.reset_password(db, reset_data)


@router.post(
    "/verify-email",
    response_model=UserResponse,
    summary="Verify email",
    description="Verify email address using verification token"
)
async def verify_email(
    verification: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify email address using token from email.

    - **token**: Email verification token from email

    Returns the user with email_verified set to true.
    """
    user = await AuthService.verify_email(db, verification.token)
    return user


@router.post(
    "/verify-email/resend",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Resend verification email",
    description="Resend email verification link"
)
async def resend_verification_email(
    resend_data: EmailVerificationResend,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Resend email verification link.

    - **email**: Email address to resend verification to

    Returns success message regardless of whether account exists (security).
    """
    user = await AuthService.get_user_by_email(db, resend_data.email)

    if user and not user.email_verified:
        token = AuthService.create_email_verification_token_for_user(user.email)

        # In production, send email with token here
        # For now, return token in response (development only)
        return {
            "message": "Verification email has been sent",
            "token": token  # TODO: Remove in production, send via email instead
        }

    return {
        "message": "Verification email has been sent"
    }


@router.get(
    "/status",
    response_model=AuthStatus,
    summary="Check authentication status",
    description="Check if user is authenticated"
)
async def check_auth_status(
    current_user: User = Depends(get_current_user)
) -> AuthStatus:
    """
    Check authentication status.

    Requires authentication. Returns user info if authenticated.
    """
    return AuthStatus(
        authenticated=True,
        user=current_user,
        message="User is authenticated"
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logout current user (client should delete tokens)"
)
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Logout current user.

    Since we're using stateless JWT tokens, the client should delete
    the tokens from storage. In a production system, you might want to
    implement token blacklisting or use short-lived tokens with a
    token refresh strategy.

    Requires authentication.
    """
    # With JWT, logout is typically handled client-side by deleting tokens
    # Server-side logout would require token blacklisting (Redis) or
    # database tracking, which we can add later if needed
    pass
