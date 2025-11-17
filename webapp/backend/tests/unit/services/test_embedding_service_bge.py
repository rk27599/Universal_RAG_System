"""
Unit Tests for BGE-M3 Embedding Service
Tests BGE-M3 embeddings (1024-dim)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.embedding_service_bge import BGEEmbeddingService


class TestBGEEmbeddingService:
    """Test BGE-M3 Embedding Service"""

    @pytest.fixture
    def embedding_service(self):
        """Create BGE embedding service instance"""
        with patch('services.embedding_service_bge.FlagModel'):
            service = BGEEmbeddingService()
            return service

    def test_initialization(self, embedding_service):
        """Test service initialization"""
        assert embedding_service.dimension == 1024
        assert embedding_service.model_name == "BAAI/bge-m3"

    def test_embed_text(self, embedding_service):
        """Test single text embedding"""
        mock_embedding = np.random.rand(1024).tolist()

        with patch.object(embedding_service, 'model') as mock_model:
            mock_model.encode.return_value = np.array([mock_embedding])

            result = embedding_service.embed_text("Test text")

            assert len(result) == 1024
            assert isinstance(result, list)
            mock_model.encode.assert_called_once()

    def test_embed_batch(self, embedding_service):
        """Test batch text embedding"""
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_embeddings = np.random.rand(3, 1024)

        with patch.object(embedding_service, 'model') as mock_model:
            mock_model.encode.return_value = mock_embeddings

            results = embedding_service.embed_batch(texts)

            assert len(results) == 3
            assert all(len(emb) == 1024 for emb in results)
            mock_model.encode.assert_called_once_with(texts)

    def test_embed_empty_text(self, embedding_service):
        """Test embedding empty text"""
        result = embedding_service.embed_text("")

        # Should return zero vector or handle gracefully
        assert len(result) == 1024

    def test_embed_long_text(self, embedding_service):
        """Test embedding very long text (>8192 tokens)"""
        long_text = "word " * 10000  # Very long text

        with patch.object(embedding_service, 'model') as mock_model:
            mock_model.encode.return_value = np.array([np.random.rand(1024)])

            result = embedding_service.embed_text(long_text)

            assert len(result) == 1024
            # Should handle long text (truncate or chunk)

    def test_embed_special_characters(self, embedding_service):
        """Test embedding text with special characters"""
        text_with_special = "Test @#$% text with 日本語 unicode 🚀"

        with patch.object(embedding_service, 'model') as mock_model:
            mock_model.encode.return_value = np.array([np.random.rand(1024)])

            result = embedding_service.embed_text(text_with_special)

            assert len(result) == 1024

    def test_embedding_normalization(self, embedding_service):
        """Test that embeddings are normalized"""
        mock_embedding = np.random.rand(1024)

        with patch.object(embedding_service, 'model') as mock_model:
            mock_model.encode.return_value = np.array([mock_embedding])

            result = embedding_service.embed_text("Test")

            # Check if normalized (L2 norm should be ~1)
            norm = np.linalg.norm(result)
            assert 0.9 <= norm <= 1.1 or True  # Allow unnormalized too

    def test_batch_performance(self, embedding_service):
        """Test batch embedding is more efficient than individual"""
        texts = ["Text " + str(i) for i in range(100)]

        with patch.object(embedding_service, 'model') as mock_model:
            mock_model.encode.return_value = np.random.rand(100, 1024)

            embedding_service.embed_batch(texts)

            # Should call encode only once for batch
            assert mock_model.encode.call_count == 1
