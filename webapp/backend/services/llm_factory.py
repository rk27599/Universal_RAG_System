"""
LLM Service Factory
Creates appropriate LLM service instance based on configuration
Provides unified interface for switching between providers
"""

from typing import Optional
from core.config import settings
from services.llm_base import BaseLLMService, LLMServiceError
from services.ollama_service import OllamaService
from services.vllm_service import VLLMService


class LLMServiceFactory:
    """Factory for creating LLM service instances"""

    _instance: Optional[BaseLLMService] = None
    _provider: Optional[str] = None

    @classmethod
    def get_service(cls, provider: Optional[str] = None) -> BaseLLMService:
        """
        Get LLM service instance (singleton pattern)

        Args:
            provider: LLM provider name ('ollama' or 'vllm')
                     If None, uses settings.LLM_PROVIDER

        Returns:
            BaseLLMService: Configured LLM service instance

        Raises:
            LLMServiceError: If provider is invalid or service creation fails
        """
        # Determine provider
        if provider is None:
            provider = settings.LLM_PROVIDER.lower()
        else:
            provider = provider.lower()

        # Return existing instance if provider hasn't changed
        if cls._instance is not None and cls._provider == provider:
            return cls._instance

        # Create new instance based on provider
        if provider == "ollama":
            cls._instance = OllamaService()
            cls._provider = "ollama"
            print(f"✅ LLM Service initialized: Ollama ({settings.OLLAMA_BASE_URL})")

        elif provider == "vllm":
            cls._instance = VLLMService()
            cls._provider = "vllm"
            print(f"✅ LLM Service initialized: vLLM ({settings.VLLM_BASE_URL})")

        else:
            raise LLMServiceError(
                f"Invalid LLM provider: {provider}. "
                f"Supported providers: 'ollama', 'vllm'"
            )

        return cls._instance

    @classmethod
    def reset(cls):
        """Reset factory (useful for testing or provider switching)"""
        cls._instance = None
        cls._provider = None


# Convenience functions for backward compatibility
async def get_llm_service() -> BaseLLMService:
    """Get the configured LLM service instance"""
    return LLMServiceFactory.get_service()


async def check_llm_connection() -> bool:
    """Check if LLM service is running"""
    service = LLMServiceFactory.get_service()
    return await service.check_connection()


async def get_available_models() -> list:
    """Get list of available models"""
    service = LLMServiceFactory.get_service()
    return await service.list_models()


async def generate_response(
    prompt: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    context: Optional[str] = None
) -> Optional[str]:
    """Generate a response using configured LLM service"""
    service = LLMServiceFactory.get_service()
    return await service.generate(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        context=context
    )


# Provider information
def get_current_provider() -> str:
    """Get the name of the currently configured provider"""
    return settings.LLM_PROVIDER


def get_provider_info() -> dict:
    """Get information about the current provider"""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "ollama":
        return {
            "provider": "ollama",
            "base_url": settings.OLLAMA_BASE_URL,
            "default_model": settings.DEFAULT_MODEL,
            "features": {
                "streaming": True,
                "multi_gpu": False,
                "concurrent_requests": "serialized"
            }
        }
    elif provider == "vllm":
        return {
            "provider": "vllm",
            "base_url": settings.VLLM_BASE_URL,
            "default_model": settings.DEFAULT_MODEL,
            "gpu_count": getattr(settings, 'VLLM_GPU_COUNT', 1),
            "tensor_parallel_size": getattr(settings, 'VLLM_TENSOR_PARALLEL_SIZE', 1),
            "features": {
                "streaming": True,
                "multi_gpu": True,
                "concurrent_requests": "parallel"
            }
        }
    else:
        return {
            "provider": "unknown",
            "error": f"Invalid provider: {provider}"
        }
