"""
Conversation and Message Models with Security-First Design
Local chat history with comprehensive audit trail
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, List

from core.database import BaseModel, SecurityAuditMixin


class Conversation(BaseModel, SecurityAuditMixin):
    """Conversation model for chat sessions"""
    __tablename__ = "conversations"

    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-set
    description = Column(Text, nullable=True)   # Optional description

    # Status and settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)

    # Model configuration
    model_name = Column(String(100), nullable=False, default="mistral")
    model_parameters = Column(JSON, nullable=True)  # Temperature, max_tokens, etc.

    # Conversation statistics
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Performance metrics
    avg_response_time = Column(Float, nullable=True)  # Average response time in seconds
    total_response_time = Column(Float, default=0.0)  # Cumulative response time

    # Context management
    context_length = Column(Integer, default=0)  # Current context window size
    max_context_length = Column(Integer, default=4096)  # Maximum context to maintain

    # Privacy and security
    retention_until = Column(DateTime(timezone=True), nullable=True)  # Auto-delete date
    is_sensitive = Column(Boolean, default=False)  # User-marked sensitive
    anonymize_after = Column(DateTime(timezone=True), nullable=True)  # Anonymization date

    # Document context (if any)
    document_context = Column(JSON, nullable=True)  # Referenced document IDs

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan",
                          order_by="Message.created_at")

    # Database indexes
    __table_args__ = (
        Index('idx_conversation_user', 'user_id'),
        Index('idx_conversation_active', 'is_active'),
        Index('idx_conversation_last_activity', 'last_activity'),
        Index('idx_conversation_model', 'model_name'),
        Index('idx_conversation_archived', 'is_archived'),
    )

    def __repr__(self):
        title_preview = self.title[:30] + "..." if self.title and len(self.title) > 30 else (self.title or "Untitled")
        return f"<Conversation(id={self.id}, title='{title_preview}', messages={self.message_count})>"

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def increment_message_count(self):
        """Increment message count"""
        self.message_count += 1
        self.update_activity()

    def add_response_time(self, response_time: float):
        """Add response time and update average"""
        self.total_response_time += response_time
        if self.message_count > 0:
            self.avg_response_time = self.total_response_time / (self.message_count / 2)  # Divide by 2 for assistant messages only

    def add_tokens(self, token_count: int):
        """Add tokens to total count"""
        self.total_tokens += token_count

    def archive(self):
        """Archive conversation"""
        self.is_archived = True
        self.is_active = False
        self.update_activity()

    def activate(self):
        """Activate conversation"""
        self.is_archived = False
        self.is_active = True
        self.update_activity()

    def set_retention_policy(self, days: int):
        """Set retention policy for conversation"""
        from datetime import timedelta
        self.retention_until = datetime.utcnow() + timedelta(days=days)

    def get_summary(self) -> dict:
        """Get conversation summary"""
        return {
            "id": self.id,
            "title": self.title,
            "message_count": self.message_count,
            "model_name": self.model_name,
            "total_tokens": self.total_tokens,
            "avg_response_time": self.avg_response_time,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat()
        }


class Message(BaseModel, SecurityAuditMixin):
    """Message model for chat messages"""
    __tablename__ = "messages"

    # Conversation relationship
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Message metadata
    token_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=False, default=0)

    # Processing information (for assistant messages)
    model_name = Column(String(100), nullable=True)  # Model used for generation
    model_parameters = Column(JSON, nullable=True)  # Parameters used
    response_time = Column(Float, nullable=True)     # Generation time in seconds

    # Context information
    context_documents = Column(JSON, nullable=True)  # Document chunks used for context
    context_length = Column(Integer, nullable=True)   # Context window size used

    # Quality metrics
    similarity_score = Column(Float, nullable=True)   # Relevance score
    confidence_score = Column(Float, nullable=True)   # Model confidence

    # User feedback
    user_rating = Column(Integer, nullable=True)      # 1-5 rating from user
    user_feedback = Column(Text, nullable=True)       # Optional text feedback

    # Message status
    is_edited = Column(Boolean, default=False)
    edit_count = Column(Integer, default=0)
    is_regenerated = Column(Boolean, default=False)   # If assistant message was regenerated

    # Security and audit
    content_hash = Column(String(64), nullable=True)  # Hash for integrity
    is_sensitive = Column(Boolean, default=False)     # Flagged as sensitive

    # Processing metadata
    processing_metadata = Column(JSON, nullable=True)  # Additional processing info

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Database indexes
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_role', 'role'),
        Index('idx_message_created', 'created_at'),
        Index('idx_message_model', 'model_name'),
        Index('idx_message_rating', 'user_rating'),
    )

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role='{self.role}', content='{content_preview}')>"

    def set_content_stats(self):
        """Calculate and set content statistics"""
        if self.content:
            self.character_count = len(self.content)
            # Rough token estimation (1 token ≈ 4 characters for English)
            if not self.token_count:
                self.token_count = max(1, len(self.content) // 4)

    def set_response_metrics(self, response_time: float, model_name: str, model_params: dict = None):
        """Set response generation metrics"""
        self.response_time = response_time
        self.model_name = model_name
        if model_params:
            self.model_parameters = model_params

    def set_context_info(self, context_docs: List[dict], context_length: int, similarity_score: float = None):
        """Set context information used for generation"""
        self.context_documents = context_docs
        self.context_length = context_length
        if similarity_score:
            self.similarity_score = similarity_score

    def add_user_feedback(self, rating: int, feedback: str = None):
        """Add user feedback for message"""
        if 1 <= rating <= 5:
            self.user_rating = rating
        if feedback:
            self.user_feedback = feedback

    def mark_edited(self):
        """Mark message as edited"""
        self.is_edited = True
        self.edit_count += 1

    def mark_regenerated(self):
        """Mark assistant message as regenerated"""
        self.is_regenerated = True

    def get_context_summary(self) -> dict:
        """Get context information summary"""
        return {
            "model_name": self.model_name,
            "response_time": self.response_time,
            "token_count": self.token_count,
            "context_length": self.context_length,
            "similarity_score": self.similarity_score,
            "confidence_score": self.confidence_score,
            "document_count": len(self.context_documents) if self.context_documents else 0,
            "user_rating": self.user_rating
        }


class ConversationSummary(BaseModel):
    """Conversation summary for efficient loading"""
    __tablename__ = "conversation_summaries"

    conversation_id = Column(Integer, ForeignKey("conversations.id"), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Summary content
    summary_text = Column(Text, nullable=False)
    key_topics = Column(JSON, nullable=True)      # Extracted topics
    entities_mentioned = Column(JSON, nullable=True)  # Named entities

    # Summary metadata
    messages_summarized = Column(Integer, nullable=False)
    summary_model = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Update tracking
    last_message_id = Column(Integer, nullable=True)  # Last message included in summary
    needs_update = Column(Boolean, default=False)

    # Summary statistics
    summary_length = Column(Integer, nullable=False, default=0)
    compression_ratio = Column(Float, nullable=True)  # Original length / summary length

    # Database indexes
    __table_args__ = (
        Index('idx_summary_conversation', 'conversation_id'),
        Index('idx_summary_user', 'user_id'),
        Index('idx_summary_update', 'needs_update'),
    )

    def __repr__(self):
        return f"<ConversationSummary(conversation_id={self.conversation_id}, messages={self.messages_summarized})>"

    def mark_for_update(self):
        """Mark summary as needing update"""
        self.needs_update = True

    def update_summary(self, summary_text: str, message_count: int, last_message_id: int):
        """Update summary content"""
        self.summary_text = summary_text
        self.messages_summarized = message_count
        self.last_message_id = last_message_id
        self.needs_update = False
        self.summary_length = len(summary_text)


class MessageSearchIndex(BaseModel):
    """Search index for message content"""
    __tablename__ = "message_search_index"

    message_id = Column(Integer, ForeignKey("messages.id"), unique=True, nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Searchable content
    searchable_content = Column(Text, nullable=False)  # Processed content for search
    keywords = Column(JSON, nullable=True)           # Extracted keywords
    entities = Column(JSON, nullable=True)           # Named entities

    # Search metadata
    language = Column(String(10), default="en")
    content_type = Column(String(50), nullable=True)  # text, code, math, etc.

    # Full-text search vector (PostgreSQL specific)
    search_vector = Column(Text, nullable=True)  # tsvector for full-text search

    # Database indexes
    __table_args__ = (
        Index('idx_search_message', 'message_id'),
        Index('idx_search_conversation', 'conversation_id'),
        Index('idx_search_user', 'user_id'),
        Index('idx_search_content', 'searchable_content', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<MessageSearchIndex(message_id={self.message_id}, conversation_id={self.conversation_id})>"