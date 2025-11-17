# Universal RAG System - Test Suite

Comprehensive test suite for the Universal RAG System with **~200 tests** covering all components.

## 📊 Test Coverage Overview

### Test Distribution
- **Unit Tests**: ~140 tests (70%) - Individual component testing
- **Integration Tests**: ~40 tests (20%) - Component interaction testing
- **E2E Tests**: ~20 tests (10%) - Full workflow testing

### Coverage by Component

#### ✅ Implemented Tests

**Backend Services** (20+ tests)
- `test_embedding_service_bge.py` - BGE-M3 embeddings (8 tests)
- `test_bm25_retriever.py` - BM25 keyword search (10 tests)
- `test_reranker_service.py` - Cross-encoder reranking (10 tests)
- More service tests to be added...

**LLM Providers** (15+ tests)
- `test_llm_factory.py` - LLM provider factory (6 tests)
- `test_ollama_service.py` - Ollama integration (8 tests)
- `test_vllm_service.py` - vLLM integration (8 tests)

**Core Modules** (15+ tests)
- `test_security.py` - JWT & password hashing (15 tests)

**Database Models** (20+ tests)
- `test_user.py` - User model (10 tests)
- `test_document.py` - Document & Chunk models (15 tests)

**API Integration** (15+ tests)
- `test_auth_api.py` - Authentication endpoints (14 tests)

**Existing E2E Tests**
- `test_enhanced_rag_e2e.py` - Enhanced RAG features
- `test_phase3_integration.py` - Integration & security
- `test_pdf_sample.py` - PDF processing

## 🚀 Running Tests

### Install Dependencies
```bash
# Install test dependencies
pip install -r webapp/backend/requirements.txt

# Additional test tools
pip install pytest-cov pytest-xdist pytest-html
```

### Run All Tests
```bash
# Run all tests
cd webapp/backend
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run in parallel (faster)
pytest tests/ -n auto

# Run with detailed output
pytest tests/ -v --tb=short
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Specific test file
pytest tests/unit/services/test_embedding_service_bge.py

# Specific test
pytest tests/unit/services/test_embedding_service_bge.py::TestBGEEmbeddingService::test_embed_text

# Tests matching pattern
pytest -k "test_embedding"
```

### Run Tests by Marker

```bash
# Async tests only
pytest -m asyncio

# Integration tests
pytest -m integration

# Unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

## 📁 Test Structure

```
webapp/backend/tests/
├── conftest.py                          # Pytest configuration & fixtures
├── pytest.ini                           # Pytest settings
├── README.md                            # This file
│
├── fixtures/                            # Test fixtures (shared data)
│   ├── database.py
│   ├── auth.py
│   ├── documents.py
│   ├── models.py
│   └── embeddings.py
│
├── mocks/                               # Mock services
│   ├── ollama_mock.py
│   ├── vllm_mock.py
│   └── redis_mock.py
│
├── test_data/                           # Test data files
│   ├── pdfs/
│   ├── html/
│   ├── embeddings/
│   └── responses/
│
├── unit/                                # Unit tests (70%)
│   ├── services/                        # Service tests
│   │   ├── test_embedding_service_bge.py
│   │   ├── test_bm25_retriever.py
│   │   ├── test_reranker_service.py
│   │   └── ...
│   ├── llm_providers/                   # LLM provider tests
│   │   ├── test_ollama_service.py
│   │   ├── test_vllm_service.py
│   │   └── test_llm_factory.py
│   ├── core/                            # Core module tests
│   │   ├── test_security.py
│   │   ├── test_config.py
│   │   └── test_database.py
│   └── models/                          # Database model tests
│       ├── test_user.py
│       ├── test_document.py
│       └── test_conversation.py
│
├── integration/                         # Integration tests (20%)
│   ├── api/                             # API endpoint tests
│   │   ├── test_auth_api.py
│   │   ├── test_documents_api.py
│   │   └── test_chat_api.py
│   ├── services/                        # Service integration
│   │   └── test_rag_pipeline.py
│   └── database/                        # Database workflows
│       └── test_user_workflows.py
│
└── e2e/                                 # E2E tests (10%)
    ├── test_enhanced_rag_e2e.py         # ✅ Existing
    ├── test_phase3_integration.py       # ✅ Existing
    └── test_pdf_sample.py               # ✅ Existing
```

## 🔧 Test Infrastructure

### Fixtures (conftest.py)

**Database Fixtures**
- `test_db_engine` - In-memory SQLite engine
- `test_db_session` - Test database session
- `test_db` - Alias for test_db_session

**User Fixtures**
- `test_user` - Standard test user
- `test_admin_user` - Admin test user
- `test_auth_token` - JWT token for authentication

**Document Fixtures**
- `test_document` - Test PDF document
- `test_document_chunks` - Document chunks with embeddings

**Conversation Fixtures**
- `test_conversation` - Test conversation
- `test_messages` - Test messages (user + assistant)

**Mock Service Fixtures**
- `mock_ollama_service` - Mock Ollama API
- `mock_vllm_service` - Mock vLLM API
- `mock_embedding_service` - Mock embedding generation
- `mock_redis_client` - Mock Redis operations

### Test Data

**Sample Files**
- `test_data/html/simple.html` - Simple HTML for scraping tests
- `test_data/responses/ollama_responses.json` - Mock Ollama responses
- `test_data/responses/vllm_responses.json` - Mock vLLM responses

**Generated Data**
- Sample embeddings (1024-dim vectors)
- Sample PDF files (simple, with tables, with images)
- Sample text chunks

## 📈 Coverage Goals

### Current Status
- **Unit Tests**: 70+ tests implemented
- **Integration Tests**: 15+ tests implemented
- **E2E Tests**: 3 existing tests

### Target Coverage
- **Code Coverage**: 80%+ for critical paths
- **Service Coverage**: 100% of public APIs tested
- **API Coverage**: All endpoints with success/failure cases
- **Edge Cases**: Empty inputs, timeouts, errors

## 🧪 Writing New Tests

### Unit Test Template
```python
"""
Unit Tests for MyService
Brief description
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.my_service import MyService


class TestMyService:
    """Test MyService"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return MyService()

    def test_basic_functionality(self, service):
        """Test basic functionality"""
        result = service.do_something()
        assert result is not None

    def test_error_handling(self, service):
        """Test error handling"""
        with pytest.raises(ValueError):
            service.do_something(invalid_input)
```

### Integration Test Template
```python
"""
Integration Tests for MyAPI
Brief description
"""

import pytest
from fastapi.testclient import TestClient

class TestMyAPI:
    """Test MyAPI"""

    @pytest.fixture
    def client(self, test_db_session):
        """Create test client"""
        # Setup client with DB override
        pass

    def test_endpoint_success(self, client):
        """Test successful API call"""
        response = client.get("/api/my-endpoint")
        assert response.status_code == 200
```

## 🐛 Debugging Tests

### Run with Debug Output
```bash
# Show print statements
pytest tests/ -s

# Show full traceback
pytest tests/ --tb=long

# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb
```

### Common Issues

**Import Errors**
- Ensure `sys.path.insert(0, ...)` is correct
- Check that `__init__.py` files exist

**Database Errors**
- Use `test_db_session` fixture for clean database state
- Check that models are imported before running tests

**Async Test Errors**
- Use `@pytest.mark.asyncio` decorator
- Ensure `pytest-asyncio` is installed

## 📊 Continuous Integration

### GitHub Actions (Planned)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/ --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 🎯 Next Steps

### Priority Tests to Implement
1. ✅ Core service unit tests (embeddings, retrieval, LLM)
2. ✅ Database model tests
3. ✅ Authentication API tests
4. 🔄 Document API tests (in progress)
5. 🔄 Chat API tests (in progress)
6. ⏳ RAG pipeline integration tests
7. ⏳ Performance benchmarks
8. ⏳ Security hardening tests

### Future Enhancements
- Load testing with locust
- Security scanning integration
- Performance regression detection
- Automated test data generation
- Visual regression testing (frontend)

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/core/testing.html)
- [Async Testing](https://pytest-asyncio.readthedocs.io/)

---

**Last Updated**: 2025-11-17
**Test Count**: 70+ (growing to 200+)
**Coverage**: In Progress (targeting 80%+)
