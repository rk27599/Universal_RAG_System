"""
Image Processing Service - OCR and Vision Model Integration
Handles image upload, OCR text extraction, and multimodal LLM descriptions
"""

import logging
import asyncio
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from io import BytesIO

# Initialize logger first
logger = logging.getLogger(__name__)

# Check for PIL/Pillow (required for image handling)
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.error("Pillow not available. Install with: pip install Pillow")

# Check for EasyOCR (preferred OCR engine)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logger.info("EasyOCR available for text extraction")
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.info("EasyOCR not available. Install with: pip install easyocr")

# Check for pytesseract (fallback OCR)
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
    logger.info("Pytesseract available as OCR fallback")
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.info("Pytesseract not available. Install with: pip install pytesseract")


@dataclass
class ImageProcessorConfig:
    """Configuration for image processing"""
    chunk_size: int = 1000
    overlap: int = 200
    enable_ocr: bool = True
    enable_vision_model: bool = True
    ocr_languages: List[str] = None  # Default: ['en']
    max_image_size: Tuple[int, int] = (2048, 2048)  # Max width, height
    image_quality: int = 85  # JPEG quality for storage
    generate_thumbnail: bool = True
    thumbnail_size: Tuple[int, int] = (300, 300)

    def __post_init__(self):
        if self.ocr_languages is None:
            self.ocr_languages = ['en']


class ImageProcessor:
    """
    Process images with OCR and vision models for RAG integration

    Features:
    - Multiple OCR engines (EasyOCR preferred, Tesseract fallback)
    - Multimodal LLM integration (LLaVA via Ollama)
    - Image preprocessing and optimization
    - Semantic chunking of extracted text
    - Metadata extraction (dimensions, format, EXIF)
    """

    def __init__(self, config: Optional[ImageProcessorConfig] = None):
        self.config = config or ImageProcessorConfig()
        self._ocr_reader = None
        self._vision_model = None

        if not PILLOW_AVAILABLE:
            raise ImportError("Pillow is required for image processing. Install: pip install Pillow")

        # Check OCR availability
        if self.config.enable_ocr:
            if not EASYOCR_AVAILABLE and not PYTESSERACT_AVAILABLE:
                logger.warning("No OCR engine available. Text extraction will be disabled.")
                self.config.enable_ocr = False

    async def _init_ocr_reader(self):
        """Lazily initialize OCR reader"""
        if self._ocr_reader is not None:
            return

        if EASYOCR_AVAILABLE:
            logger.info("Initializing EasyOCR reader...")
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._ocr_reader = await loop.run_in_executor(
                None,
                lambda: easyocr.Reader(self.config.ocr_languages, gpu=True)
            )
            logger.info("EasyOCR reader initialized")
        elif PYTESSERACT_AVAILABLE:
            logger.info("Using Pytesseract for OCR")
            self._ocr_reader = "pytesseract"  # Marker for pytesseract
        else:
            logger.warning("No OCR engine available")

    async def _extract_text_with_ocr(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        if not self.config.enable_ocr:
            return ""

        await self._init_ocr_reader()

        try:
            if EASYOCR_AVAILABLE and self._ocr_reader and self._ocr_reader != "pytesseract":
                # EasyOCR
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: self._ocr_reader.readtext(
                        image,
                        detail=0,  # Return only text, not bounding boxes
                        paragraph=True
                    )
                )
                text = " ".join(results)
                logger.info(f"EasyOCR extracted {len(text)} characters")
                return text

            elif PYTESSERACT_AVAILABLE:
                # Pytesseract fallback
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    lambda: pytesseract.image_to_string(image, lang="+".join(self.config.ocr_languages))
                )
                logger.info(f"Pytesseract extracted {len(text)} characters")
                return text.strip()

            else:
                logger.warning("No OCR engine available")
                return ""

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    async def _generate_image_description(
        self,
        image_path: Path,
        llm_service=None
    ) -> str:
        """Generate image description using multimodal LLM (LLaVA)"""
        if not self.config.enable_vision_model or llm_service is None:
            return ""

        try:
            # Check if LLM service supports vision
            if not hasattr(llm_service, 'generate_with_image'):
                logger.warning("LLM service does not support vision models")
                return ""

            # Generate description using LLaVA
            description = await llm_service.generate_with_image(
                prompt="Describe this image in detail, focusing on key elements, text, diagrams, and any technical content.",
                image_path=str(image_path),
                model="llava"  # Default vision model
            )

            logger.info(f"Generated image description: {len(description)} characters")
            return description

        except Exception as e:
            logger.error(f"Image description generation failed: {e}")
            return ""

    def _extract_image_metadata(self, image: Image.Image, file_path: Path) -> Dict:
        """Extract image metadata (dimensions, format, EXIF)"""
        metadata = {
            'width': image.width,
            'height': image.height,
            'format': image.format or file_path.suffix[1:].upper(),
            'mode': image.mode,
            'file_size_kb': file_path.stat().st_size / 1024,
            'has_transparency': image.mode in ('RGBA', 'LA', 'P'),
        }

        # Extract EXIF data if available
        try:
            exif_data = image.getexif()
            if exif_data:
                metadata['exif'] = {
                    'DateTimeOriginal': exif_data.get(36867),  # Date taken
                    'Make': exif_data.get(271),  # Camera maker
                    'Model': exif_data.get(272),  # Camera model
                    'Software': exif_data.get(305),  # Software used
                }
        except Exception as e:
            logger.debug(f"Could not extract EXIF data: {e}")

        return metadata

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image: resize, convert mode if needed"""
        # Convert to RGB if needed (for OCR and vision models)
        if image.mode not in ('RGB', 'L'):
            logger.info(f"Converting image from {image.mode} to RGB")
            image = image.convert('RGB')

        # Resize if too large
        max_width, max_height = self.config.max_image_size
        if image.width > max_width or image.height > max_height:
            logger.info(f"Resizing image from {image.width}x{image.height}")
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized to {image.width}x{image.height}")

        return image

    def _generate_thumbnail(self, image: Image.Image, output_path: Path):
        """Generate thumbnail for preview"""
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(self.config.thumbnail_size, Image.Resampling.LANCZOS)
            thumbnail.save(output_path, 'JPEG', quality=self.config.image_quality)
            logger.info(f"Generated thumbnail: {output_path}")
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into semantic chunks"""
        if not text:
            return []

        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para.split())

            # If paragraph alone exceeds chunk size, split it
            if para_size > self.config.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph by sentences
                sentences = para.split('. ')
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue

                    sent_size = len(sent.split())
                    if current_size + sent_size > self.config.chunk_size and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = []
                        current_size = 0

                    current_chunk.append(sent)
                    current_size += sent_size

            # If adding paragraph exceeds chunk size, save current chunk
            elif current_size + para_size > self.config.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [para]
                current_size = para_size

            else:
                current_chunk.append(para)
                current_size += para_size

        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    async def process_image(
        self,
        image_path: Path,
        document_id: int,
        llm_service=None,
        progress_callback=None
    ) -> Optional[Dict]:
        """
        Process an image: OCR, vision model description, chunking

        Args:
            image_path: Path to image file
            document_id: Database document ID
            llm_service: Optional LLM service for image descriptions
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with processing results or None on error
        """
        try:
            if progress_callback:
                await progress_callback(document_id, "loading_image", 10)

            # Load image
            image = Image.open(image_path)
            logger.info(f"Loaded image: {image_path} ({image.width}x{image.height}, {image.format})")

            # Extract metadata
            metadata = self._extract_image_metadata(image, image_path)

            if progress_callback:
                await progress_callback(document_id, "preprocessing", 20)

            # Preprocess
            image = self._preprocess_image(image)

            # Generate thumbnail
            if self.config.generate_thumbnail:
                thumbnail_path = image_path.parent / f"{image_path.stem}_thumb.jpg"
                self._generate_thumbnail(image, thumbnail_path)
                metadata['thumbnail_path'] = str(thumbnail_path)

            if progress_callback:
                await progress_callback(document_id, "ocr_extraction", 40)

            # Extract text with OCR
            ocr_text = await self._extract_text_with_ocr(image)

            if progress_callback:
                await progress_callback(document_id, "vision_model", 60)

            # Generate description with vision model
            vision_description = await self._generate_image_description(image_path, llm_service)

            if progress_callback:
                await progress_callback(document_id, "chunking", 80)

            # Combine OCR text and vision description
            combined_text = f"{vision_description}\n\n{ocr_text}".strip()

            # Chunk the text
            chunks = self._chunk_text(combined_text)

            if progress_callback:
                await progress_callback(document_id, "completed", 100)

            result = {
                'page_title': image_path.stem,
                'content_text': combined_text,
                'ocr_text': ocr_text,
                'vision_description': vision_description,
                'chunks': chunks,
                'total_sections': len(chunks),
                'metadata': {
                    **metadata,
                    'ocr_char_count': len(ocr_text),
                    'vision_char_count': len(vision_description),
                    'total_char_count': len(combined_text),
                    'chunk_count': len(chunks),
                    'processing_method': 'ocr_vision' if vision_description else 'ocr_only',
                }
            }

            logger.info(f"Image processing complete: {len(chunks)} chunks, {len(combined_text)} characters")
            return result

        except Exception as e:
            logger.error(f"Image processing failed: {e}", exc_info=True)
            return None

    @staticmethod
    def is_supported_format(file_path: Path) -> bool:
        """Check if file format is supported for image processing"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        return file_path.suffix.lower() in supported_formats

    @staticmethod
    def get_image_info(file_path: Path) -> Dict:
        """Get basic image info without full processing"""
        try:
            image = Image.open(file_path)
            return {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_kb': file_path.stat().st_size / 1024,
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return {}
