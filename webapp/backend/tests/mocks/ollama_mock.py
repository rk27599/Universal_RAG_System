"""
Mock Ollama Service for Testing
Simulates Ollama API responses without requiring actual Ollama server
"""

from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock


class MockOllamaService:
    """Mock Ollama service for testing"""

    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.models = [
            {"name": "mistral", "size": "4.1GB", "modified": "2024-01-15"},
            {"name": "llama2", "size": "3.8GB", "modified": "2024-01-10"},
            {"name": "qwen", "size": "2.3GB", "modified": "2024-01-05"}
        ]

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
            "response": f"Mock response for prompt: {prompt[:50]}...",
            "model": model,
            "done": True,
            "context": [1, 2, 3],
            "total_duration": 1000000000,
            "load_duration": 500000000,
            "prompt_eval_count": len(prompt.split()),
            "eval_count": 50
        }

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock chat method"""
        last_message = messages[-1]["content"] if messages else ""
        return {
            "message": {
                "role": "assistant",
                "content": f"Mock chat response for: {last_message[:50]}..."
            },
            "model": model,
            "done": True
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        """Mock list models method"""
        return self.models

    async def is_available(self) -> bool:
        """Mock availability check"""
        return True

    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Mock model pull"""
        return {
            "status": "success",
            "model": model
        }
