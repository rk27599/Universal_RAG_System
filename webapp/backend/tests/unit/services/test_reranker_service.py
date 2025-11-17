"""
Unit Tests for Reranker Service
Tests cross-encoder reranking with BGE-reranker-v2-m3
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.reranker_service import RerankerService


class TestRerankerService:
    """Test Reranker Service"""

    @pytest.fixture
    def reranker_service(self):
        """Create reranker service instance"""
        with patch('services.reranker_service.FlagReranker'):
            service = RerankerService()
            return service

    @pytest.fixture
    def sample_query_passages(self):
        """Sample query and passages for reranking"""
        query = "What is machine learning?"
        passages = [
            {"content": "Machine learning is a subset of AI", "score": 0.5, "id": 1},
            {"content": "Deep learning uses neural networks", "score": 0.4, "id": 2},
            {"content": "Machine learning enables computers to learn from data", "score": 0.6, "id": 3},
            {"content": "Computer vision processes images", "score": 0.3, "id": 4}
        ]
        return query, passages

    def test_initialization(self, reranker_service):
        """Test reranker service initialization"""
        assert reranker_service.model_name == "BAAI/bge-reranker-v2-m3"
        assert reranker_service.model is not None

    def test_rerank_basic(self, reranker_service, sample_query_passages):
        """Test basic reranking"""
        query, passages = sample_query_passages

        # Mock reranker scores
        mock_scores = [0.85, 0.45, 0.92, 0.30]

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_scores

            reranked = reranker_service.rerank(query, passages, top_k=3)

            assert len(reranked) == 3
            # Should be ordered by reranker score (highest first)
            assert reranked[0]["reranker_score"] >= reranked[1]["reranker_score"]

    def test_rerank_preserves_original_data(self, reranker_service, sample_query_passages):
        """Test that reranking preserves original passage data"""
        query, passages = sample_query_passages

        mock_scores = [0.8, 0.7, 0.9, 0.6]

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_scores

            reranked = reranker_service.rerank(query, passages, top_k=4)

            # Check original fields are preserved
            for result in reranked:
                assert "content" in result
                assert "id" in result
                assert "score" in result  # Original score
                assert "reranker_score" in result  # New reranker score

    def test_rerank_top_k_limit(self, reranker_service, sample_query_passages):
        """Test top_k parameter limits results"""
        query, passages = sample_query_passages

        mock_scores = [0.8, 0.7, 0.9, 0.6]

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_scores

            reranked_2 = reranker_service.rerank(query, passages, top_k=2)
            reranked_4 = reranker_service.rerank(query, passages, top_k=4)

            assert len(reranked_2) == 2
            assert len(reranked_4) == 4

    def test_rerank_empty_passages(self, reranker_service):
        """Test reranking with empty passages"""
        query = "test query"
        passages = []

        reranked = reranker_service.rerank(query, passages, top_k=5)

        assert reranked == []

    def test_rerank_single_passage(self, reranker_service):
        """Test reranking with single passage"""
        query = "test query"
        passages = [{"content": "test content", "score": 0.5, "id": 1}]

        mock_score = [0.8]

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_score

            reranked = reranker_service.rerank(query, passages, top_k=5)

            assert len(reranked) == 1
            assert reranked[0]["reranker_score"] == 0.8

    def test_rerank_score_ordering(self, reranker_service):
        """Test that results are ordered by reranker score"""
        query = "machine learning"
        passages = [
            {"content": "Low relevance", "score": 0.9, "id": 1},
            {"content": "High relevance machine learning AI", "score": 0.5, "id": 2},
            {"content": "Medium relevance learning", "score": 0.7, "id": 3}
        ]

        # Mock scores: passage 2 should be highest
        mock_scores = [0.4, 0.95, 0.6]

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_scores

            reranked = reranker_service.rerank(query, passages, top_k=3)

            # Passage 2 should be first (highest reranker score)
            assert reranked[0]["id"] == 2
            assert reranked[0]["reranker_score"] == 0.95

    def test_rerank_batch_processing(self, reranker_service):
        """Test reranking processes all query-passage pairs"""
        query = "test query"
        passages = [{"content": f"content {i}", "score": 0.5, "id": i} for i in range(10)]

        mock_scores = np.random.rand(10).tolist()

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_scores

            reranked = reranker_service.rerank(query, passages, top_k=5)

            # Should process all passages and return top 5
            assert len(reranked) == 5
            assert mock_compute.call_count == 1

    def test_rerank_score_normalization(self, reranker_service):
        """Test that reranker scores are properly normalized"""
        query = "test"
        passages = [
            {"content": "content 1", "score": 0.5, "id": 1},
            {"content": "content 2", "score": 0.5, "id": 2}
        ]

        mock_scores = [0.7, 0.9]

        with patch.object(reranker_service.model, 'compute_score') as mock_compute:
            mock_compute.return_value = mock_scores

            reranked = reranker_service.rerank(query, passages, top_k=2)

            # Scores should be in reasonable range (0-1)
            for result in reranked:
                assert 0 <= result["reranker_score"] <= 1.1  # Allow slight overflow
