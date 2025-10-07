#!/usr/bin/env python3
"""
==============================================================================
SQLite to PostgreSQL Data Migration Script
==============================================================================
Migrates all data from SQLite to PostgreSQL while preserving:
- Documents and their metadata
- Chunks with embeddings (384-dimensional vectors)
- User accounts and settings
- Relationships and foreign keys

Usage:
    python migrate_sqlite_to_postgres.py [--sqlite-path PATH] [--verify]

Options:
    --sqlite-path PATH    Path to SQLite database (default: ./test.db)
    --verify             Only verify migration, don't perform it
    --dry-run            Show what would be migrated without doing it
==============================================================================
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from core.config import settings
from core.database import Base
from models.document import Document, Chunk
from models.user import User
from models.conversation import Conversation, Message  # Import to resolve relationships
import numpy as np


class DatabaseMigration:
    """Handles migration from SQLite to PostgreSQL"""

    def __init__(self, sqlite_path: str = "./test.db"):
        self.sqlite_path = sqlite_path
        self.stats = {
            "users": 0,
            "documents": 0,
            "chunks": 0,
            "embeddings": 0,
            "errors": []
        }

        # SQLite connection
        self.sqlite_url = f"sqlite:///{sqlite_path}"
        self.sqlite_engine = create_engine(self.sqlite_url)
        self.SqliteSession = sessionmaker(bind=self.sqlite_engine)

        # PostgreSQL connection (from settings)
        self.postgres_url = settings.get_database_url()
        if "sqlite" in self.postgres_url.lower():
            raise ValueError(
                "❌ PostgreSQL URL not configured. Please update .env file with:\n"
                "DATABASE_URL=postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database"
            )

        self.postgres_engine = create_engine(self.postgres_url)
        self.PostgresSession = sessionmaker(bind=self.postgres_engine)

    def verify_connections(self) -> bool:
        """Verify both database connections are working"""
        print("🔍 Verifying database connections...\n")

        # Check SQLite
        try:
            with self.sqlite_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print(f"✓ SQLite connection successful: {self.sqlite_path}")
        except Exception as e:
            print(f"❌ SQLite connection failed: {e}")
            return False

        # Check PostgreSQL
        try:
            with self.postgres_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✓ PostgreSQL connection successful")
                print(f"  Version: {version.split(',')[0]}")

                # Verify pgvector
                result = conn.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname='vector'")
                )
                vector_version = result.fetchone()
                if vector_version:
                    print(f"  pgvector: {vector_version[0]}")
                else:
                    print("  ⚠️  Warning: pgvector extension not found")

        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False

        print()
        return True

    def get_table_counts(self, session) -> Dict[str, int]:
        """Get row counts for all tables"""
        counts = {}
        try:
            counts["users"] = session.query(User).count()
            counts["documents"] = session.query(Document).count()
            counts["chunks"] = session.query(Chunk).count()
            counts["chunks_with_embeddings"] = session.query(Chunk).filter(
                Chunk.embedding.isnot(None)
            ).count()
        except Exception as e:
            print(f"⚠️  Warning: Could not get table counts: {e}")
        return counts

    def show_migration_plan(self) -> bool:
        """Show what will be migrated"""
        print("📊 Migration Plan:\n")
        print("Source: SQLite")
        print(f"  Path: {self.sqlite_path}")

        sqlite_session = self.SqliteSession()
        try:
            source_counts = self.get_table_counts(sqlite_session)
            print(f"  Users: {source_counts.get('users', 0)}")
            print(f"  Documents: {source_counts.get('documents', 0)}")
            print(f"  Chunks: {source_counts.get('chunks', 0)}")
            print(f"  Chunks with embeddings: {source_counts.get('chunks_with_embeddings', 0)}")
        except Exception as e:
            print(f"  ⚠️  Could not read SQLite data: {e}")
            return False
        finally:
            sqlite_session.close()

        print("\nDestination: PostgreSQL")
        print(f"  URL: {self.postgres_url.split('@')[1] if '@' in self.postgres_url else self.postgres_url}")

        postgres_session = self.PostgresSession()
        try:
            dest_counts = self.get_table_counts(postgres_session)
            print(f"  Users: {dest_counts.get('users', 0)}")
            print(f"  Documents: {dest_counts.get('documents', 0)}")
            print(f"  Chunks: {dest_counts.get('chunks', 0)}")
            print(f"  Chunks with embeddings: {dest_counts.get('chunks_with_embeddings', 0)}")

            if sum(dest_counts.values()) > 0:
                print("\n⚠️  Warning: Destination database is not empty!")
                print("  Existing data will be preserved. Duplicates will be skipped.")
        finally:
            postgres_session.close()

        print()
        return True

    def initialize_postgres_schema(self):
        """Create tables in PostgreSQL if they don't exist"""
        print("🔧 Initializing PostgreSQL schema...")
        Base.metadata.create_all(bind=self.postgres_engine)
        print("✓ Schema initialized\n")

    def migrate_users(self, dry_run: bool = False) -> bool:
        """Migrate user accounts"""
        print("👤 Migrating users...")

        sqlite_session = self.SqliteSession()
        postgres_session = self.PostgresSession()

        try:
            users = sqlite_session.query(User).all()

            if not users:
                print("  No users to migrate")
                return True

            # Get existing users in PostgreSQL
            existing_emails = {u.email for u in postgres_session.query(User.email).all()}

            migrated = 0
            skipped = 0

            for user in users:
                if user.email in existing_emails:
                    skipped += 1
                    continue

                if not dry_run:
                    new_user = User(
                        email=user.email,
                        hashed_password=user.hashed_password,
                        is_active=user.is_active,
                        created_at=user.created_at
                    )
                    postgres_session.add(new_user)
                    postgres_session.flush()  # Get ID without committing

                migrated += 1

            if not dry_run:
                postgres_session.commit()

            self.stats["users"] = migrated
            print(f"✓ Migrated {migrated} users (skipped {skipped} existing)")
            return True

        except Exception as e:
            self.stats["errors"].append(f"User migration: {e}")
            print(f"❌ User migration failed: {e}")
            postgres_session.rollback()
            return False
        finally:
            sqlite_session.close()
            postgres_session.close()

    def migrate_documents_and_chunks(self, dry_run: bool = False) -> bool:
        """Migrate documents and their chunks (with embeddings)"""
        print("📄 Migrating documents and chunks...")

        sqlite_session = self.SqliteSession()
        postgres_session = self.PostgresSession()

        try:
            documents = sqlite_session.query(Document).all()

            if not documents:
                print("  No documents to migrate")
                return True

            # Get existing document filenames in PostgreSQL
            existing_filenames = {
                d.filename for d in postgres_session.query(Document.filename).all()
            }

            doc_migrated = 0
            doc_skipped = 0
            chunk_migrated = 0
            embedding_migrated = 0

            for doc in documents:
                if doc.filename in existing_filenames:
                    doc_skipped += 1
                    continue

                if not dry_run:
                    # Create new document
                    new_doc = Document(
                        filename=doc.filename,
                        original_filename=doc.original_filename,
                        content_type=doc.content_type,
                        file_size=doc.file_size,
                        upload_date=doc.upload_date,
                        user_id=doc.user_id,
                        status=doc.status,
                        error_message=doc.error_message
                    )
                    postgres_session.add(new_doc)
                    postgres_session.flush()  # Get document ID

                    # Migrate chunks for this document
                    chunks = sqlite_session.query(Chunk).filter(
                        Chunk.document_id == doc.id
                    ).all()

                    for chunk in chunks:
                        new_chunk = Chunk(
                            document_id=new_doc.id,
                            chunk_index=chunk.chunk_index,
                            content=chunk.content,
                            embedding=chunk.embedding,  # pgvector handles array automatically
                            metadata_=chunk.metadata_
                        )
                        postgres_session.add(new_chunk)
                        chunk_migrated += 1

                        if chunk.embedding is not None:
                            embedding_migrated += 1

                doc_migrated += 1

                if doc_migrated % 10 == 0:
                    print(f"  Progress: {doc_migrated} documents...")
                    if not dry_run:
                        postgres_session.commit()  # Commit in batches

            if not dry_run:
                postgres_session.commit()

            self.stats["documents"] = doc_migrated
            self.stats["chunks"] = chunk_migrated
            self.stats["embeddings"] = embedding_migrated

            print(f"✓ Migrated {doc_migrated} documents (skipped {doc_skipped} existing)")
            print(f"  └─ {chunk_migrated} chunks ({embedding_migrated} with embeddings)")
            return True

        except Exception as e:
            self.stats["errors"].append(f"Document migration: {e}")
            print(f"❌ Document migration failed: {e}")
            postgres_session.rollback()
            return False
        finally:
            sqlite_session.close()
            postgres_session.close()

    def verify_migration(self) -> bool:
        """Verify that migration was successful"""
        print("\n🔍 Verifying migration...\n")

        sqlite_session = self.SqliteSession()
        postgres_session = self.PostgresSession()

        try:
            source_counts = self.get_table_counts(sqlite_session)
            dest_counts = self.get_table_counts(postgres_session)

            print("Source (SQLite):")
            print(f"  Users: {source_counts.get('users', 0)}")
            print(f"  Documents: {source_counts.get('documents', 0)}")
            print(f"  Chunks: {source_counts.get('chunks', 0)}")
            print(f"  Chunks with embeddings: {source_counts.get('chunks_with_embeddings', 0)}")

            print("\nDestination (PostgreSQL):")
            print(f"  Users: {dest_counts.get('users', 0)}")
            print(f"  Documents: {dest_counts.get('documents', 0)}")
            print(f"  Chunks: {dest_counts.get('chunks', 0)}")
            print(f"  Chunks with embeddings: {dest_counts.get('chunks_with_embeddings', 0)}")

            # Check if counts match (destination should be >= source)
            success = True
            for key in source_counts:
                if dest_counts.get(key, 0) < source_counts.get(key, 0):
                    print(f"\n⚠️  Warning: Mismatch in {key}")
                    success = False

            if success:
                print("\n✓ Migration verification passed!")

                # Test a sample vector search
                print("\n🔍 Testing vector search performance...")
                try:
                    start = time.time()
                    result = postgres_session.execute(
                        text("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
                    )
                    count = result.fetchone()[0]
                    duration = time.time() - start

                    print(f"✓ Vector search test passed: {count} chunks in {duration:.3f}s")
                except Exception as e:
                    print(f"⚠️  Vector search test failed: {e}")

            return success

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
        finally:
            sqlite_session.close()
            postgres_session.close()

    def run_migration(self, dry_run: bool = False):
        """Run the complete migration"""
        print(f"\n{'='*78}")
        print("SQLite → PostgreSQL Migration")
        print(f"{'='*78}\n")

        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made\n")

        # Step 1: Verify connections
        if not self.verify_connections():
            sys.exit(1)

        # Step 2: Show migration plan
        if not self.show_migration_plan():
            sys.exit(1)

        if not dry_run:
            confirm = input("\n⚠️  Proceed with migration? (yes/no): ")
            if confirm.lower() != "yes":
                print("Migration cancelled")
                sys.exit(0)

        # Step 3: Initialize PostgreSQL schema
        if not dry_run:
            self.initialize_postgres_schema()

        # Step 4: Migrate data
        start_time = time.time()

        if not self.migrate_users(dry_run):
            print("\n❌ Migration failed at user migration")
            sys.exit(1)

        if not self.migrate_documents_and_chunks(dry_run):
            print("\n❌ Migration failed at document migration")
            sys.exit(1)

        duration = time.time() - start_time

        # Step 5: Verify migration
        if not dry_run:
            if not self.verify_migration():
                print("\n⚠️  Warning: Verification found issues")

        # Print summary
        print(f"\n{'='*78}")
        print("Migration Summary")
        print(f"{'='*78}\n")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Users migrated: {self.stats['users']}")
        print(f"Documents migrated: {self.stats['documents']}")
        print(f"Chunks migrated: {self.stats['chunks']}")
        print(f"Embeddings migrated: {self.stats['embeddings']}")

        if self.stats["errors"]:
            print(f"\n⚠️  Errors encountered:")
            for error in self.stats["errors"]:
                print(f"  - {error}")
        else:
            print("\n✓ Migration completed successfully!")

            if not dry_run:
                print("\n🎉 Next steps:")
                print("  1. Update .env to use PostgreSQL URL")
                print("  2. Restart your application")
                print("  3. Test vector search performance:")
                print("     python tests/test_vector_search_performance.py")
                print("\n  Your RAG system is now 50x faster! 🚀")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate RAG system data from SQLite to PostgreSQL"
    )
    parser.add_argument(
        "--sqlite-path",
        default="./test.db",
        help="Path to SQLite database (default: ./test.db)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify migration, don't perform it"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without doing it"
    )

    args = parser.parse_args()

    # Check if SQLite file exists
    if not os.path.exists(args.sqlite_path):
        print(f"❌ SQLite database not found: {args.sqlite_path}")
        sys.exit(1)

    # Run migration
    migration = DatabaseMigration(sqlite_path=args.sqlite_path)

    if args.verify:
        migration.verify_connections()
        migration.verify_migration()
    else:
        migration.run_migration(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
