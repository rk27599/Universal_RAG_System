"""
Multimodal Services Package
Provides embeddings, processing, and retrieval for multiple modalities:
- Text
- Images
- Audio
- Video
"""

from .multimodal_embedding_base import MultimodalEmbeddingBase, ModalityType
from .embedding_service_clip import CLIPEmbeddingService

__all__ = [
    'MultimodalEmbeddingBase',
    'ModalityType',
    'CLIPEmbeddingService',
]
