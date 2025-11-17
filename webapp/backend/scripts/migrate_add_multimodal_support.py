#!/usr/bin/env python3
"""
Database Migration: Add Multimodal Support
Adds tables and columns for multimodal RAG functionality
- media_metadata table
- transcript_segments table
- Updated relationships

Run: python webapp/backend/scripts/migrate_add_multimodal_support.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from core.config import settings
from core.database import Base

# Import all models to ensure they're registered
from models.user import User
from models.document import Document, Chunk, DocumentProcessingLog
from models.conversation import Conversation, Message
from models.media import MediaMetadata, TranscriptSegment, ModalityType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_table_exists(engine, table_name: str) -> bool:
    """Check if table exists in database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if column exists in table"""
    inspector = inspect(engine)
    if not check_table_exists(engine, table_name):
        return False

    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_add_multimodal_support():
    """Add multimodal support to database"""
    logger.info("Starting multimodal support migration...")

    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        logger.info(f"Connected to database: {settings.DATABASE_URL.split('@')[-1]}")

        # Check if pgvector extension is installed
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if not result.fetchone():
                logger.error("❌ pgvector extension not installed!")
                logger.error("Run: CREATE EXTENSION IF NOT EXISTS vector;")
                return False

        logger.info("✅ pgvector extension found")

        # Create new tables
        logger.info("\n📋 Creating new tables...")

        # Check if media_metadata table exists
        if not check_table_exists(engine, "media_metadata"):
            logger.info("Creating media_metadata table...")
            MediaMetadata.__table__.create(engine)
            logger.info("✅ media_metadata table created")
        else:
            logger.info("⏭️  media_metadata table already exists")

        # Check if transcript_segments table exists
        if not check_table_exists(engine, "transcript_segments"):
            logger.info("Creating transcript_segments table...")
            TranscriptSegment.__table__.create(engine)
            logger.info("✅ transcript_segments table created")
        else:
            logger.info("⏭️  transcript_segments table already exists")

        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info("\n📊 Current database tables:")
        for table in sorted(tables):
            logger.info(f"  - {table}")

        # Create HNSW indexes for vector columns
        logger.info("\n🔍 Creating vector indexes...")

        with engine.begin() as conn:
            # Check if CLIP embedding index exists
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'media_metadata' AND indexname = 'idx_media_clip_embedding'
            """))

            if not result.fetchone():
                logger.info("Creating HNSW index for CLIP embeddings...")
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_media_clip_embedding
                        ON media_metadata
                        USING hnsw (clip_embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """))
                    logger.info("✅ CLIP embedding index created")
                except Exception as e:
                    logger.warning(f"Could not create CLIP index (may already exist): {e}")
            else:
                logger.info("⏭️  CLIP embedding index already exists")

        logger.info("\n✅ Multimodal support migration completed successfully!")
        logger.info("\n📚 New tables added:")
        logger.info("  1. media_metadata - Stores media files metadata (images, audio, video)")
        logger.info("  2. transcript_segments - Stores audio/video transcripts")
        logger.info("\n🎯 Next steps:")
        logger.info("  1. Upload images, audio, or video files")
        logger.info("  2. System will automatically extract and index media")
        logger.info("  3. Use cross-modal search (text query → find images)")

        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def rollback_migration():
    """Rollback multimodal support migration (for testing)"""
    logger.warning("⚠️  Rolling back multimodal support migration...")

    try:
        engine = create_engine(settings.DATABASE_URL)

        with engine.begin() as conn:
            # Drop tables in reverse order (due to foreign keys)
            logger.info("Dropping transcript_segments table...")
            conn.execute(text("DROP TABLE IF EXISTS transcript_segments CASCADE"))

            logger.info("Dropping media_metadata table...")
            conn.execute(text("DROP TABLE IF EXISTS media_metadata CASCADE"))

        logger.info("✅ Rollback completed")
        return True

    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False


def verify_migration():
    """Verify migration was successful"""
    logger.info("\n🔍 Verifying migration...")

    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)

        # Check required tables
        required_tables = ["media_metadata", "transcript_segments"]
        missing_tables = []

        for table in required_tables:
            if check_table_exists(engine, table):
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.error(f"❌ Table '{table}' missing")
                missing_tables.append(table)

        if missing_tables:
            logger.error(f"❌ Verification failed: Missing tables: {missing_tables}")
            return False

        # Check media_metadata columns
        logger.info("\n📋 Checking media_metadata columns...")
        media_columns = {col['name']: col['type'] for col in inspector.get_columns('media_metadata')}

        required_columns = [
            'chunk_id', 'modality', 'media_path', 'clip_embedding',
            'image_width', 'audio_duration_seconds', 'video_duration_seconds',
            'caption', 'ocr_text'
        ]

        for col in required_columns:
            if col in media_columns:
                logger.info(f"  ✅ Column '{col}' exists")
            else:
                logger.warning(f"  ⚠️  Column '{col}' missing")

        logger.info("\n✅ Migration verification completed")
        return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate database for multimodal support")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    parser.add_argument("--verify", action="store_true", help="Verify migration only")

    args = parser.parse_args()

    if args.rollback:
        success = rollback_migration()
    elif args.verify:
        success = verify_migration()
    else:
        success = migrate_add_multimodal_support()
        if success:
            verify_migration()

    sys.exit(0 if success else 1)
