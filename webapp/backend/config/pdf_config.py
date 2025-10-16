"""
PDF Processing Configuration

This module contains configuration settings for PDF processing,
including chunking parameters, table detection, and performance tuning.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PDFProcessorConfig:
    """Configuration for PDF processing"""

    # Chunking settings
    chunk_size: int = 1000
    """Maximum words per semantic chunk (default: 1000)"""

    overlap: int = 200
    """Word overlap between adjacent chunks for context preservation (default: 200)"""

    min_chunk_words: int = 50
    """Minimum words required for a chunk to be created (default: 50)"""

    # Table detection settings
    table_detection_threshold: float = 0.7
    """Threshold for detecting table structures (0.0-1.0, default: 0.7)"""

    enable_table_extraction: bool = True
    """Enable pdfplumber-based table extraction (default: True)"""

    # Image extraction settings
    enable_image_extraction: bool = True
    """Enable image extraction from PDFs (default: True)"""

    image_resolution: int = 150
    """DPI resolution for extracted images (default: 150)"""

    # File validation
    max_file_size_mb: int = 50
    """Maximum PDF file size in MB before warning (default: 50)"""

    # Performance settings
    async_processing: bool = True
    """Use async processing for large operations (default: True)"""

    @classmethod
    def from_dict(cls, config_dict: dict) -> "PDFProcessorConfig":
        """Create config from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})


# Pre-configured profiles for different use cases
PROFILES = {
    "default": PDFProcessorConfig(),

    "fast": PDFProcessorConfig(
        chunk_size=500,
        overlap=50,
        enable_image_extraction=False,
        enable_table_extraction=False,
    ),

    "balanced": PDFProcessorConfig(
        chunk_size=1000,
        overlap=200,
        enable_image_extraction=True,
        enable_table_extraction=True,
    ),

    "quality": PDFProcessorConfig(
        chunk_size=1500,
        overlap=300,
        enable_image_extraction=True,
        enable_table_extraction=True,
        image_resolution=300,
        table_detection_threshold=0.6,
    ),

    "large_files": PDFProcessorConfig(
        chunk_size=2000,
        overlap=400,
        enable_image_extraction=False,
        enable_table_extraction=True,
        max_file_size_mb=200,
    ),
}


def get_config(profile: str = "default") -> PDFProcessorConfig:
    """
    Get PDF processor configuration by profile name

    Args:
        profile: Configuration profile name ("default", "fast", "balanced", "quality", "large_files")

    Returns:
        PDFProcessorConfig instance

    Raises:
        ValueError: If profile name is not recognized
    """
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Available profiles: {list(PROFILES.keys())}")
    return PROFILES[profile]
