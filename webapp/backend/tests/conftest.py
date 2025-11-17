"""
Pytest Configuration and Shared Fixtures
Provides common fixtures for all tests
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Base, get_db
from core.config import Settings
from models.user import User
from models.document import Document, Chunk
from models.conversation import Conversation, Message


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test application settings"""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["POSTGRES_USER"] = "test_user"
    os.environ["POSTGRES_PASSWORD"] = "test_password"
    os.environ["POSTGRES_DB"] = "test_db"

    from core.config import Settings
    return Settings()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine (in-memory SQLite)"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_db(test_db_session) -> Generator[Session, None, None]:
    """Alias for test_db_session"""
    return test_db_session


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def test_user(test_db_session: Session) -> User:
    """Create a test user"""
    from core.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return user


@pytest.fixture
def test_admin_user(test_db_session: Session) -> User:
    """Create a test admin user"""
    from core.security import get_password_hash

    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("Admin@123"),
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return user


@pytest.fixture
def test_auth_token(test_user: User) -> str:
    """Create a test JWT token"""
    from core.security import create_access_token

    token = create_access_token(data={"sub": test_user.username})
    return token


# ============================================================================
# Document Fixtures
# ============================================================================

@pytest.fixture
def test_document(test_db_session: Session, test_user: User) -> Document:
    """Create a test document"""
    document = Document(
        title="Test Document",
        source_path="/test/path/test.pdf",
        source_type="file",
        content_type="application/pdf",
        file_size=1024,
        content_hash="test_hash_123",
        user_id=test_user.id,
        processing_status="completed"
    )
    test_db_session.add(document)
    test_db_session.commit()
    test_db_session.refresh(document)

    return document


@pytest.fixture
def test_document_chunks(test_db_session: Session, test_document: Document):
    """Create test document chunks"""
    chunks = []
    for i in range(5):
        chunk = Chunk(
            document_id=test_document.id,
            chunk_order=i,
            content=f"Test chunk content {i}. This is a sample text for testing.",
            content_hash=f"hash{i}",
            character_count=50,
            token_count=10,
            word_count=8,
            page_number=i + 1
        )
        chunks.append(chunk)
        test_db_session.add(chunk)

    test_db_session.commit()
    return chunks


# ============================================================================
# Conversation Fixtures
# ============================================================================

@pytest.fixture
def test_conversation(test_db_session: Session, test_user: User) -> Conversation:
    """Create a test conversation"""
    conversation = Conversation(
        title="Test Conversation",
        user_id=test_user.id
    )
    test_db_session.add(conversation)
    test_db_session.commit()
    test_db_session.refresh(conversation)

    return conversation


@pytest.fixture
def test_messages(test_db_session: Session, test_conversation: Conversation):
    """Create test messages"""
    messages = []

    # User message
    user_msg = Message(
        conversation_id=test_conversation.id,
        role="user",
        content="What is machine learning?"
    )
    messages.append(user_msg)
    test_db_session.add(user_msg)

    # Assistant message
    assistant_msg = Message(
        conversation_id=test_conversation.id,
        role="assistant",
        content="Machine learning is a subset of artificial intelligence...",
        metadata_={"sources": [], "model": "mistral"}
    )
    messages.append(assistant_msg)
    test_db_session.add(assistant_msg)

    test_db_session.commit()
    return messages


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_ollama_service():
    """Mock Ollama service"""
    mock = AsyncMock()
    mock.generate.return_value = {
        "response": "This is a test response from Ollama",
        "model": "mistral",
        "done": True
    }
    mock.list_models.return_value = [
        {"name": "mistral", "size": "4.1GB"},
        {"name": "llama2", "size": "3.8GB"}
    ]
    mock.is_available.return_value = True
    return mock


@pytest.fixture
def mock_vllm_service():
    """Mock vLLM service"""
    mock = AsyncMock()
    mock.generate.return_value = {
        "response": "This is a test response from vLLM",
        "model": "Qwen3-4B-Thinking-2507-FP8",
        "done": True
    }
    mock.is_available.return_value = True
    return mock


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    mock = Mock()
    mock.embed_text.return_value = [0.1] * 1024  # BGE-M3 dimension
    mock.embed_batch.return_value = [[0.1] * 1024 for _ in range(5)]
    mock.dimension = 1024
    return mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock = AsyncMock()
    mock.set = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=True)
    mock.ping = AsyncMock(return_value=True)
    return mock


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_pdf_path() -> Path:
    """Path to sample PDF for testing"""
    return Path(__file__).parent / "test_data" / "pdfs" / "simple.pdf"


@pytest.fixture
def sample_html_path() -> Path:
    """Path to sample HTML for testing"""
    return Path(__file__).parent / "test_data" / "html" / "simple.html"


@pytest.fixture
def sample_embedding_vector():
    """Sample embedding vector (BGE-M3 1024-dim)"""
    import numpy as np
    return np.random.rand(1024).tolist()


@pytest.fixture
def sample_text_chunk():
    """Sample text chunk for testing"""
    return """
    Machine learning is a subset of artificial intelligence that focuses on
    building systems that can learn from and make decisions based on data.
    It involves algorithms that improve automatically through experience.
    """


# ============================================================================
# Event Loop Fixtures for Async Tests
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test"""
    yield

    # Cleanup any temporary test files
    test_uploads = Path("/tmp/test_uploads")
    if test_uploads.exists():
        import shutil
        shutil.rmtree(test_uploads)
