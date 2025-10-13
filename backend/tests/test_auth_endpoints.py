"""
Tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user import User
from backend.core.security import create_email_verification_token, create_password_reset_token


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints"""

    async def test_register_user(self, client: AsyncClient, test_user_data):
        """Test user registration"""
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert "password" not in data
        assert "password_hash" not in data
        assert data["plan_tier"] == "starter"
        assert data["is_active"] is True
        assert data["email_verified"] is False
        assert "id" in data

    async def test_register_user_duplicate_email(
        self, client: AsyncClient, test_user_data
    ):
        """Test registration with duplicate email fails"""
        # Register first user
        response1 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201

        # Try to register with same email
        response2 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    async def test_register_user_invalid_password(self, client: AsyncClient):
        """Test registration with invalid password"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "short"  # Too short
        }

        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

    async def test_register_user_password_validation(self, client: AsyncClient):
        """Test password must contain letter and digit"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "onlyletters"  # No digit
        }

        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

        user_data["password"] = "12345678"  # No letter
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    async def test_login_user(self, client: AsyncClient, test_user_data):
        """Test user login"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50
        assert len(data["refresh_token"]) > 50

    async def test_login_user_wrong_password(
        self, client: AsyncClient, test_user_data
    ):
        """Test login with wrong password fails"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Try to login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_user_nonexistent(self, client: AsyncClient):
        """Test login with non-existent user fails"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, test_user_data):
        """Test getting current authenticated user"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token fails"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No credentials

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token fails"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, test_user_data):
        """Test refreshing access token"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refreshing with invalid token fails"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401

    async def test_update_user_profile(self, client: AsyncClient, test_user_data):
        """Test updating user profile"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Update profile
        update_data = {"name": "Updated Name"}
        response = await client.put(
            "/api/v1/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Name"

    async def test_change_password(self, client: AsyncClient, test_user_data):
        """Test changing password"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Change password
        new_password = "newpassword123"
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": test_user_data["password"],
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Try to login with old password (should fail)
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 401

        # Login with new password (should succeed)
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": new_password
            }
        )
        assert response.status_code == 200

    async def test_change_password_wrong_current(
        self, client: AsyncClient, test_user_data
    ):
        """Test changing password with wrong current password fails"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Try to change password with wrong current password
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

    async def test_password_reset_request(
        self, client: AsyncClient, test_user_data
    ):
        """Test requesting password reset"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Request password reset
        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user_data["email"]}
        )

        assert response.status_code == 202
        data = response.json()

        assert "token" in data  # TODO: Remove in production, send via email

    async def test_password_reset_confirm(
        self, client: AsyncClient, test_user_data, test_db
    ):
        """Test confirming password reset"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Generate reset token
        token = create_password_reset_token(test_user_data["email"])

        # Reset password
        new_password = "resetpassword123"
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": token,
                "new_password": new_password
            }
        )

        assert response.status_code == 204

        # Login with new password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": new_password
            }
        )
        assert response.status_code == 200

    async def test_verify_email(
        self, client: AsyncClient, test_user_data, test_db
    ):
        """Test email verification"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Generate verification token
        token = create_email_verification_token(test_user_data["email"])

        # Verify email
        response = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": token}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email_verified"] is True

    async def test_auth_status(self, client: AsyncClient, test_user_data):
        """Test checking authentication status"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Check auth status
        response = await client.get(
            "/api/v1/auth/status",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["authenticated"] is True
        assert data["user"]["email"] == test_user_data["email"]

    async def test_logout(self, client: AsyncClient, test_user_data):
        """Test logout endpoint"""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204
