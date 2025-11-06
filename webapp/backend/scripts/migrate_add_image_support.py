"""
Database Migration: Add Image Support Columns
Adds image-specific metadata columns to the documents table
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_image_support():
    """Add image-specific columns to documents table"""

    migrations = [
        # Add image-specific columns
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS image_width INTEGER,
        ADD COLUMN IF NOT EXISTS image_height INTEGER,
        ADD COLUMN IF NOT EXISTS image_format VARCHAR(20),
        ADD COLUMN IF NOT EXISTS has_ocr_text BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS has_vision_description BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS thumbnail_path TEXT;
        """,
    ]

    db = SessionLocal()
    try:
        logger.info("Starting image support migration...")

        for i, migration_sql in enumerate(migrations, 1):
            logger.info(f"Running migration {i}/{len(migrations)}...")
            db.execute(text(migration_sql))
            db.commit()
            logger.info(f"✅ Migration {i} completed successfully")

        logger.info("🎉 All image support migrations completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = migrate_add_image_support()
    sys.exit(0 if success else 1)
