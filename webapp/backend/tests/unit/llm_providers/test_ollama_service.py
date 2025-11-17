"""
Unit Tests for Ollama Service
Tests Ollama LLM integration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path
import aiohttp

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.ollama_service import OllamaService


class TestOllamaService:
    """Test Ollama Service"""

    @pytest.fixture
    def ollama_service(self):
        """Create Ollama service instance"""
        return OllamaService(base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_generate_success(self, ollama_service):
        """Test successful text generation"""
        mock_response = {
            "response": "Test response",
            "model": "mistral",
            "done": True
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            result = await ollama_service.generate(
                model="mistral",
                prompt="Test prompt"
            )

            assert result["response"] == "Test response"
            assert result["model"] == "mistral"
            assert result["done"] is True

    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, ollama_service):
        """Test generation with custom parameters"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"response": "Test", "done": True}
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            await ollama_service.generate(
                model="mistral",
                prompt="Test",
                temperature=0.8,
                max_tokens=100
            )

            # Verify parameters were passed
            call_args = mock_post.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_generate_timeout(self, ollama_service):
        """Test generation timeout handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()

            with pytest.raises(Exception):
                await ollama_service.generate(
                    model="mistral",
                    prompt="Test"
                )

    @pytest.mark.asyncio
    async def test_list_models(self, ollama_service):
        """Test listing available models"""
        mock_models = {
            "models": [
                {"name": "mistral", "size": 4368438272},
                {"name": "llama2", "size": 3826730240}
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_models
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            models = await ollama_service.list_models()

            assert len(models) == 2
            assert models[0]["name"] == "mistral"
            assert models[1]["name"] == "llama2"

    @pytest.mark.asyncio
    async def test_is_available_success(self, ollama_service):
        """Test availability check when service is up"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200

            is_available = await ollama_service.is_available()

            assert is_available is True

    @pytest.mark.asyncio
    async def test_is_available_failure(self, ollama_service):
        """Test availability check when service is down"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError()

            is_available = await ollama_service.is_available()

            assert is_available is False

    @pytest.mark.asyncio
    async def test_chat_completion(self, ollama_service):
        """Test chat completion"""
        messages = [
            {"role": "user", "content": "What is ML?"}
        ]

        mock_response = {
            "message": {
                "role": "assistant",
                "content": "Machine learning is..."
            },
            "done": True
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            result = await ollama_service.chat(
                model="mistral",
                messages=messages
            )

            assert result["message"]["role"] == "assistant"
            assert "Machine learning" in result["message"]["content"]

import asyncio
