"""
BGE-M3 Embedding Service - Multi-Functional Embedding Model
Supports dense, multi-vector, and sparse retrieval with 1024 dimensions
"""

import logging
from typing import List, Optional, Dict
import numpy as np
import torch

logger = logging.getLogger(__name__)

try:
    from FlagEmbedding import BGEM3FlagModel
    BGE_AVAILABLE = True
except ImportError:
    BGE_AVAILABLE = False
    logger.warning("FlagEmbedding not available. Install with: pip install -U FlagEmbedding")


class BGEEmbeddingService:
    """
    BGE-M3 Embedding Service for high-quality embeddings

    Features:
    - 1024-dimensional dense embeddings
    - Multi-vector and sparse retrieval support
    - 100+ languages supported
    - Max input: 8192 tokens
    - State-of-the-art MTEB performance
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True):
        """
        Initialize BGE-M3 embedding service

        Args:
            model_name: Model identifier (default: BAAI/bge-m3)
            use_fp16: Use half precision for faster inference (default: True)
        """
        if not BGE_AVAILABLE:
            raise RuntimeError(
                "FlagEmbedding library not installed. "
                "Install with: pip install -U FlagEmbedding"
            )

        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.model: Optional[BGEM3FlagModel] = None
        self._embedding_dim = 1024  # BGE-M3 fixed dimension

        # Check for GPU availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Initializing BGE-M3 Embedding Service")
        logger.info(f"Model: {model_name}")
        logger.info(f"Device: {self.device}")
        logger.info(f"FP16: {use_fp16}")

    def load_model(self):
        """Load the BGE-M3 model (lazy loading)"""
        if self.model is None:
            try:
                logger.info(f"Loading BGE-M3 model: {self.model_name}")

                self.model = BGEM3FlagModel(
                    self.model_name,
                    use_fp16=self.use_fp16,
                    devices=self.device  # Note: BGEM3FlagModel uses 'devices' not 'device'
                )

                logger.info(f"✅ BGE-M3 model loaded successfully")
                logger.info(f"📊 Embedding dimension: {self._embedding_dim}")
                logger.info(f"💾 Device: {self.device}")

            except Exception as e:
                logger.error(f"❌ Failed to load BGE-M3 model: {e}")
                raise RuntimeError(f"Failed to load BGE-M3 model: {e}")

    @property
    def embedding_dimension(self) -> int:
        """Get the embedding dimension of the model"""
        return self._embedding_dim

    def generate_embedding(self, text: str, return_dense: bool = True) -> Optional[List[float]]:
        """
        Generate embedding for a single text using BGE-M3

        Args:
            text: Input text to embed
            return_dense: Return dense embeddings (default: True)

        Returns:
            List of floats representing the embedding vector, or None on failure
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            # BGE-M3 encode returns dict with 'dense_vecs', 'lexical_weights', 'colbert_vecs'
            result = self.model.encode(
                [text],  # BGE-M3 expects list
                batch_size=1,
                max_length=8192  # BGE-M3 supports up to 8192 tokens
            )

            if return_dense:
                # Return dense embeddings (1024-dim)
                dense_embedding = result['dense_vecs'][0]
                return dense_embedding.tolist()
            else:
                # Could return multi-vector or sparse if needed
                return result

        except Exception as e:
            logger.error(f"Error generating BGE-M3 embedding: {e}")
            return None

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 12,
        show_progress: bool = False
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (default: 12 for BGE-M3)
            show_progress: Show progress bar

        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            # Filter empty texts
            valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
            valid_texts = [texts[i] for i in valid_indices]

            if not valid_texts:
                logger.warning("No valid texts to embed")
                return [None] * len(texts)

            # Encode in batches
            all_embeddings = []
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]

                result = self.model.encode(
                    batch,
                    batch_size=len(batch),
                    max_length=8192
                )

                # Extract dense embeddings
                batch_embeddings = result['dense_vecs']
                all_embeddings.extend([emb.tolist() for emb in batch_embeddings])

                if show_progress:
                    logger.info(f"Processed {min(i + batch_size, len(valid_texts))}/{len(valid_texts)} texts")

            # Reconstruct full list with None for empty texts
            embeddings = [None] * len(texts)
            for idx, emb_idx in enumerate(valid_indices):
                embeddings[emb_idx] = all_embeddings[idx]

            return embeddings

        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            return [None] * len(texts)

    def encode_query(self, query: str) -> Optional[List[float]]:
        """
        Encode a search query (same as generate_embedding for BGE-M3)

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return self.generate_embedding(query)

    def encode_documents(self, documents: List[str], batch_size: int = 12) -> List[Optional[List[float]]]:
        """
        Encode multiple documents for indexing

        Args:
            documents: List of document texts
            batch_size: Processing batch size

        Returns:
            List of document embedding vectors
        """
        return self.generate_embeddings_batch(documents, batch_size=batch_size, show_progress=True)

    async def generate_embeddings_batch_async(
        self,
        texts: List[str],
        batch_size: int = 12,
        show_progress: bool = False
    ) -> List[Optional[List[float]]]:
        """
        Async wrapper for batch embedding generation
        BGE-M3 doesn't have native async, so we run sync in executor

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            show_progress: Show progress logging

        Returns:
            List of embedding vectors
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_embeddings_batch,
            texts,
            batch_size,
            show_progress
        )
