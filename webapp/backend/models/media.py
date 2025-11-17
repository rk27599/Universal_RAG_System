"""
Media Metadata Models for Multimodal RAG System
Stores metadata for images, audio, video, and other media
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum

from core.database import BaseModel, SecurityAuditMixin


class ModalityType(str, enum.Enum):
    """Supported modality types"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CHART = "chart"
    DIAGRAM = "diagram"
    TABLE = "table"
    CODE = "code"


class MediaMetadata(BaseModel, SecurityAuditMixin):
    """
    Media metadata model for multimodal content
    Stores detailed metadata for images, audio, video, etc.
    """
    __tablename__ = "media_metadata"

    # Reference to chunk
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False, unique=True, index=True)

    # Modality information
    modality = Column(SQLEnum(ModalityType), nullable=False, index=True)

    # Media file information
    media_path = Column(Text, nullable=False)  # Path to media file
    media_url = Column(Text, nullable=True)    # Optional URL if from web
    media_format = Column(String(50), nullable=True)  # jpg, png, mp3, mp4, etc.
    file_size_bytes = Column(Integer, nullable=True)  # File size

    # Image-specific metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    image_resolution_dpi = Column(Integer, nullable=True)
    image_format = Column(String(20), nullable=True)  # JPEG, PNG, etc.

    # Audio-specific metadata
    audio_duration_seconds = Column(Float, nullable=True)
    audio_sample_rate = Column(Integer, nullable=True)
    audio_channels = Column(Integer, nullable=True)
    audio_bitrate = Column(Integer, nullable=True)

    # Video-specific metadata
    video_duration_seconds = Column(Float, nullable=True)
    video_width = Column(Integer, nullable=True)
    video_height = Column(Integer, nullable=True)
    video_fps = Column(Float, nullable=True)
    video_codec = Column(String(50), nullable=True)

    # Content understanding
    caption = Column(Text, nullable=True)  # Auto-generated caption
    ocr_text = Column(Text, nullable=True)  # OCR extracted text
    detected_objects = Column(JSON, nullable=True)  # List of detected objects
    scene_description = Column(Text, nullable=True)  # Scene/context description

    # Embeddings for multimodal search
    clip_embedding = Column(Vector(768), nullable=True)  # CLIP ViT-L-14 embeddings
    clip_model = Column(String(100), nullable=True)  # CLIP model used

    # Extraction metadata
    extraction_method = Column(String(100), nullable=True)  # How media was extracted
    source_page = Column(Integer, nullable=True)  # PDF page number
    source_timestamp = Column(Float, nullable=True)  # Video/audio timestamp
    position_metadata = Column(JSON, nullable=True)  # Position in source (x, y, bbox)

    # Quality and processing
    quality_score = Column(Float, nullable=True)  # Quality assessment score
    processing_metadata = Column(JSON, nullable=True)  # Processing parameters

    # Relationships
    chunk = relationship("Chunk", back_populates="media")

    # Database indexes
    __table_args__ = (
        Index('idx_media_chunk', 'chunk_id'),
        Index('idx_media_modality', 'modality'),
        Index('idx_media_format', 'media_format'),
        # HNSW index for CLIP embeddings
        Index('idx_media_clip_embedding', 'clip_embedding',
              postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64},
              postgresql_ops={'clip_embedding': 'vector_cosine_ops'}),
    )

    def __repr__(self):
        return f"<MediaMetadata(chunk_id={self.chunk_id}, modality={self.modality}, format={self.media_format})>"

    def get_metadata_dict(self) -> dict:
        """Get metadata as dictionary"""
        metadata = {
            "modality": self.modality.value if self.modality else None,
            "media_path": self.media_path,
            "media_format": self.media_format,
            "file_size_bytes": self.file_size_bytes,
        }

        # Add modality-specific metadata
        if self.modality == ModalityType.IMAGE:
            metadata.update({
                "width": self.image_width,
                "height": self.image_height,
                "resolution_dpi": self.image_resolution_dpi,
                "format": self.image_format,
            })
        elif self.modality == ModalityType.AUDIO:
            metadata.update({
                "duration_seconds": self.audio_duration_seconds,
                "sample_rate": self.audio_sample_rate,
                "channels": self.audio_channels,
                "bitrate": self.audio_bitrate,
            })
        elif self.modality == ModalityType.VIDEO:
            metadata.update({
                "duration_seconds": self.video_duration_seconds,
                "width": self.video_width,
                "height": self.video_height,
                "fps": self.video_fps,
                "codec": self.video_codec,
            })

        # Add content understanding
        if self.caption:
            metadata["caption"] = self.caption
        if self.ocr_text:
            metadata["ocr_text"] = self.ocr_text
        if self.detected_objects:
            metadata["detected_objects"] = self.detected_objects

        return metadata

    @property
    def has_clip_embedding(self) -> bool:
        """Check if media has CLIP embedding"""
        return self.clip_embedding is not None

    @property
    def is_image(self) -> bool:
        """Check if media is an image"""
        return self.modality in [ModalityType.IMAGE, ModalityType.CHART, ModalityType.DIAGRAM]

    @property
    def is_audio(self) -> bool:
        """Check if media is audio"""
        return self.modality == ModalityType.AUDIO

    @property
    def is_video(self) -> bool:
        """Check if media is video"""
        return self.modality == ModalityType.VIDEO

    def get_display_info(self) -> dict:
        """Get information for UI display"""
        info = {
            "modality": self.modality.value if self.modality else None,
            "format": self.media_format,
            "caption": self.caption or "No caption",
        }

        # Add dimension info
        if self.is_image and self.image_width and self.image_height:
            info["dimensions"] = f"{self.image_width}x{self.image_height}"
        elif self.is_video and self.video_width and self.video_height:
            info["dimensions"] = f"{self.video_width}x{self.video_height}"

        # Add duration for audio/video
        if self.audio_duration_seconds:
            info["duration"] = f"{self.audio_duration_seconds:.1f}s"
        elif self.video_duration_seconds:
            info["duration"] = f"{self.video_duration_seconds:.1f}s"

        return info


class TranscriptSegment(BaseModel):
    """
    Transcript segments for audio/video content
    Stores time-aligned text segments from speech recognition
    """
    __tablename__ = "transcript_segments"

    # Reference to media
    media_id = Column(Integer, ForeignKey("media_metadata.id"), nullable=False, index=True)

    # Segment information
    segment_order = Column(Integer, nullable=False)  # Order within transcript
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)    # End time in seconds

    # Content
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # Transcription confidence (0-1)

    # Speaker identification (optional)
    speaker_id = Column(String(100), nullable=True)
    speaker_label = Column(String(255), nullable=True)

    # Language detection
    language = Column(String(10), nullable=True)  # ISO 639-1 code (en, es, etc.)

    # Metadata
    segment_metadata = Column(JSON, nullable=True)

    # Relationships
    media = relationship("MediaMetadata", backref="transcript_segments")

    # Database indexes
    __table_args__ = (
        Index('idx_transcript_media', 'media_id'),
        Index('idx_transcript_order', 'media_id', 'segment_order'),
        Index('idx_transcript_time', 'media_id', 'start_time'),
        Index('idx_transcript_speaker', 'speaker_id'),
    )

    def __repr__(self):
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<TranscriptSegment(media_id={self.media_id}, time={self.start_time:.1f}-{self.end_time:.1f}, text='{text_preview}')>"

    @property
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end_time - self.start_time

    def get_timestamp_label(self) -> str:
        """Get formatted timestamp label"""
        def format_time(seconds: float) -> str:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"

        return f"[{format_time(self.start_time)} - {format_time(self.end_time)}]"
