"""
LLM Service Base Class
Abstract interface for LLM providers (Ollama, vLLM, etc.)
Ensures consistent API across different providers
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator


class BaseLLMService(ABC):
    """Abstract base class for LLM service providers"""

    @abstractmethod
    async def check_connection(self) -> bool:
        """
        Check if the LLM service is running and accessible

        Returns:
            bool: True if service is accessible, False otherwise
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """
        Get list of available models from the LLM service

        Returns:
            List[str]: List of model names/identifiers
        """
        pass

    @abstractmethod
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model

        Args:
            model_name: Name/identifier of the model

        Returns:
            Optional[Dict[str, Any]]: Model information dict or None if not found
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate text completion using the LLM

        Args:
            prompt: The user's input prompt
            model: Model name to use (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system-level instructions
            context: Optional context (e.g., retrieved documents)

        Returns:
            Optional[str]: Generated text or None if generation failed
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text completion with streaming (async generator)

        Args:
            prompt: The user's input prompt
            model: Model name to use (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system-level instructions
            context: Optional context (e.g., retrieved documents)

        Yields:
            str: Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def pull_model(self, model_name: str) -> bool:
        """
        Download/pull a model (if supported by provider)

        Args:
            model_name: Name of the model to pull

        Returns:
            bool: True if successful, False otherwise
        """
        pass


class LLMServiceError(Exception):
    """Base exception for LLM service errors"""
    pass


class LLMConnectionError(LLMServiceError):
    """Raised when connection to LLM service fails"""
    pass


class LLMGenerationError(LLMServiceError):
    """Raised when text generation fails"""
    pass


class LLMModelNotFoundError(LLMServiceError):
    """Raised when requested model is not available"""
    pass
