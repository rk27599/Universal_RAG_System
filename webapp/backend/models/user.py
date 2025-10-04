"""
User Model with Security-First Design
Local authentication with comprehensive audit trail
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from core.database import BaseModel, SecurityAuditMixin


class User(BaseModel, SecurityAuditMixin):
    """User model with security features"""
    __tablename__ = "users"

    # Basic user information
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)

    # Authentication
    password_hash = Column(String(255), nullable=False)
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Security features
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    # Session management
    current_session_id = Column(String(64), nullable=True)
    session_created_at = Column(DateTime(timezone=True), nullable=True)

    # User preferences
    preferred_model = Column(String(50), default="mistral")
    max_conversation_length = Column(Integer, default=100)
    enable_conversation_history = Column(Boolean, default=True)

    # Data privacy settings
    data_retention_days = Column(Integer, default=365)  # How long to keep user data
    allow_analytics = Column(Boolean, default=False)    # Always False for privacy

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    # Database indexes for performance
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_active', 'is_active'),
        Index('idx_user_session', 'current_session_id'),
    )

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

    @property
    def is_locked(self) -> bool:
        """Check if user account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def can_login(self) -> bool:
        """Check if user can login (active and not locked)"""
        return self.is_active and not self.is_locked

    def increment_failed_attempts(self, max_attempts: int = 5, lockout_minutes: int = 15):
        """Increment failed login attempts and lock if necessary"""
        self.failed_login_attempts += 1

        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)

    def reset_failed_attempts(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()

    def update_session(self, session_id: str, ip_address: str = None):
        """Update user session information"""
        self.current_session_id = session_id
        self.session_created_at = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address

    def clear_session(self):
        """Clear user session"""
        self.current_session_id = None
        self.session_created_at = None

    def get_security_summary(self) -> dict:
        """Get security summary for user"""
        return {
            "account_status": "active" if self.is_active else "inactive",
            "is_locked": self.is_locked,
            "failed_attempts": self.failed_login_attempts,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "password_age_days": (datetime.utcnow() - self.password_changed_at).days,
            "has_active_session": self.current_session_id is not None,
            "is_admin": self.is_admin
        }


class UserLoginLog(BaseModel):
    """User login audit log"""
    __tablename__ = "user_login_logs"

    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)  # Store username for audit even if user deleted

    # Login attempt details
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)

    # Security details
    session_id = Column(String(64), nullable=True)
    failure_reason = Column(String(100), nullable=True)  # If login failed

    # Geographic info (if available locally)
    country = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)

    # Additional security metadata
    security_flags = Column(Text, nullable=True)  # JSON string of security flags

    # Database indexes
    __table_args__ = (
        Index('idx_login_log_user', 'user_id'),
        Index('idx_login_log_timestamp', 'created_at'),
        Index('idx_login_log_ip', 'ip_address'),
        Index('idx_login_log_success', 'success'),
    )

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<LoginLog({status}: {self.username} from {self.ip_address})>"


class UserSession(BaseModel):
    """Active user sessions tracking"""
    __tablename__ = "user_sessions"

    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session details
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)

    # Session management
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Security tracking
    login_method = Column(String(20), default="password")  # password, token, etc.
    security_level = Column(String(20), default="standard")  # standard, elevated

    # Device tracking (for user convenience)
    device_fingerprint = Column(String(64), nullable=True)
    device_name = Column(String(100), nullable=True)

    # Database indexes
    __table_args__ = (
        Index('idx_session_user', 'user_id'),
        Index('idx_session_id', 'session_id'),
        Index('idx_session_active', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<Session({self.session_id}: User {self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

    def extend_session(self, minutes: int = 30):
        """Extend session expiration"""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.last_activity = datetime.utcnow()

    def invalidate(self):
        """Invalidate session"""
        self.is_active = False