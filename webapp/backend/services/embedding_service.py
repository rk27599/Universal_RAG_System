"""
Embedding Service - Vector Generation for RAG
Generates vector embeddings for text chunks using sentence-transformers
"""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model

        Args:
            model_name: HuggingFace model identifier
                - all-MiniLM-L6-v2: Fast, 384 dimensions (recommended for production)
                - all-mpnet-base-v2: Better quality, 768 dimensions (slower)
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._embedding_dim: Optional[int] = None

        # Check for GPU availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Initializing EmbeddingService with model: {model_name}")
        logger.info(f"Using device: {self.device}")

    def load_model(self):
        """Load the sentence transformer model (lazy loading)"""
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name, device=self.device)
                self._embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded successfully. Embedding dimension: {self._embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(f"Failed to load embedding model: {e}")

    @property
    def embedding_dimension(self) -> int:
        """Get the embedding dimension of the model"""
        if self._embedding_dim is None:
            self.load_model()
        return self._embedding_dim

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

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

            # Generate embedding
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )

            # Convert to list for database storage
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently (synchronous version)

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []

            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)

            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding")
                return [None] * len(texts)

            # Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(valid_texts)} texts (batch_size={batch_size})")

            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(valid_texts) > 100,
                normalize_embeddings=True
            )

            # Convert to list and map back to original indices
            result = [None] * len(texts)
            for idx, embedding in zip(valid_indices, embeddings):
                result[idx] = embedding.tolist()

            logger.info(f"Successfully generated {len(valid_texts)} embeddings")
            return result

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)

    async def generate_embeddings_batch_async(
        self,
        texts: List[str],
        batch_size: int = 32,
        progress_callback: Optional[callable] = None
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently (async version - non-blocking)

        This method runs the CPU-intensive embedding generation in a thread pool,
        allowing the FastAPI event loop to remain responsive for other requests.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            progress_callback: Optional callback function(progress: float) called with progress 0.0-1.0

        Returns:
            List of embedding vectors (one per input text)
        """
        import asyncio

        # If progress callback provided, wrap the batch generation with progress tracking
        if progress_callback:
            result = await self._generate_with_progress(texts, batch_size, progress_callback)
        else:
            # Run the synchronous embedding generation in a thread pool
            # This prevents blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                self.generate_embeddings_batch,
                texts,
                batch_size
            )

        return result

    async def _generate_with_progress(
        self,
        texts: List[str],
        batch_size: int,
        progress_callback: callable
    ) -> List[Optional[List[float]]]:
        """Generate embeddings with progress tracking"""
        import asyncio

        if not texts:
            return []

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []

            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)

            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding")
                return [None] * len(texts)

            # Process in batches with progress tracking
            result = [None] * len(texts)
            num_batches = (len(valid_texts) + batch_size - 1) // batch_size

            logger.info(f"Generating embeddings for {len(valid_texts)} texts in {num_batches} batches")

            for batch_idx in range(num_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(valid_texts))
                batch_texts = valid_texts[start_idx:end_idx]

                # Run embedding generation in thread pool
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    None,
                    lambda: self.model.encode(
                        batch_texts,
                        convert_to_numpy=True,
                        show_progress_bar=False,
                        normalize_embeddings=True
                    )
                )

                # Store results
                for i, embedding in enumerate(batch_embeddings):
                    orig_idx = valid_indices[start_idx + i]
                    result[orig_idx] = embedding.tolist()

                # Update progress
                progress = (batch_idx + 1) / num_batches
                try:
                    progress_callback(progress)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

            logger.info(f"Successfully generated {len(valid_texts)} embeddings")
            return result

        except Exception as e:
            logger.error(f"Error generating batch embeddings with progress: {e}")
            return [None] * len(texts)

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (-1 to 1, where 1 is most similar)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            # Convert to Python scalars to avoid numpy array comparison issues
            norm1_scalar = float(norm1)
            norm2_scalar = float(norm2)

            if norm1_scalar == 0.0 or norm2_scalar == 0.0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            # Ensure we return a Python float, not numpy float
            return float(similarity)

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0


# Global instance for reuse (singleton pattern)
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance"""
    global _embedding_service_instance

    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()

    return _embedding_service_instance
