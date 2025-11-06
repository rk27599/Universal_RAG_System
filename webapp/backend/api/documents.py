"""
Documents API - File Upload, Processing, and RAG Search
Handles document management with chunking, embedding, and retrieval
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Body, Form
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.document import Document
from services.document_service import DocumentProcessingService

router = APIRouter(prefix="/documents", tags=["Documents"])


# Pydantic models for request/response
class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    size: int
    uploadedAt: str
    status: str
    progress: float = 0.0
    chunksCount: int
    processingTime: Optional[float] = None
    processingError: Optional[str] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    documentIds: Optional[List[int]] = None
    topK: int = 5
    minSimilarity: float = 0.3


class SearchResult(BaseModel):
    chunkId: int
    documentId: int
    documentTitle: str
    content: str
    similarity: float
    sectionPath: str
    contentType: Optional[str]
    wordCount: int


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process a document (HTML, TXT, JSON, JSONL, PDF, or Images)

    The document will be processed asynchronously:
    1. Content extraction using intelligent parsing (HTML, JSON, PDF, Images)
    2. Semantic chunking based on document structure (configurable chunk size)
    3. Vector embedding generation for each chunk
    4. Storage in database with metadata

    PDF Processing Features:
    - Page-by-page text extraction
    - Image extraction with metadata
    - Code block detection in technical documentation
    - Table of contents structure preservation
    - Page number tracking for citations

    Image Processing Features (NEW):
    - OCR text extraction (EasyOCR/Pytesseract)
    - Vision model descriptions (LLaVA via Ollama)
    - Automatic image preprocessing and optimization
    - Thumbnail generation for preview
    - Metadata extraction (dimensions, format, EXIF)
    - Supported formats: JPG, JPEG, PNG, GIF, BMP, TIFF, WebP

    Args:
        file: Document file to upload
        chunk_size: Maximum characters per chunk (default: 2000, range: 500-10000)
    """

    # Create document processing service
    service = DocumentProcessingService(db, current_user.id)

    # Check if embeddings are available
    embeddings_enabled = service.embedding_service is not None

    # Process uploaded file
    document, error = await service.process_uploaded_file(file, chunk_size=chunk_size)

    if error:
        raise HTTPException(status_code=400, detail=error)

    # Build status message with embedding info
    if embeddings_enabled:
        status_message = "Document uploaded successfully. Processing with semantic embeddings in background."
        processing_method = "semantic_embeddings"
    else:
        status_message = "Document uploaded successfully. Processing with TF-IDF fallback in background."
        processing_method = "tfidf_fallback"

    # Return document info with embedding status
    return {
        "success": True,
        "data": {
            "id": document.id,
            "title": document.title,
            "filename": document.original_filename,
            "size": document.file_size,
            "uploadedAt": document.created_at.isoformat(),
            "status": document.processing_status,
            "chunksCount": document.total_chunks,
            "embeddingsEnabled": embeddings_enabled,
            "processingMethod": processing_method
        },
        "message": status_message
    }


@router.post("/upload-html-docs")
async def upload_html_documentation(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process HTML documentation by discovering and processing linked .htm/.html files

    The home/index .htm file will be parsed to discover all linked HTML files:
    1. Parse home file to extract all internal .htm/.html links
    2. Discover all related documentation files
    3. Process all files together as a documentation collection
    4. Generate semantic chunks and embeddings
    5. Store as searchable knowledge base

    Note: Currently processes only the home file. In future versions,
    will support uploading entire documentation directories.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received HTML documentation upload: {file.filename} ({file.content_type})")

        # Create document processing service
        service = DocumentProcessingService(db, current_user.id)

        # Check if embeddings are available
        embeddings_enabled = service.embedding_service is not None

        # Process HTML documentation
        logger.info("Starting HTML documentation processing...")
        document, error, stats = await service.process_local_html_documentation(file)

        if error:
            logger.error(f"HTML documentation processing failed: {error}")
            raise HTTPException(status_code=400, detail=error)

        if not document:
            logger.error("No document returned from processing (but no error)")
            raise HTTPException(status_code=500, detail="Failed to create document record")

        logger.info(f"HTML documentation processed successfully: {document.id}")

        # Build response with discovery stats
        return {
            "success": True,
            "data": {
                "id": document.id,
                "title": document.title,
                "filename": document.original_filename,
                "size": document.file_size,
                "uploadedAt": document.created_at.isoformat(),
                "status": document.processing_status,
                "chunksCount": document.total_chunks,
                "embeddingsEnabled": embeddings_enabled,
                "processingMethod": "semantic_embeddings" if embeddings_enabled else "tfidf_fallback",
                "discoveryStats": stats
            },
            "message": f"HTML documentation uploaded. Discovered {stats['total_files_discovered']} files. Processing in background."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in HTML documentation upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class HtmlFolderRequest(BaseModel):
    folder_path: str
    metadata: Optional[dict] = None
    chunk_size: Optional[int] = 2000  # Default 2000 characters


@router.post("/upload-html-folder")
async def upload_html_folder(
    request: HtmlFolderRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process all HTML files in a folder and its subdirectories

    Recursively finds and processes all .htm/.html files in the specified folder:
    1. Scan folder and all subfolders for HTML files
    2. Process all files together as a documentation collection
    3. Generate semantic chunks and embeddings
    4. Store as searchable knowledge base

    Supports both Windows and Unix paths. Windows paths are automatically converted to WSL paths.

    Example paths:
    - Windows: C:\\Program Files (x86)\\Windows Kits\\10\\bin\\10.0.26100.0\\arm64\\AccChecker
    - Unix/WSL: /mnt/c/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/arm64/AccChecker
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received HTML folder processing request: {request.folder_path}")

        # Create document processing service
        service = DocumentProcessingService(db, current_user.id)

        # Check if embeddings are available
        embeddings_enabled = service.embedding_service is not None

        # Process HTML folder
        logger.info(f"Starting HTML folder processing with chunk_size={request.chunk_size}...")
        document, error, stats = await service.process_html_folder(request.folder_path, request.metadata, request.chunk_size)

        if error:
            logger.error(f"HTML folder processing failed: {error}")
            raise HTTPException(status_code=400, detail=error)

        if not document:
            logger.error("No document returned from processing (but no error)")
            raise HTTPException(status_code=500, detail="Failed to create document record")

        logger.info(f"HTML folder processed successfully: {document.id}")

        # Build response with discovery stats
        return {
            "success": True,
            "data": {
                "id": document.id,
                "title": document.title,
                "filename": document.original_filename,
                "size": document.file_size,
                "uploadedAt": document.created_at.isoformat(),
                "status": document.processing_status,
                "chunksCount": document.total_chunks,
                "embeddingsEnabled": embeddings_enabled,
                "processingMethod": "semantic_embeddings" if embeddings_enabled else "tfidf_fallback",
                "discoveryStats": stats
            },
            "message": f"HTML folder processed. Found {stats['total_files_discovered']} files, processed {stats['total_files_processed']} files. Processing in background."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in HTML folder processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/")
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all documents for the current user

    Returns documents with their processing status and statistics
    """

    service = DocumentProcessingService(db, current_user.id)
    documents = service.get_documents(skip=skip, limit=limit)

    # Format response
    data = []
    for doc in documents:
        doc_data = {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.original_filename,
            "size": doc.file_size,
            "uploadedAt": doc.created_at.isoformat(),
            "status": doc.processing_status,
            "progress": doc.processing_progress,
            "chunksCount": doc.total_chunks,
            "processingTime": doc.processing_duration,
            "processingError": doc.processing_error,
            "sourceType": doc.source_type
        }

        # Add discovery stats for HTML documentation
        if doc.source_type == "html_documentation" and doc.processing_config:
            doc_data["discoveryStats"] = {
                "discoveredFiles": doc.processing_config.get("discovered_files", []),
                "totalFiles": doc.processing_config.get("total_files", 0)
            }

        data.append(doc_data)

    return {
        "success": True,
        "data": data,
        "message": f"Retrieved {len(data)} documents"
    }


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific document

    Includes processing summary and chunk statistics
    """

    service = DocumentProcessingService(db, current_user.id)
    document = service.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Increment access count
    document.increment_access_count()
    db.commit()

    # Include discovery stats for HTML documentation
    response_data = {
        "id": document.id,
        "title": document.title,
        "filename": document.original_filename,
        "size": document.file_size,
        "uploadedAt": document.created_at.isoformat(),
        "status": document.processing_status,
        "progress": document.processing_progress,
        "chunksCount": document.total_chunks,
        "totalCharacters": document.total_characters,
        "totalTokens": document.total_tokens,
        "processingTime": document.processing_duration,
        "processingError": document.processing_error,
        "accessCount": document.access_count,
        "processingSummary": document.get_processing_summary(),
        "sourceType": document.source_type
    }

    # Add discovery stats for HTML documentation
    if document.source_type == "html_documentation" and document.processing_config:
        response_data["discoveryStats"] = {
            "discoveredFiles": document.processing_config.get("discovered_files", []),
            "totalFiles": document.processing_config.get("total_files", 0)
        }

    return {
        "success": True,
        "data": response_data,
        "message": "Document retrieved successfully"
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document (soft delete)

    The document and its chunks will be marked as deleted but not removed from database
    """

    service = DocumentProcessingService(db, current_user.id)
    success, error = service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail=error or "Failed to delete document")

    return {
        "success": True,
        "message": "Document deleted successfully"
    }


@router.get("/{document_id}/export-chunks")
async def export_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export all extracted chunks from a document

    Returns the processed content showing exactly what was extracted and chunked
    from the original document. Useful for analyzing extraction quality and
    debugging the RAG pipeline.

    Returns:
        JSON with document metadata and all chunks with their content,
        section hierarchy, and extraction metadata
    """

    service = DocumentProcessingService(db, current_user.id)
    export_data, error = service.export_document_chunks(document_id)

    if error:
        raise HTTPException(status_code=404, detail=error)

    return {
        "success": True,
        "data": export_data,
        "message": "Document chunks exported successfully"
    }


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Semantic search across document chunks using vector similarity

    This endpoint enables RAG (Retrieval-Augmented Generation) by finding
    the most relevant document chunks for a given query.

    Args:
        query: Natural language search query
        documentIds: Optional list of document IDs to search within
        topK: Number of results to return (default: 5)
        minSimilarity: Minimum similarity threshold (0-1, default: 0.3)

    Returns:
        List of matching chunks sorted by relevance score
    """

    service = DocumentProcessingService(db, current_user.id)

    # Perform semantic search
    results = await service.search_documents(
        query=request.query,
        top_k=request.topK,
        document_ids=request.documentIds,
        min_similarity=request.minSimilarity
    )

    # Format response
    data = []
    for result in results:
        data.append({
            "chunkId": result['chunk_id'],
            "documentId": result['document_id'],
            "documentTitle": result['document_title'],
            "content": result['content'],
            "similarity": round(result['similarity'], 4),
            "sectionPath": result['section_path'],
            "contentType": result['content_type'],
            "wordCount": result['word_count'],
            "metadata": result.get('metadata', {})
        })

    return {
        "success": True,
        "data": data,
        "message": f"Found {len(data)} relevant chunks"
    }


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get chunks for a specific document

    Returns paginated list of document chunks with metadata
    """

    service = DocumentProcessingService(db, current_user.id)
    document = service.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks
    from models.document import Chunk
    chunks = db.query(Chunk).filter(
        Chunk.document_id == document_id
    ).order_by(Chunk.chunk_order).offset(skip).limit(limit).all()

    # Format response
    data = []
    for chunk in chunks:
        data.append({
            "id": chunk.id,
            "order": chunk.chunk_order,
            "content": chunk.content,
            "contentType": chunk.content_type,
            "sectionPath": chunk.get_section_path(),
            "characterCount": chunk.character_count,
            "wordCount": chunk.word_count,
            "tokenCount": chunk.token_count,
            "hasEmbedding": chunk.has_embedding,
            "metadata": chunk.get_metadata_summary()
        })

    return {
        "success": True,
        "data": data,
        "message": f"Retrieved {len(data)} chunks"
    }
