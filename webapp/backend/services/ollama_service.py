"""
Ollama Service - Local LLM Integration
Handles communication with local Ollama instance
"""

import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from core.config import settings


class OllamaService:
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
                        return data.get("response", "")
                    else:
                        error_text = await response.text()
                        print(f"❌ Ollama generation failed: {error_text}")
                        return None
        except asyncio.TimeoutError:
            print("⏱️  Ollama request timed out")
            return None
        except Exception as e:
            print(f"❌ Ollama generation error: {e}")
            return None

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
                                    if 'response' in data:
                                        yield data['response']
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Ollama streaming error: {e}")
            print(f"Error details: {error_details}")
            yield None

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
