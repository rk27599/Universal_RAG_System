"""
Document Processing Service - Core RAG Document Management
Handles document upload, chunking, embedding, and storage
"""

import logging
import hashlib
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import UploadFile
import aiofiles
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add project root to path to import from src
# From services/document_service.py:
# parent = services/, parent.parent = backend/, parent.parent.parent = webapp/, parent x4 = RAG/
project_root = str(Path(__file__).parent.parent.parent.parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
from models.document import Document, Chunk, DocumentProcessingLog

# Try to import embedding service, but make it optional
try:
    from services.embedding_service import get_embedding_service
    EMBEDDINGS_AVAILABLE = True
except Exception as e:
    EMBEDDINGS_AVAILABLE = False
    get_embedding_service = None
    print(f"Warning: Embedding service not available: {e}. Documents will be processed without embeddings.")

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing documents with chunking and embedding generation"""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.embedding_service = get_embedding_service() if EMBEDDINGS_AVAILABLE else None
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def process_uploaded_file(
        self,
        file: UploadFile,
        metadata: Optional[Dict] = None,
        chunk_size: int = 2000
    ) -> Tuple[Optional[Document], Optional[str]]:
        """
        Process an uploaded file: save, extract content, chunk, embed, and store

        Args:
            file: Uploaded file from FastAPI
            metadata: Optional metadata about the document
            chunk_size: Maximum characters per chunk (default: 2000, range: 500-10000)

        Returns:
            Tuple of (Document object, error message if any)
        """
        file_path = None

        try:
            # 1. Validate file
            if not file.filename:
                return None, "No filename provided"

            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.html', '.htm', '.txt', '.json', '.jsonl']:
                return None, f"Unsupported file type: {file_ext}. Only .html, .htm, .txt, .json, and .jsonl files are supported."

            # 2. Read file content
            content = await file.read()
            if not content:
                return None, "Empty file provided"

            content_hash = hashlib.sha256(content).hexdigest()

            # Check for duplicate
            existing_doc = self.db.query(Document).filter(
                Document.user_id == self.user_id,
                Document.content_hash == content_hash,
                Document.processing_status != "deleted"
            ).first()

            if existing_doc:
                return None, f"Document already exists: {existing_doc.title}"

            # 3. Save file temporarily
            safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            file_path = self.upload_dir / safe_filename

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            logger.info(f"Saved uploaded file to: {file_path}")

            # 4. Create document record
            document = Document(
                user_id=self.user_id,
                title=file.filename,
                original_filename=file.filename,
                source_type="file",
                source_path=str(file_path),
                content_type=file.content_type or "text/html",
                file_size=len(content),
                content_hash=content_hash,
                processing_status="pending",
                processing_config=metadata or {}
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(f"Created document record: {document.id}")

            # 5. Start processing asynchronously
            # Store the task to prevent garbage collection
            task = asyncio.create_task(self._process_document_async(document.id, file_path, chunk_size))
            # Keep a reference to prevent GC (store in a module-level set if needed in production)
            # For now, we'll add a done callback to handle completion
            task.add_done_callback(lambda t: logger.info(f"Document {document.id} processing task completed") if not t.exception() else logger.error(f"Document {document.id} processing task failed: {t.exception()}"))

            return document, None

        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            if file_path and file_path.exists():
                file_path.unlink()  # Clean up file on error
            return None, f"Error processing file: {str(e)}"

    async def _process_document_async(self, document_id: int, file_path: Path, chunk_size: int = 2000):
        """
        Background task to process document content asynchronously

        Args:
            document_id: Database ID of document to process
            file_path: Path to uploaded file
            chunk_size: Maximum characters per chunk (default: 2000)
        """
        start_time = datetime.utcnow()
        db = None

        try:
            logger.info(f"🚀 Background task started for document {document_id}")

            # Get document from database (new session for background task)
            from core.database import get_db
            db = next(get_db())

            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"❌ Document {document_id} not found in database")
                return

            # Mark as processing
            logger.info(f"📝 Marking document {document_id} as processing")
            document.start_processing()
            db.commit()

            logger.info(f"✅ Starting async processing for document {document_id}: {document.title}")

            # Create processing log
            log = DocumentProcessingLog(
                document_id=document_id,
                user_id=document.user_id,
                operation="process",
                status="started",
                started_at=start_time
            )
            db.add(log)
            db.commit()

            # 1. Extract content using AsyncWebScraper (0-20%)
            document.update_progress(5.0)
            db.commit()

            structured_content = await self._extract_content(file_path, document.content_type)

            if not structured_content:
                raise ValueError("Failed to extract content from file")

            document.update_progress(20.0)
            db.commit()

            # 2. Create semantic chunks (20-40%)
            document.update_progress(25.0)
            db.commit()

            chunks_data = self._create_chunks(structured_content, max_chunk_size=chunk_size)

            if not chunks_data:
                raise ValueError("Failed to create chunks from content")

            logger.info(f"Created {len(chunks_data)} chunks for document {document_id}")

            document.update_progress(40.0)
            db.commit()

            # 3. Generate embeddings for all chunks (40-95%)
            embeddings = []
            if self.embedding_service:
                chunk_texts = [chunk['text'] for chunk in chunks_data]
                # Use async version to prevent blocking the event loop
                logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
                embeddings = await self.embedding_service.generate_embeddings_batch_async(chunk_texts)
                logger.info(f"Embedding generation complete")
                document.update_progress(95.0)
                db.commit()
            else:
                logger.warning("Embedding service not available - storing chunks without embeddings")
                embeddings = [None] * len(chunks_data)
                document.update_progress(95.0)
                db.commit()

            # 4. Store chunks in database (95-100%)
            total_chars = 0
            total_tokens = 0

            for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
                if embedding is None and self.embedding_service:
                    logger.warning(f"Failed to generate embedding for chunk {i}")
                    # Continue anyway - store chunk without embedding

                chunk_content = chunk_data['text']
                chunk_hash = hashlib.sha256(chunk_content.encode()).hexdigest()

                chunk = Chunk(
                    document_id=document_id,
                    content=chunk_content,
                    content_hash=chunk_hash,
                    embedding=embedding,
                    embedding_model=self.embedding_service.model_name if self.embedding_service else None,
                    chunk_order=i,
                    content_type=chunk_data.get('content_type', 'text'),
                    section_hierarchy=chunk_data.get('section_hierarchy'),
                    character_count=len(chunk_content),
                    word_count=chunk_data.get('word_count', len(chunk_content.split())),
                    token_count=chunk_data.get('token_count', len(chunk_content) // 4),
                    extraction_metadata=chunk_data.get('metadata', {})
                )

                chunk.set_content_stats()
                total_chars += chunk.character_count
                total_tokens += chunk.token_count

                db.add(chunk)

                # Update progress only at 25%, 50%, 75% and end to reduce database writes
                progress_points = [len(chunks_data) // 4, len(chunks_data) // 2, 3 * len(chunks_data) // 4, len(chunks_data) - 1]
                if i in progress_points:
                    progress = 95.0 + (5.0 * (i + 1) / len(chunks_data))
                    document.update_progress(progress)
                    db.commit()

            # 5. Mark document as completed
            document.complete_processing(
                chunk_count=len(chunks_data),
                char_count=total_chars,
                token_count=total_tokens
            )

            # Update processing log
            log.status = "completed"
            completed_time = datetime.utcnow()
            log.completed_at = completed_time

            # Handle timezone-aware vs naive datetime comparison
            start_time = log.started_at
            if start_time.tzinfo is not None and completed_time.tzinfo is None:
                completed_time = completed_time.replace(tzinfo=timezone.utc)
            elif start_time.tzinfo is None and completed_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            log.duration_seconds = (completed_time - start_time).total_seconds()
            log.chunks_created = len(chunks_data)
            log.tokens_processed = total_tokens

            db.commit()

            logger.info(f"Successfully processed document {document_id}: {len(chunks_data)} chunks created")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ Error processing document {document_id}: {e}")
            logger.error(f"Traceback:\n{error_details}")

            # Mark document as failed
            if db and document:
                try:
                    document.fail_processing(str(e))

                    # Update processing log if it exists
                    if 'log' in locals():
                        log.status = "failed"
                        log.completed_at = datetime.utcnow()
                        log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
                        log.error_message = str(e)[:1000]  # Limit error message length

                    db.commit()
                    logger.info(f"✅ Marked document {document_id} as failed in database")
                except Exception as db_error:
                    logger.error(f"❌ Failed to mark document {document_id} as failed: {db_error}")

        finally:
            if db:
                db.close()
                logger.info(f"🔒 Database session closed for document {document_id}")

    def _update_embedding_progress(self, db, document, start_pct: float, end_pct: float, progress: float):
        """
        Update document progress during embedding generation

        Args:
            db: Database session
            document: Document instance
            start_pct: Starting percentage (e.g., 40.0)
            end_pct: Ending percentage (e.g., 95.0)
            progress: Current progress (0.0 to 1.0)
        """
        try:
            current_progress = start_pct + (end_pct - start_pct) * progress
            document.update_progress(current_progress)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to update embedding progress: {e}")

    def _clean_text_content(self, text: str) -> str:
        """
        Clean text content by removing UI/navigation noise

        Args:
            text: Raw text content

        Returns:
            Cleaned text content
        """
        # Common UI/navigation phrases to remove
        noise_patterns = [
            'Log Console',
            'Skip To Main Content',
            'Account',
            'Settings',
            'Logout',
            'Submit Search',
            'Home',
            'Contents',
            'Index',
            'Glossary',
            'Browse',
            'Community',
            'Search Filters',
            'Previous',
            'Next',
            'Create Profile',
            'Username *',
            'Email Address *',
            'Email Notifications',
            'Submit',
            'Cancel',
            'Filter:',
            'returned',
            'result(s)',
        ]

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip lines that are just noise patterns
            if any(noise in line for noise in noise_patterns):
                # Only skip if the line is mostly noise (< 50% content)
                if len(line) < 100:
                    continue

            # Skip very short lines that are likely navigation
            if len(line) < 3:
                continue

            # Skip lines with excessive special characters (likely UI elements)
            special_char_ratio = sum(1 for c in line if not c.isalnum() and not c.isspace()) / max(len(line), 1)
            if special_char_ratio > 0.5:
                continue

            cleaned_lines.append(line)

        # Join and remove excessive whitespace
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = '\n'.join(line for line in cleaned_text.split('\n') if line.strip())

        return cleaned_text

    async def _parse_json_file(self, file_path: Path) -> Optional[Dict]:
        """
        Parse JSON/JSONL file containing pre-extracted document content

        Expected format per line (JSONL) or array (JSON):
        {
            "filepath": "/path/to/original/file.html",
            "filetype": "html",
            "text": "Extracted text content..."
        }

        Args:
            file_path: Path to JSON/JSONL file

        Returns:
            Structured document content compatible with chunking
        """
        try:
            import json

            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()

            # Detect format: JSONL (one JSON per line) or JSON array
            entries = []

            # Try JSONL first (one JSON object per line)
            lines = content.strip().split('\n')
            is_jsonl = False

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict) and 'text' in entry:
                        entries.append(entry)
                        is_jsonl = True
                except json.JSONDecodeError:
                    continue

            # If not JSONL, try parsing as JSON array
            if not is_jsonl:
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        entries = [e for e in data if isinstance(e, dict) and 'text' in e]
                    elif isinstance(data, dict) and 'text' in data:
                        entries = [data]
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON file {file_path}: {e}")
                    return None

            if not entries:
                logger.error(f"No valid entries found in JSON file {file_path}")
                return None

            logger.info(f"Parsed {len(entries)} entries from JSON file {file_path}")

            # Convert entries to structured sections format
            sections = []
            total_words = 0

            for idx, entry in enumerate(entries):
                text_content = entry.get('text', '').strip()
                if not text_content or len(text_content) < 20:
                    continue

                # Clean the text content
                text_content = self._clean_text_content(text_content)

                # Extract metadata
                filepath = entry.get('filepath', f'entry_{idx}')
                filetype = entry.get('filetype', 'unknown')

                # Create section title from filepath
                section_title = Path(filepath).name if filepath else f'Section {idx + 1}'

                word_count = len(text_content.split())
                total_words += word_count

                sections.append({
                    'title': section_title,
                    'level': 1,
                    'content_text': text_content,
                    'word_count': word_count,
                    'metadata': {
                        'source_filepath': filepath,
                        'source_filetype': filetype,
                        'entry_index': idx
                    }
                })

            if not sections:
                logger.error(f"No valid sections created from JSON file {file_path}")
                return None

            # Return structured format compatible with existing chunking
            return {
                'page_title': file_path.stem,
                'url': f"file://{file_path}",
                'domain': 'local_json',
                'total_sections': len(sections),
                'total_entries': len(entries),
                'sections': sections,
                'metadata': {
                    'source_type': 'json',
                    'total_word_count': total_words
                }
            }

        except Exception as e:
            logger.error(f"Error parsing JSON file {file_path}: {e}")
            return None

    async def _extract_content(self, file_path: Path, content_type: str) -> Optional[Dict]:
        """
        Extract structured content from file using AsyncWebScraper

        Args:
            file_path: Path to file
            content_type: MIME type of file

        Returns:
            Structured document content or None
        """
        try:
            file_ext = file_path.suffix.lower()

            # Handle JSON/JSONL files with pre-extracted content
            if file_ext in ['.json', '.jsonl'] or (content_type and 'application/json' in content_type):
                logger.info(f"Processing JSON/JSONL file: {file_path}")
                return await self._parse_json_file(file_path)

            # Handle plain text files with cleaning
            elif content_type and 'text/plain' in content_type:
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = await f.read()

                # Clean UI/navigation noise from text
                text_content = self._clean_text_content(text_content)

                return {
                    'page_title': file_path.name,
                    'url': f"file://{file_path}",
                    'domain': 'local',
                    'total_sections': 1,
                    'sections': [{
                        'title': file_path.name,
                        'level': 1,
                        'content_text': text_content,
                        'word_count': len(text_content.split())
                    }]
                }

            else:
                # Handle HTML files using AsyncWebScraper
                config = ScrapingConfig(concurrent_limit=1)
                async with AsyncWebScraper(config) as scraper:
                    doc_structure = await scraper.extract_from_local_file_async(str(file_path))
                    return doc_structure

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return None

    def _create_chunks(self, structured_content: Dict, max_chunk_size: int = 2000) -> List[Dict]:
        """
        Create semantic chunks from structured content

        Args:
            structured_content: Structured document from AsyncWebScraper
            max_chunk_size: Maximum characters per chunk (default: 2000, range: 500-10000)

        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []

        try:
            page_title = structured_content.get('page_title', 'Unknown')[:100]
            url = structured_content.get('url', '')
            domain = structured_content.get('domain', 'local')

            sections = structured_content.get('sections', [])

            for section in sections:
                content_text = section.get('content_text', '')
                if len(content_text.strip()) < 20:  # Reduced from 50 for technical documentation
                    continue

                section_title = section.get('title', '')[:100]
                section_level = section.get('level', 1)

                # Extract section metadata (for JSON files with filepath info)
                section_metadata = section.get('metadata', {})

                # Build section hierarchy
                hierarchy = [page_title]
                if section_title and section_title != page_title:
                    hierarchy.append(section_title)

                # Determine content type
                content_type = 'text'
                if '<code>' in content_text or '<pre>' in content_text:
                    content_type = 'code'
                elif section_level == 1:
                    content_type = 'heading'

                # Create chunk(s) for this section
                if len(content_text) <= max_chunk_size:
                    # Single chunk
                    chunk_text = f"# {section_title or page_title}\n\n{content_text}"

                    # Merge section metadata with chunk metadata
                    chunk_metadata = {
                        'section_level': section_level,
                        'has_code': 'code' in content_type,
                        **section_metadata  # Include source filepath, filetype, etc.
                    }

                    chunks.append({
                        'text': chunk_text,
                        'title': section_title or page_title,
                        'page_title': page_title,
                        'url': url,
                        'domain': domain,
                        'content_type': content_type,
                        'section_hierarchy': hierarchy,
                        'word_count': len(chunk_text.split()),
                        'token_count': len(chunk_text) // 4,
                        'metadata': chunk_metadata
                    })

                else:
                    # Split large sections with overlap for context
                    overlap = 150  # Character overlap between chunks
                    parts = []
                    start = 0

                    while start < len(content_text):
                        # Try to find semantic boundary (paragraph, sentence)
                        end = start + max_chunk_size

                        if end < len(content_text):
                            # Look for paragraph break
                            paragraph_break = content_text.rfind('\n\n', start, end)
                            if paragraph_break > start + max_chunk_size // 2:
                                end = paragraph_break
                            else:
                                # Look for sentence break
                                sentence_break = max(
                                    content_text.rfind('. ', start, end),
                                    content_text.rfind('.\n', start, end),
                                    content_text.rfind('!\n', start, end),
                                    content_text.rfind('?\n', start, end)
                                )
                                if sentence_break > start + max_chunk_size // 2:
                                    end = sentence_break + 1

                        parts.append(content_text[start:end].strip())
                        start = max(start + 1, end - overlap)  # Add overlap

                    for part_num, part in enumerate(parts, 1):
                        # Add context from section title
                        chunk_text = f"# {section_title or page_title} (Part {part_num}/{len(parts)})\n\n{part}"

                        # Merge section metadata with chunk metadata for multi-part chunks
                        chunk_metadata = {
                            'section_level': section_level,
                            'part_number': part_num,
                            'total_parts': len(parts),
                            'has_overlap': part_num > 1,
                            'has_code': 'code' in content_type,
                            **section_metadata  # Include source filepath, filetype, etc.
                        }

                        chunks.append({
                            'text': chunk_text,
                            'title': f"{section_title or page_title} (Part {part_num}/{len(parts)})",
                            'page_title': page_title,
                            'url': url,
                            'domain': domain,
                            'content_type': content_type,
                            'section_hierarchy': hierarchy,
                            'word_count': len(chunk_text.split()),
                            'token_count': len(chunk_text) // 4,
                            'metadata': chunk_metadata
                        })

            logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")
            return chunks

        except Exception as e:
            logger.error(f"Error creating chunks: {e}")
            return []

    def get_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all documents for current user"""
        return self.db.query(Document).filter(
            Document.user_id == self.user_id,
            Document.processing_status != "deleted"
        ).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def get_document(self, document_id: int) -> Optional[Document]:
        """Get a specific document with access check"""
        return self.db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == self.user_id,
            Document.processing_status != "deleted"
        ).first()

    async def search_with_tfidf(
        self,
        query: str,
        document_ids: Optional[List[int]] = None,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Fallback search using TF-IDF when embeddings are unavailable
        Provides actual relevance scoring instead of random chunks

        Args:
            query: Search query
            document_ids: Optional filter by document IDs
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of ranked chunks with TF-IDF similarity scores
        """
        try:
            # Build base query
            query_builder = self.db.query(Chunk, Document).join(
                Document, Chunk.document_id == Document.id
            ).filter(
                Document.user_id == self.user_id,
                Document.processing_status == "completed"
            )

            # Filter by specific documents if requested
            if document_ids:
                query_builder = query_builder.filter(Document.id.in_(document_ids))

            # Get all chunks
            all_chunks = query_builder.all()

            if not all_chunks:
                logger.info("No chunks found for TF-IDF search")
                return []

            # Extract content and metadata
            chunk_texts = []
            chunk_info = []

            for chunk, document in all_chunks:
                chunk_texts.append(chunk.content)
                chunk_info.append({
                    'chunk': chunk,
                    'document': document
                })

            # Create TF-IDF vectorizer with optimized parameters
            vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 3),  # Include trigrams
                sublinear_tf=True,   # Sublinear TF scaling
                min_df=1,
                stop_words='english'
            )

            # Fit and transform chunk texts
            tfidf_matrix = vectorizer.fit_transform(chunk_texts)

            # Transform query
            query_vector = vectorizer.transform([query])

            # Compute cosine similarity
            similarities = cosine_similarity(query_vector, tfidf_matrix)[0]

            # Create results with scores
            results = []
            for idx, similarity in enumerate(similarities):
                if similarity >= min_similarity:
                    chunk = chunk_info[idx]['chunk']
                    document = chunk_info[idx]['document']

                    results.append({
                        'chunk_id': chunk.id,
                        'document_id': document.id,
                        'document_title': document.title,
                        'content': chunk.content,
                        'similarity': float(similarity),
                        'section_path': chunk.get_section_path(),
                        'content_type': chunk.content_type,
                        'word_count': chunk.word_count,
                        'metadata': chunk.extraction_metadata
                    })

            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = results[:top_k]

            logger.info(f"TF-IDF search returned {len(top_results)} relevant chunks (from {len(results)} matches)")
            return top_results

        except Exception as e:
            logger.error(f"Error in TF-IDF search: {e}")
            return []

    def delete_document(self, document_id: int) -> Tuple[bool, Optional[str]]:
        """Soft-delete a document"""
        try:
            document = self.get_document(document_id)
            if not document:
                return False, "Document not found or access denied"

            document.processing_status = "deleted"
            self.db.commit()

            logger.info(f"Deleted document {document_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            self.db.rollback()
            return False, str(e)

    def export_document_chunks(self, document_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Export all chunks from a document with their metadata

        Returns structured data showing exactly what was extracted and how it was chunked
        """
        try:
            document = self.get_document(document_id)
            if not document:
                return None, "Document not found or access denied"

            # Get all chunks for this document
            chunks = self.db.query(Chunk).filter(
                Chunk.document_id == document_id
            ).order_by(Chunk.chunk_order).all()

            # Build export data
            chunks_data = []
            for chunk in chunks:
                chunk_info = {
                    "order": chunk.chunk_order,
                    "content": chunk.content,
                    "content_type": chunk.content_type,
                    "character_count": chunk.character_count,
                    "word_count": chunk.word_count,
                    "token_count": chunk.token_count,
                    "section_hierarchy": chunk.section_hierarchy,
                    "section_path": chunk.get_section_path(),
                    "page_number": chunk.page_number,
                    "extraction_metadata": chunk.extraction_metadata,
                    "search_keywords": chunk.search_keywords,
                    "importance_score": chunk.importance_score
                }
                chunks_data.append(chunk_info)

            export_data = {
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "filename": document.original_filename,
                    "source_type": document.source_type,
                    "source_url": document.source_url,
                    "source_path": document.source_path,
                    "total_chunks": document.total_chunks,
                    "total_characters": document.total_characters,
                    "total_tokens": document.total_tokens,
                    "processing_config": document.processing_config,
                    "extraction_metadata": document.extraction_metadata,
                    "created_at": document.created_at.isoformat(),
                    "processing_completed_at": document.processing_completed_at.isoformat() if document.processing_completed_at else None
                },
                "chunks": chunks_data,
                "export_metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "total_chunks": len(chunks_data),
                    "export_version": "1.0"
                }
            }

            logger.info(f"Exported {len(chunks_data)} chunks from document {document_id}")
            return export_data, None

        except Exception as e:
            logger.error(f"Error exporting document chunks: {e}")
            return None, str(e)

    async def process_html_folder(
        self,
        folder_path: str,
        metadata: Optional[Dict] = None,
        chunk_size: int = 2000
    ) -> Tuple[Optional[Document], Optional[str], Optional[Dict]]:
        """
        Process all HTML files in a folder and its subdirectories

        Args:
            folder_path: Path to folder containing HTML documentation
            metadata: Optional metadata about the documentation
            chunk_size: Maximum characters per chunk (default: 2000, range: 500-10000)

        Returns:
            Tuple of (Document object, error message if any, stats dict)
        """
        try:
            # 1. Convert Windows path to WSL path if needed
            if folder_path.startswith('C:\\') or folder_path.startswith('c:\\'):
                # Convert Windows path to WSL path
                import subprocess
                try:
                    wsl_path = subprocess.check_output(['wslpath', folder_path], text=True).strip()
                    folder_path = wsl_path
                    logger.info(f"Converted Windows path to WSL: {folder_path}")
                except Exception as e:
                    logger.warning(f"Failed to convert Windows path, using as-is: {e}")

            folder = Path(folder_path)
            if not folder.exists():
                return None, f"Folder not found: {folder_path}", None

            if not folder.is_dir():
                return None, f"Path is not a directory: {folder_path}", None

            logger.info(f"Processing HTML folder: {folder}")

            # 2. Find all HTML files in folder and subdirectories
            config = ScrapingConfig(concurrent_limit=4)
            async with AsyncWebScraper(config) as scraper:
                # Use find_html_files to recursively find all HTML files
                html_files = scraper.find_html_files(str(folder), pattern="**/*.htm*")

                if not html_files:
                    return None, f"No HTML files found in folder: {folder_path}", None

                logger.info(f"Found {len(html_files)} HTML files in folder")

                # 3. Process all HTML files
                all_sections = []
                total_word_count = 0
                processed_files = []

                for file_path_str in html_files:
                    file_path = Path(file_path_str)

                    logger.info(f"Processing: {file_path.name}")
                    doc_structure = await scraper.extract_from_local_file_async(file_path_str)

                    if doc_structure:
                        sections = doc_structure.get('sections', [])
                        if sections:
                            all_sections.extend(sections)
                            processed_files.append(file_path.name)
                            for section in sections:
                                total_word_count += section.get('word_count', 0)

                logger.info(f"Processed {len(processed_files)} files, {len(all_sections)} sections, {total_word_count} words")

            if not all_sections:
                return None, "No content extracted from HTML files", None

            # 4. Create combined structured content
            folder_name = folder.name or "HTML Documentation"
            combined_content = {
                'page_title': f"{folder_name} (Complete Folder)",
                'url': f"file://{folder}",
                'domain': 'local_html_folder',
                'total_sections': len(all_sections),
                'sections': all_sections,
                'metadata': {
                    'source_type': 'html_folder',
                    'folder_path': str(folder),
                    'discovered_files': html_files,
                    'processed_files': processed_files,
                    'total_files_discovered': len(html_files),
                    'total_files_processed': len(processed_files),
                    'total_word_count': total_word_count
                }
            }

            # 5. Calculate content hash for deduplication
            content_str = str(combined_content)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()

            # Check for duplicate
            existing_doc = self.db.query(Document).filter(
                Document.user_id == self.user_id,
                Document.content_hash == content_hash,
                Document.processing_status != "deleted"
            ).first()

            if existing_doc:
                return None, f"Documentation already exists: {existing_doc.title}", None

            # 6. Create document record
            doc_title = metadata.get('title', f"{folder_name} Documentation") if metadata else f"{folder_name} Documentation"

            document = Document(
                user_id=self.user_id,
                title=doc_title,
                original_filename=f"{folder_name} (Folder)",
                source_type="html_folder",
                source_path=str(folder),
                content_type="text/html",
                file_size=len(content_str),
                content_hash=content_hash,
                processing_status="pending",
                processing_config={
                    'discovered_files': [Path(f).name for f in html_files],
                    'total_files': len(html_files),
                    'folder_path': str(folder),
                    **(metadata or {})
                }
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(f"Created HTML folder documentation record: {document.id}")

            # 7. Start processing asynchronously
            asyncio.create_task(self._process_html_docs_async(document.id, combined_content, None, chunk_size))

            stats = {
                'discovered_files': [Path(f).name for f in html_files],
                'total_files_discovered': len(html_files),
                'total_files_processed': len(processed_files),
                'total_sections': len(all_sections),
                'total_words': total_word_count,
                'folder_path': str(folder)
            }

            return document, None, stats

        except Exception as e:
            logger.error(f"Error processing HTML folder: {e}", exc_info=True)
            return None, f"Error processing HTML folder: {str(e)}", None

    async def process_local_html_documentation(
        self,
        home_file: UploadFile,
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[Document], Optional[str], Optional[Dict]]:
        """
        Process local HTML documentation by crawling all linked .htm/.html files

        Args:
            home_file: The home/index .htm file to start from
            metadata: Optional metadata about the documentation

        Returns:
            Tuple of (Document object, error message if any, stats dict)
        """
        temp_dir = None
        try:
            # 1. Validate home file
            if not home_file.filename:
                return None, "No filename provided", None

            file_ext = Path(home_file.filename).suffix.lower()
            if file_ext not in ['.html', '.htm']:
                return None, f"Home file must be .html or .htm, got: {file_ext}", None

            # 2. Save home file to temporary directory
            import tempfile
            temp_dir = Path(tempfile.mkdtemp(prefix="html_docs_"))
            home_path = temp_dir / home_file.filename

            content = await home_file.read()
            async with aiofiles.open(home_path, 'wb') as f:
                await f.write(content)

            logger.info(f"Saved home file to: {home_path}")

            # 3. Parse home file to discover linked .htm files
            from bs4 import BeautifulSoup

            async with aiofiles.open(home_path, 'r', encoding='utf-8', errors='ignore') as f:
                home_html = await f.read()

            soup = BeautifulSoup(home_html, 'html.parser')

            # Extract all links
            discovered_files = {home_file.filename}  # Include home file
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Filter for .htm/.html files only (ignore external URLs, anchors, etc.)
                if href.startswith(('http://', 'https://', 'mailto:', 'tel:', 'javascript:', '#')):
                    continue

                # Extract just the filename/relative path
                href_lower = href.lower()
                if href_lower.endswith('.htm') or href_lower.endswith('.html'):
                    # Clean query params and anchors
                    clean_href = href.split('?')[0].split('#')[0]
                    discovered_files.add(clean_href)

            logger.info(f"Discovered {len(discovered_files)} HTML files from home page")

            # 4. Copy/expect all linked files to be in the same directory
            # Since we're processing local docs, we assume user will upload all files
            # For now, we'll just process the home file and note the expected files

            files_to_process = [str(home_path)]

            # 5. Process all HTML files using AsyncWebScraper
            logger.info(f"Processing {len(files_to_process)} HTML file(s)...")
            config = ScrapingConfig(concurrent_limit=4)

            try:
                async with AsyncWebScraper(config) as scraper:
                    all_sections = []
                    total_word_count = 0

                    for file_path_str in files_to_process:
                        file_path = Path(file_path_str)
                        if not file_path.exists():
                            logger.warning(f"File not found: {file_path}")
                            continue

                        logger.info(f"Extracting content from: {file_path.name}")
                        doc_structure = await scraper.extract_from_local_file_async(file_path_str)

                        if doc_structure:
                            sections = doc_structure.get('sections', [])
                            logger.info(f"Extracted {len(sections)} sections from {file_path.name}")

                            if sections:
                                all_sections.extend(sections)
                                for section in sections:
                                    total_word_count += section.get('word_count', 0)
                        else:
                            logger.warning(f"No content extracted from {file_path.name}")

                logger.info(f"Total extracted: {len(all_sections)} sections, {total_word_count} words")

            except Exception as e:
                logger.error(f"Error during content extraction: {e}", exc_info=True)
                return None, f"Failed to extract content: {str(e)}", None

            if not all_sections:
                error_msg = "No content extracted from HTML documentation. The file may be empty or use unsupported HTML structure."
                logger.error(error_msg)
                return None, error_msg, None

            # 6. Create combined structured content
            combined_content = {
                'page_title': f"{home_file.filename} (Documentation Collection)",
                'url': f"file://{home_path}",
                'domain': 'local_html_docs',
                'total_sections': len(all_sections),
                'sections': all_sections,
                'metadata': {
                    'source_type': 'html_documentation',
                    'home_file': home_file.filename,
                    'discovered_files': list(discovered_files),
                    'total_files_discovered': len(discovered_files),
                    'total_word_count': total_word_count
                }
            }

            # 7. Calculate content hash for deduplication
            content_str = str(combined_content)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()

            # Check for duplicate
            existing_doc = self.db.query(Document).filter(
                Document.user_id == self.user_id,
                Document.content_hash == content_hash,
                Document.processing_status != "deleted"
            ).first()

            if existing_doc:
                return None, f"Documentation already exists: {existing_doc.title}", None

            # 8. Create document record
            doc_title = metadata.get('title', f"{home_file.filename} Documentation") if metadata else f"{home_file.filename} Documentation"

            document = Document(
                user_id=self.user_id,
                title=doc_title,
                original_filename=home_file.filename,
                source_type="html_documentation",
                source_path=str(home_path),
                content_type="text/html",
                file_size=len(content_str),
                content_hash=content_hash,
                processing_status="pending",
                processing_config={
                    'discovered_files': list(discovered_files),
                    'total_files': len(discovered_files),
                    **(metadata or {})
                }
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(f"Created HTML documentation record: {document.id}")

            # 9. Start processing asynchronously
            asyncio.create_task(self._process_html_docs_async(document.id, combined_content, temp_dir))

            stats = {
                'discovered_files': list(discovered_files),
                'total_files_discovered': len(discovered_files),
                'total_sections': len(all_sections),
                'total_words': total_word_count
            }

            return document, None, stats

        except Exception as e:
            logger.error(f"Error processing HTML documentation: {e}")
            # Clean up temp directory on error
            if temp_dir and temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None, f"Error processing HTML documentation: {str(e)}", None

    async def _process_html_docs_async(self, document_id: int, combined_content: Dict, temp_dir: Path, chunk_size: int = 2000):
        """
        Background task to process HTML documentation asynchronously

        Args:
            document_id: Database ID of document to process
            combined_content: Pre-extracted combined content from all HTML files
            temp_dir: Temporary directory to clean up after processing
            chunk_size: Maximum characters per chunk (default: 2000)
        """
        start_time = datetime.utcnow()

        try:
            # Get document from database (new session for background task)
            from core.database import get_db
            db = next(get_db())

            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                return

            # Mark as processing
            document.start_processing()
            db.commit()

            logger.info(f"Starting async processing for HTML documentation {document_id}: {document.title}")

            # Create processing log
            log = DocumentProcessingLog(
                document_id=document_id,
                user_id=document.user_id,
                operation="process_html_docs",
                status="started",
                started_at=start_time
            )
            db.add(log)
            db.commit()

            # Progress: 0-20% (content already extracted)
            document.update_progress(20.0)
            db.commit()

            # 2. Create semantic chunks (20-40%)
            document.update_progress(25.0)
            db.commit()

            chunks_data = self._create_chunks(combined_content, max_chunk_size=chunk_size)

            if not chunks_data:
                raise ValueError("Failed to create chunks from HTML documentation")

            logger.info(f"Created {len(chunks_data)} chunks for HTML documentation {document_id}")

            document.update_progress(40.0)
            db.commit()

            # 3. Generate embeddings for all chunks (40-95%)
            embeddings = []
            if self.embedding_service:
                chunk_texts = [chunk['text'] for chunk in chunks_data]
                logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
                embeddings = await self.embedding_service.generate_embeddings_batch_async(chunk_texts)
                logger.info(f"Embedding generation complete")
                document.update_progress(95.0)
                db.commit()
            else:
                logger.warning("Embedding service not available - storing chunks without embeddings")
                embeddings = [None] * len(chunks_data)
                document.update_progress(95.0)
                db.commit()

            # 4. Store chunks in database (95-100%)
            total_chars = 0
            total_tokens = 0

            for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
                if embedding is None and self.embedding_service:
                    logger.warning(f"Failed to generate embedding for chunk {i}")

                chunk_content = chunk_data['text']
                chunk_hash = hashlib.sha256(chunk_content.encode()).hexdigest()

                chunk = Chunk(
                    document_id=document_id,
                    content=chunk_content,
                    content_hash=chunk_hash,
                    embedding=embedding,
                    embedding_model=self.embedding_service.model_name if self.embedding_service else None,
                    chunk_order=i,
                    content_type=chunk_data.get('content_type', 'text'),
                    section_hierarchy=chunk_data.get('section_hierarchy'),
                    character_count=len(chunk_content),
                    word_count=chunk_data.get('word_count', len(chunk_content.split())),
                    token_count=chunk_data.get('token_count', len(chunk_content) // 4),
                    extraction_metadata=chunk_data.get('metadata', {})
                )

                chunk.set_content_stats()
                total_chars += chunk.character_count
                total_tokens += chunk.token_count

                db.add(chunk)

                # Update progress periodically
                progress_points = [len(chunks_data) // 4, len(chunks_data) // 2, 3 * len(chunks_data) // 4, len(chunks_data) - 1]
                if i in progress_points:
                    progress = 95.0 + (5.0 * (i + 1) / len(chunks_data))
                    document.update_progress(progress)
                    db.commit()

            # 5. Mark document as completed
            document.complete_processing(
                chunk_count=len(chunks_data),
                char_count=total_chars,
                token_count=total_tokens
            )

            # Update processing log
            log.status = "completed"
            completed_time = datetime.utcnow()
            log.completed_at = completed_time

            # Handle timezone-aware vs naive datetime comparison
            start_time = log.started_at
            if start_time.tzinfo is not None and completed_time.tzinfo is None:
                completed_time = completed_time.replace(tzinfo=timezone.utc)
            elif start_time.tzinfo is None and completed_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            log.duration_seconds = (completed_time - start_time).total_seconds()
            log.chunks_created = len(chunks_data)
            log.tokens_processed = total_tokens

            db.commit()

            logger.info(f"Successfully processed HTML documentation {document_id}: {len(chunks_data)} chunks created")

        except Exception as e:
            logger.error(f"Error processing HTML documentation {document_id}: {e}")

            # Mark document as failed
            try:
                document.fail_processing(str(e))

                # Update processing log
                log.status = "failed"
                log.completed_at = datetime.utcnow()
                log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
                log.error_message = str(e)

                db.commit()
            except:
                pass

        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

            db.close()

    async def search_documents(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Search documents using semantic similarity with PostgreSQL vector operations

        This method uses pgvector's HNSW index for efficient similarity search,
        providing O(log n) performance instead of O(n) Python-based computation.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            document_ids: Optional filter by document IDs
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of matching chunks with similarity scores, sorted by relevance
        """
        try:
            # Check if embeddings are available - if not, fall back to TF-IDF search
            if not self.embedding_service:
                logger.warning("Embedding service not available - using TF-IDF fallback")
                return await self.search_with_tfidf(
                    query=query,
                    document_ids=document_ids,
                    top_k=top_k,
                    min_similarity=min_similarity
                )

            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Check database type - pgvector operators only work with PostgreSQL
            from sqlalchemy import inspect
            import numpy as np

            dialect_name = inspect(self.db.bind).dialect.name

            if dialect_name == 'postgresql':
                # Use optimized pgvector operations
                logger.info(f"🔍 Vector search (pgvector): dimensions={len(query_embedding)}, top_k={top_k}, min_similarity={min_similarity}")

                distance = Chunk.embedding.cosine_distance(query_embedding)
                similarity = 1 - (distance / 2)

                query_builder = self.db.query(
                    Chunk,
                    Document,
                    similarity.label('similarity')
                ).join(
                    Document, Chunk.document_id == Document.id
                ).filter(
                    Document.user_id == self.user_id,
                    Document.processing_status == "completed",
                    Chunk.embedding.isnot(None)
                )

                if document_ids:
                    query_builder = query_builder.filter(Document.id.in_(document_ids))

                max_distance = 2 * (1 - min_similarity)
                query_builder = query_builder.filter(distance <= max_distance)
                query_builder = query_builder.order_by(distance).limit(top_k)

                logger.info(f"📊 Executing vector similarity search with HNSW index...")
                db_results = query_builder.all()

                results = []
                for chunk, document, sim_score in db_results:
                    results.append({
                        'chunk_id': chunk.id,
                        'document_id': document.id,
                        'document_title': document.title,
                        'content': chunk.content,
                        'similarity': float(sim_score),
                        'section_path': chunk.get_section_path(),
                        'content_type': chunk.content_type,
                        'word_count': chunk.word_count,
                        'metadata': chunk.extraction_metadata
                    })

                logger.info(f"✅ Found {len(results)} results above threshold {min_similarity}")
                return results

            else:
                # SQLite fallback - use Python-based similarity
                logger.info(f"🔍 Vector search (Python/SQLite): dimensions={len(query_embedding)}, top_k={top_k}, min_similarity={min_similarity}")

                query_builder = self.db.query(Chunk, Document).join(
                    Document, Chunk.document_id == Document.id
                ).filter(
                    Document.user_id == self.user_id,
                    Document.processing_status == "completed",
                    Chunk.embedding.isnot(None)
                )

                if document_ids:
                    query_builder = query_builder.filter(Document.id.in_(document_ids))

                all_chunks = query_builder.all()
                logger.info(f"📦 Computing similarities for {len(all_chunks)} chunks...")

                results = []
                query_vec = np.array(query_embedding)
                query_norm = np.linalg.norm(query_vec)

                for chunk, document in all_chunks:
                    try:
                        chunk_emb = chunk.embedding
                        if hasattr(chunk_emb, 'tolist'):
                            chunk_emb = chunk_emb.tolist()
                        elif not isinstance(chunk_emb, list):
                            import json
                            if isinstance(chunk_emb, str):
                                chunk_emb = json.loads(chunk_emb)
                            else:
                                chunk_emb = list(chunk_emb)

                        if not chunk_emb:
                            continue

                        chunk_vec = np.array(chunk_emb)
                        chunk_norm = np.linalg.norm(chunk_vec)

                        if query_norm == 0 or chunk_norm == 0:
                            continue

                        similarity = float(np.dot(query_vec, chunk_vec) / (query_norm * chunk_norm))

                        if similarity >= min_similarity:
                            results.append({
                                'chunk_id': chunk.id,
                                'document_id': document.id,
                                'document_title': document.title,
                                'content': chunk.content,
                                'similarity': similarity,
                                'section_path': chunk.get_section_path(),
                                'content_type': chunk.content_type,
                                'word_count': chunk.word_count,
                                'metadata': chunk.extraction_metadata
                            })
                    except Exception as e:
                        logger.warning(f"Error processing chunk {chunk.id}: {e}")
                        continue

                # Sort and return top_k
                results.sort(key=lambda x: x['similarity'], reverse=True)
                logger.info(f"✅ Found {len(results[:top_k])} results above threshold {min_similarity}")
                return results[:top_k]

        except Exception as e:
            logger.error(f"Error searching documents with vector operations: {e}")
            logger.exception(e)  # Full stack trace for debugging
            return []
