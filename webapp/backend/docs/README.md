# RAG Backend Documentation

Welcome to the RAG Backend documentation. This directory contains comprehensive guides for setting up, migrating, and optimizing the RAG system.

## 📚 Documentation Index

### Migration & Setup

- **[migration/QUICK_START.md](migration/QUICK_START.md)** - Quick migration guide from SQLite to PostgreSQL
- **[migration/POSTGRESQL_MIGRATION_GUIDE.md](migration/POSTGRESQL_MIGRATION_GUIDE.md)** - Complete step-by-step migration guide
- **[migration/MIGRATION_COMPLETE.md](migration/MIGRATION_COMPLETE.md)** - Migration completion checklist and verification

### Performance & Optimization

- **[VECTOR_SEARCH_OPTIMIZATION.md](VECTOR_SEARCH_OPTIMIZATION.md)** - Vector search performance optimization with pgvector

### Testing

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing guide for the RAG system

## 🛠️ Scripts

All migration and setup scripts are located in the [`../scripts/`](../scripts/) directory:

- **[setup_postgres.sh](../scripts/setup_postgres.sh)** - Automated PostgreSQL installation and configuration
- **[migrate_to_postgres.sh](../scripts/migrate_to_postgres.sh)** - Quick migration script
- **[migrate_sqlite_to_postgres.py](../scripts/migrate_sqlite_to_postgres.py)** - Python migration utility
- **[migrate_data_direct.py](../scripts/migrate_data_direct.py)** - Direct data migration script
- **[migrate_complete.py](../scripts/migrate_complete.py)** - Complete migration verification

## 🚀 Quick Links

### For New Users
1. Start with [../INSTALLATION_GUIDE.md](../../INSTALLATION_GUIDE.md) for initial setup
2. Follow [migration/QUICK_START.md](migration/QUICK_START.md) for PostgreSQL setup
3. Review [TESTING_GUIDE.md](TESTING_GUIDE.md) to verify your installation

### For Existing Users
1. Check [migration/POSTGRESQL_MIGRATION_GUIDE.md](migration/POSTGRESQL_MIGRATION_GUIDE.md) for migration steps
2. See [VECTOR_SEARCH_OPTIMIZATION.md](VECTOR_SEARCH_OPTIMIZATION.md) for performance tuning
3. Verify with [migration/MIGRATION_COMPLETE.md](migration/MIGRATION_COMPLETE.md)

## 🔧 System Requirements

- **PostgreSQL**: 14+ (15+ recommended)
- **pgvector Extension**: 0.5.1+
- **Python**: 3.12+
- **RAM**: 8GB minimum, 16GB recommended

## 📊 Performance Comparison

| Database | Vector Search | Index Type | Speed |
|----------|---------------|------------|-------|
| SQLite | Basic | None | Baseline |
| PostgreSQL + pgvector | Optimized | HNSW | **50x faster** |

## 🆘 Getting Help

If you encounter issues:
1. Check the [troubleshooting section](../../INSTALLATION_GUIDE.md#troubleshooting) in the installation guide
2. Review relevant documentation in this directory
3. Check the backend logs for error messages

## 📝 Contributing

When adding new documentation:
1. Place migration-related docs in `migration/`
2. Place general docs in this directory
3. Update this README.md index
4. Keep all scripts in the `scripts/` directory
