"""
vLLM Service - High-Performance Local LLM Integration
Handles communication with local vLLM instance for multi-GPU inference
Supports concurrent request processing and tensor parallelism
"""

import aiohttp
import asyncio
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from core.config import settings
from services.llm_base import BaseLLMService, LLMConnectionError, LLMGenerationError


class VLLMService(BaseLLMService):
    """Service for interacting with vLLM API (OpenAI-compatible)"""

    def __init__(self):
        self.base_url = settings.VLLM_BASE_URL
        self.default_model = settings.DEFAULT_MODEL
        # Increased timeout for large models
        self.timeout = aiohttp.ClientTimeout(total=600)

    async def check_connection(self) -> bool:
        """Check if vLLM is running and accessible"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # vLLM uses OpenAI-compatible /v1/models endpoint
                async with session.get(f"{self.base_url}/v1/models") as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ vLLM connection failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        """Get list of available models from vLLM"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        # vLLM returns OpenAI-compatible format
                        return [model['id'] for model in data.get('data', [])]
                    return [self.default_model]
        except Exception as e:
            print(f"⚠️  Failed to fetch models from vLLM: {e}")
            return [self.default_model]

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        for model in data.get('data', []):
                            if model['id'] == model_name:
                                return model
                    return None
        except Exception as e:
            print(f"⚠️  Failed to get model info: {e}")
            return None

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> Optional[str]:
        """Generate text completion using vLLM (OpenAI-compatible API)"""
        model = model or self.default_model

        try:
            # Build messages array (OpenAI chat format)
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Build user message with context
            user_content = prompt
            if context:
                user_content = f"Context:\n{context}\n\nQuestion: {prompt}"

            messages.append({"role": "user", "content": user_content})

            # vLLM uses OpenAI-compatible /v1/chat/completions endpoint
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract content from OpenAI-compatible response
                        return data['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        print(f"❌ vLLM generation failed: {error_text}")
                        return None
        except asyncio.TimeoutError:
            print("⏱️  vLLM request timed out")
            return None
        except Exception as e:
            print(f"❌ vLLM generation error: {e}")
            return None

    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate text completion with streaming (OpenAI-compatible)"""
        model = model or self.default_model

        try:
            # Build messages array (OpenAI chat format)
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Build user message with context
            user_content = prompt
            if context:
                user_content = f"Context:\n{context}\n\nQuestion: {prompt}"

            messages.append({"role": "user", "content": user_content})

            # vLLM streaming endpoint
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True  # Enable streaming
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    if response.status == 200:
                        # Process Server-Sent Events (SSE) stream
                        async for line in response.content:
                            if line:
                                line_str = line.decode('utf-8').strip()

                                # Skip empty lines and "data: " prefix
                                if not line_str or line_str == "data: [DONE]":
                                    continue

                                # Remove "data: " prefix
                                if line_str.startswith("data: "):
                                    line_str = line_str[6:]

                                try:
                                    data = json.loads(line_str)
                                    # Extract delta content from streaming response
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.text()
                        print(f"❌ vLLM streaming failed: {error_text}")
                        yield None
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ vLLM streaming error: {e}")
            print(f"Error details: {error_details}")
            yield None

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model
        Note: vLLM requires manual model setup, so this returns info message
        """
        print(f"⚠️  vLLM requires manual model setup. Please configure model: {model_name}")
        print(f"   Model should be placed in: {settings.VLLM_MODEL_PATH}")
        return False


# Global instance
vllm_service = VLLMService()


# Convenience functions for FastAPI (backward compatible)
async def check_vllm_connection() -> bool:
    """Check if vLLM service is running"""
    return await vllm_service.check_connection()


async def get_available_models() -> List[str]:
    """Get list of available models"""
    return await vllm_service.list_models()


async def generate_response(
    prompt: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    context: Optional[str] = None
) -> Optional[str]:
    """Generate a response using vLLM"""
    return await vllm_service.generate(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        context=context
    )
