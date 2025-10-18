"""
Document Recovery Service - Startup Recovery for Stuck Documents
Detects and resumes processing for documents that were interrupted by server restarts
"""

import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session

from models.document import Document
from core.database import get_db

logger = logging.getLogger(__name__)


async def detect_stuck_documents(
    db: Session,
    stuck_threshold_minutes: int = 5
) -> List[Document]:
    """
    Detect documents stuck in processing or pending status

    A document is considered "stuck" if:
    - Status is "pending" or "processing"
    - Created/updated more than threshold_minutes ago
    - Not in "completed", "failed", or "deleted" status

    Args:
        db: Database session
        stuck_threshold_minutes: Minutes before a document is considered stuck

    Returns:
        List of stuck Document objects
    """
    try:
        threshold_time = datetime.now(timezone.utc) - timedelta(minutes=stuck_threshold_minutes)

        stuck_docs = db.query(Document).filter(
            Document.processing_status.in_(["pending", "processing"]),
            Document.created_at < threshold_time
        ).all()

        if stuck_docs:
            logger.info(f"🔍 Found {len(stuck_docs)} stuck document(s)")
            for doc in stuck_docs:
                age_minutes = (datetime.now(timezone.utc) - doc.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60
                logger.info(
                    f"  - Document {doc.id}: '{doc.title}' | "
                    f"Status: {doc.processing_status} | "
                    f"Progress: {doc.processing_progress}% | "
                    f"Age: {age_minutes:.1f} minutes"
                )

        return stuck_docs

    except Exception as e:
        logger.error(f"Error detecting stuck documents: {e}")
        return []


async def recover_document(
    document: Document,
    db: Session
) -> bool:
    """
    Recover a single stuck document by restarting its processing

    Args:
        document: Document to recover
        db: Database session

    Returns:
        True if recovery was initiated successfully, False otherwise
    """
    try:
        # Verify file exists on disk
        if not document.source_path:
            logger.error(f"❌ Document {document.id} has no source_path - cannot recover")
            document.fail_processing("No source file path found")
            db.commit()
            return False

        file_path = Path(document.source_path)

        if not file_path.exists():
            logger.error(f"❌ Source file not found: {file_path}")
            document.fail_processing(f"Source file not found: {file_path}")
            db.commit()
            return False

        # Get chunk size from processing config or use default
        chunk_size = document.processing_config.get('chunk_size', 2000) if document.processing_config else 2000

        # Reset document to pending status
        document.processing_status = "pending"
        document.processing_progress = 0.0
        document.processing_error = None
        db.commit()

        logger.info(
            f"🔄 Recovering document {document.id}: '{document.title}' | "
            f"File: {file_path.name} | "
            f"Size: {document.file_size / 1024 / 1024:.2f}MB"
        )

        # Re-queue for processing using DocumentProcessingService
        from services.document_service import DocumentProcessingService

        service = DocumentProcessingService(db, document.user_id)

        # Start async processing task with recovery flag
        task = asyncio.create_task(
            service._process_document_async(
                document_id=document.id,
                file_path=file_path,
                chunk_size=chunk_size,
                is_recovery=True
            )
        )

        # Add completion callback for logging
        task.add_done_callback(
            lambda t: logger.info(f"✅ Recovery task completed for document {document.id}")
            if not t.exception()
            else logger.error(f"❌ Recovery task failed for document {document.id}: {t.exception()}")
        )

        logger.info(f"✅ Recovery initiated for document {document.id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error recovering document {document.id}: {e}", exc_info=True)
        try:
            document.fail_processing(f"Recovery failed: {str(e)}")
            db.commit()
        except:
            pass
        return False


async def recover_all_stuck_documents(
    stuck_threshold_minutes: int = 5,
    max_concurrent_recoveries: int = 3
) -> int:
    """
    Detect and recover all stuck documents during application startup

    Args:
        stuck_threshold_minutes: Minutes before document is considered stuck
        max_concurrent_recoveries: Maximum documents to recover concurrently

    Returns:
        Number of documents successfully recovered
    """
    db = None
    recovered_count = 0

    try:
        # Get database session
        db = next(get_db())

        # Detect stuck documents
        stuck_docs = await detect_stuck_documents(db, stuck_threshold_minutes)

        if not stuck_docs:
            logger.info("✅ No stuck documents found")
            return 0

        logger.info(f"🔄 Starting recovery for {len(stuck_docs)} stuck document(s)...")

        # Recover documents (limit concurrency to avoid overwhelming the system)
        for i in range(0, len(stuck_docs), max_concurrent_recoveries):
            batch = stuck_docs[i:i + max_concurrent_recoveries]

            # Process batch concurrently
            recovery_tasks = [
                recover_document(doc, db)
                for doc in batch
            ]

            results = await asyncio.gather(*recovery_tasks, return_exceptions=True)

            # Count successful recoveries
            for result in results:
                if isinstance(result, bool) and result:
                    recovered_count += 1
                elif isinstance(result, Exception):
                    logger.error(f"Recovery task raised exception: {result}")

        logger.info(
            f"✅ Recovery complete: {recovered_count}/{len(stuck_docs)} documents recovered"
        )

        return recovered_count

    except Exception as e:
        logger.error(f"❌ Error in recovery service: {e}", exc_info=True)
        return recovered_count

    finally:
        if db:
            db.close()


# Optional: Manual recovery function for API endpoint
async def recover_stuck_documents_for_user(
    user_id: int,
    stuck_threshold_minutes: int = 5
) -> Tuple[int, List[str]]:
    """
    Recover stuck documents for a specific user (for manual recovery endpoint)

    Args:
        user_id: User ID to recover documents for
        stuck_threshold_minutes: Minutes before document is considered stuck

    Returns:
        Tuple of (recovered_count, list of recovered document titles)
    """
    db = None
    recovered_count = 0
    recovered_titles = []

    try:
        db = next(get_db())

        # Detect stuck documents for this user
        threshold_time = datetime.now(timezone.utc) - timedelta(minutes=stuck_threshold_minutes)

        stuck_docs = db.query(Document).filter(
            Document.user_id == user_id,
            Document.processing_status.in_(["pending", "processing"]),
            Document.created_at < threshold_time
        ).all()

        if not stuck_docs:
            return 0, []

        logger.info(f"🔄 User {user_id}: Recovering {len(stuck_docs)} stuck document(s)")

        # Recover each document
        for doc in stuck_docs:
            success = await recover_document(doc, db)
            if success:
                recovered_count += 1
                recovered_titles.append(doc.title)

        return recovered_count, recovered_titles

    except Exception as e:
        logger.error(f"❌ Error recovering documents for user {user_id}: {e}")
        return recovered_count, recovered_titles

    finally:
        if db:
            db.close()
