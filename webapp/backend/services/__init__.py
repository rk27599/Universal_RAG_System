"""
Services Package
Business logic and external integrations
"""

# Import base classes and factory
from .llm_base import BaseLLMService, LLMServiceError, LLMConnectionError, LLMGenerationError
from .llm_factory import (
    LLMServiceFactory,
    get_llm_service,
    check_llm_connection,
    get_available_models,
    generate_response,
    get_current_provider,
    get_provider_info
)

# Import specific providers (for direct access if needed)
from .ollama_service import OllamaService, ollama_service
from .vllm_service import VLLMService, vllm_service

# Backward compatibility: Default to factory methods
# This ensures existing code continues to work without changes
check_ollama_connection = check_llm_connection  # Alias for backward compatibility

__all__ = [
    # Base classes
    'BaseLLMService',
    'LLMServiceError',
    'LLMConnectionError',
    'LLMGenerationError',

    # Factory and convenience functions
    'LLMServiceFactory',
    'get_llm_service',
    'check_llm_connection',
    'get_available_models',
    'generate_response',
    'get_current_provider',
    'get_provider_info',

    # Specific providers (for direct access)
    'OllamaService',
    'ollama_service',
    'VLLMService',
    'vllm_service',

    # Backward compatibility
    'check_ollama_connection',
]
