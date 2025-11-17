"""
Integration Tests for Authentication API
Tests authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main import app
from core.database import get_db
from models.user import User
from core.security import get_password_hash


class TestAuthAPI:
    """Test Authentication API"""

    @pytest.fixture
    def client(self, test_db_session):
        """Create test client with database override"""
        def override_get_db():
            try:
                yield test_db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def existing_user(self, test_db_session):
        """Create an existing user for login tests"""
        user = User(
            username="existinguser",
            email="existing@example.com",
            hashed_password=get_password_hash("Password123!"),
            is_active=True
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        return user

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert data["data"]["user"]["username"] == "newuser"

    def test_register_duplicate_username(self, client, existing_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": existing_user.username,
                "email": "different@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["message"].lower()

    def test_register_duplicate_email(self, client, existing_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": existing_user.email,
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "weak"
            }
        )

        # Should fail validation (depending on password requirements)
        assert response.status_code in [400, 422]

    def test_login_success(self, client, existing_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": existing_user.username,
                "password": "Password123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert data["data"]["user"]["username"] == existing_user.username

    def test_login_wrong_password(self, client, existing_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": existing_user.username,
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "Password123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_login_inactive_user(self, client, test_db_session):
        """Test login with inactive user"""
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=get_password_hash("Password123!"),
            is_active=False
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "username": "inactive",
                "password": "Password123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_protected_endpoint_with_token(self, client, existing_user):
        """Test accessing protected endpoint with valid token"""
        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": existing_user.username,
                "password": "Password123!"
            }
        )

        token = login_response.json()["data"]["token"]

        # Access protected endpoint
        response = client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should succeed (200 or 404 if no documents)
        assert response.status_code in [200, 404]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/documents")

        assert response.status_code == 401

    def test_protected_endpoint_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/documents",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )

        assert response.status_code == 401

    def test_token_expiration(self, client, existing_user):
        """Test token expiration handling"""
        # This would require mocking time or using short-lived tokens
        # Placeholder for actual implementation
        pass
