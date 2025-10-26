"""
vLLM Service - High-Performance Local LLM Integration
Handles communication with local vLLM instance for multi-GPU inference
Supports concurrent request processing and tensor parallelism
"""

import aiohttp
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from core.config import settings
from services.llm_base import BaseLLMService, LLMConnectionError, LLMGenerationError

logger = logging.getLogger(__name__)


class VLLMService(BaseLLMService):
    """Service for interacting with vLLM API (OpenAI-compatible)"""

    def __init__(self):
        self.base_url = settings.VLLM_BASE_URL
        self.default_model = settings.DEFAULT_MODEL
        # Increased timeout for large models
        self.timeout = aiohttp.ClientTimeout(total=600)

    def _parse_vllm_error(self, error_text: str, status_code: int) -> str:
        """
        Parse vLLM error response and return user-friendly message

        Args:
            error_text: Raw error response from vLLM API
            status_code: HTTP status code

        Returns:
            User-friendly error message with actionable suggestions
        """
        try:
            error_json = json.loads(error_text)
            if 'error' in error_json:
                error_data = error_json['error']
                msg = error_data.get('message', str(error_data))

                # Make common errors user-friendly with actionable advice
                if 'max_tokens' in msg or 'maximum context length' in msg or 'context length' in msg:
                    return ("❌ Context Window Exceeded: Your query and retrieved documents are too large for the model. "
                           "Try: (1) Disable RAG, (2) Reduce document chunks in settings, or (3) Use a model with larger context window.")

                elif 'CUDA out of memory' in msg or 'out of memory' in msg.lower():
                    return ("❌ GPU Out of Memory: The model is too large for your GPU. "
                           "Try: (1) Restart vLLM with --gpu-memory-utilization 0.8, (2) Use a smaller model, or (3) Reduce --max-model-len.")

                elif 'model not found' in msg.lower() or 'no such file' in msg.lower():
                    return f"❌ Model Not Found: vLLM couldn't load the requested model. Check if the model is downloaded and vLLM is configured correctly."

                elif 'timeout' in msg.lower():
                    return "❌ Request Timeout: vLLM took too long to respond. The model may be overloaded or the request is too complex."

                else:
                    # Return original message for unknown errors
                    return f"❌ vLLM Error: {msg}"
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.warning(f"Failed to parse vLLM error: {e}")

        # Fallback for unparseable errors
        if status_code == 400:
            return f"❌ Bad Request: {error_text[:200]}"
        elif status_code == 404:
            return "❌ vLLM endpoint not found. Check if vLLM server is running on the correct port."
        elif status_code == 500:
            return f"❌ vLLM Internal Error: {error_text[:200]}"
        elif status_code == 503:
            return "❌ vLLM Service Unavailable: The server is overloaded or temporarily down."
        else:
            return f"❌ vLLM HTTP {status_code}: {error_text[:200]}"

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
        logger.info(f"🔵 vLLM generate_stream called (prompt length: {len(prompt)} chars)")

        # Get available models from vLLM with timeout handling
        # This handles case where UI sends Ollama model names
        try:
            available_models = await asyncio.wait_for(
                self.list_models(),
                timeout=5.0  # 5 second timeout
            )
            if available_models:
                model = available_models[0]  # Use first available vLLM model
                logger.info(f"🔄 Using vLLM model from API: {model}")
            else:
                # No models returned, use hardcoded fallback
                model = "Qwen/Qwen3-4B-Thinking-2507-FP8"
                logger.warning(f"⚠️  No models from API, using fallback: {model}")
        except asyncio.TimeoutError:
            # API timeout, use hardcoded fallback
            model = "Qwen/Qwen3-4B-Thinking-2507-FP8"
            logger.warning(f"⏱️  vLLM API timeout, using fallback: {model}")
        except Exception as e:
            # Any other error, use hardcoded fallback
            model = "Qwen/Qwen3-4B-Thinking-2507-FP8"
            logger.error(f"❌ Error getting models ({e}), using fallback: {model}")

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

            logger.info(f"🌐 Calling vLLM API: {self.base_url}/v1/chat/completions")
            logger.info(f"📦 Payload: model={model}, temp={temperature}, max_tokens={max_tokens}, messages={len(messages)}")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    logger.info(f"📡 vLLM API response status: {response.status}")
                    if response.status == 200:
                        logger.info(f"✅ vLLM streaming started successfully")
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
                        # Parse error and raise exception with user-friendly message
                        error_text = await response.text()
                        error_msg = self._parse_vllm_error(error_text, response.status)
                        logger.error(f"❌ vLLM HTTP {response.status}: {error_text}")
                        raise LLMGenerationError(error_msg)

        except LLMGenerationError:
            # Re-raise our custom errors
            raise
        except asyncio.TimeoutError:
            error_msg = "❌ Request Timeout: vLLM took too long to respond. The model may be overloaded or the request is too complex."
            logger.error(f"⏱️ vLLM timeout")
            raise LLMGenerationError(error_msg)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ vLLM streaming error: {e}")
            logger.error(f"Error details: {error_details}")
            # Wrap generic exceptions in user-friendly message
            error_msg = f"❌ vLLM Connection Error: {str(e)[:200]}"
            raise LLMGenerationError(error_msg)

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
