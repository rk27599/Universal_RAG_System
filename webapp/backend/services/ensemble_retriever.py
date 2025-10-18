"""
Ensemble Retriever - Combines BM25 (sparse) and Vector (dense) retrieval
Implements weighted score fusion for hybrid search
"""

import logging
from typing import List, Dict, Optional, Tuple, Callable
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class EnsembleRetriever:
    """
    Hybrid retrieval combining BM25 and vector search

    Strategy:
    - BM25 (sparse): Good for exact keyword matches
    - Vector (dense): Good for semantic similarity
    - Ensemble: Best of both worlds

    Score Fusion:
    - Weighted sum: score = w1 * bm25_score + w2 * vector_score
    - Default weights: [0.3, 0.7] favors semantic search
    - Adjustable based on use case

    Example:
        Query: "How to optimize Forcite simulations?"

        BM25 Results:
        1. "Forcite optimization parameters" (high - exact match)
        2. "Forcite performance tuning" (medium)

        Vector Results:
        1. "Improving MD simulation speed" (high - semantic)
        2. "Forcite optimization parameters" (high)

        Ensemble:
        1. "Forcite optimization parameters" (highest - both methods agree)
        2. "Improving MD simulation speed" (high - semantic)
        3. "Forcite performance tuning" (medium)
    """

    def __init__(
        self,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        normalize_scores: bool = True
    ):
        """
        Initialize ensemble retriever

        Args:
            bm25_weight: Weight for BM25 scores (default: 0.3)
            vector_weight: Weight for vector scores (default: 0.7)
            normalize_scores: Normalize scores to [0, 1] before fusion
        """
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.normalize_scores = normalize_scores

        # Validate weights
        total_weight = bm25_weight + vector_weight
        if not np.isclose(total_weight, 1.0):
            logger.warning(
                f"Weights don't sum to 1.0 ({total_weight}). "
                "Normalizing..."
            )
            self.bm25_weight = bm25_weight / total_weight
            self.vector_weight = vector_weight / total_weight

        logger.info(
            f"EnsembleRetriever initialized "
            f"(BM25: {self.bm25_weight:.2f}, Vector: {self.vector_weight:.2f})"
        )

    def merge_results(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        top_k: int = 20,
        id_field: str = 'id'
    ) -> List[Dict]:
        """
        Merge BM25 and vector search results using weighted score fusion

        Args:
            bm25_results: Results from BM25 search (with 'bm25_score')
            vector_results: Results from vector search (with 'similarity' or 'vector_score')
            top_k: Number of top results to return
            id_field: Field name for document ID

        Returns:
            Merged and ranked results
        """
        # Normalize scores if requested
        if self.normalize_scores:
            bm25_results = self._normalize_bm25_scores(bm25_results)
            vector_results = self._normalize_vector_scores(vector_results)

        # Build score maps
        bm25_scores = {
            doc.get(id_field): doc.get('bm25_score', 0.0)
            for doc in bm25_results
        }

        vector_scores = {
            doc.get(id_field): doc.get('similarity') or doc.get('vector_score', 0.0)
            for doc in vector_results
        }

        # Get all unique document IDs
        all_ids = set(bm25_scores.keys()) | set(vector_scores.keys())

        # Compute ensemble scores
        ensemble_scores = {}
        for doc_id in all_ids:
            bm25_score = bm25_scores.get(doc_id, 0.0)
            vector_score = vector_scores.get(doc_id, 0.0)

            # Weighted fusion
            ensemble_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score
            )

            ensemble_scores[doc_id] = ensemble_score

        # Get document metadata (prefer vector results for richer metadata)
        doc_map = {}
        for doc in vector_results:
            doc_map[doc.get(id_field)] = doc

        for doc in bm25_results:
            doc_id = doc.get(id_field)
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        # Create scored results
        scored_results = []
        for doc_id, ensemble_score in ensemble_scores.items():
            if doc_id in doc_map:
                doc = doc_map[doc_id].copy()
                doc['ensemble_score'] = float(ensemble_score)
                doc['bm25_score'] = float(bm25_scores.get(doc_id, 0.0))
                doc['vector_score'] = float(vector_scores.get(doc_id, 0.0))
                scored_results.append((ensemble_score, doc))

        # Sort by ensemble score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Return top_k
        top_results = [doc for _, doc in scored_results[:top_k]]

        logger.info(
            f"Ensemble merge: BM25={len(bm25_results)}, Vector={len(vector_results)} "
            f"→ {len(top_results)} results"
        )

        return top_results

    def _normalize_bm25_scores(self, results: List[Dict]) -> List[Dict]:
        """Normalize BM25 scores to [0, 1] range"""
        if not results:
            return results

        scores = [doc.get('bm25_score', 0.0) for doc in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            # All scores are the same
            normalized_results = [
                {**doc, 'bm25_score': 1.0 if max_score > 0 else 0.0}
                for doc in results
            ]
        else:
            # Min-max normalization
            normalized_results = [
                {
                    **doc,
                    'bm25_score': (doc.get('bm25_score', 0.0) - min_score) / (max_score - min_score)
                }
                for doc in results
            ]

        return normalized_results

    def _normalize_vector_scores(self, results: List[Dict]) -> List[Dict]:
        """Normalize vector scores to [0, 1] range"""
        if not results:
            return results

        # Vector scores are typically already in [0, 1] from cosine similarity
        # But we'll normalize just in case
        scores = [doc.get('similarity') or doc.get('vector_score', 0.0) for doc in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            normalized_results = [
                {**doc, 'vector_score': 1.0 if max_score > 0 else 0.0}
                for doc in results
            ]
        else:
            normalized_results = [
                {
                    **doc,
                    'vector_score': (
                        (doc.get('similarity') or doc.get('vector_score', 0.0)) - min_score
                    ) / (max_score - min_score)
                }
                for doc in results
            ]

        return normalized_results

    def rerank_with_fusion(
        self,
        query: str,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        reranker_fn: Optional[Callable] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Three-stage retrieval: BM25 + Vector → Fusion → Reranking

        Args:
            query: Search query
            bm25_results: BM25 search results
            vector_results: Vector search results
            reranker_fn: Optional reranker function(query, docs) -> ranked_docs
            top_k: Final number of results

        Returns:
            Top-k reranked results
        """
        # Stage 1: Ensemble fusion
        ensemble_results = self.merge_results(
            bm25_results,
            vector_results,
            top_k=100  # Get more candidates for reranking
        )

        # Stage 2: Reranking (if provided)
        if reranker_fn is not None:
            logger.info("Applying reranker to ensemble results...")
            reranked_results = reranker_fn(query, ensemble_results)
            return reranked_results[:top_k]

        return ensemble_results[:top_k]

    def reciprocal_rank_fusion(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        top_k: int = 20,
        k: int = 60,
        id_field: str = 'id'
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) - Alternative to weighted fusion

        RRF Formula: score(d) = sum(1 / (k + rank(d)))

        Advantages:
        - No need to normalize scores
        - Robust to score distribution differences
        - Used by many search engines

        Args:
            bm25_results: BM25 results (ranked)
            vector_results: Vector results (ranked)
            top_k: Number of results to return
            k: RRF constant (default: 60)
            id_field: Document ID field

        Returns:
            Merged results using RRF
        """
        # Build rank maps
        bm25_ranks = {
            doc.get(id_field): rank + 1
            for rank, doc in enumerate(bm25_results)
        }

        vector_ranks = {
            doc.get(id_field): rank + 1
            for rank, doc in enumerate(vector_results)
        }

        # Get all unique document IDs
        all_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

        # Compute RRF scores
        rrf_scores = {}
        for doc_id in all_ids:
            rrf_score = 0.0

            if doc_id in bm25_ranks:
                rrf_score += 1.0 / (k + bm25_ranks[doc_id])

            if doc_id in vector_ranks:
                rrf_score += 1.0 / (k + vector_ranks[doc_id])

            rrf_scores[doc_id] = rrf_score

        # Get document metadata
        doc_map = {}
        for doc in vector_results:
            doc_map[doc.get(id_field)] = doc
        for doc in bm25_results:
            if doc.get(id_field) not in doc_map:
                doc_map[doc.get(id_field)] = doc

        # Create scored results
        scored_results = []
        for doc_id, rrf_score in rrf_scores.items():
            if doc_id in doc_map:
                doc = doc_map[doc_id].copy()
                doc['rrf_score'] = float(rrf_score)
                scored_results.append((rrf_score, doc))

        # Sort by RRF score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Return top_k
        top_results = [doc for _, doc in scored_results[:top_k]]

        logger.info(f"RRF merge: {len(top_results)} results")

        return top_results


# Example usage
if __name__ == "__main__":
    # Test ensemble retriever
    ensemble = EnsembleRetriever(bm25_weight=0.3, vector_weight=0.7)

    # BM25 results (keyword matching)
    bm25_results = [
        {"id": "1", "content": "Forcite optimization parameters", "bm25_score": 15.2},
        {"id": "2", "content": "Forcite performance tuning", "bm25_score": 10.5},
        {"id": "3", "content": "DMol3 calculations", "bm25_score": 3.1}
    ]

    # Vector results (semantic matching)
    vector_results = [
        {"id": "1", "content": "Forcite optimization parameters", "similarity": 0.92},
        {"id": "4", "content": "Improving MD simulation speed", "similarity": 0.85},
        {"id": "5", "content": "Molecular dynamics best practices", "similarity": 0.78}
    ]

    # Merge with weighted fusion
    merged = ensemble.merge_results(bm25_results, vector_results, top_k=5)

    print("\n=== Ensemble Results (Weighted Fusion) ===")
    for i, doc in enumerate(merged, 1):
        print(f"{i}. Ensemble: {doc['ensemble_score']:.3f} | "
              f"BM25: {doc['bm25_score']:.3f} | "
              f"Vector: {doc['vector_score']:.3f}")
        print(f"   {doc['content']}\n")

    # Alternative: RRF
    rrf_results = ensemble.reciprocal_rank_fusion(bm25_results, vector_results, top_k=5)

    print("=== Ensemble Results (RRF) ===")
    for i, doc in enumerate(rrf_results, 1):
        print(f"{i}. RRF: {doc['rrf_score']:.3f}")
        print(f"   {doc['content']}\n")
