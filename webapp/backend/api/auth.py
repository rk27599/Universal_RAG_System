from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from core.database import get_db
from core.security import (
    security_manager,
    get_current_user as get_current_user_dep,
    audit_logger
)
from models.user import User, UserLoginLog

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    fullName: str = "User"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    fullName: str
    isAdmin: bool
    isActive: bool


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint with database validation"""
    try:
        # Find user by username
        user = db.query(User).filter(User.username == request.username).first()

        if not user:
            audit_logger.log_authentication_attempt(request.username, False, "unknown")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if account is active and not locked
        if not user.can_login():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked or inactive"
            )

        # Verify password
        if not security_manager.verify_password(request.password, user.password_hash):
            user.increment_failed_attempts()
            db.commit()
            audit_logger.log_authentication_attempt(request.username, False, "unknown")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Reset failed attempts on successful login
        user.reset_failed_attempts()

        # Create session
        session_id = security_manager.generate_session_id()
        user.update_session(session_id)
        db.commit()

        # Generate JWT token
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "session_id": session_id
        }
        access_token = security_manager.create_access_token(
            token_data,
            expires_delta=timedelta(minutes=30)
        )

        # Log successful login
        audit_logger.log_authentication_attempt(user.username, True, "unknown")

        # Return user data
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "fullName": user.full_name or "User",
            "isAdmin": user.is_admin,
            "isActive": user.is_active
        }

        return {
            "success": True,
            "data": {
                "token": access_token,
                "user": user_data
            },
            "message": "Login successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user endpoint"""
    try:
        # Check if username exists
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Check if email exists
        existing_email = db.query(User).filter(User.email == request.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate password strength
        if not security_manager.validate_password_strength(request.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            )

        # Create new user
        hashed_password = security_manager.get_password_hash(request.password)
        new_user = User(
            username=request.username,
            email=request.email,
            full_name=request.fullName,
            password_hash=hashed_password,
            is_active=True,
            is_admin=False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✅ New user registered: {new_user.username}")

        return {
            "success": True,
            "data": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            },
            "message": "Registration successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_user_dep)):
    """Get current authenticated user"""
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "fullName": current_user.full_name or "User",
        "isAdmin": current_user.is_admin,
        "isActive": current_user.is_active
    }

    return {
        "success": True,
        "data": user_data,
        "message": "User retrieved successfully"
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user_dep), db: Session = Depends(get_db)):
    """Logout current user"""
    try:
        # Clear user session
        current_user.clear_session()
        db.commit()

        audit_logger.log_data_access(current_user.username, "logout", "performed")

        return {
            "success": True,
            "message": "Logged out successfully"
        }
    except Exception as e:
        print(f"❌ Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
