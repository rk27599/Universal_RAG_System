"""
Unit Tests for Document Model
Tests Document and DocumentChunk database models
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from models.document import Document, Chunk
from models.user import User


class TestDocumentModel:
    """Test Document Model"""

    def test_create_document(self, test_db_session, test_user):
        """Test creating a new document"""
        document = Document(
            title="Test PDF",
            source_path="/uploads/test.pdf",
            source_type="file",
            content_type="application/pdf",
            content_hash="test_hash",
            file_size=2048,
            user_id=test_user.id
        )

        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)

        assert document.id is not None
        assert document.title == "Test PDF"
        assert document.content_type == "application/pdf"
        assert document.processing_status == "pending"  # Default
        assert document.created_at is not None

    def test_document_user_relationship(self, test_db_session, test_document):
        """Test document belongs to user"""
        assert test_document.user is not None
        assert test_document.user.username == "testuser"

    def test_document_processing_status(self, test_db_session, test_user):
        """Test document processing status transitions"""
        document = Document(
            title="Processing Test",
            source_path="/test.pdf",
            source_type="file",
            content_type="application/pdf",
            content_hash="test_hash2",
            file_size=1024,
            user_id=test_user.id,
            processing_status="pending"
        )
        test_db_session.add(document)
        test_db_session.commit()

        # Update to processing
        document.start_processing()
        test_db_session.commit()
        assert document.processing_status == "processing"

        # Update to completed
        document.complete_processing(chunk_count=5)
        test_db_session.commit()
        assert document.processing_status == "completed"

    def test_document_chunks_relationship(self, test_db_session, test_document):
        """Test document has many chunks"""
        # Create chunks
        for i in range(3):
            chunk = Chunk(
                document_id=test_document.id,
                chunk_order=i,
                content=f"Chunk {i} content",
                content_hash=f"chunk_hash_{i}",
                character_count=20,
                token_count=5,
                word_count=3
            )
            test_db_session.add(chunk)

        test_db_session.commit()
        test_db_session.refresh(test_document)

        assert len(test_document.chunks) == 3
        assert test_document.chunks[0].chunk_order == 0

    def test_document_deletion_cascades(self, test_db_session, test_document):
        """Test deleting document deletes chunks"""
        # Create chunks
        for i in range(3):
            chunk = Chunk(
                document_id=test_document.id,
                chunk_order=i,
                content=f"Chunk {i}",
                content_hash=f"del_hash_{i}",
                character_count=10,
                token_count=2,
                word_count=2
            )
            test_db_session.add(chunk)

        test_db_session.commit()
        doc_id = test_document.id

        # Delete document
        test_db_session.delete(test_document)
        test_db_session.commit()

        # Chunks should also be deleted (cascade)
        remaining_chunks = test_db_session.query(Chunk).filter_by(
            document_id=doc_id
        ).all()

        assert len(remaining_chunks) == 0


class TestChunkModel:
    """Test Chunk Model"""

    def test_create_chunk(self, test_db_session, test_document):
        """Test creating a document chunk"""
        chunk = Chunk(
            document_id=test_document.id,
            chunk_order=0,
            content="This is a test chunk of text.",
            content_hash="test_chunk_hash",
            character_count=30,
            token_count=7,
            word_count=7,
            page_number=1
        )

        test_db_session.add(chunk)
        test_db_session.commit()
        test_db_session.refresh(chunk)

        assert chunk.id is not None
        assert chunk.chunk_order == 0
        assert chunk.content == "This is a test chunk of text."
        assert chunk.character_count == 30

    def test_chunk_document_relationship(self, test_db_session, test_document_chunks):
        """Test chunk belongs to document"""
        chunk = test_document_chunks[0]

        assert chunk.document is not None
        assert chunk.document.title == "Test Document"

    def test_chunk_metadata(self, test_db_session, test_document):
        """Test chunk metadata storage"""
        metadata = {
            "section": "Introduction",
            "heading": "Overview",
            "table_count": 2
        }

        chunk = Chunk(
            document_id=test_document.id,
            chunk_order=0,
            content="Test content",
            content_hash="meta_hash",
            extraction_metadata=metadata,
            character_count=12,
            token_count=2,
            word_count=2
        )

        test_db_session.add(chunk)
        test_db_session.commit()
        test_db_session.refresh(chunk)

        assert chunk.extraction_metadata["section"] == "Introduction"
        assert chunk.extraction_metadata["heading"] == "Overview"
        assert chunk.extraction_metadata["table_count"] == 2

    def test_chunk_ordering(self, test_db_session, test_document):
        """Test chunks are ordered by chunk_order"""
        # Create chunks out of order
        for i in [2, 0, 1]:
            chunk = Chunk(
                document_id=test_document.id,
                chunk_order=i,
                content=f"Chunk {i}",
                content_hash=f"order_hash_{i}",
                character_count=10,
                token_count=2,
                word_count=2
            )
            test_db_session.add(chunk)

        test_db_session.commit()
        test_db_session.refresh(test_document)

        # Query chunks ordered
        chunks = test_db_session.query(Chunk).filter_by(
            document_id=test_document.id
        ).order_by(Chunk.chunk_order).all()

        assert chunks[0].chunk_order == 0
        assert chunks[1].chunk_order == 1
        assert chunks[2].chunk_order == 2

    def test_chunk_page_number(self, test_db_session, test_document):
        """Test chunk page number tracking"""
        chunk = Chunk(
            document_id=test_document.id,
            chunk_order=0,
            content="Page 5 content",
            content_hash="page_hash",
            character_count=15,
            token_count=3,
            word_count=3,
            page_number=5
        )

        test_db_session.add(chunk)
        test_db_session.commit()

        assert chunk.page_number == 5

    def test_chunk_content_stats(self, test_db_session, test_document):
        """Test chunk content statistics"""
        chunk = Chunk(
            document_id=test_document.id,
            chunk_order=0,
            content="This is a test of content statistics",
            content_hash="stats_hash",
            character_count=0,
            token_count=0,
            word_count=0
        )

        # Calculate stats
        chunk.set_content_stats()

        test_db_session.add(chunk)
        test_db_session.commit()

        assert chunk.character_count > 0
        assert chunk.word_count > 0
        assert chunk.token_count > 0
