"""
Document and Chunk Models with Security-First Design
Local storage with comprehensive metadata and vector embeddings
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, Float
from sqlalchemy import JSON

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import Optional, List, Dict

from core.database import BaseModel, SecurityAuditMixin


class Document(BaseModel, SecurityAuditMixin):
    """Document model with security and audit features"""
    __tablename__ = "documents"

    # Owner relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Document metadata
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    source_type = Column(String(20), nullable=False)  # 'file', 'url', 'text'
    source_url = Column(Text, nullable=True)  # Original URL if scraped
    source_path = Column(Text, nullable=True)  # Local file path

    # Content information
    content_type = Column(String(100), nullable=True)  # MIME type
    file_size = Column(Integer, nullable=True)  # Size in bytes
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for integrity

    # Processing status
    processing_status = Column(String(20), default="pending", nullable=False)
    # pending, processing, completed, failed, deleted
    processing_progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Content statistics
    total_chunks = Column(Integer, default=0)
    total_characters = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)  # Estimated token count

    # Security and privacy
    is_sensitive = Column(Boolean, default=False)  # User-marked sensitive data
    retention_until = Column(DateTime(timezone=True), nullable=True)  # Auto-delete date
    access_count = Column(Integer, default=0)  # Number of times accessed

    # Metadata for processing
    processing_config = Column(JSON, nullable=True)  # Processing parameters used
    extraction_metadata = Column(JSON, nullable=True)  # Metadata from extraction

    # Image-specific metadata (for image documents)
    image_width = Column(Integer, nullable=True)  # Image width in pixels
    image_height = Column(Integer, nullable=True)  # Image height in pixels
    image_format = Column(String(20), nullable=True)  # Image format (JPEG, PNG, etc.)
    has_ocr_text = Column(Boolean, default=False)  # Whether OCR was performed
    has_vision_description = Column(Boolean, default=False)  # Whether vision model generated description
    thumbnail_path = Column(Text, nullable=True)  # Path to thumbnail image

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    # Database indexes
    __table_args__ = (
        Index('idx_document_user', 'user_id'),
        Index('idx_document_status', 'processing_status'),
        Index('idx_document_hash', 'content_hash'),
        Index('idx_document_type', 'source_type'),
        Index('idx_document_created', 'created_at'),
    )

    def __repr__(self):
        return f"<Document(title='{self.title}', user_id={self.user_id}, status='{self.processing_status}')>"

    @property
    def is_processed(self) -> bool:
        """Check if document processing is complete"""
        return self.processing_status == "completed"

    @property
    def processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None

    def start_processing(self):
        """Mark document processing as started"""
        self.processing_status = "processing"
        self.processing_progress = 0.0
        self.processing_started_at = datetime.utcnow()

    def update_progress(self, progress: float):
        """Update processing progress (0.0 to 100.0)"""
        self.processing_progress = max(0.0, min(100.0, progress))

    def complete_processing(self, chunk_count: int = 0, char_count: int = 0, token_count: int = 0):
        """Mark document processing as completed"""
        self.processing_status = "completed"
        self.processing_progress = 100.0
        self.processing_completed_at = datetime.utcnow()
        self.total_chunks = chunk_count
        self.total_characters = char_count
        self.total_tokens = token_count

    def fail_processing(self, error_message: str):
        """Mark document processing as failed"""
        self.processing_status = "failed"
        self.processing_error = error_message
        self.processing_completed_at = datetime.utcnow()

    def increment_access_count(self):
        """Increment access count and update last accessed time"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def get_processing_summary(self) -> dict:
        """Get processing summary"""
        return {
            "status": self.processing_status,
            "progress": self.processing_progress,
            "chunks": self.total_chunks,
            "characters": self.total_characters,
            "tokens": self.total_tokens,
            "duration_seconds": self.processing_duration,
            "started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "completed_at": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            "error": self.processing_error
        }

    @classmethod
    def get_stuck_documents(cls, db, stuck_threshold_minutes: int = 5) -> List['Document']:
        """
        Find documents stuck in processing or pending status

        A document is considered stuck if it's in "pending" or "processing" status
        and was created more than stuck_threshold_minutes ago.

        Args:
            db: Database session (Session object)
            stuck_threshold_minutes: Minutes before document is considered stuck (default: 5)

        Returns:
            List of Document objects stuck in processing
        """
        from datetime import datetime, timezone, timedelta
        from sqlalchemy.orm import Session

        threshold_time = datetime.now(timezone.utc) - timedelta(minutes=stuck_threshold_minutes)

        stuck_docs = db.query(cls).filter(
            cls.processing_status.in_(["pending", "processing"]),
            cls.created_at < threshold_time
        ).all()

        return stuck_docs


class Chunk(BaseModel, SecurityAuditMixin):
    """Document chunk model with vector embeddings"""
    __tablename__ = "chunks"

    # Document relationship
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    # Chunk content
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)  # Hash for deduplication

    # Vector embedding (using pgvector)
    embedding = Column(Vector(384), nullable=True)  # 384 dimensions for all-MiniLM-L6-v2 (old)
    embedding_model = Column(String(100), nullable=True)  # Model used for embedding (old)

    # New BGE-M3 embeddings (1024 dimensions)
    embedding_new = Column(Vector(1024), nullable=True)  # 1024 dimensions for BAAI/bge-m3
    embedding_model_new = Column(String(100), nullable=True)  # Model used for new embedding

    # Chunk metadata
    chunk_order = Column(Integer, nullable=False)  # Order within document
    content_type = Column(String(50), nullable=True)  # paragraph, heading, code, list, etc.

    # Content statistics
    character_count = Column(Integer, nullable=False, default=0)
    token_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)

    # Hierarchical information
    section_hierarchy = Column(JSON, nullable=True)  # ["Chapter 1", "Section 1.1", etc.]
    page_number = Column(Integer, nullable=True)  # If applicable

    # Processing metadata
    extraction_metadata = Column(JSON, nullable=True)  # Metadata from content extraction
    similarity_threshold = Column(Float, nullable=True)  # Quality threshold used

    # Search and retrieval optimization
    search_keywords = Column(JSON, nullable=True)  # Keywords for enhanced search
    importance_score = Column(Float, nullable=True)  # Content importance score

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Database indexes for performance
    __table_args__ = (
        Index('idx_chunk_document', 'document_id'),
        Index('idx_chunk_order', 'document_id', 'chunk_order'),
        Index('idx_chunk_hash', 'content_hash'),
        Index('idx_chunk_type', 'content_type'),
        # HNSW index for vector similarity with cosine distance
        # m: max number of connections per layer (16 = good balance)
        # ef_construction: size of dynamic candidate list (64 = good quality)
        Index('idx_chunk_embedding', 'embedding',
              postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64},
              postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Chunk(document_id={self.document_id}, order={self.chunk_order}, content='{content_preview}')>"

    @property
    def has_embedding(self) -> bool:
        """Check if chunk has an embedding"""
        return self.embedding is not None

    def set_content_stats(self):
        """Calculate and set content statistics"""
        if self.content:
            self.character_count = len(self.content)
            self.word_count = len(self.content.split())
            # Rough token estimation (1 token ≈ 4 characters for English)
            self.token_count = max(1, len(self.content) // 4)

    def get_section_path(self) -> str:
        """Get human-readable section path"""
        if self.section_hierarchy:
            return " > ".join(self.section_hierarchy)
        return f"Chunk {self.chunk_order}"

    def calculate_similarity(self, query_embedding: List[float]) -> Optional[float]:
        """
        Calculate cosine similarity with query embedding

        Note: For production use, prefer database-level similarity search using
        pgvector operators for better performance with HNSW index.

        Args:
            query_embedding: Query vector to compare against

        Returns:
            Cosine similarity score (0-1), or None if embeddings unavailable
        """
        if not self.embedding or not query_embedding:
            return None

        # This method is for fallback/debugging only
        # In production, use pgvector's cosine_distance operator in queries
        # which leverages the HNSW index for O(log n) performance
        try:
            import numpy as np
            from numpy.linalg import norm

            # Convert embeddings to numpy arrays
            emb1 = np.array(self.embedding)
            emb2 = np.array(query_embedding)

            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))
            return float(similarity)
        except Exception:
            return None

    def get_metadata_summary(self) -> dict:
        """Get chunk metadata summary"""
        return {
            "order": self.chunk_order,
            "content_type": self.content_type,
            "character_count": self.character_count,
            "word_count": self.word_count,
            "token_count": self.token_count,
            "section_path": self.get_section_path(),
            "page_number": self.page_number,
            "has_embedding": self.has_embedding,
            "embedding_model": self.embedding_model,
            "importance_score": self.importance_score
        }


class DocumentProcessingLog(BaseModel):
    """Log of document processing operations"""
    __tablename__ = "document_processing_logs"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Processing details
    operation = Column(String(50), nullable=False)  # upload, process, delete, etc.
    status = Column(String(20), nullable=False)     # started, completed, failed

    # Timing information
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Processing configuration
    processing_config = Column(JSON, nullable=True)
    model_used = Column(String(100), nullable=True)

    # Results
    chunks_created = Column(Integer, default=0)
    tokens_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # System information
    server_instance = Column(String(100), nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    cpu_time_seconds = Column(Float, nullable=True)

    # Database indexes
    __table_args__ = (
        Index('idx_processing_log_document', 'document_id'),
        Index('idx_processing_log_user', 'user_id'),
        Index('idx_processing_log_operation', 'operation'),
        Index('idx_processing_log_status', 'status'),
        Index('idx_processing_log_time', 'started_at'),
    )

    def __repr__(self):
        return f"<ProcessingLog(document_id={self.document_id}, operation='{self.operation}', status='{self.status}')>"