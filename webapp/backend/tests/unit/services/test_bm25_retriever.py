"""
Unit Tests for BM25 Retriever
Tests BM25 keyword search
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.bm25_retriever import BM25Retriever


class TestBM25Retriever:
    """Test BM25 Retriever"""

    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing"""
        return [
            {
                "id": 1,
                "content": "Machine learning is a subset of artificial intelligence",
                "document_id": 1
            },
            {
                "id": 2,
                "content": "Deep learning uses neural networks with multiple layers",
                "document_id": 1
            },
            {
                "id": 3,
                "content": "Natural language processing enables computers to understand text",
                "document_id": 2
            },
            {
                "id": 4,
                "content": "Computer vision allows machines to interpret visual information",
                "document_id": 2
            }
        ]

    def test_build_index(self, sample_chunks):
        """Test building BM25 index"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        assert retriever.bm25 is not None
        assert len(retriever.chunks) == 4

    def test_search_basic(self, sample_chunks):
        """Test basic BM25 search"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results = retriever.search("machine learning", top_k=2)

        assert len(results) <= 2
        assert results[0]["content"] == "Machine learning is a subset of artificial intelligence"

    def test_search_multiple_terms(self, sample_chunks):
        """Test search with multiple terms"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results = retriever.search("neural networks deep learning", top_k=2)

        assert len(results) > 0
        # Should prioritize chunk with both terms
        assert "neural networks" in results[0]["content"]

    def test_search_no_results(self, sample_chunks):
        """Test search with no matching results"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results = retriever.search("quantum physics", top_k=5)

        # Should still return results (BM25 always returns something)
        assert isinstance(results, list)

    def test_search_with_scores(self, sample_chunks):
        """Test that search returns scores"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results = retriever.search("machine learning", top_k=3)

        for result in results:
            assert "score" in result
            assert result["score"] >= 0

    def test_empty_query(self, sample_chunks):
        """Test search with empty query"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results = retriever.search("", top_k=3)

        assert isinstance(results, list)

    def test_top_k_parameter(self, sample_chunks):
        """Test top_k parameter limits results"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results_2 = retriever.search("learning", top_k=2)
        results_3 = retriever.search("learning", top_k=3)

        assert len(results_2) == 2
        assert len(results_3) == 3

    def test_save_and_load_index(self, sample_chunks, tmp_path):
        """Test saving and loading BM25 index"""
        retriever1 = BM25Retriever()
        retriever1.build_index(sample_chunks, user_id=1)

        # Save index
        index_path = tmp_path / "bm25_test.pkl"
        retriever1.save_index(str(index_path))

        # Load index
        retriever2 = BM25Retriever()
        retriever2.load_index(str(index_path))

        # Test that loaded index works
        results = retriever2.search("machine learning", top_k=2)

        assert len(results) > 0
        assert results[0]["content"] == "Machine learning is a subset of artificial intelligence"

    def test_rebuild_index(self, sample_chunks):
        """Test rebuilding index with new data"""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks, user_id=1)

        results_before = retriever.search("machine learning", top_k=1)

        # Add more chunks and rebuild
        new_chunks = sample_chunks + [
            {
                "id": 5,
                "content": "Reinforcement learning teaches agents through rewards",
                "document_id": 3
            }
        ]

        retriever.build_index(new_chunks, user_id=1)

        results_after = retriever.search("reinforcement learning", top_k=1)

        assert len(retriever.chunks) == 5
        assert "Reinforcement learning" in results_after[0]["content"]
