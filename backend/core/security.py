"""
Security utilities for password hashing and JWT token management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
from jose import jwt, JWTError

from backend.core.config import settings


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Data to encode in the token (typically {"sub": user_id})

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token.

    Args:
        email: User email address

    Returns:
        Encoded JWT token for password reset
    """
    to_encode = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "type": "password_reset"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and return the email.

    Args:
        token: Password reset token

    Returns:
        Email address if valid, None otherwise
    """
    payload = verify_token(token)

    if not payload or payload.get("type") != "password_reset":
        return None

    return payload.get("sub")


def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.

    Args:
        email: User email address

    Returns:
        Encoded JWT token for email verification
    """
    to_encode = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
        "type": "email_verification"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token and return the email.

    Args:
        token: Email verification token

    Returns:
        Email address if valid, None otherwise
    """
    payload = verify_token(token)

    if not payload or payload.get("type") != "email_verification":
        return None

    return payload.get("sub")
