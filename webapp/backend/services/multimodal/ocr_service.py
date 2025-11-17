"""
OCR Service - Extract text from images and scanned documents
Uses Tesseract OCR and EasyOCR for multi-language support
"""

import logging
from typing import List, Optional, Dict, Union
from pathlib import Path
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

# Check for Tesseract OCR
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available. Install with: pip install pytesseract pillow")

# Check for EasyOCR (better for multilingual)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.info("EasyOCR not available. Install with: pip install easyocr")


@dataclass
class OCRResult:
    """OCR extraction result"""
    text: str
    confidence: float
    language: str
    bounding_boxes: List[Dict] = None  # List of {text, bbox, confidence}
    method: str = "unknown"  # tesseract, easyocr


class OCRService:
    """
    OCR Service for text extraction from images

    Features:
    - Tesseract OCR (fast, accurate for English)
    - EasyOCR (better for multilingual)
    - Automatic language detection
    - Confidence scoring
    - Bounding box extraction
    """

    def __init__(
        self,
        use_easyocr: bool = False,
        languages: List[str] = None,
        tesseract_config: str = "--oem 3 --psm 6"
    ):
        """
        Initialize OCR service

        Args:
            use_easyocr: Use EasyOCR instead of Tesseract
            languages: List of language codes (e.g., ['en', 'es', 'zh'])
            tesseract_config: Tesseract configuration string
        """
        self.use_easyocr = use_easyocr and EASYOCR_AVAILABLE
        self.languages = languages or ['en']
        self.tesseract_config = tesseract_config
        self.easyocr_reader = None

        if self.use_easyocr:
            if not EASYOCR_AVAILABLE:
                logger.warning("EasyOCR not available, falling back to Tesseract")
                self.use_easyocr = False
            else:
                logger.info(f"Using EasyOCR with languages: {self.languages}")
        else:
            if not TESSERACT_AVAILABLE:
                raise RuntimeError(
                    "Neither Tesseract nor EasyOCR available. "
                    "Install: pip install pytesseract easyocr pillow"
                )
            logger.info(f"Using Tesseract OCR")

    def load_easyocr_model(self):
        """Lazy load EasyOCR model"""
        if self.use_easyocr and self.easyocr_reader is None:
            try:
                logger.info(f"Loading EasyOCR model for languages: {self.languages}")
                self.easyocr_reader = easyocr.Reader(
                    self.languages,
                    gpu=True,  # Use GPU if available
                    verbose=False
                )
                logger.info("✅ EasyOCR model loaded")
            except Exception as e:
                logger.error(f"Failed to load EasyOCR: {e}")
                self.use_easyocr = False

    def extract_text(
        self,
        image_path: Union[str, Path],
        language: Optional[str] = None
    ) -> Optional[OCRResult]:
        """
        Extract text from image using OCR

        Args:
            image_path: Path to image file
            language: Language code (overrides default)

        Returns:
            OCRResult with extracted text and metadata
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Image not found: {image_path}")
                return None

            # Load image
            image = Image.open(image_path)

            # Use EasyOCR or Tesseract
            if self.use_easyocr:
                return self._extract_with_easyocr(image, language)
            else:
                return self._extract_with_tesseract(image, language)

        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return None

    def _extract_with_tesseract(
        self,
        image: Image.Image,
        language: Optional[str] = None
    ) -> OCRResult:
        """Extract text using Tesseract OCR"""
        try:
            lang = language or self.languages[0]

            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=self.tesseract_config
            )

            # Get confidence data
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )

            # Calculate average confidence
            confidences = [
                conf for conf in data['conf']
                if conf != -1  # Filter invalid values
            ]
            avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0

            # Extract bounding boxes
            bounding_boxes = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:  # Filter low confidence
                    bounding_boxes.append({
                        'text': data['text'][i],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        },
                        'confidence': data['conf'][i] / 100.0
                    })

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                language=lang,
                bounding_boxes=bounding_boxes,
                method="tesseract"
            )

        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return OCRResult(text="", confidence=0.0, language=language or 'en', method="tesseract")

    def _extract_with_easyocr(
        self,
        image: Image.Image,
        language: Optional[str] = None
    ) -> OCRResult:
        """Extract text using EasyOCR"""
        try:
            # Load model if needed
            if self.easyocr_reader is None:
                self.load_easyocr_model()

            # Convert PIL Image to numpy array
            image_np = np.array(image)

            # Extract text
            results = self.easyocr_reader.readtext(image_np)

            # Parse results
            texts = []
            confidences = []
            bounding_boxes = []

            for bbox, text, confidence in results:
                texts.append(text)
                confidences.append(confidence)

                # Convert bbox format
                bounding_boxes.append({
                    'text': text,
                    'bbox': {
                        'points': bbox  # List of 4 corner points
                    },
                    'confidence': confidence
                })

            # Combine text
            full_text = " ".join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0

            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                language=language or self.languages[0],
                bounding_boxes=bounding_boxes,
                method="easyocr"
            )

        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return OCRResult(text="", confidence=0.0, language=language or 'en', method="easyocr")

    def detect_text_regions(
        self,
        image_path: Union[str, Path]
    ) -> List[Dict]:
        """
        Detect text regions without full OCR

        Args:
            image_path: Path to image file

        Returns:
            List of bounding boxes with text regions
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                return []

            image = Image.open(image_path)

            if self.use_easyocr:
                if self.easyocr_reader is None:
                    self.load_easyocr_model()

                image_np = np.array(image)
                results = self.easyocr_reader.readtext(image_np)

                return [
                    {
                        'bbox': bbox,
                        'text': text,
                        'confidence': conf
                    }
                    for bbox, text, conf in results
                ]
            else:
                # Use Tesseract for region detection
                data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT
                )

                regions = []
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    if int(data['conf'][i]) > 30:  # Confidence threshold
                        regions.append({
                            'bbox': {
                                'x': data['left'][i],
                                'y': data['top'][i],
                                'width': data['width'][i],
                                'height': data['height'][i]
                            },
                            'text': data['text'][i],
                            'confidence': data['conf'][i] / 100.0
                        })

                return regions

        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return []

    def is_scanned_pdf_page(
        self,
        image_path: Union[str, Path],
        min_text_length: int = 50
    ) -> bool:
        """
        Detect if an image/PDF page is scanned (needs OCR)

        Args:
            image_path: Path to image
            min_text_length: Minimum text length to consider as "text-based"

        Returns:
            True if page appears to be scanned (has text via OCR but not native text)
        """
        try:
            result = self.extract_text(image_path)
            if result and len(result.text.strip()) >= min_text_length:
                return True
            return False

        except Exception as e:
            logger.error(f"Error checking if scanned: {e}")
            return False

    def batch_extract_text(
        self,
        image_paths: List[Union[str, Path]],
        language: Optional[str] = None
    ) -> List[Optional[OCRResult]]:
        """
        Extract text from multiple images

        Args:
            image_paths: List of image paths
            language: Language code

        Returns:
            List of OCRResult objects
        """
        results = []
        for i, img_path in enumerate(image_paths):
            logger.info(f"Processing {i+1}/{len(image_paths)}: {img_path}")
            result = self.extract_text(img_path, language)
            results.append(result)

        return results


# Singleton instance
_ocr_service_instance = None


def get_ocr_service(use_easyocr: bool = False) -> OCRService:
    """Get singleton OCR service instance"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService(use_easyocr=use_easyocr)
    return _ocr_service_instance


# Example usage
if __name__ == "__main__":
    # Test OCR service
    ocr = OCRService(use_easyocr=False)

    # Test with sample image
    test_image = "test_document.jpg"
    if Path(test_image).exists():
        result = ocr.extract_text(test_image)
        if result:
            print(f"\n📄 Extracted Text:")
            print(result.text)
            print(f"\n📊 Confidence: {result.confidence:.2%}")
            print(f"🌐 Language: {result.language}")
            print(f"🔧 Method: {result.method}")
            print(f"📦 Bounding boxes: {len(result.bounding_boxes)}")
    else:
        print(f"Test image not found: {test_image}")
