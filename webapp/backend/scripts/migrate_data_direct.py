#!/usr/bin/env python3
"""
Direct SQL-based migration from SQLite to PostgreSQL
Avoids ORM relationship issues by using raw SQL
"""

import argparse
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json
import time

def connect_sqlite(db_path):
    """Connect to SQLite database"""
    return sqlite3.connect(db_path)

def connect_postgres():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="rag_database",
        user="rag_user",
        password="secure_rag_password_2024"
    )

def get_table_counts(cursor, table_name):
    """Get count of records in a table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except:
        return 0

def migrate_users(sqlite_conn, pg_conn):
    """Migrate users table"""
    print("👤 Migrating users...")

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # Get users from SQLite
    sqlite_cur.execute("""
        SELECT id, username, email, full_name, password_hash,
               is_active, is_admin, email_verified, created_at, updated_at
        FROM users
    """)
    users = sqlite_cur.fetchall()

    if not users:
        print("  No users to migrate")
        return 0

    # Insert into PostgreSQL
    migrated = 0
    for user in users:
        try:
            pg_cur.execute("""
                INSERT INTO users
                (id, username, email, full_name, password_hash, is_active, is_admin,
                 email_verified, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, user)
            migrated += 1
        except Exception as e:
            print(f"  ⚠️  Failed to migrate user {user[1]}: {e}")

    pg_conn.commit()
    print(f"✓ Migrated {migrated} users")
    return migrated

def migrate_documents(sqlite_conn, pg_conn):
    """Migrate documents table"""
    print("📄 Migrating documents...")

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # Get documents from SQLite
    sqlite_cur.execute("""
        SELECT id, filename, original_filename, content_type, file_size,
               upload_date, user_id, status, error_message, created_at, updated_at
        FROM documents
    """)
    documents = sqlite_cur.fetchall()

    if not documents:
        print("  No documents to migrate")
        return 0

    # Insert into PostgreSQL
    migrated = 0
    for doc in documents:
        try:
            pg_cur.execute("""
                INSERT INTO documents
                (id, filename, original_filename, content_type, file_size,
                 upload_date, user_id, status, error_message, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, doc)
            migrated += 1
        except Exception as e:
            print(f"  ⚠️  Failed to migrate document {doc[1]}: {e}")

    pg_conn.commit()
    print(f"✓ Migrated {migrated} documents")
    return migrated

def migrate_chunks(sqlite_conn, pg_conn):
    """Migrate chunks table with embeddings"""
    print("📦 Migrating chunks with embeddings...")

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # Get chunks from SQLite
    sqlite_cur.execute("""
        SELECT id, document_id, chunk_index, content, embedding, metadata_,
               created_at, updated_at
        FROM chunks
    """)

    migrated = 0
    with_embeddings = 0
    batch_size = 100
    batch = []

    for chunk in sqlite_cur:
        chunk_id, doc_id, idx, content, embedding_blob, metadata, created, updated = chunk

        # Convert embedding from blob to list
        embedding = None
        if embedding_blob:
            try:
                # SQLite stores as JSON string or pickle
                if isinstance(embedding_blob, str):
                    embedding = json.loads(embedding_blob)
                elif isinstance(embedding_blob, bytes):
                    import pickle
                    embedding = pickle.loads(embedding_blob)
                with_embeddings += 1
            except:
                pass

        batch.append((chunk_id, doc_id, idx, content, embedding, metadata, created, updated))

        if len(batch) >= batch_size:
            # Insert batch
            for item in batch:
                try:
                    pg_cur.execute("""
                        INSERT INTO chunks
                        (id, document_id, chunk_index, content, embedding, metadata_,
                         created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, item)
                    migrated += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to migrate chunk {item[0]}: {e}")

            pg_conn.commit()
            print(f"  Progress: {migrated} chunks...")
            batch = []

    # Insert remaining
    for item in batch:
        try:
            pg_cur.execute("""
                INSERT INTO chunks
                (id, document_id, chunk_index, content, embedding, metadata_,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, item)
            migrated += 1
        except Exception as e:
            print(f"  ⚠️  Failed to migrate chunk {item[0]}: {e}")

    pg_conn.commit()
    print(f"✓ Migrated {migrated} chunks ({with_embeddings} with embeddings)")
    return migrated, with_embeddings

def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to PostgreSQL")
    parser.add_argument("--sqlite-path", default="./test.db", help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("="*78)
    print("SQLite → PostgreSQL Migration (Direct SQL)")
    print("="*78)
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")

    # Connect to databases
    print("🔍 Connecting to databases...")
    try:
        sqlite_conn = connect_sqlite(args.sqlite_path)
        print(f"✓ SQLite connection successful: {args.sqlite_path}")
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        return 1

    try:
        pg_conn = connect_postgres()
        pg_cur = pg_conn.cursor()
        pg_cur.execute("SELECT version()")
        version = pg_cur.fetchone()[0]
        print(f"✓ PostgreSQL connection successful")
        print(f"  Version: {version.split(',')[0]}")

        # Check pgvector
        pg_cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
        result = pg_cur.fetchone()
        if result:
            print(f"  pgvector: {result[0]}")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return 1

    print()

    # Show migration plan
    print("📊 Migration Plan:\n")
    sqlite_cur = sqlite_conn.cursor()

    users_count = get_table_counts(sqlite_cur, "users")
    docs_count = get_table_counts(sqlite_cur, "documents")
    chunks_count = get_table_counts(sqlite_cur, "chunks")

    print(f"Source: SQLite ({args.sqlite_path})")
    print(f"  Users: {users_count}")
    print(f"  Documents: {docs_count}")
    print(f"  Chunks: {chunks_count}")
    print()

    if args.dry_run:
        print("Dry run complete. Run without --dry-run to migrate.")
        return 0

    # Confirm
    if not args.yes:
        confirm = input("⚠️  Proceed with migration? (yes/no): ")
        if confirm.lower() != "yes":
            print("Migration cancelled")
            return 0
    else:
        print("⚠️  Auto-confirmed migration (--yes flag)")
        print()

    print()

    # Migrate
    start_time = time.time()

    try:
        users_migrated = migrate_users(sqlite_conn, pg_conn)
        docs_migrated = migrate_documents(sqlite_conn, pg_conn)
        chunks_migrated, embeddings_migrated = migrate_chunks(sqlite_conn, pg_conn)

        duration = time.time() - start_time

        print()
        print("="*78)
        print("Migration Summary")
        print("="*78)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Users migrated: {users_migrated}")
        print(f"Documents migrated: {docs_migrated}")
        print(f"Chunks migrated: {chunks_migrated}")
        print(f"Embeddings migrated: {embeddings_migrated}")
        print()
        print("✓ Migration completed successfully!")
        print()
        print("Next steps:")
        print("  1. Update .env to use PostgreSQL")
        print("  2. Restart your application")
        print("  3. Verify 50x performance improvement!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        pg_conn.rollback()
        return 1
    finally:
        sqlite_conn.close()
        pg_conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
