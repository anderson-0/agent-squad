"""
Tests for security module
"""
import pytest
from datetime import timedelta

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


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_generate_different_hashes(self):
        """Test that same password generates different hashes (due to salt)"""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_access_token_with_expiration(self):
        """Test access token with custom expiration"""
        data = {"sub": "user123"}
        expires = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires)

        assert token is not None

    def test_verify_access_token(self):
        """Test access token verification"""
        user_id = "user123"
        data = {"sub": user_id}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)

        assert payload is None

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_verify_refresh_token(self):
        """Test refresh token verification"""
        user_id = "user123"
        data = {"sub": user_id}
        token = create_refresh_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens are different"""
        data = {"sub": "user123"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        assert access_token != refresh_token

        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


class TestPasswordResetTokens:
    """Test password reset token functionality"""

    def test_create_password_reset_token(self):
        """Test password reset token creation"""
        email = "test@example.com"
        token = create_password_reset_token(email)

        assert token is not None
        assert isinstance(token, str)

    def test_verify_password_reset_token(self):
        """Test password reset token verification"""
        email = "test@example.com"
        token = create_password_reset_token(email)

        verified_email = verify_password_reset_token(token)

        assert verified_email == email

    def test_verify_invalid_password_reset_token(self):
        """Test verification of invalid password reset token"""
        invalid_token = "invalid.token.here"
        verified_email = verify_password_reset_token(invalid_token)

        assert verified_email is None

    def test_verify_wrong_token_type_for_password_reset(self):
        """Test that access token is rejected for password reset"""
        data = {"sub": "test@example.com"}
        access_token = create_access_token(data)

        verified_email = verify_password_reset_token(access_token)

        assert verified_email is None


class TestEmailVerificationTokens:
    """Test email verification token functionality"""

    def test_create_email_verification_token(self):
        """Test email verification token creation"""
        email = "test@example.com"
        token = create_email_verification_token(email)

        assert token is not None
        assert isinstance(token, str)

    def test_verify_email_verification_token(self):
        """Test email verification token verification"""
        email = "test@example.com"
        token = create_email_verification_token(email)

        verified_email = verify_email_verification_token(token)

        assert verified_email == email

    def test_verify_invalid_email_verification_token(self):
        """Test verification of invalid email verification token"""
        invalid_token = "invalid.token.here"
        verified_email = verify_email_verification_token(invalid_token)

        assert verified_email is None

    def test_verify_wrong_token_type_for_email_verification(self):
        """Test that access token is rejected for email verification"""
        data = {"sub": "test@example.com"}
        access_token = create_access_token(data)

        verified_email = verify_email_verification_token(access_token)

        assert verified_email is None
