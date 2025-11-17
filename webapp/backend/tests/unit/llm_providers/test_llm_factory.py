"""
Unit Tests for LLM Factory
Tests LLM provider factory pattern (Ollama/vLLM switching)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.llm_factory import LLMFactory, LLMProvider
from services.ollama_service import OllamaService
from services.vllm_service import VLLMService


class TestLLMFactory:
    """Test LLM Factory"""

    def test_create_ollama_provider(self):
        """Test creating Ollama provider"""
        with patch.dict('os.environ', {'LLM_PROVIDER': 'ollama'}):
            provider = LLMFactory.create_provider()
            assert isinstance(provider, OllamaService)

    def test_create_vllm_provider(self):
        """Test creating vLLM provider"""
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'vllm',
            'VLLM_BASE_URL': 'http://localhost:8001'
        }):
            provider = LLMFactory.create_provider()
            assert isinstance(provider, VLLMService)

    def test_default_provider(self):
        """Test default provider (should be Ollama)"""
        with patch.dict('os.environ', {}, clear=True):
            provider = LLMFactory.create_provider()
            assert isinstance(provider, OllamaService)

    def test_invalid_provider(self):
        """Test invalid provider name"""
        with patch.dict('os.environ', {'LLM_PROVIDER': 'invalid'}):
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                LLMFactory.create_provider()

    def test_get_provider_name(self):
        """Test getting provider name"""
        with patch.dict('os.environ', {'LLM_PROVIDER': 'ollama'}):
            assert LLMFactory.get_provider_name() == 'ollama'

        with patch.dict('os.environ', {'LLM_PROVIDER': 'vllm'}):
            assert LLMFactory.get_provider_name() == 'vllm'

    def test_provider_caching(self):
        """Test that provider instances are cached"""
        with patch.dict('os.environ', {'LLM_PROVIDER': 'ollama'}):
            provider1 = LLMFactory.create_provider()
            provider2 = LLMFactory.create_provider()
            # Should return same instance if created with same config
            assert type(provider1) == type(provider2)
