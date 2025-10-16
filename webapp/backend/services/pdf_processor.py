"""
PDF Processing Service - Hybrid Approach with PyMuPDF + pdfplumber
Uses PyMuPDF for text (better spacing) and pdfplumber for tables
"""

import logging
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass

# Initialize logger first
logger = logging.getLogger(__name__)

# Check for PyMuPDF (required)
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.error("PyMuPDF (fitz) not available. Install with: pip install PyMuPDF")

# Check for pdfplumber (optional but recommended for tables)
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. Table extraction will be limited.")

# Check for Pillow (optional, for image extraction)
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow not available. Image extraction will be disabled.")

# Check for NLTK (optional, for better sentence tokenization)
try:
    from nltk.tokenize import sent_tokenize
    import nltk
    NLTK_AVAILABLE = True
    # Try to find punkt_tab (NLTK 3.8.2+)
    try:
        nltk.data.find('tokenizers/punkt_tab/english/')
    except LookupError:
        try:
            nltk.download('punkt_tab', quiet=True)
        except Exception as e:
            # If download fails, disable NLTK and use regex fallback
            NLTK_AVAILABLE = False
            logger.warning(f"NLTK punkt_tab download failed: {e}. Using regex fallback for sentence splitting.")
except ImportError:
    NLTK_AVAILABLE = False
    logger.info("NLTK not available. Using regex sentence splitting.")


@dataclass
class PDFProcessorConfig:
    """Configuration for PDF processing"""
    chunk_size: int = 1000
    overlap: int = 200
    min_chunk_words: int = 50
    table_detection_threshold: float = 0.7
    enable_image_extraction: bool = True
    enable_table_extraction: bool = True
    image_resolution: int = 150
    max_file_size_mb: int = 50


class SemanticChunk:
    """Represents a semantically meaningful chunk of text"""
    def __init__(self, text: str, heading: str = None, level: int = 0, 
                 page_numbers: List[int] = None, metadata: Dict = None):
        self.text = text
        self.heading = heading or "Content"
        self.level = level
        self.page_numbers = page_numbers or []
        self.metadata = metadata or {}
        
    def to_dict(self):
        return {
            'title': self.heading,
            'level': self.level,
            'content_text': self.text,
            'word_count': len(self.text.split()),
            'metadata': {
                **self.metadata,
                'page_numbers': self.page_numbers,
                'has_code': self._detect_code(),
            }
        }
    
    def _detect_code(self):
        code_patterns = [r'\{.*\}', r'function\s*\(', r'class\s+\w+', r'def\s+\w+']
        return any(re.search(pattern, self.text) for pattern in code_patterns)


class PDFProcessor:
    """
    Service for processing PDF documents using PyMuPDF for better text extraction

    Features:
    - Hybrid approach: PyMuPDF for text + pdfplumber for tables
    - Semantic chunking with configurable size
    - Image extraction with per-page storage
    - Intelligent table detection and markdown formatting
    - Font-based heading detection
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200, config: Optional[PDFProcessorConfig] = None):
        """
        Initialize PDF processor

        Args:
            chunk_size: Maximum words per chunk (default: 1000)
            overlap: Word overlap between chunks (default: 200)
            config: Optional PDFProcessorConfig for advanced settings
        """
        self.config = config or PDFProcessorConfig(chunk_size=chunk_size, overlap=overlap)
        self.chunk_size = self.config.chunk_size
        self.overlap = self.config.overlap
        self.image_storage_base = Path("data/uploads/images")
        self.image_storage_base.mkdir(parents=True, exist_ok=True)

    async def process_pdf(self, pdf_path: Path, document_id: int) -> Optional[Dict]:
        """
        Main entry point using PyMuPDF for text extraction

        Args:
            pdf_path: Path to PDF file
            document_id: Document ID for image storage

        Returns:
            Structured document data with sections, tables, images, and metadata
        """
        try:
            if isinstance(pdf_path, str):
                pdf_path = Path(pdf_path)

            if not PYMUPDF_AVAILABLE:
                logger.error("PyMuPDF is required. Install with: pip install PyMuPDF")
                return None

            # Validate file exists
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return None

            # Check file size
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                logger.warning(f"Large PDF file ({file_size_mb:.1f}MB) - processing may take time. Consider splitting the file.")

            logger.info(f"Processing PDF with PyMuPDF: {pdf_path} ({file_size_mb:.1f}MB)")

            # Extract metadata
            metadata = await asyncio.to_thread(self.extract_metadata, pdf_path)
            
            # Extract structured content using PyMuPDF (better spacing)
            structured_content = await asyncio.to_thread(
                self.extract_with_pymupdf, pdf_path
            )
            logger.info(f"Extracted content from {len(structured_content)} pages")

            # Extract tables using pdfplumber (if available)
            tables_data = []
            if PDFPLUMBER_AVAILABLE:
                tables_data = await asyncio.to_thread(
                    self.extract_tables_pdfplumber, pdf_path
                )

            # Extract images
            images_data = []
            if PDFPLUMBER_AVAILABLE and PILLOW_AVAILABLE:
                images_data = await self.extract_images_per_page(pdf_path, document_id)

            # Integrate tables into content
            structured_content = self._integrate_tables(structured_content, tables_data)

            # Create semantic chunks
            semantic_chunks = self.create_semantic_chunks(structured_content, images_data)
            logger.info(f"Created {len(semantic_chunks)} semantic chunks")

            sections = [chunk.to_dict() for chunk in semantic_chunks]
            total_words = sum(s['word_count'] for s in sections)

            return {
                'page_title': metadata.get('title', pdf_path.stem),
                'url': f"file://{pdf_path}",
                'domain': 'local_pdf',
                'total_sections': len(sections),
                'sections': sections,
                'images': images_data,
                'metadata': {
                    'source_type': 'pdf',
                    'total_pages': metadata.get('total_pages'),
                    'author': metadata.get('author'),
                    'creation_date': metadata.get('creation_date'),
                    'total_word_count': total_words,
                    'image_count': len(images_data),
                    'table_count': len(tables_data),
                    'chunking_method': 'pymupdf_semantic'
                }
            }

        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            return None

    def _post_process_blocks_for_tables(self, blocks: List[Dict]) -> List[Dict]:
        """
        Post-process blocks to detect and format implicit tables
        Specifically targets keyboard shortcut patterns
        """
        processed_blocks = []
        
        for block in blocks:
            if block['type'] == 'paragraph':
                text = block['text']
                
                # Check if this looks like a keyboard shortcut table
                if self._is_keyboard_shortcut_table(text):
                    # Format as markdown table
                    table_md = self._format_keyboard_shortcuts(text)
                    processed_blocks.append({
                        'text': table_md,
                        'type': 'table',
                        'font_size': block['font_size'],
                        'page_number': block['page_number']
                    })
                else:
                    processed_blocks.append(block)
            else:
                processed_blocks.append(block)
        
        return processed_blocks

    def _is_keyboard_shortcut_table(self, text: str) -> bool:
        """
        Detect if text represents a keyboard shortcut table
        Pattern: Multiple lines with action descriptions followed by key combinations
        """
        lines = text.split('\n')
        
        if len(lines) < 3:
            return False
        
        # Count lines that match shortcut pattern
        shortcut_pattern_count = 0
        for line in lines:
            # Look for patterns like "Pan view ALT + LEFT arrow"
            if re.search(r'(HOME|ALT|CTRL|LEFT|RIGHT|UP|DOWN|Middle|mouse|drag|\+|\-)', line, re.IGNORECASE):
                shortcut_pattern_count += 1
        
        # If >60% of lines look like shortcuts, treat as table
        return shortcut_pattern_count / len(lines) > 0.6

    def _format_keyboard_shortcuts(self, text: str) -> str:
        """
        Format keyboard shortcuts as a markdown table
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return text
        
        table_rows = []
        table_rows.append("| Action | Shortcut |")
        table_rows.append("| --- | --- |")
        
        for line in lines:
            # Try to split action from shortcut
            # Pattern 1: "Action KEY" or "Action KEY + KEY"
            match = re.search(r'^(.+?)\s+((?:HOME|ALT|CTRL|SHIFT|LEFT|RIGHT|UP|DOWN|Middle|Left|Right|mouse|drag|\+|\-|\w+\s+mouse\s+drag)+)$', line, re.IGNORECASE)
            
            if match:
                action = match.group(1).strip()
                shortcut = match.group(2).strip()
                table_rows.append(f"| {action} | {shortcut} |")
            else:
                # Can't parse - add as single column
                table_rows.append(f"| {line} | |")
        
        return '\n'.join(table_rows)

    def extract_with_pymupdf(self, pdf_path: Path) -> List[Dict]:
        """
        Extract content using PyMuPDF with proper spacing preservation
        
        PyMuPDF handles text spacing much better than pdfplumber for many PDFs
        """
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        structured_pages = []

        try:
            doc = fitz.open(str(pdf_path))
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text with layout preservation
                # Using "dict" mode gives us detailed structure with positioning
                text_dict = page.get_text("dict")
                
                # Extract blocks with proper spacing
                blocks = self._process_pymupdf_blocks(text_dict, page_num + 1)
                
                # Post-process for table detection
                blocks = self._post_process_blocks_for_tables(blocks)
                
                structured_pages.append({
                    'page_number': page_num + 1,
                    'blocks': blocks
                })
            
            doc.close()

        except Exception as e:
            logger.error(f"Error with PyMuPDF extraction: {e}")

        return structured_pages

    def _process_pymupdf_blocks(self, text_dict: Dict, page_num: int) -> List[Dict]:
        """
        Enhanced: Better table detection based on layout patterns
        """
        blocks = []
        
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            
            block_text_parts = []
            avg_font_size = 0
            font_sizes = []
            
            # Track line positions for table detection
            line_x_positions = []
            
            for line in block.get("lines", []):
                line_text_parts = []
                line_x0 = line.get("bbox", [0])[0]
                line_x_positions.append(line_x0)
                
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    font_size = span.get("size", 10)
                    font_sizes.append(font_size)
                    
                    if text.strip():
                        line_text_parts.append(text)
                
                if line_text_parts:
                    line_text = " ".join(line_text_parts)
                    block_text_parts.append(line_text)
            
            if not block_text_parts:
                continue
            
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 10.0
            
            # Join lines
            block_text = " ".join(block_text_parts)
            block_text = re.sub(r' +', ' ', block_text).strip()
            
            if len(block_text) < 10:
                continue
            
            # Enhanced table detection
            is_table = self._is_table_structure(block_text_parts, line_x_positions)
            
            if is_table:
                # Format as markdown table
                table_md = self._format_as_markdown_table(block_text_parts)
                blocks.append({
                    'text': table_md,
                    'type': 'table',
                    'font_size': avg_font_size,
                    'page_number': page_num
                })
            else:
                block_type = self._classify_block_pymupdf(block_text, avg_font_size, font_sizes)
                blocks.append({
                    'text': block_text,
                    'type': block_type,
                    'font_size': avg_font_size,
                    'page_number': page_num
                })
        
        return blocks

    def _is_table_structure(self, lines: List[str], x_positions: List[float]) -> bool:
        """
        Detect if lines form a table structure
        
        Tables have:
        - Multiple lines with similar patterns
        - Consistent left alignment or multiple alignment columns
        - Key-value or action-shortcut patterns
        """
        if len(lines) < 3:
            return False
        
        # Check for consistent patterns like "Action KEY" or "To Press"
        pattern_matches = 0
        for line in lines:
            # Two-column pattern: text followed by short code/key
            parts = line.split()
            if len(parts) >= 2:
                # Check if last part looks like a key/shortcut (uppercase, short)
                last_part = parts[-1]
                if (last_part.isupper() and len(last_part) <= 15) or \
                re.match(r'^(HOME|ALT|CTRL|LEFT|RIGHT|UP|DOWN|\+|\-|[A-Z]+)$', last_part):
                    pattern_matches += 1
        
        # If >70% of lines match table pattern, it's a table
        if pattern_matches / len(lines) > 0.7:
            return True
        
        # Check for alignment consistency (table columns)
        if len(set(x_positions)) <= 2:  # Max 2 different x-positions = columns
            # Check if content looks like table data
            has_short_entries = sum(1 for line in lines if len(line.split()) <= 5) > len(lines) * 0.5
            if has_short_entries:
                return True
        
        return False

    def _format_as_markdown_table(self, lines: List[str]) -> str:
        """
        Format lines as a markdown table
        
        Assumes 2-column format: Action | Shortcut
        """
        if not lines:
            return ""
        
        table_lines = []
        
        # Add header
        table_lines.append("| Action | Shortcut |")
        table_lines.append("| --- | --- |")
        
        # Process each line
        for line in lines:
            # Split line into parts
            parts = line.split()
            
            if len(parts) >= 2:
                # Find the split point (usually last 1-3 words are the shortcut)
                # Look for uppercase words, special keys, or operators
                split_idx = len(parts) - 1
                
                for i in range(len(parts) - 1, 0, -1):
                    part = parts[i]
                    # If this looks like part of shortcut, include it
                    if part.isupper() or part in ['+', '-', '|'] or \
                    re.match(r'^(ALT|CTRL|SHIFT|HOME|END|LEFT|RIGHT|UP|DOWN)$', part):
                        split_idx = i
                    else:
                        break
                
                action = " ".join(parts[:split_idx])
                shortcut = " ".join(parts[split_idx:])
                
                table_lines.append(f"| {action} | {shortcut} |")
            else:
                # Single column entry
                table_lines.append(f"| {line} | |")
        
        return "\n".join(table_lines)


    def _classify_block_pymupdf(self, text: str, avg_font_size: float, 
                                font_sizes: List[float]) -> str:
        """Classify block type based on text and font characteristics"""
        
        word_count = len(text.split())
        max_font_size = max(font_sizes) if font_sizes else avg_font_size
        
        # Check if font is larger than average (heading indicator)
        is_large_font = max_font_size > 12  # Typical body text is ~10-11pt
        is_short = word_count < 15
        
        # Heading patterns
        has_heading_pattern = bool(re.match(
            r'^(Chapter|Section|CHAPTER|SECTION|\d+\.|\d+\.\d+|Access methods|Default|Mouse|Keyboard)\s+',
            text
        ))
        
        # Check capitalization
        upper_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        is_mostly_upper = upper_ratio > 0.5
        
        # Heading detection
        if (is_large_font and is_short) or has_heading_pattern:
            return 'heading'
        if is_short and is_mostly_upper and word_count < 10:
            return 'heading'
        
        # List detection
        if re.match(r'^\s*[-•○●]\s+', text) or re.match(r'^\s*\d+\.\s+', text):
            return 'list_item'
        
        # Note detection
        if re.match(r'^(Note|NOTE|Tip|TIP|Warning|WARNING):', text):
            return 'note'
        
        # Table detection (will be replaced by pdfplumber tables if available)
        if '\t' in text or len(re.findall(r'\s{3,}', text)) >= 2:
            return 'table_row'
        
        return 'paragraph'

    def extract_tables_pdfplumber(self, pdf_path: Path) -> List[Dict]:
        """
        Extract tables using pdfplumber's table detection
        
        pdfplumber is excellent at detecting table structures
        """
        if not PDFPLUMBER_AVAILABLE:
            return []

        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        tables_data = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract tables from page
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if table:
                            # Convert table to markdown format
                            table_md = self._table_to_markdown(table)
                            
                            tables_data.append({
                                'page_number': page_num,
                                'table_index': table_idx,
                                'table_markdown': table_md,
                                'row_count': len(table),
                                'col_count': len(table[0]) if table else 0
                            })

        except Exception as e:
            logger.warning(f"Error extracting tables: {e}")

        return tables_data

    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """Convert table data to markdown format"""
        if not table:
            return ""

        # Clean table data
        cleaned_table = []
        for row in table:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            cleaned_table.append(cleaned_row)

        # Create markdown table
        md_lines = []
        
        # Header row
        if cleaned_table:
            header = cleaned_table[0]
            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
            
            # Data rows
            for row in cleaned_table[1:]:
                md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def _integrate_tables(self, structured_pages: List[Dict], 
                         tables_data: List[Dict]) -> List[Dict]:
        """
        Replace table_row blocks with properly formatted markdown tables
        """
        # Create table lookup by page
        tables_by_page = defaultdict(list)
        for table in tables_data:
            tables_by_page[table['page_number']].append(table)

        # Update pages with table data
        for page in structured_pages:
            page_num = page['page_number']
            if page_num in tables_by_page:
                blocks = page['blocks']
                
                # Find and replace table_row blocks
                new_blocks = []
                table_idx = 0
                skip_next_table_rows = 0
                
                for block in blocks:
                    if block['type'] == 'table_row' and skip_next_table_rows == 0:
                        # Replace with markdown table
                        if table_idx < len(tables_by_page[page_num]):
                            table = tables_by_page[page_num][table_idx]
                            new_blocks.append({
                                'text': table['table_markdown'],
                                'type': 'table',
                                'font_size': block['font_size'],
                                'page_number': page_num
                            })
                            table_idx += 1
                            # Skip next few table_row blocks (they're part of same table)
                            skip_next_table_rows = 3
                        else:
                            new_blocks.append(block)
                    elif block['type'] == 'table_row' and skip_next_table_rows > 0:
                        skip_next_table_rows -= 1
                        # Skip this block as it's part of the table we just added
                    else:
                        new_blocks.append(block)
                
                page['blocks'] = new_blocks

        return structured_pages

    def create_semantic_chunks(self, structured_pages: List[Dict], 
                              images_data: List[Dict]) -> List[SemanticChunk]:
        """Create semantic chunks from structured content"""
        chunks = []
        current_heading = None
        current_heading_level = 0
        current_blocks = []
        current_pages = []
        current_word_count = 0

        for page_data in structured_pages:
            page_num = page_data['page_number']
            blocks = page_data['blocks']

            for block in blocks:
                block_text = block['text'].strip()
                if not block_text or len(block_text) < 5:
                    continue

                block_type = block['type']
                word_count = len(block_text.split())

                if block_type == 'heading':
                    # Save current chunk
                    if current_blocks and current_word_count > 50:
                        chunk_text = self._format_chunk_text(current_blocks)
                        chunk_images = [img for img in images_data 
                                      if img['page_number'] in current_pages]
                        
                        chunk = SemanticChunk(
                            text=chunk_text,
                            heading=current_heading,
                            level=current_heading_level,
                            page_numbers=current_pages.copy(),
                            metadata={'images': chunk_images}
                        )
                        chunks.append(chunk)
                        current_blocks = []
                        current_pages = []
                        current_word_count = 0

                    # Start new section
                    current_heading = block_text
                    current_heading_level = self._determine_heading_level(block)
                    if page_num not in current_pages:
                        current_pages.append(page_num)

                else:
                    # Add to current chunk
                    current_blocks.append({'text': block_text, 'type': block_type})
                    current_word_count += word_count
                    if page_num not in current_pages:
                        current_pages.append(page_num)

                    # Check chunk size
                    if current_word_count >= self.chunk_size:
                        chunk_text = self._format_chunk_text(current_blocks)
                        split_point = self._find_sentence_boundary(chunk_text, self.chunk_size)
                        
                        if 0 < split_point < len(chunk_text):
                            first_part = chunk_text[:split_point].strip()
                            second_part = chunk_text[split_point:].strip()

                            chunk_images = [img for img in images_data 
                                          if img['page_number'] in current_pages]

                            chunk = SemanticChunk(
                                text=first_part,
                                heading=current_heading,
                                level=current_heading_level,
                                page_numbers=current_pages.copy(),
                                metadata={'images': chunk_images}
                            )
                            chunks.append(chunk)

                            overlap_text = self._get_overlap_text(first_part, self.overlap)
                            if second_part:
                                current_blocks = [{'text': overlap_text + ' ' + second_part, 'type': 'paragraph'}]
                                current_word_count = len(current_blocks[0]['text'].split())
                            else:
                                current_blocks = []
                                current_word_count = 0

        # Final chunk
        if current_blocks and current_word_count > 50:
            chunk_text = self._format_chunk_text(current_blocks)
            chunk_images = [img for img in images_data 
                          if img['page_number'] in current_pages]
            
            chunk = SemanticChunk(
                text=chunk_text,
                heading=current_heading or "Document Content",
                level=current_heading_level,
                page_numbers=current_pages,
                metadata={'images': chunk_images}
            )
            chunks.append(chunk)

        return chunks

    def _format_chunk_text(self, blocks: List[Dict]) -> str:
        """Format blocks into clean chunk text"""
        formatted_parts = []
        
        for block in blocks:
            text = block['text']
            block_type = block.get('type', 'paragraph')
            
            if block_type == 'heading':
                formatted_parts.append(f"\n\n{text}\n")
            elif block_type == 'table':
                formatted_parts.append(f"\n\n{text}\n\n")
            elif block_type == 'list_item':
                formatted_parts.append(f"\n{text}")
            elif block_type == 'note':
                formatted_parts.append(f"\n\n{text}\n")
            else:
                formatted_parts.append(f"\n\n{text}")
        
        full_text = ''.join(formatted_parts).strip()
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        
        return full_text

    def _determine_heading_level(self, block: Dict) -> int:
        font_size = block.get('font_size', 10)
        if font_size >= 18:
            return 1
        elif font_size >= 14:
            return 2
        elif font_size >= 12:
            return 3
        return 4

    def _find_sentence_boundary(self, text: str, target_words: int) -> int:
        """Find nearest sentence boundary to target word count"""
        
        if NLTK_AVAILABLE:
            try:
                sentences = sent_tokenize(text)
                current_pos = 0
                current_words = 0
                for sentence in sentences:
                    sentence_words = len(sentence.split())
                    if current_words + sentence_words >= target_words:
                        return current_pos + len(sentence)
                    current_pos += len(sentence)
                    current_words += sentence_words
            except Exception as e:
                logger.warning(f"NLTK tokenization failed: {e}, using fallback")
        
        # Regex fallback (always works)
        sentence_ends = [m.end() for m in re.finditer(r'[.!?](?:\s+|\n+|$)', text)]
        if sentence_ends:
            target_chars = target_words * 5
            closest = min(sentence_ends, key=lambda x: abs(x - target_chars))
            return closest
    
        return len(text)
        
    def _get_overlap_text(self, text: str, overlap_words: int) -> str:
        words = text.split()
        if len(words) <= overlap_words:
            return text
        return ' '.join(words[-overlap_words:])

    def extract_metadata(self, pdf_path: Path) -> Dict:
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        metadata = {'total_pages': 0, 'title': None, 'author': None, 'creation_date': None}

        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(str(pdf_path))
                metadata['total_pages'] = len(doc)
                pdf_metadata = doc.metadata
                metadata['title'] = pdf_metadata.get('title', pdf_path.stem)
                metadata['author'] = pdf_metadata.get('author')
                metadata['creation_date'] = pdf_metadata.get('creationDate')
                doc.close()
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    async def extract_images_per_page(self, pdf_path: Path, document_id: int) -> List[Dict]:
        if not PDFPLUMBER_AVAILABLE or not PILLOW_AVAILABLE:
            return []

        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        doc_image_dir = self.image_storage_base / str(document_id)
        doc_image_dir.mkdir(parents=True, exist_ok=True)

        def extract_images():
            saved_images = []
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, start=1):
                        try:
                            if hasattr(page, 'images') and page.images:
                                page_img = page.to_image(resolution=150)
                                for img_idx, img_info in enumerate(page.images):
                                    try:
                                        image_id = f"page_{page_num}_img_{img_idx}"
                                        image_path = doc_image_dir / f"{image_id}.png"

                                        x0 = img_info.get('x0', 0)
                                        y0 = img_info.get('top', 0)
                                        x1 = img_info.get('x1', x0 + img_info.get('width', 100))
                                        y1 = img_info.get('bottom', y0 + img_info.get('height', 100))

                                        cropped_img = page_img.original.crop((x0, y0, x1, y1))
                                        cropped_img.save(image_path, 'PNG')

                                        saved_images.append({
                                            'image_id': image_id,
                                            'page_number': page_num,
                                            'path': str(image_path),
                                            'format': 'PNG',
                                            'width': img_info.get('width'),
                                            'height': img_info.get('height')
                                        })
                                    except Exception as e:
                                        logger.warning(f"Image error: {e}")
                        except Exception as e:
                            logger.warning(f"Page {page_num} error: {e}")
            except Exception as e:
                logger.error(f"Image extraction error: {e}")
            return saved_images

        return await asyncio.to_thread(extract_images)


# Usage
async def main():
    processor = PDFProcessor(chunk_size=500, overlap=100)
    result = await processor.process_pdf("Materials_Studio.pdf", document_id=1)
    
    if result:
        print(f"Title: {result['page_title']}")
        print(f"Sections: {result['total_sections']}")
        for i, section in enumerate(result['sections'][:2]):
            print(f"\n{'='*70}")
            print(f"Section {i+1}: {section['title']}")
            print(f"{'='*70}")
            print(section['content_text'][:500])


if __name__ == "__main__":
    asyncio.run(main())
