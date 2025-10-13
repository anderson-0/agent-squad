"""
Authentication schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class UserRegister(BaseModel):
    """Schema for user registration request"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password contains at least one letter and one number"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: UUID
    email: str
    name: str
    plan_tier: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator("new_password")
    def validate_password_strength(cls, v):
        """Validate password contains at least one letter and one number"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator("new_password")
    def validate_password_strength(cls, v):
        """Validate password contains at least one letter and one number"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    token: str


class EmailVerificationResend(BaseModel):
    """Schema for resending email verification"""
    email: EmailStr


class AuthStatus(BaseModel):
    """Schema for authentication status"""
    authenticated: bool
    user: Optional[UserResponse] = None
    message: Optional[str] = None
