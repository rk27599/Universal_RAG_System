#!/usr/bin/env python3
"""
Complete SQLite to PostgreSQL Migration
Handles schema differences and data type conversions
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json
import time
import sys

def migrate_users(sqlite_conn, pg_conn):
    """Migrate users with proper type casting"""
    print("👤 Migrating users...")

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # Get users from SQLite
    sqlite_cur.execute("SELECT * FROM users")
    columns = [description[0] for description in sqlite_cur.description]
    users = sqlite_cur.fetchall()

    if not users:
        print("  No users to migrate")
        return 0

    migrated = 0
    for user in users:
        user_dict = dict(zip(columns, user))

        # Map SQLite schema to PostgreSQL schema
        try:
            pg_cur.execute("""
                INSERT INTO users (
                    id, username, email, password_hash,
                    is_active, is_admin, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash
            """, (
                user_dict['id'],
                user_dict.get('username', user_dict.get('email', 'user')),
                user_dict['email'],
                user_dict.get('hashed_password', user_dict.get('password_hash', '')),
                bool(user_dict.get('is_active', 1)),
                bool(user_dict.get('is_admin', 0)),
                user_dict.get('created_at'),
                user_dict.get('updated_at')
            ))
            migrated += 1
        except Exception as e:
            print(f"  ⚠️  Failed to migrate user {user_dict.get('email')}: {e}")

    pg_conn.commit()
    print(f"✓ Migrated {migrated} users")
    return migrated

def migrate_documents(sqlite_conn, pg_conn):
    """Migrate documents with schema mapping"""
    print("📄 Migrating documents...")

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # Get documents from SQLite
    sqlite_cur.execute("SELECT * FROM documents")
    columns = [description[0] for description in sqlite_cur.description]
    documents = sqlite_cur.fetchall()

    if not documents:
        print("  No documents to migrate")
        return 0

    migrated = 0
    for doc in documents:
        doc_dict = dict(zip(columns, doc))

        try:
            # Map column names (SQLite might use 'filename', PostgreSQL uses 'file_path')
            pg_cur.execute("""
                INSERT INTO documents (
                    id, file_path, original_name, content_type, file_size,
                    upload_date, user_id, status, error_message,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                doc_dict['id'],
                doc_dict.get('filename', doc_dict.get('file_path', '')),
                doc_dict.get('original_filename', doc_dict.get('original_name', '')),
                doc_dict.get('content_type', 'application/octet-stream'),
                doc_dict.get('file_size', 0),
                doc_dict.get('upload_date'),
                doc_dict.get('user_id'),
                doc_dict.get('status', 'completed'),
                doc_dict.get('error_message'),
                doc_dict.get('created_at'),
                doc_dict.get('updated_at')
            ))
            migrated += 1
        except Exception as e:
            print(f"  ⚠️  Failed to migrate document {doc_dict.get('filename')}: {e}")
            # Print schema info for debugging
            if migrated == 0:
                print(f"  Available columns: {list(doc_dict.keys())}")

    pg_conn.commit()
    print(f"✓ Migrated {migrated} documents")
    return migrated

def migrate_chunks(sqlite_conn, pg_conn):
    """Migrate chunks with embeddings"""
    print("📦 Migrating chunks with embeddings...")

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # Get chunks from SQLite
    sqlite_cur.execute("SELECT * FROM chunks")
    columns = [description[0] for description in sqlite_cur.description]

    migrated = 0
    with_embeddings = 0
    batch_size = 100
    batch = []

    for chunk in sqlite_cur:
        chunk_dict = dict(zip(columns, chunk))

        # Convert embedding
        embedding = None
        embedding_blob = chunk_dict.get('embedding')
        if embedding_blob:
            try:
                if isinstance(embedding_blob, str):
                    embedding = json.loads(embedding_blob)
                elif isinstance(embedding_blob, bytes):
                    import pickle
                    embedding = pickle.loads(embedding_blob)
                with_embeddings += 1
            except:
                pass

        batch.append((
            chunk_dict['id'],
            chunk_dict['document_id'],
            chunk_dict.get('chunk_index', 0),
            chunk_dict['content'],
            embedding,
            chunk_dict.get('metadata_', chunk_dict.get('metadata')),
            chunk_dict.get('created_at'),
            chunk_dict.get('updated_at')
        ))

        if len(batch) >= batch_size:
            # Insert batch
            for item in batch:
                try:
                    pg_cur.execute("""
                        INSERT INTO chunks (
                            id, document_id, chunk_index, content, embedding,
                            metadata_, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, item)
                    migrated += 1
                except Exception as e:
                    if migrated == 0:
                        print(f"  ⚠️  Error: {e}")

            pg_conn.commit()
            print(f"  Progress: {migrated} chunks...")
            batch = []

    # Insert remaining
    for item in batch:
        try:
            pg_cur.execute("""
                INSERT INTO chunks (
                    id, document_id, chunk_index, content, embedding,
                    metadata_, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, item)
            migrated += 1
        except:
            pass

    pg_conn.commit()
    print(f"✓ Migrated {migrated} chunks ({with_embeddings} with embeddings)")
    return migrated, with_embeddings

def main():
    print("="*78)
    print("Complete SQLite → PostgreSQL Migration")
    print("="*78)
    print()

    # Connect
    print("🔍 Connecting to databases...")
    sqlite_conn = sqlite3.connect("./test.db")
    print("✓ SQLite: ./test.db")

    pg_conn = psycopg2.connect(
        host="localhost", port=5432,
        database="rag_database", user="rag_user",
        password="secure_rag_password_2024"
    )
    print("✓ PostgreSQL: rag_database")
    print()

    # Show plan
    sqlite_cur = sqlite_conn.cursor()
    users_count = sqlite_cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    docs_count = sqlite_cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunks_count = sqlite_cur.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    print("📊 Migration Plan:")
    print(f"  Users: {users_count}")
    print(f"  Documents: {docs_count}")
    print(f"  Chunks: {chunks_count}")
    print()

    # Migrate
    start = time.time()

    users_migrated = migrate_users(sqlite_conn, pg_conn)
    docs_migrated = migrate_documents(sqlite_conn, pg_conn)
    chunks_migrated, embeddings_migrated = migrate_chunks(sqlite_conn, pg_conn)

    duration = time.time() - start

    # Summary
    print()
    print("="*78)
    print("✅ Migration Complete!")
    print("="*78)
    print(f"Duration: {duration:.2f}s")
    print(f"Users: {users_migrated}")
    print(f"Documents: {docs_migrated}")
    print(f"Chunks: {chunks_migrated} ({embeddings_migrated} with embeddings)")
    print()
    print("🚀 Next: Restart backend to use PostgreSQL!")

    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
