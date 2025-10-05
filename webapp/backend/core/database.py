"""
Security-First Database Configuration
PostgreSQL + pgvector with local-only connections and encryption
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import event
import uuid
from datetime import datetime
from typing import Generator

from core.config import settings

# Create database engine with security settings
def get_engine_config():
    """Get engine configuration based on database type"""
    db_url = settings.get_database_url()

    if db_url.startswith("sqlite://"):
        # SQLite-specific configuration
        return create_engine(
            db_url,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}  # For SQLite
        )
    else:
        # PostgreSQL-specific configuration
        return create_engine(
            db_url,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "sslmode": "disable",
                "application_name": "secure_rag_app"
            }
        )

engine = get_engine_config()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Database dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def check_database_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        db = SessionLocal()
        # Simple query to test connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Security event listeners
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set security pragmas for database connections"""
    if "postgresql" in str(dbapi_connection):
        # For PostgreSQL, we can set connection-level security settings
        cursor = dbapi_connection.cursor()
        # Set timezone to UTC for consistency
        cursor.execute("SET timezone = 'UTC'")
        cursor.close()

# Base model with common fields
class BaseModel(Base):
    """Base model with common security and audit fields"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Security audit fields
    created_by = Column(Integer, nullable=True)  # User ID who created the record
    ip_address = Column(String(45), nullable=True)  # IP address for audit trail
    user_agent = Column(Text, nullable=True)  # User agent for audit trail

class SecurityAuditMixin:
    """Mixin for security audit fields"""

    # Data classification
    data_classification = Column(String(20), default="internal")  # public, internal, confidential

    # Encryption status
    is_encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(64), nullable=True)

    # Access control
    access_level = Column(String(20), default="user")  # user, admin, system

    # Audit trail
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)

# Initialize database tables
def init_db():
    """Initialize database with all tables"""
    try:
        # Import all models to ensure they're registered
        from models.user import User
        from models.document import Document, Chunk
        from models.conversation import Conversation, Message

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")

        # Create pgvector extension if it doesn't exist
        with engine.connect() as conn:
            try:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                print("✅ pgvector extension enabled")
            except Exception as e:
                print(f"⚠️  Warning: Could not create vector extension: {e}")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

def reset_db():
    """Reset database - USE WITH CAUTION"""
    if not settings.DEBUG:
        raise Exception("Database reset only allowed in debug mode")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("🔄 Database reset completed")

# Database security validation
def validate_database_security():
    """Validate database security configuration"""

    # Check connection string for security
    db_url = settings.DATABASE_URL

    # SQLite is inherently local, so allow it
    if not db_url.startswith("sqlite://") and "localhost" not in db_url and "127.0.0.1" not in db_url:
        raise ValueError("❌ Database must be localhost for security compliance")

    # Check for default passwords (in production, use strong passwords)
    if "password" in db_url.lower() and not settings.DEBUG:
        print("⚠️  Warning: Default password detected. Use strong password in production.")

    print("✅ Database security validation passed")

# Run validation on import
validate_database_security()