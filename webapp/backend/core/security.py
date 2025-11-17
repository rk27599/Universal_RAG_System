"""
Security-First Authentication & Authorization
Local-only authentication with no external dependencies
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import hashlib
import secrets
import time

from core.config import settings
from core.database import get_db

# Password hashing configuration (reduced rounds for development)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=4  # Reduced from default 12 for faster development (use 12+ in production)
)

# JWT token configuration
security = HTTPBearer()

# Security constants
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class SecurityManager:
    """Centralized security management"""

    def __init__(self):
        self.failed_attempts = {}  # Track failed login attempts
        self.rate_limits = {}      # Track rate limiting

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)

    def validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        return True

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None

    def check_rate_limit(self, identifier: str, max_requests: int = 100, window: int = 60) -> bool:
        """Check if request is within rate limits"""
        now = time.time()
        window_start = now - window

        # Clean old entries
        if identifier in self.rate_limits:
            self.rate_limits[identifier] = [
                req_time for req_time in self.rate_limits[identifier]
                if req_time > window_start
            ]
        else:
            self.rate_limits[identifier] = []

        # Check if under limit
        if len(self.rate_limits[identifier]) >= max_requests:
            return False

        # Add current request
        self.rate_limits[identifier].append(now)
        return True

    def check_failed_attempts(self, identifier: str, max_attempts: int = 5, lockout_time: int = 300) -> bool:
        """Check if identifier is locked out due to failed attempts"""
        now = time.time()

        if identifier in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[identifier]

            # Reset if lockout time has passed
            if now - last_attempt > lockout_time:
                del self.failed_attempts[identifier]
                return True

            # Check if under limit
            if attempts >= max_attempts:
                return False

        return True

    def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt"""
        now = time.time()
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, now)
        else:
            self.failed_attempts[identifier] = (1, now)

    def generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()

# Global security manager
security_manager = SecurityManager()

# Security dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security_manager.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    from models.user import User
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def check_admin_privileges(current_user = Depends(get_current_user)):
    """Check if current user has admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Rate limiting middleware
async def rate_limit_middleware(request: Request):
    """Rate limiting middleware"""
    client_ip = request.client.host

    if not security_manager.check_rate_limit(
        client_ip,
        max_requests=settings.RATE_LIMIT_REQUESTS,
        window=settings.RATE_LIMIT_WINDOW
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

# Security validation functions
def validate_input_security(data: str, max_length: int = 1000) -> bool:
    """Validate input for security threats"""
    # Check length
    if len(data) > max_length:
        return False

    # Check for common injection patterns
    dangerous_patterns = [
        "<script", "javascript:", "onload=", "onerror=",
        "SELECT", "DROP", "INSERT", "UPDATE", "DELETE",
        "../", "..\\", "/etc/", "C:\\",
        "eval(", "exec(", "system(", "shell_exec("
    ]

    data_lower = data.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in data_lower:
            return False

    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for secure storage"""
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]

    # Remove dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename

def generate_secure_token() -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(32)

# Security audit logging
class SecurityAuditLogger:
    """Security event logging"""

    @staticmethod
    def log_authentication_attempt(username: str, success: bool, ip_address: str):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        print(f"🔐 AUTH {status}: {username} from {ip_address} at {datetime.utcnow()}")

    @staticmethod
    def log_authorization_failure(username: str, resource: str, ip_address: str):
        """Log authorization failure"""
        print(f"🚫 AUTHZ FAILED: {username} attempted {resource} from {ip_address}")

    @staticmethod
    def log_security_violation(violation_type: str, details: str, ip_address: str):
        """Log security violation"""
        print(f"🚨 SECURITY VIOLATION: {violation_type} - {details} from {ip_address}")

    @staticmethod
    def log_data_access(username: str, resource: str, action: str):
        """Log data access for audit trail"""
        print(f"📊 DATA ACCESS: {username} {action} {resource} at {datetime.utcnow()}")

# Global audit logger
audit_logger = SecurityAuditLogger()

# Security validation on startup
def validate_security_configuration():
    """Validate security configuration"""

    # Check secret key strength
    if len(SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")

    # Check token expiration
    if ACCESS_TOKEN_EXPIRE_MINUTES > 480:  # 8 hours max
        print("⚠️  Warning: Token expiration time is very long")

    # Validate algorithm
    if ALGORITHM not in ["HS256", "HS384", "HS512"]:
        raise ValueError("Invalid JWT algorithm")

    print("✅ Security configuration validated")

# Run validation on import
validate_security_configuration()
# ============================================================================
# Convenience Functions for Testing and Simple Use Cases
# ============================================================================

# Create a global security manager instance
_security_manager = SecurityManager()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash - convenience wrapper"""
    return _security_manager.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash - convenience wrapper"""
    return _security_manager.get_password_hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token - convenience wrapper"""
    return _security_manager.create_access_token(data, expires_delta)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT token and return payload - convenience wrapper"""
    return _security_manager.verify_token(token)
