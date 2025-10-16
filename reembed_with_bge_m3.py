#!/usr/bin/env python3
"""
Re-embed all chunks with BGE-M3 (1024 dimensions)
Replaces old all-MiniLM-L6-v2 embeddings (384 dimensions) with better quality BGE-M3
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "webapp" / "backend"))

from services.embedding_service_bge import BGEEmbeddingService
from core.database import SessionLocal
from sqlalchemy import text, func

def reembed_all_chunks():
    """Re-embed all existing chunks with BGE-M3"""

    print("="*70)
    print("BGE-M3 RE-EMBEDDING SCRIPT")
    print("="*70)
    print()

    # Initialize BGE-M3 embedding service
    print("🚀 Initializing BGE-M3 embedding service...")
    embedding_service = BGEEmbeddingService(use_fp16=True)
    embedding_service.load_model()
    print(f"✅ Model loaded: {embedding_service.model_name}")
    print(f"📊 Embedding dimension: {embedding_service.embedding_dimension}")
    print()

    # Get database session (avoid model imports)
    db = SessionLocal()

    try:
        # Count total chunks with existing embeddings
        result = db.execute(text("""
            SELECT COUNT(*) FROM chunks
            WHERE embedding IS NOT NULL
        """))
        total_chunks = result.scalar()

        print(f"📦 Total chunks to re-embed: {total_chunks:,}")
        print()

        if total_chunks == 0:
            print("❌ No chunks found with existing embeddings")
            return

        # Process in batches
        batch_size = 12  # BGE-M3 recommended batch size
        processed = 0
        start_time = time.time()

        while processed < total_chunks:
            # Fetch batch of chunks that need re-embedding
            result = db.execute(text("""
                SELECT id, content
                FROM chunks
                WHERE embedding IS NOT NULL
                  AND embedding_new IS NULL
                LIMIT :batch_size
            """), {"batch_size": batch_size})

            chunks = result.fetchall()

            if not chunks:
                break

            # Extract texts and IDs
            chunk_ids = [row[0] for row in chunks]
            texts = [row[1] for row in chunks]

            # Generate BGE-M3 embeddings
            embeddings = embedding_service.generate_embeddings_batch(texts, batch_size=len(texts))

            # Update chunks with new embeddings
            success_count = 0
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                if embedding:
                    db.execute(text("""
                        UPDATE chunks
                        SET embedding_new = :embedding,
                            embedding_model_new = :model
                        WHERE id = :chunk_id
                    """), {
                        "embedding": embedding,
                        "model": "BAAI/bge-m3",
                        "chunk_id": chunk_id
                    })
                    success_count += 1

            db.commit()
            processed += success_count

            # Progress update
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = total_chunks - processed
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60

            progress_pct = (processed / total_chunks) * 100
            print(f"⏳ Progress: {processed:,}/{total_chunks:,} ({progress_pct:.1f}%) | "
                  f"Rate: {rate:.1f} chunks/sec | ETA: {eta_minutes:.1f} min")

        total_time = time.time() - start_time
        print()
        print("="*70)
        print(f"✅ RE-EMBEDDING COMPLETE!")
        print(f"📊 Total chunks processed: {processed:,}")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"📈 Average rate: {processed/total_time:.1f} chunks/second")
        print("="*70)
        print()
        print("🔄 Next steps:")
        print("1. Test query quality with new embeddings")
        print("2. Update embedding_service.py to use BGE-M3 by default")
        print("3. Update search queries to use 'embedding_new' column")
        print("4. Once validated, drop old 'embedding' column")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reembed_all_chunks()
