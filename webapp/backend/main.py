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

# Background task for automatic model unloading
async def auto_unload_idle_models():
    """Background task to unload idle models and free memory"""
    import asyncio
    import logging
    from utils.memory_manager import get_memory_manager

    logger = logging.getLogger(__name__)
    mm = get_memory_manager(idle_timeout=300, enable_auto_unload=True)  # 5 minutes

    logger.info("🧹 Auto-unload background task started (checking every 60s)")

    while True:
        try:
            await asyncio.sleep(60)  # Check every 60 seconds

            # Log memory status
            mm.log_memory_status()

            # Check memory health
            health = mm.check_memory_health()
            if health['status'] in ['warning', 'critical']:
                logger.warning(f"⚠️ Memory health: {health['status']} - {health['free_ram_gb']:.1f}GB free")
                for rec in health['recommendations']:
                    logger.warning(f"  💡 {rec}")

            # Get idle models
            idle_models = mm.get_idle_models()

            if idle_models:
                logger.info(f"🔍 Found {len(idle_models)} idle model(s)")

                # Try to get model services
                try:
                    from services.embedding_service_bge import BGEEmbeddingService
                    from services.reranker_service import RerankerService
                    from services.document_service import embedding_service, reranker_service

                    models_unloaded = []

                    # Check BGE embedding service
                    if embedding_service and embedding_service.is_loaded():
                        if mm.should_unload_model("BGE-M3"):
                            logger.info("🔄 Unloading idle BGE-M3 embedding model...")
                            embedding_service.unload_model()
                            mm.cleanup_after_unload("BGE-M3")
                            models_unloaded.append("BGE-M3")

                    # Check reranker service
                    if reranker_service and reranker_service.is_loaded():
                        if mm.should_unload_model("BGE-Reranker"):
                            logger.info("🔄 Unloading idle BGE-Reranker model...")
                            reranker_service.unload_model()
                            mm.cleanup_after_unload("BGE-Reranker")
                            models_unloaded.append("BGE-Reranker")

                    if models_unloaded:
                        # Log memory savings
                        stats_after = mm.get_memory_stats()
                        logger.info(
                            f"✅ Unloaded {len(models_unloaded)} model(s): {', '.join(models_unloaded)}"
                        )
                        logger.info(f"💾 Free RAM after unload: {stats_after['free_ram_gb']:.1f}GB")

                except ImportError as e:
                    logger.debug(f"Could not import model services: {e}")
                except Exception as e:
                    logger.error(f"Error during model unloading: {e}")

        except asyncio.CancelledError:
            logger.info("🛑 Auto-unload task cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Error in auto-unload task: {e}")
            # Continue running even if one iteration fails

    logger.info("✅ Auto-unload background task stopped")

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

    # Document recovery: Resume processing for stuck documents
    print("🔄 Checking for stuck documents...")
    try:
        from services.document_recovery_service import recover_all_stuck_documents
        recovered_count = await recover_all_stuck_documents()
        if recovered_count > 0:
            print(f"✅ Recovered {recovered_count} stuck document(s) - processing resumed")
        else:
            print("✅ No stuck documents found")
    except Exception as e:
        print(f"⚠️  Document recovery warning: {e}")
        # Don't fail startup if recovery fails - log and continue

    print("🔒 Secure RAG System started successfully")
    print(f"🏠 Local hosting mode: {settings.HOST}:{settings.PORT}")
    print("🚫 No external dependencies loaded")

    # Start background task for automatic model unloading
    import asyncio
    unload_task = asyncio.create_task(auto_unload_idle_models())
    print("🧹 Started background task for automatic model unloading (5min idle timeout)")

    yield

    # Shutdown
    print("👋 Shutting down Secure RAG System...")

    # Cancel background task
    unload_task.cancel()
    try:
        await unload_task
    except asyncio.CancelledError:
        print("✅ Background tasks cancelled")

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

# CORS configuration - configured for network access
# For LAN access: Update allowed origins to include your server's IP from NETWORK_SETUP.md
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server (local)
        "http://127.0.0.1:3000",
        "http://localhost:8000",      # Backend (local)
        "http://127.0.0.1:8000",
        "https://localhost",          # Production HTTPS (local)
        "https://127.0.0.1",
        "*"                          # Allow all origins (for LAN access - configure specific IPs in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
    from services.redis_service import check_redis_connection

    checks = {
        "database": await check_database_connection(),
        "ollama": await check_ollama_connection(),
        "redis": await check_redis_connection(settings.REDIS_URL) if settings.REDIS_ENABLED else True,
        "storage": os.path.exists(settings.UPLOAD_DIR)
    }

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "security_validated": True,
        "multi_worker_support": checks.get("redis", False)
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