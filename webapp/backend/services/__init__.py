"""
Services Package
Business logic and external integrations
"""

from .ollama_service import ollama_service, check_ollama_connection, get_available_models, generate_response

__all__ = [
    'ollama_service',
    'check_ollama_connection',
    'get_available_models',
    'generate_response',
]
