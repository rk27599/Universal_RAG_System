"""
PDF Processing Service - Text & Image Extraction
Handles PDF document processing with text extraction, image extraction,
code block detection, and structure preservation
"""

import logging
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

# PDF processing libraries
try:
    import PyPDF2
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("Warning: PyPDF2 not available. PDF processing will be limited.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. Advanced PDF features will be limited.")

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("Warning: Pillow not available. Image extraction will be disabled.")

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF documents with text and image extraction"""

    def __init__(self):
        self.image_storage_base = Path("data/uploads/images")
        self.image_storage_base.mkdir(parents=True, exist_ok=True)

    async def process_pdf(self, pdf_path: Path, document_id: int) -> Optional[Dict]:
        """
        Main entry point for PDF processing (async, non-blocking)

        Args:
            pdf_path: Path to PDF file (can be string or Path object)
            document_id: Database ID for organizing extracted images

        Returns:
            Structured document content compatible with chunking system
        """
        try:
            # Ensure pdf_path is a Path object
            if isinstance(pdf_path, str):
                pdf_path = Path(pdf_path)

            if not PYPDF2_AVAILABLE:
                logger.error("PyPDF2 is not available - cannot process PDF")
                return None

            logger.info(f"Starting async PDF processing: {pdf_path}")

            # Extract metadata (run in thread to avoid blocking)
            metadata = await asyncio.to_thread(self.extract_metadata, pdf_path)
            logger.info(f"PDF metadata: {metadata.get('total_pages', 0)} pages, title: {metadata.get('title', 'Unknown')}")

            # Extract text per page (run in thread to avoid blocking)
            pages_data = await asyncio.to_thread(self.extract_text_per_page, pdf_path)
            logger.info(f"Extracted text from {len(pages_data)} pages")

            # Extract images if Pillow is available (async with actual file saving)
            images_data = []
            if PILLOW_AVAILABLE and PDFPLUMBER_AVAILABLE:
                images_data = await self.extract_images_per_page(pdf_path, document_id)
                logger.info(f"Extracted {len(images_data)} images")

            # Detect table of contents structure
            toc_structure = self.detect_table_of_contents(pages_data[:5])  # Check first 5 pages
            has_toc = toc_structure is not None
            logger.info(f"Table of contents detected: {has_toc}")

            # Build sections (one per page or logical section)
            sections = []
            total_words = 0

            for page_data in pages_data:
                page_num = page_data['page_number']
                text_content = page_data['text']

                if not text_content or len(text_content.strip()) < 20:
                    continue

                # Detect code blocks in text
                has_code = self.detect_code_blocks(text_content)

                # Find images for this page
                page_images = [img for img in images_data if img['page_number'] == page_num]

                word_count = len(text_content.split())
                total_words += word_count

                # Determine section title
                section_title = self._extract_section_title(text_content, page_num, metadata.get('title', ''))

                sections.append({
                    'title': section_title,
                    'level': 1,
                    'content_text': text_content,
                    'word_count': word_count,
                    'metadata': {
                        'page_number': page_num,
                        'has_code': has_code,
                        'has_table': False,  # Can be enhanced with table detection
                        'images': page_images
                    }
                })

            logger.info(f"Created {len(sections)} sections from {len(pages_data)} pages")

            # Return structured format compatible with existing chunking
            return {
                'page_title': metadata.get('title', pdf_path.stem),
                'url': f"file://{pdf_path}",
                'domain': 'local_pdf',
                'total_sections': len(sections),
                'sections': sections,
                'images': images_data,
                'metadata': {
                    'source_type': 'pdf',
                    'total_pages': metadata.get('total_pages', len(pages_data)),
                    'author': metadata.get('author'),
                    'creation_date': metadata.get('creation_date'),
                    'has_toc': has_toc,
                    'total_word_count': total_words,
                    'image_count': len(images_data)
                }
            }

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}", exc_info=True)
            return None

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """
        Extract PDF metadata (author, title, creation date, page count, etc.)

        Args:
            pdf_path: Path to PDF file (can be string or Path object)

        Returns:
            Dictionary with PDF metadata
        """
        # Ensure pdf_path is a Path object
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        metadata = {
            'total_pages': 0,
            'title': None,
            'author': None,
            'creation_date': None,
            'subject': None
        }

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                metadata['total_pages'] = len(pdf_reader.pages)

                # Extract document info
                if pdf_reader.metadata:
                    metadata['title'] = pdf_reader.metadata.get('/Title', pdf_path.stem)
                    metadata['author'] = pdf_reader.metadata.get('/Author')
                    metadata['subject'] = pdf_reader.metadata.get('/Subject')

                    # Handle creation date
                    creation_date = pdf_reader.metadata.get('/CreationDate')
                    if creation_date:
                        metadata['creation_date'] = str(creation_date)

        except Exception as e:
            logger.warning(f"Error extracting PDF metadata: {e}")

        return metadata

    def extract_text_per_page(self, pdf_path: Path) -> List[Dict]:
        """
        Extract text from each page with PyPDF2

        Args:
            pdf_path: Path to PDF file (can be string or Path object)

        Returns:
            List of dictionaries with page number and text content
        """
        # Ensure pdf_path is a Path object
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        pages_data = []

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    try:
                        text = page.extract_text()

                        # Clean extracted text
                        text = self._clean_pdf_text(text)

                        pages_data.append({
                            'page_number': page_num,
                            'text': text
                        })
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num}: {e}")
                        pages_data.append({
                            'page_number': page_num,
                            'text': ''
                        })

        except Exception as e:
            logger.error(f"Error reading PDF file: {e}")

        return pages_data

    async def extract_images_per_page(self, pdf_path: Path, document_id: int) -> List[Dict]:
        """
        Extract and save embedded images using pdfplumber and Pillow (async, non-blocking)

        Args:
            pdf_path: Path to PDF file (can be string or Path object)
            document_id: Database document ID for organizing images

        Returns:
            List of dictionaries with image metadata (only for successfully saved images)
        """
        if not PDFPLUMBER_AVAILABLE or not PILLOW_AVAILABLE:
            return []

        # Ensure pdf_path is a Path object
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        images_data = []
        doc_image_dir = self.image_storage_base / str(document_id)
        doc_image_dir.mkdir(parents=True, exist_ok=True)

        def extract_and_save_images():
            """Blocking image extraction - will be run in thread"""
            saved_images = []

            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, start=1):
                        try:
                            # Convert page to image for extraction
                            page_img = page.to_image(resolution=150)

                            # Extract images from page
                            if hasattr(page, 'images') and page.images:
                                for img_idx, img_info in enumerate(page.images):
                                    try:
                                        # Generate unique image ID
                                        image_id = f"page_{page_num}_img_{img_idx}"
                                        image_filename = f"{image_id}.png"
                                        image_path = doc_image_dir / image_filename

                                        # Get bounding box coordinates
                                        x0 = img_info.get('x0', 0)
                                        y0 = img_info.get('top', 0)
                                        x1 = img_info.get('x1', x0 + img_info.get('width', 100))
                                        y1 = img_info.get('bottom', y0 + img_info.get('height', 100))
                                        bbox = (x0, y0, x1, y1)

                                        # Crop image from page
                                        cropped_img = page_img.original.crop(bbox)

                                        # Save the image
                                        cropped_img.save(image_path, 'PNG')

                                        logger.info(f"✅ Saved image: {image_path}")

                                        saved_images.append({
                                            'image_id': image_id,
                                            'page_number': page_num,
                                            'path': str(image_path),
                                            'format': 'PNG',
                                            'width': img_info.get('width'),
                                            'height': img_info.get('height'),
                                            'x0': x0,
                                            'y0': y0
                                        })

                                    except Exception as img_error:
                                        logger.warning(f"Error extracting/saving image {img_idx} from page {page_num}: {img_error}")

                        except Exception as page_error:
                            logger.warning(f"Error processing images on page {page_num}: {page_error}")

            except Exception as e:
                logger.error(f"Error extracting images from PDF: {e}")

            return saved_images

        # Run image extraction in thread pool to avoid blocking
        images_data = await asyncio.to_thread(extract_and_save_images)

        return images_data

    def detect_code_blocks(self, text: str) -> bool:
        """
        Detect if text contains code blocks

        Args:
            text: Text content to analyze

        Returns:
            True if code blocks are detected
        """
        # Pattern 1: Heavy indentation (code-like)
        lines = text.split('\n')
        indented_lines = [line for line in lines if len(line) > 0 and line.startswith('    ')]
        if len(indented_lines) > len(lines) * 0.3:  # 30% or more indented
            return True

        # Pattern 2: Programming keywords
        code_keywords = [
            'function', 'class', 'def', 'import', 'return', 'if', 'else', 'for', 'while',
            'public', 'private', 'protected', 'static', 'void', 'int', 'string', 'const',
            'var', 'let', '#include', 'namespace', 'struct', 'enum'
        ]
        keyword_count = sum(1 for keyword in code_keywords if re.search(rf'\b{keyword}\b', text, re.IGNORECASE))
        if keyword_count >= 3:
            return True

        # Pattern 3: Code syntax patterns
        code_patterns = [
            r'\{.*\}',  # Curly braces
            r'\(.*\)',  # Function calls
            r'^\s*//.*$',  # Single-line comments
            r'^\s*/\*.*\*/$',  # Multi-line comments
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(',  # Function definitions
            r'=\s*[^=]',  # Assignment operators
            r'->'  # Arrow operators
        ]

        pattern_matches = sum(1 for pattern in code_patterns if re.search(pattern, text, re.MULTILINE))
        if pattern_matches >= 4:
            return True

        return False

    def detect_table_of_contents(self, first_pages: List[Dict]) -> Optional[List[Dict]]:
        """
        Detect table of contents structure from first few pages

        Args:
            first_pages: List of page data dictionaries

        Returns:
            List of ToC entries or None if no ToC detected
        """
        toc_entries = []

        for page_data in first_pages:
            text = page_data.get('text', '')

            # Look for ToC indicators
            if re.search(r'\bcontents?\b', text, re.IGNORECASE):
                # Pattern for ToC entries: "Chapter 1: Title ........ 15"
                toc_pattern = r'(Chapter|Section|\d+\.?\d*)\s+(.+?)\s+\.{2,}\s*(\d+)'
                matches = re.findall(toc_pattern, text, re.IGNORECASE)

                for match in matches:
                    toc_entries.append({
                        'type': match[0],
                        'title': match[1].strip(),
                        'page': match[2]
                    })

        return toc_entries if toc_entries else None

    def _clean_pdf_text(self, text: str) -> str:
        """Clean extracted PDF text by removing artifacts and normalizing whitespace"""
        if not text:
            return ''

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers at end of lines
        text = re.sub(r'\s+\d+\s*$', '', text, flags=re.MULTILINE)

        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove control characters
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

        return text.strip()

    def _extract_section_title(self, text: str, page_num: int, doc_title: str) -> str:
        """
        Extract section title from text content

        Args:
            text: Text content
            page_num: Page number
            doc_title: Document title

        Returns:
            Section title string
        """
        # Try to find heading patterns
        lines = text.split('\n')[:5]  # Check first 5 lines

        for line in lines:
            line = line.strip()

            # Pattern 1: "Chapter X: Title"
            chapter_match = re.match(r'(Chapter|Section)\s+\d+\s*[:\-]\s*(.+)', line, re.IGNORECASE)
            if chapter_match:
                return line

            # Pattern 2: Short capitalized line (likely a heading)
            if len(line) > 5 and len(line) < 100 and line[0].isupper():
                # Check if mostly capital letters or title case
                if sum(1 for c in line if c.isupper()) > len(line) * 0.5:
                    return line

        # Fallback: Use document title + page number
        return f"{doc_title} - Page {page_num}"
