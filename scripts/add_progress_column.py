"""
Add processing_progress column to documents table
Run this once to migrate the existing database
"""

import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from sqlalchemy import Column, Float, text
from core.database import engine

def add_progress_column():
    """Add processing_progress column to documents table"""

    with engine.connect() as conn:
        try:
            # Check if column already exists using SQLite's pragma
            result = conn.execute(text("PRAGMA table_info(documents)"))
            columns = [row[1] for row in result]

            if 'processing_progress' in columns:
                print("✅ Column 'processing_progress' already exists")
                return

            # Add the column with default value
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN processing_progress FLOAT DEFAULT 0.0 NOT NULL
            """))

            conn.commit()
            print("✅ Successfully added 'processing_progress' column to documents table")

        except Exception as e:
            print(f"❌ Error adding column: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("Adding processing_progress column to documents table...")
    add_progress_column()
    print("Migration complete!")
