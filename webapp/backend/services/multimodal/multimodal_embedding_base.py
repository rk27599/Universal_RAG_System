"""
Multimodal Embedding Base Class
Abstract interface for multimodal embedding services
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ModalityType(Enum):
    """Supported modality types"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CHART = "chart"
    DIAGRAM = "diagram"


class MultimodalEmbeddingBase(ABC):
    """
    Abstract base class for multimodal embedding services

    Provides unified interface for:
    - Single-modal embeddings (text, image, audio, video)
    - Cross-modal embeddings (shared embedding space)
    - Batch processing
    - Similarity computation
    """

    def __init__(self, model_name: str, embedding_dim: int):
        """
        Initialize multimodal embedding service

        Args:
            model_name: Name/path of the model
            embedding_dim: Dimension of embedding vectors
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.model = None

    @abstractmethod
    def load_model(self):
        """Load the embedding model"""
        pass

    @abstractmethod
    def unload_model(self):
        """Unload the model to free memory"""
        pass

    @property
    @abstractmethod
    def supported_modalities(self) -> List[ModalityType]:
        """Return list of supported modalities"""
        pass

    @abstractmethod
    def encode_text(self, text: str) -> Optional[List[float]]:
        """
        Encode text into embedding vector

        Args:
            text: Input text

        Returns:
            Embedding vector or None on failure
        """
        pass

    @abstractmethod
    def encode_image(self, image_path: Union[str, Path]) -> Optional[List[float]]:
        """
        Encode image into embedding vector

        Args:
            image_path: Path to image file

        Returns:
            Embedding vector or None on failure
        """
        pass

    def encode_audio(self, audio_path: Union[str, Path]) -> Optional[List[float]]:
        """
        Encode audio into embedding vector (optional)

        Args:
            audio_path: Path to audio file

        Returns:
            Embedding vector or None if not supported
        """
        logger.warning(f"{self.__class__.__name__} does not support audio encoding")
        return None

    def encode_video(self, video_path: Union[str, Path]) -> Optional[List[float]]:
        """
        Encode video into embedding vector (optional)

        Args:
            video_path: Path to video file

        Returns:
            Embedding vector or None if not supported
        """
        logger.warning(f"{self.__class__.__name__} does not support video encoding")
        return None

    @abstractmethod
    def encode_batch(
        self,
        inputs: List[Union[str, Path]],
        modality: ModalityType
    ) -> List[Optional[List[float]]]:
        """
        Encode multiple inputs of the same modality

        Args:
            inputs: List of texts or file paths
            modality: Type of modality to encode

        Returns:
            List of embedding vectors
        """
        pass

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Normalize vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)

        # Compute cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        return float(similarity)

    def is_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self.model is not None

    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "supported_modalities": [m.value for m in self.supported_modalities],
            "is_loaded": self.is_loaded()
        }
