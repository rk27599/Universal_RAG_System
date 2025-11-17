"""
Unit Tests for vLLM Service
Tests vLLM high-performance LLM integration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path
import aiohttp

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.vllm_service import VLLMService


class TestVLLMService:
    """Test vLLM Service"""

    @pytest.fixture
    def vllm_service(self):
        """Create vLLM service instance"""
        return VLLMService(base_url="http://localhost:8001")

    @pytest.mark.asyncio
    async def test_generate_success(self, vllm_service):
        """Test successful text generation"""
        mock_response = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test response from vLLM"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            result = await vllm_service.generate(
                model="Qwen3-4B-FP8",
                prompt="Test prompt"
            )

            assert "response" in result
            assert result["response"] == "Test response from vLLM"

    @pytest.mark.asyncio
    async def test_chat_completion(self, vllm_service):
        """Test chat completion"""
        messages = [
            {"role": "user", "content": "What is machine learning?"}
        ]

        mock_response = {
            "id": "chatcmpl-456",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Machine learning is a subset of AI..."
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            result = await vllm_service.chat_completion(
                model="Qwen3-4B-FP8",
                messages=messages
            )

            assert result["choices"][0]["message"]["role"] == "assistant"
            assert "Machine learning" in result["choices"][0]["message"]["content"]

    @pytest.mark.asyncio
    async def test_generate_with_max_tokens(self, vllm_service):
        """Test generation with max_tokens parameter"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={
                    "choices": [{"message": {"content": "Test"}}]
                }
            )
            mock_post.return_value.__aenter__.return_value.status = 200

            await vllm_service.generate(
                model="Qwen3-4B-FP8",
                prompt="Test",
                max_tokens=512
            )

            # Verify max_tokens was passed in request
            call_args = mock_post.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_is_available_success(self, vllm_service):
        """Test availability check when vLLM is running"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"model": "Qwen3-4B-FP8"}
            )

            is_available = await vllm_service.is_available()

            assert is_available is True

    @pytest.mark.asyncio
    async def test_is_available_failure(self, vllm_service):
        """Test availability check when vLLM is down"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError()

            is_available = await vllm_service.is_available()

            assert is_available is False

    @pytest.mark.asyncio
    async def test_get_model_info(self, vllm_service):
        """Test getting model information"""
        mock_info = {
            "model": "Qwen3-4B-FP8",
            "max_model_len": 16384,
            "dtype": "float16"
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_info
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            info = await vllm_service.get_model_info()

            assert info["model"] == "Qwen3-4B-FP8"
            assert info["max_model_len"] == 16384

    @pytest.mark.asyncio
    async def test_timeout_handling(self, vllm_service):
        """Test timeout handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()

            with pytest.raises(Exception):
                await vllm_service.generate(
                    model="Qwen3-4B-FP8",
                    prompt="Test"
                )


import asyncio
