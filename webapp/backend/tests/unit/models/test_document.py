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

from models.document import Document, DocumentChunk
from models.user import User


class TestDocumentModel:
    """Test Document Model"""

    def test_create_document(self, test_db_session, test_user):
        """Test creating a new document"""
        document = Document(
            title="Test PDF",
            file_path="/uploads/test.pdf",
            file_type="application/pdf",
            file_size=2048,
            user_id=test_user.id
        )

        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)

        assert document.id is not None
        assert document.title == "Test PDF"
        assert document.file_type == "application/pdf"
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
            file_path="/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            user_id=test_user.id,
            processing_status="pending"
        )
        test_db_session.add(document)
        test_db_session.commit()

        # Update to processing
        document.processing_status = "processing"
        test_db_session.commit()
        assert document.processing_status == "processing"

        # Update to completed
        document.processing_status = "completed"
        test_db_session.commit()
        assert document.processing_status == "completed"

    def test_document_chunks_relationship(self, test_db_session, test_document):
        """Test document has many chunks"""
        # Create chunks
        for i in range(3):
            chunk = DocumentChunk(
                document_id=test_document.id,
                chunk_index=i,
                content=f"Chunk {i} content",
                embedding=[0.1] * 1024
            )
            test_db_session.add(chunk)

        test_db_session.commit()
        test_db_session.refresh(test_document)

        assert len(test_document.chunks) == 3
        assert test_document.chunks[0].chunk_index == 0

    def test_document_deletion_cascades(self, test_db_session, test_document):
        """Test deleting document deletes chunks"""
        # Create chunks
        for i in range(3):
            chunk = DocumentChunk(
                document_id=test_document.id,
                chunk_index=i,
                content=f"Chunk {i}",
                embedding=[0.1] * 1024
            )
            test_db_session.add(chunk)

        test_db_session.commit()
        doc_id = test_document.id

        # Delete document
        test_db_session.delete(test_document)
        test_db_session.commit()

        # Chunks should also be deleted (cascade)
        remaining_chunks = test_db_session.query(DocumentChunk).filter_by(
            document_id=doc_id
        ).all()

        assert len(remaining_chunks) == 0


class TestDocumentChunkModel:
    """Test DocumentChunk Model"""

    def test_create_chunk(self, test_db_session, test_document):
        """Test creating a document chunk"""
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="This is a test chunk of text.",
            embedding=[0.1] * 1024,
            page_number=1
        )

        test_db_session.add(chunk)
        test_db_session.commit()
        test_db_session.refresh(chunk)

        assert chunk.id is not None
        assert chunk.chunk_index == 0
        assert chunk.content == "This is a test chunk of text."
        assert len(chunk.embedding) == 1024

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

        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="Test content",
            embedding=[0.1] * 1024,
            metadata_=metadata
        )

        test_db_session.add(chunk)
        test_db_session.commit()
        test_db_session.refresh(chunk)

        assert chunk.metadata_["section"] == "Introduction"
        assert chunk.metadata_["heading"] == "Overview"
        assert chunk.metadata_["table_count"] == 2

    def test_chunk_ordering(self, test_db_session, test_document):
        """Test chunks are ordered by chunk_index"""
        # Create chunks out of order
        for i in [2, 0, 1]:
            chunk = DocumentChunk(
                document_id=test_document.id,
                chunk_index=i,
                content=f"Chunk {i}",
                embedding=[0.1] * 1024
            )
            test_db_session.add(chunk)

        test_db_session.commit()
        test_db_session.refresh(test_document)

        # Query chunks ordered
        chunks = test_db_session.query(DocumentChunk).filter_by(
            document_id=test_document.id
        ).order_by(DocumentChunk.chunk_index).all()

        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1
        assert chunks[2].chunk_index == 2

    def test_chunk_page_number(self, test_db_session, test_document):
        """Test chunk page number tracking"""
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="Page 5 content",
            embedding=[0.1] * 1024,
            page_number=5
        )

        test_db_session.add(chunk)
        test_db_session.commit()

        assert chunk.page_number == 5

    def test_chunk_embedding_dimension(self, test_db_session, test_document):
        """Test chunk embedding has correct dimension"""
        # BGE-M3 uses 1024 dimensions
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_index=0,
            content="Test",
            embedding=[0.1] * 1024
        )

        test_db_session.add(chunk)
        test_db_session.commit()

        assert len(chunk.embedding) == 1024
