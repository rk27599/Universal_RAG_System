#!/usr/bin/env python3
"""
Process stuck files that were uploaded but never processed
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.database import SessionLocal
from app.services.document_service import DocumentProcessingService
from app.models.document import Document
from fastapi import UploadFile
from io import BytesIO

async def process_file(file_path: Path, user_id: int = 1):
    """Process a single file from uploads directory"""
    print(f"Processing: {file_path.name}")

    # Create database session
    db = SessionLocal()

    try:
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()

        # Create UploadFile object
        upload_file = UploadFile(
            filename=file_path.name.split('_', 2)[-1],  # Remove timestamp prefix
            file=BytesIO(content)
        )

        # Process the file
        service = DocumentProcessingService(db, user_id)
        document, error = await service.process_uploaded_file(upload_file)

        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Created document ID: {document.id}")
            print(f"   Status: {document.processing_status}")
            print(f"   Waiting for async processing...")

            # Wait for processing to complete
            for i in range(60):  # Wait up to 60 seconds
                await asyncio.sleep(1)
                db.refresh(document)
                print(f"   [{i+1}s] Status: {document.processing_status}, Chunks: {document.total_chunks}")

                if document.processing_status in ['completed', 'failed']:
                    break

            if document.processing_status == 'completed':
                print(f"✅ Processing completed! {document.total_chunks} chunks created")
            else:
                print(f"⚠️  Still processing after 60s. Check manually.")

    finally:
        db.close()

async def main():
    uploads_dir = Path(__file__).parent / "data" / "uploads"

    # Find all MS docs files
    stuck_files = list(uploads_dir.glob("*all_MS_docs.txt"))

    if not stuck_files:
        print("No stuck files found")
        return

    print(f"Found {len(stuck_files)} stuck files:")
    for f in stuck_files:
        print(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")

    # Process the most recent one
    if stuck_files:
        latest = max(stuck_files, key=lambda p: p.stat().st_mtime)
        await process_file(latest)

if __name__ == "__main__":
    asyncio.run(main())
