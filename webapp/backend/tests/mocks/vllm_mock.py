"""
Mock vLLM Service for Testing
Simulates vLLM API responses without requiring actual vLLM server
"""

from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock


class MockVLLMService:
    """Mock vLLM service for testing"""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.model = "Qwen/Qwen3-4B-Thinking-2507-FP8"

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock generate method"""
        return {
            "response": f"Mock vLLM response for prompt: {prompt[:50]}...",
            "model": model,
            "done": True,
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 50,
                "total_tokens": len(prompt.split()) + 50
            }
        }

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 512,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock chat completion method"""
        last_message = messages[-1]["content"] if messages else ""
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Mock vLLM chat response for: {last_message[:50]}..."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 50,
                "total_tokens": 70
            }
        }

    async def is_available(self) -> bool:
        """Mock availability check"""
        return True

    async def get_model_info(self) -> Dict[str, Any]:
        """Mock model info"""
        return {
            "model": self.model,
            "max_model_len": 16384,
            "dtype": "float16"
        }
