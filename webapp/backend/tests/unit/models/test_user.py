"""
Unit Tests for User Model
Tests User database model
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from models.user import User
from core.security import get_password_hash


class TestUserModel:
    """Test User Model"""

    def test_create_user(self, test_db_session):
        """Test creating a new user"""
        user = User(
            username="newuser",
            email="new@example.com",
            hashed_password=get_password_hash("Password123!")
        )

        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.is_active is True  # Default value
        assert user.created_at is not None

    def test_user_unique_username(self, test_db_session):
        """Test username must be unique"""
        user1 = User(
            username="duplicate",
            email="user1@example.com",
            hashed_password=get_password_hash("Pass1")
        )
        test_db_session.add(user1)
        test_db_session.commit()

        # Try to create user with same username
        user2 = User(
            username="duplicate",
            email="user2@example.com",
            hashed_password=get_password_hash("Pass2")
        )
        test_db_session.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db_session.commit()

    def test_user_unique_email(self, test_db_session):
        """Test email must be unique"""
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            hashed_password=get_password_hash("Pass1")
        )
        test_db_session.add(user1)
        test_db_session.commit()

        # Try to create user with same email
        user2 = User(
            username="user2",
            email="duplicate@example.com",
            hashed_password=get_password_hash("Pass2")
        )
        test_db_session.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db_session.commit()

    def test_user_relationships(self, test_db_session, test_user):
        """Test user relationships (documents, conversations)"""
        # Create document for user
        from models.document import Document

        document = Document(
            title="Test Doc",
            file_path="/test/doc.pdf",
            file_type="application/pdf",
            file_size=1024,
            user_id=test_user.id
        )
        test_db_session.add(document)
        test_db_session.commit()

        # Refresh user
        test_db_session.refresh(test_user)

        # Check relationship
        assert len(test_user.documents) == 1
        assert test_user.documents[0].title == "Test Doc"

    def test_user_soft_delete(self, test_db_session, test_user):
        """Test user soft delete (is_active flag)"""
        # Deactivate user
        test_user.is_active = False
        test_db_session.commit()

        # User still exists but is inactive
        user = test_db_session.query(User).filter_by(id=test_user.id).first()
        assert user is not None
        assert user.is_active is False

    def test_user_password_not_exposed(self, test_user):
        """Test that password hash is stored securely"""
        # Password should be hashed, not plain text
        assert test_user.hashed_password != "TestPassword123!"
        assert test_user.hashed_password.startswith("$2b$")

    def test_user_created_at_timestamp(self, test_db_session):
        """Test user created_at timestamp"""
        before = datetime.utcnow()

        user = User(
            username="timetest",
            email="time@example.com",
            hashed_password=get_password_hash("Pass123!")
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)

        after = datetime.utcnow()

        assert before <= user.created_at <= after

    def test_user_query_by_username(self, test_db_session, test_user):
        """Test querying user by username"""
        user = test_db_session.query(User).filter_by(
            username=test_user.username
        ).first()

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_user_query_by_email(self, test_db_session, test_user):
        """Test querying user by email"""
        user = test_db_session.query(User).filter_by(
            email=test_user.email
        ).first()

        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
