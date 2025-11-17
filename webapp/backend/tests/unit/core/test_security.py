"""
Unit Tests for Security Module
Tests JWT & password hashing
"""

import pytest
from datetime import timedelta
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_password_hashing(self):
        """Test password is hashed correctly"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_password_verification_success(self):
        """Test correct password verification"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test incorrect password verification"""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # Different due to random salt
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_empty_password(self):
        """Test empty password handling"""
        hashed = get_password_hash("")
        assert len(hashed) > 0
        assert verify_password("", hashed)

    def test_special_characters_password(self):
        """Test password with special characters"""
        password = "P@$$w0rd!#%&*(){}[]"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed)

    def test_unicode_password(self):
        """Test password with unicode characters"""
        password = "パスワード123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed)


class TestJWTTokens:
    """Test JWT token functions"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT format: header.payload.signature

    def test_create_token_with_expiration(self):
        """Test JWT token with custom expiration"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding valid JWT token"""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded.get("sub") == "testuser"
        assert decoded.get("role") == "user"
        assert "exp" in decoded  # Expiration should be added

    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token"""
        invalid_token = "invalid.jwt.token"

        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_expired_token(self):
        """Test decoding expired JWT token"""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)

        # Wait a moment to ensure expiration
        import time
        time.sleep(0.1)

        decoded = decode_access_token(token)

        assert decoded is None  # Expired token should return None

    def test_token_with_extra_claims(self):
        """Test JWT token with extra claims"""
        data = {
            "sub": "testuser",
            "email": "test@example.com",
            "roles": ["admin", "user"],
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded.get("sub") == "testuser"
        assert decoded.get("email") == "test@example.com"
        assert decoded.get("roles") == ["admin", "user"]
        assert decoded.get("permissions") == ["read", "write"]

    def test_token_without_subject(self):
        """Test JWT token without subject claim"""
        data = {"user_id": 123}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded.get("user_id") == 123

    def test_multiple_tokens_different(self):
        """Test that multiple tokens for same data are different"""
        data = {"sub": "testuser"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        # Tokens should be different due to different 'iat' (issued at) claim
        assert token1 != token2

        # But both should decode to same data (except timestamp)
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)

        assert decoded1["sub"] == decoded2["sub"]
