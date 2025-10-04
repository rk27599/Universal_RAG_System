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
from datetime import datetime
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
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[Document], Optional[str]]:
        """
        Process an uploaded file: save, extract content, chunk, embed, and store

        Args:
            file: Uploaded file from FastAPI
            metadata: Optional metadata about the document

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
            asyncio.create_task(self._process_document_async(document.id, file_path))

            return document, None

        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            if file_path and file_path.exists():
                file_path.unlink()  # Clean up file on error
            return None, f"Error processing file: {str(e)}"

    async def _process_document_async(self, document_id: int, file_path: Path):
        """
        Background task to process document content asynchronously

        Args:
            document_id: Database ID of document to process
            file_path: Path to uploaded file
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

            logger.info(f"Starting async processing for document {document_id}: {document.title}")

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

            chunks_data = self._create_chunks(structured_content)

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
            log.completed_at = datetime.utcnow()
            log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
            log.chunks_created = len(chunks_data)
            log.tokens_processed = total_tokens

            db.commit()

            logger.info(f"Successfully processed document {document_id}: {len(chunks_data)} chunks created")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")

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
            db.close()

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

    def _create_chunks(self, structured_content: Dict, max_chunk_size: int = 1200) -> List[Dict]:
        """
        Create semantic chunks from structured content

        Args:
            structured_content: Structured document from AsyncWebScraper
            max_chunk_size: Maximum characters per chunk

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
                if len(content_text.strip()) < 50:
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

    async def search_documents(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Search documents using semantic similarity

        Args:
            query: Natural language search query
            top_k: Number of results to return
            document_ids: Optional filter by document IDs
            min_similarity: Minimum similarity threshold

        Returns:
            List of matching chunks with similarity scores
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

            # Build base query for chunks
            query_builder = self.db.query(Chunk, Document).join(
                Document, Chunk.document_id == Document.id
            ).filter(
                Document.user_id == self.user_id,
                Document.processing_status == "completed",
                Chunk.embedding.isnot(None)
            )

            # Filter by specific documents if requested
            if document_ids:
                query_builder = query_builder.filter(Document.id.in_(document_ids))

            # Get all chunks (will compute similarity in Python for now)
            # In production, use pgvector for database-level similarity search
            all_chunks = query_builder.all()

            logger.info(f"📦 Found {len(all_chunks)} chunks to search (user_id={self.user_id}, doc_ids={document_ids})")

            if not all_chunks:
                logger.warning(f"⚠️ No chunks found for search - user_id={self.user_id}, document_ids={document_ids}")
                return []

            # Compute similarity scores
            results = []
            processed_count = 0
            error_count = 0

            logger.info(f"🔍 Computing similarities for {len(all_chunks)} chunks...")
            for chunk, document in all_chunks:
                processed_count += 1
                try:
                    # Check if embedding exists (handle both None and empty arrays)
                    if chunk.embedding is None:
                        if processed_count <= 3:  # Log first few
                            logger.debug(f"Chunk {chunk.id}: embedding is None, skipping")
                        continue

                    # Convert to list if it's a numpy array or other array-like object
                    chunk_emb = chunk.embedding
                    if hasattr(chunk_emb, 'tolist'):
                        chunk_emb = chunk_emb.tolist()
                    elif not isinstance(chunk_emb, list):
                        # Might be JSON string - try to parse
                        import json
                        if isinstance(chunk_emb, str):
                            try:
                                chunk_emb = json.loads(chunk_emb)
                            except:
                                logger.warning(f"Chunk {chunk.id}: Failed to parse embedding JSON string")
                                continue
                        else:
                            chunk_emb = list(chunk_emb)

                    if not chunk_emb or len(chunk_emb) == 0:
                        if processed_count <= 3:
                            logger.debug(f"Chunk {chunk.id}: embedding is empty, skipping")
                        continue

                    if processed_count <= 3:  # Log first few successful embeddings
                        logger.debug(f"Chunk {chunk.id}: embedding has {len(chunk_emb)} dimensions")

                    similarity = self.embedding_service.compute_similarity(
                        query_embedding,
                        chunk_emb
                    )

                    if processed_count <= 3:  # Log first few similarities
                        logger.info(f"Chunk {chunk.id}: similarity = {similarity:.4f} (threshold: {min_similarity})")

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
                    error_count += 1
                    logger.warning(f"❌ Error processing chunk {chunk.id}: {e}")
                    continue

            logger.info(f"✅ Processed {processed_count} chunks, {error_count} errors, {len(results)} results above threshold {min_similarity}")

            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
