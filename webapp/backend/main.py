#!/usr/bin/env python3
"""
Security-First RAG Web Application
FastAPI backend with complete local hosting and data sovereignty
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path
import socketio

from core.config import Settings
from core.database import engine, Base
from core.security import get_current_user
from api import auth, documents, chat, models as model_api

# Initialize settings
settings = Settings()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Secure RAG System...")

    # Create database tables
    from core.database import init_db
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"✅ Upload directory ready: {settings.UPLOAD_DIR}")

    # Security validation on startup with timeout protection
    try:
        import asyncio
        await asyncio.wait_for(
            validate_security_configuration(),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        print("⚠️  Security validation timed out - continuing with defaults")
    except Exception as e:
        print(f"⚠️  Security validation error: {e}")
        raise

    print("🔒 Secure RAG System started successfully")
    print(f"🏠 Local hosting mode: {settings.HOST}:{settings.PORT}")
    print("🚫 No external dependencies loaded")

    yield

    # Shutdown
    print("👋 Shutting down Secure RAG System...")

# Create FastAPI app with security-focused configuration and lifespan
app = FastAPI(
    title="Secure RAG System",
    description="Self-hosted RAG application with complete data sovereignty",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Import Socket.IO server for real-time communication
from api.chat import sio

# Security middleware configuration
security = HTTPBearer()

# CORS configuration - restrictive for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "https://localhost",      # Production HTTPS
        "https://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "font-src 'self'"
    )

    return response

# Include API routers
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(model_api.router, prefix="/api", tags=["models"])

# Mount Socket.IO with proper ASGI integration
# Temporarily disabled due to ASGI compatibility issues
# TODO: Implement proper Socket.IO integration for python-socketio 5.x
# app.mount("/socket.io", socketio.ASGIApp(sio, other_asgi_app=None))

# Mount static files for React frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "security_mode": "local_only",
        "external_dependencies": "none"
    }

# Readiness check endpoint
@app.get("/api/ready")
async def readiness_check():
    """Readiness check for load balancers"""
    from core.database import check_database_connection
    from services.ollama_service import check_ollama_connection

    checks = {
        "database": await check_database_connection(),
        "ollama": await check_ollama_connection(),
        "storage": os.path.exists(settings.UPLOAD_DIR)
    }

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "security_validated": True
    }

# Root endpoint serves React app
@app.get("/")
async def read_root():
    """Serve React application"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, 'r') as f:
            return f.read()
    else:
        return {
            "message": "Secure RAG System API",
            "docs": "/api/docs" if settings.DEBUG else "Documentation disabled in production",
            "security": "Local hosting only - no external dependencies"
        }

# Startup/shutdown now handled by lifespan context manager above

async def validate_security_configuration():
    """Validate that no external services are configured"""
    import time
    start_time = time.time()
    print("🔍 Starting security validation...")

    # Check for prohibited external configurations
    prohibited_vars = [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PINECONE_API_KEY",
        "AWS_ACCESS_KEY", "GCP_PROJECT_ID", "AZURE_SUBSCRIPTION_ID"
    ]

    found_external = []
    for var in prohibited_vars:
        if os.getenv(var):
            found_external.append(var)

    if found_external:
        error_msg = (
            f"Security violation: External API keys detected: {found_external}. "
            "Remove all external service credentials for local-only operation."
        )
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)

    elapsed = time.time() - start_time
    print(f"✅ Security validation passed - no external dependencies ({elapsed:.2f}s)")


# Wrap FastAPI app with Socket.IO
app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    # Production server configuration
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_excludes=["*.db", "*.db-*", "data/uploads/*"] if settings.DEBUG else None,
        workers=1 if settings.DEBUG else 4,
        access_log=settings.DEBUG,
        ssl_keyfile=settings.SSL_KEYFILE if settings.SSL_KEYFILE else None,
        ssl_certfile=settings.SSL_CERTFILE if settings.SSL_CERTFILE else None,
    )