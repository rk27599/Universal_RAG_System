"""
Ollama Service - Local LLM Integration
Handles communication with local Ollama instance
"""

import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from core.config import settings
from services.llm_base import BaseLLMService, LLMConnectionError, LLMGenerationError


class OllamaService(BaseLLMService):
    """Service for interacting with Ollama API"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.DEFAULT_MODEL
        # Increased timeout to 10 minutes for large models like gpt-oss
        self.timeout = aiohttp.ClientTimeout(total=600)

    async def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['name'] for model in data.get('models', [])]
                    return settings.AVAILABLE_MODELS
        except Exception as e:
            print(f"⚠️  Failed to fetch models from Ollama: {e}")
            return settings.AVAILABLE_MODELS

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                ) as response:
                    if response.status == 200:
                        return await response.json()
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
        """Generate text completion using Ollama"""
        model = model or self.default_model

        try:
            # Build the full prompt with context
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"

            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check for error in response
                        if 'error' in data:
                            error_msg = data['error']
                            print(f"❌ Ollama error: {error_msg}")
                            raise Exception(f"Ollama error: {error_msg}")
                        return data.get("response", "")
                    else:
                        error_text = await response.text()
                        print(f"❌ Ollama generation failed ({response.status}): {error_text}")
                        raise Exception(f"Ollama error ({response.status}): {error_text}")
        except asyncio.TimeoutError:
            error_msg = f"Request timed out for model '{model}'. The model may be too large or Ollama is not responding."
            print(f"⏱️  {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"❌ Ollama generation error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ):
        """Generate text completion with streaming (async generator)"""
        model = model or self.default_model

        try:
            # Build the full prompt with context
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"

            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                import json
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    # Check for error in response
                                    if 'error' in data:
                                        error_msg = data['error']
                                        print(f"❌ Ollama error: {error_msg}")
                                        raise Exception(f"Ollama error: {error_msg}")
                                    if 'response' in data:
                                        yield data['response']
                                except json.JSONDecodeError:
                                    continue
                    else:
                        # Handle HTTP error responses
                        error_text = await response.text()
                        print(f"❌ Ollama HTTP error ({response.status}): {error_text}")
                        raise Exception(f"Ollama error ({response.status}): {error_text}")
        except asyncio.TimeoutError:
            error_msg = f"Request timed out for model '{model}'. The model may be too large or Ollama is not responding."
            print(f"⏱️  {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Ollama streaming error: {e}")
            print(f"Error details: {error_details}")
            raise

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Failed to pull model: {e}")
            return False

    async def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Generate text completion using a multimodal vision model (LLaVA)

        Args:
            prompt: The user's input prompt
            image_path: Path to the image file
            model: Model name (defaults to 'llava')
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text description or None on error
        """
        import base64
        from pathlib import Path

        model = model or "llava"  # Default to LLaVA

        try:
            # Read and encode image as base64
            image_file = Path(image_path)
            if not image_file.exists():
                print(f"❌ Image file not found: {image_path}")
                return None

            with open(image_file, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            payload = {
                "model": model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'error' in data:
                            error_msg = data['error']
                            print(f"❌ Ollama vision error: {error_msg}")
                            return None
                        return data.get("response", "")
                    else:
                        error_text = await response.text()
                        print(f"❌ Ollama vision generation failed ({response.status}): {error_text}")
                        return None

        except Exception as e:
            print(f"❌ Vision model generation error: {e}")
            return None

    def supports_vision(self) -> bool:
        """Ollama supports vision models (LLaVA, LLaVA-1.6, etc.)"""
        return True


# Global instance
ollama_service = OllamaService()


# Convenience functions for FastAPI
async def check_ollama_connection() -> bool:
    """Check if Ollama service is running"""
    return await ollama_service.check_connection()


async def get_available_models() -> List[str]:
    """Get list of available models"""
    return await ollama_service.list_models()


async def generate_response(
    prompt: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    context: Optional[str] = None
) -> Optional[str]:
    """Generate a response using Ollama"""
    return await ollama_service.generate(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        context=context
    )
