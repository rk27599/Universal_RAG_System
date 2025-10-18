"""
Reranker Service - Cross-encoder reranking for improved retrieval quality
Uses BAAI/bge-reranker-v2-m3 for scoring query-document pairs
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import torch
import numpy as np
import gc

logger = logging.getLogger(__name__)

# Check for FlagEmbedding availability
try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logger.warning("FlagEmbedding not available. Install with: pip install FlagEmbedding")


class RerankerService:
    """
    Cross-encoder reranking service using BGE-reranker-v2-m3

    Purpose:
    - Take initial retrieval results (top 100)
    - Score each query-document pair with cross-encoder
    - Return top-k best matches (typically top 5)

    Why Reranking?
    - Bi-encoder (BGE-M3): Fast but approximate similarity
    - Cross-encoder: Slower but more accurate relevance scoring
    - Two-stage approach: Speed + Accuracy

    Performance:
    - Initial retrieval: 100 candidates in ~20ms (HNSW index)
    - Reranking: 100 pairs in ~200ms (GPU) or ~1s (CPU)
    - Total: ~220ms for high-quality results
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        use_fp16: bool = True,
        batch_size: int = 32
    ):
        """
        Initialize reranker service

        Args:
            model_name: HuggingFace model identifier
            use_fp16: Use FP16 for faster inference (requires GPU)
            batch_size: Batch size for scoring
        """
        self.model_name = model_name
        self.use_fp16 = use_fp16 and torch.cuda.is_available()
        self.batch_size = batch_size
        self.model: Optional[FlagReranker] = None
        self.last_access_time: Optional[datetime] = None  # Track for idle unloading

        # Device detection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if not RERANKER_AVAILABLE:
            logger.error("FlagEmbedding not available - reranking will be disabled")
        else:
            logger.info(f"RerankerService initialized: {model_name} on {self.device}")

    def load_model(self):
        """Load the reranker model (lazy loading)"""
        if not RERANKER_AVAILABLE:
            raise RuntimeError("FlagEmbedding not installed. Run: pip install FlagEmbedding")

        if self.model is None:
            try:
                logger.info(f"Loading reranker model: {self.model_name}")

                self.model = FlagReranker(
                    self.model_name,
                    use_fp16=self.use_fp16,
                    device=self.device
                )

                self.last_access_time = datetime.now()  # Record load time

                logger.info(f"✅ Reranker loaded successfully on {self.device}")

            except Exception as e:
                logger.error(f"Failed to load reranker model: {e}")
                raise RuntimeError(f"Failed to load reranker: {e}")

    def unload_model(self):
        """Unload the reranker model to free memory"""
        if self.model is not None:
            logger.info(f"🔄 Unloading reranker model to free memory...")

            # Delete model reference
            del self.model
            self.model = None

            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("🧹 CUDA cache cleared")

            # Force garbage collection
            gc.collect()

            # Clear access time
            self.last_access_time = None

            logger.info(f"✅ Reranker model unloaded successfully")

    def is_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self.model is not None

    def get_optimal_batch_size(self, default: int = 32) -> int:
        """
        Get optimal batch size based on available memory

        Args:
            default: Default batch size

        Returns:
            Optimal batch size
        """
        try:
            from utils.memory_manager import get_memory_manager
            mm = get_memory_manager()
            return mm.calculate_adaptive_batch_size(
                default_batch_size=default,
                model_name="BGE-Reranker"
            )
        except Exception as e:
            logger.debug(f"Failed to get adaptive batch size: {e}")
            return default

    def _record_access(self):
        """Record model access time (for idle tracking)"""
        self.last_access_time = datetime.now()

        # Also record in memory manager for centralized tracking
        try:
            from utils.memory_manager import get_memory_manager
            mm = get_memory_manager()
            mm.record_model_access("BGE-Reranker")
        except Exception:
            pass  # Silently ignore if memory manager not available

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[Dict]:
        """
        Rerank documents using cross-encoder scoring

        Args:
            query: User query text
            documents: List of document dicts with 'content' or 'text' field
            top_k: Number of top results to return
            return_scores: Include reranker scores in results

        Returns:
            Reranked documents (top_k best matches)
        """
        if not documents:
            return []

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            # Record access for idle tracking
            self._record_access()

            # Extract document texts
            doc_texts = []
            for doc in documents:
                # Support both 'content' and 'text' fields
                text = doc.get('content') or doc.get('text') or doc.get('chunk_content', '')
                if text:
                    doc_texts.append(str(text))
                else:
                    doc_texts.append("")

            if not doc_texts:
                logger.warning("No valid document texts found for reranking")
                return documents[:top_k]

            # Create query-document pairs for cross-encoder
            pairs = [[query, text] for text in doc_texts]

            logger.info(f"Reranking {len(pairs)} query-document pairs...")

            # Use adaptive batch sizing
            adaptive_batch_size = self.get_optimal_batch_size(default=self.batch_size)

            # Score all pairs
            scores = self.model.compute_score(
                pairs,
                batch_size=adaptive_batch_size,
                normalize=True  # Normalize scores to [0, 1]
            )

            # Handle single score vs batch scores
            if isinstance(scores, (float, np.floating)):
                scores = [scores]

            # Combine documents with scores
            scored_docs = []
            for i, doc in enumerate(documents):
                doc_copy = doc.copy()
                if return_scores:
                    doc_copy['reranker_score'] = float(scores[i])
                scored_docs.append((float(scores[i]), doc_copy))

            # Sort by reranker score (descending)
            scored_docs.sort(key=lambda x: x[0], reverse=True)

            # Return top_k
            top_docs = [doc for _, doc in scored_docs[:top_k]]

            logger.info(
                f"✅ Reranking complete. Top score: {scored_docs[0][0]:.4f}, "
                f"Bottom score: {scored_docs[-1][0]:.4f}"
            )

            return top_docs

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback: return original documents
            return documents[:top_k]

    def rerank_with_threshold(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict]:
        """
        Rerank documents and filter by minimum score

        Args:
            query: User query
            documents: Candidate documents
            top_k: Maximum results to return
            min_score: Minimum reranker score threshold

        Returns:
            Reranked documents above threshold
        """
        reranked = self.rerank(query, documents, top_k=len(documents), return_scores=True)

        # Filter by threshold
        filtered = [
            doc for doc in reranked
            if doc.get('reranker_score', 0) >= min_score
        ]

        logger.info(
            f"Filtered {len(reranked)} → {len(filtered)} documents "
            f"(threshold: {min_score})"
        )

        return filtered[:top_k]

    def batch_rerank(
        self,
        queries: List[str],
        document_sets: List[List[Dict]],
        top_k: int = 5
    ) -> List[List[Dict]]:
        """
        Rerank multiple query-document sets in batch

        Args:
            queries: List of queries
            document_sets: List of document lists (one per query)
            top_k: Top results per query

        Returns:
            List of reranked document lists
        """
        results = []

        for query, docs in zip(queries, document_sets):
            reranked = self.rerank(query, docs, top_k=top_k)
            results.append(reranked)

        return results

    def compute_score(
        self,
        query: str,
        document: str
    ) -> float:
        """
        Compute relevance score for a single query-document pair

        Args:
            query: User query
            document: Document text

        Returns:
            Relevance score (0-1, higher is better)
        """
        if self.model is None:
            self.load_model()

        # Record access for idle tracking
        self._record_access()

        try:
            score = self.model.compute_score(
                [[query, document]],
                normalize=True
            )

            # Handle single score
            if isinstance(score, (list, np.ndarray)):
                score = score[0]

            return float(score)

        except Exception as e:
            logger.error(f"Error computing score: {e}")
            return 0.0


# Global instance for reuse (singleton pattern)
_reranker_service_instance: Optional[RerankerService] = None


def get_reranker_service(
    model_name: str = "BAAI/bge-reranker-v2-m3",
    use_fp16: bool = True
) -> RerankerService:
    """
    Get or create the global reranker service instance

    Args:
        model_name: Reranker model to use
        use_fp16: Use FP16 precision (faster on GPU)

    Returns:
        RerankerService instance
    """
    global _reranker_service_instance

    if _reranker_service_instance is None:
        _reranker_service_instance = RerankerService(
            model_name=model_name,
            use_fp16=use_fp16
        )
        logger.info("✅ Global reranker service created")

    return _reranker_service_instance


# Example usage
if __name__ == "__main__":
    # Test reranker
    reranker = RerankerService()
    reranker.load_model()

    query = "How do I optimize molecular dynamics simulations?"

    documents = [
        {"content": "Forcite module provides molecular dynamics simulation tools for optimization."},
        {"content": "The weather today is sunny and warm."},
        {"content": "MD simulations can be optimized by adjusting timestep and cutoff parameters."},
        {"content": "Python is a programming language."},
        {"content": "To improve MD performance, use GPU acceleration and efficient force fields."},
    ]

    reranked = reranker.rerank(query, documents, top_k=3)

    print("\n=== Reranking Results ===")
    for i, doc in enumerate(reranked, 1):
        score = doc.get('reranker_score', 0)
        text = doc.get('content', '')[:80]
        print(f"{i}. Score: {score:.4f} | {text}...")
