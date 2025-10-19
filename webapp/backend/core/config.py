"""
Security-First Configuration Management
All settings prioritize local hosting and data sovereignty
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings with security-first defaults"""

    # Application settings
    APP_NAME: str = "Secure RAG System"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"  # Localhost only for security
    PORT: int = 8000

    # Security settings
    SECRET_KEY: str = os.urandom(32).hex()  # Generate secure key
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # SSL/TLS settings for production
    SSL_KEYFILE: Optional[str] = None
    SSL_CERTFILE: Optional[str] = None

    # Database settings - LOCAL ONLY
    # PostgreSQL (Primary - 50x faster vector search with pgvector)
    # SQLite fallback available for development (slower performance)
    DATABASE_URL: str = "postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database"
    DATABASE_ECHO: bool = False  # Set to True for SQL debugging

    # LLM Provider settings - LOCAL ONLY
    LLM_PROVIDER: str = "ollama"  # Options: "ollama", "vllm"

    # Ollama settings - LOCAL ONLY
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "mistral"
    AVAILABLE_MODELS: list = ["mistral", "llama2", "codellama"]

    # vLLM settings - LOCAL ONLY (High-performance multi-GPU inference)
    VLLM_BASE_URL: str = "http://localhost:8001"
    VLLM_MODEL_PATH: str = "/models"  # Path to vLLM models
    VLLM_GPU_COUNT: int = 1  # Number of GPUs available
    VLLM_TENSOR_PARALLEL_SIZE: int = 1  # Tensor parallelism size (1-8, must divide GPU count)

    # File storage settings - LOCAL ONLY
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: set = {".pdf", ".html", ".txt", ".md", ".docx"}

    # Vector storage settings
    VECTOR_DIMENSION: int = 1024  # For BGE-M3 embeddings (BAAI/bge-m3)
    MAX_CHUNKS_PER_DOCUMENT: int = 1000

    # Chat settings
    MAX_CONVERSATION_HISTORY: int = 100
    MAX_MESSAGE_LENGTH: int = 8000

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/rag_app.log"

    # Redis settings - LOCAL ONLY (for Socket.IO session management)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = True  # Set to False to disable Redis (single worker only)

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v):
        """Ensure Redis is localhost only"""
        if v and ("localhost" not in v and "127.0.0.1" not in v):
            raise ValueError("Redis must be localhost for security compliance")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database is localhost only"""
        if v.startswith("sqlite://"):
            return v  # SQLite is local by default
        if "localhost" not in v and "127.0.0.1" not in v:
            raise ValueError("Database must be localhost for security compliance")
        return v

    @field_validator("OLLAMA_BASE_URL")
    @classmethod
    def validate_ollama_url(cls, v):
        """Ensure Ollama is localhost only"""
        if "localhost" not in v and "127.0.0.1" not in v:
            raise ValueError("Ollama must be localhost for security compliance")
        return v

    @field_validator("VLLM_BASE_URL")
    @classmethod
    def validate_vllm_url(cls, v):
        """Ensure vLLM is localhost only"""
        if "localhost" not in v and "127.0.0.1" not in v:
            raise ValueError("vLLM must be localhost for security compliance")
        return v

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v):
        """Ensure LLM provider is valid"""
        valid_providers = ["ollama", "vllm"]
        if v.lower() not in valid_providers:
            raise ValueError(f"LLM_PROVIDER must be one of {valid_providers}")
        return v.lower()

    @field_validator("HOST")
    @classmethod
    def validate_host(cls, v):
        """Ensure host is localhost for security"""
        if v not in ["127.0.0.1", "localhost", "0.0.0.0"]:
            raise ValueError("Host must be localhost for security compliance")
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

    def get_database_url(self) -> str:
        """Get database URL with connection pooling settings"""
        if self.DATABASE_URL.startswith("sqlite://"):
            return self.DATABASE_URL
        # For PostgreSQL, add connection parameters
        if "?" in self.DATABASE_URL:
            return f"{self.DATABASE_URL}&sslmode=disable"
        else:
            return f"{self.DATABASE_URL}?sslmode=disable"

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG

    def get_allowed_origins(self) -> list:
        """Get allowed CORS origins based on environment"""
        if self.DEBUG:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000"
            ]
        else:
            return [
                "https://localhost",
                "https://127.0.0.1",
                f"https://{self.HOST}:{self.PORT}"
            ]

    def get_security_headers(self) -> dict:
        """Get security headers configuration"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }


# Global settings instance
settings = Settings()

# Validate security configuration on import
def validate_security_settings():
    """Validate that all settings comply with security requirements"""

    # Check for prohibited external service configurations
    prohibited_env_vars = [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "COHERE_API_KEY",
        "PINECONE_API_KEY", "WEAVIATE_URL", "QDRANT_URL",
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS", "GCP_PROJECT_ID",
        "AZURE_SUBSCRIPTION_ID", "AZURE_CLIENT_ID"
    ]

    external_configs_found = []
    for var in prohibited_env_vars:
        if os.getenv(var):
            external_configs_found.append(var)

    if external_configs_found:
        raise ValueError(
            f"Security violation: External service configurations detected: {external_configs_found}. "
            "Remove all external API keys and service configurations for local-only operation."
        )

    # Validate local-only URLs
    if not settings.DATABASE_URL.startswith("sqlite://") and "localhost" not in settings.DATABASE_URL and "127.0.0.1" not in settings.DATABASE_URL:
        raise ValueError("Database URL must be localhost for security compliance")

    if "localhost" not in settings.OLLAMA_BASE_URL and "127.0.0.1" not in settings.OLLAMA_BASE_URL:
        raise ValueError("Ollama URL must be localhost for security compliance")

    if "localhost" not in settings.VLLM_BASE_URL and "127.0.0.1" not in settings.VLLM_BASE_URL:
        raise ValueError("vLLM URL must be localhost for security compliance")

    print(f"✅ Security settings validation passed (LLM Provider: {settings.LLM_PROVIDER})")

# Run validation on import
validate_security_settings()