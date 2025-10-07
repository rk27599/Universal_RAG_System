# Universal RAG System for Any Website

An advanced **Retrieval-Augmented Generation (RAG) system** that works with **any website**. Features structure-aware web scraping, semantic chunking, enhanced TF-IDF retrieval, intelligent caching, and local LLM integration via Ollama.

## 🚀 Features

- **🌍 Universal Compatibility**: Works with **any website** automatically - documentation, blogs, APIs, etc.
- **📂 Local File Processing**: Process HTML files directly with async performance
- **🏗️ Structure-Aware Scraping**: Preserves HTML hierarchy (h1, h2, h3) and document structure
- **🧠 Semantic Chunking**: Respects content sections vs random word splits
- **🔍 Enhanced Retrieval**: High similarity scores (0.6+ typical vs 0.3 legacy systems)
- **📊 Rich Metadata**: Page titles, section hierarchy, content types, domain information
- **⚡ Dual Scraper Support**: Both sync (reliable) and async (3-5x faster) scrapers
- **🔄 Mixed Source Processing**: Combine web scraping + local files in single pipeline
- **💾 Smart Caching**: Content-based caching with 40-60% hit rates
- **🚀 High Performance**: Concurrent processing with configurable limits
- **🤖 Local LLM Integration**: Works with Ollama for complete text generation
- **🚦 Respectful Crawling**: Honors robots.txt, implements rate limiting, same-domain filtering

## 📋 Requirements

- **Python 3.12+** (migrated from 3.10 - see performance improvements below)
- Dependencies listed in `requirements.txt`
- Optional: Ollama for full text generation capabilities

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install and start Ollama for full generation:
```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull mistral
```

## 🚀 Quick Start

### Basic Usage Example
```bash
python examples/basic_usage.py
```

### Interactive Jupyter Notebook
```bash
jupyter notebook notebooks/RAG_HTML.ipynb
# or
jupyter lab notebooks/RAG_HTML.ipynb
```

### Custom Usage with Any Website
```python
from src.rag_system import RAGSystem

# Initialize system
rag_system = RAGSystem()

# Scrape and process any website
success = rag_system.scrape_and_process_website(
    start_urls=["https://docs.python.org/3/"],
    max_pages=15,
    output_file="data/python_docs.json"
)

# Test retrieval only
result = rag_system.demo_query("How to define functions in Python?", top_k=3)

# Full generation with Ollama (requires ollama serve)
answer = rag_system.rag_query("How to define functions in Python?", top_k=3, model="mistral")
print(answer)
```

### High-Performance Async Scraping
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

async def fast_scrape():
    # Configure for high performance
    config = ScrapingConfig(
        concurrent_limit=6,
        max_pages=50,
        requests_per_second=8.0
    )

    async with AsyncWebScraper(config) as scraper:
        results = await scraper.scrape_website_async([
            "https://docs.python.org/3/"
        ])

        print(f"✅ Processed {len(results['documents'])} pages")
        print(f"📊 Generated {len(results['semantic_chunks'])} chunks")

# Run async scraping
success = asyncio.run(fast_scrape())
```

### Local File Processing
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper

# Process local HTML files with high performance
async def process_local_docs():
    # Using the new static method for easy access
    results = await AsyncWebScraper.process_local_files_fast(
        file_paths=[
            "./docs/user-guide.html",
            "./docs/api-reference.html",
            "./docs/tutorials.html"
        ],
        output_file="data/local_documentation.json",
        concurrent_limit=4
    )

    metadata = results["metadata"]
    print(f"✅ Processed {metadata['total_files']} local files")
    print(f"📊 Created {metadata['total_chunks']} semantic chunks")
    print(f"⚡ Processing rate: {metadata['files_per_second']:.1f} files/sec")

    return results

# Process local documentation
results = asyncio.run(process_local_docs())
```

### Mixed Source Processing
```python
from src.web_scraper import WebScraper

# Process both web content and local files together
scraper = WebScraper()

results = scraper.process_mixed_sources(
    web_urls=["https://docs.python.org/3/tutorial/"],
    local_files=["./docs/custom-guide.html", "./docs/internal-api.html"],
    output_file="data/comprehensive_docs.json",
    max_pages=20
)

print(f"📊 Mixed Processing Results:")
print(f"  Total documents: {results['metadata']['total_documents']}")
print(f"  Semantic chunks: {results['metadata']['total_chunks']}")
print(f"  Sources: Web + Local files")
```

## 📁 Project Structure

This repository contains **two main components**:

### 1. Core RAG Library (Main Focus) - Document Parsing & RAG
```
├── README.md                         # This file
├── CLAUDE.md                        # AI assistant guide & detailed docs
├── LICENSE                          # Open source license
├── requirements.txt                 # Core library dependencies
│
├── src/                             # Core RAG library source code
│   ├── web_scraper.py              # Synchronous web scraper (643 lines)
│   ├── async_web_scraper.py        # Async scraper (751 lines, 3-5x faster)
│   └── rag_system.py               # Main RAG system (639 lines)
│
├── docs/                            # Core RAG documentation
│   ├── README.md                   # Documentation index
│   ├── api/                        # API reference
│   │   ├── rag_system.md           # RAG system API
│   │   ├── web_scraper.md          # Scraper API
│   │   └── async_web_scraper.md    # Async scraper API
│   ├── guides/                     # User guides
│   │   ├── getting-started.md      # Getting started guide
│   │   ├── performance.md          # Performance optimization
│   │   └── troubleshooting.md      # Troubleshooting guide
│   ├── architecture.md             # System architecture
│   ├── benchmarks/                 # Performance benchmarks
│   └── security/                   # Security reports
│
├── examples/                        # Usage examples
│   ├── basic_usage.py              # Simple example
│   ├── advanced_usage.py           # Advanced features
│   ├── benchmarking.py             # Performance testing
│   └── generic_usage.py            # Generic system demo
│
├── tests/                           # Core RAG tests
│   ├── test_rag_system.py          # RAG system tests
│   ├── test_scraper.py             # Web scraper tests
│   ├── test_async_local_files.py   # Async file processing tests
│   ├── test_local_html.py          # Local HTML tests
│   └── test_generic_system.py      # Generic system tests
│
├── scripts/                         # Utility scripts
│   ├── add_progress_column.py      # Database utility
│   └── process_stuck_files.py      # File processing utility
│
├── notebooks/                       # Jupyter notebooks
│   └── RAG_HTML.ipynb              # Interactive demo notebook
│
└── data/                            # Generated data (gitignored)
    ├── *.json                      # Scraped content
    ├── *.txt                       # Text exports
    └── *_cache.pkl                 # Processing caches
```

### 2. Optional Web Application - Full-Stack UI
```
└── webapp/                          # Complete web application
    ├── README_WEBAPP.md             # Web app overview & setup
    ├── docker-compose.prod.yml      # Production Docker setup
    ├── .pre-commit-config.yaml      # Security validation hooks
    │
    ├── backend/                     # FastAPI backend (Python)
    │   ├── api/                     # REST API endpoints
    │   ├── core/                    # Config, security, database
    │   ├── models/                  # Database models
    │   ├── services/                # Business logic
    │   ├── tests/                   # Backend unit tests
    │   ├── main.py                  # FastAPI application
    │   ├── init_db.py               # Database initialization
    │   └── requirements.txt         # Backend dependencies
    │
    ├── frontend/                    # React frontend (TypeScript)
    │   ├── src/                     # React source code
    │   ├── public/                  # Static assets
    │   ├── package.json             # Node dependencies
    │   └── README.md                # Frontend docs
    │
    ├── docs/                        # Web app documentation
    │   ├── README.md                # Docs index
    │   ├── DEPLOYMENT.md            # Manual deployment
    │   ├── DEPLOYMENT_GUIDE.md      # Docker deployment
    │   ├── ADMIN_GUIDE.md           # Admin guide
    │   ├── USER_GUIDE.md            # User guide
    │   ├── HANDOVER_DOCUMENT.md     # Project handover
    │   └── architecture/            # Architecture decisions
    │
    ├── scripts/                     # Deployment & security scripts
    │   ├── setup_database.sh
    │   ├── setup_ollama.sh
    │   ├── deploy.sh
    │   ├── backup.sh
    │   ├── restore.sh
    │   └── security_validator.py
    │
    └── tests/                       # Integration tests
        ├── test_phase3_integration.py
        ├── validate_phases_1_2.py
        └── test_backend.sh
```

### Component Summary

| Component | Purpose | Size | Tech Stack |
|-----------|---------|------|------------|
| **Core RAG Library** | Document parsing, RAG system | 184 KB | Python 3.12 |
| **Core Docs** | API reference, guides | 252 KB | Markdown |
| **Examples** | Usage examples | 76 KB | Python |
| **Tests** | Core library tests | 52 KB | pytest |
| **Web Application** | Optional full-stack UI | 976 MB | FastAPI + React + PostgreSQL (primary) / SQLite (backup) |

**Note**: The web application (`webapp/`) is **optional**. You can use the core RAG library standalone for programmatic use. See [webapp/README_WEBAPP.md](webapp/README_WEBAPP.md) for web app setup.

### Database Support for Web Application

The web application supports two database backends with different performance characteristics:

| Database | Performance | Use Case | Vector Search Speed | Setup |
|----------|------------|----------|---------------------|-------|
| **PostgreSQL + pgvector** | ⚡ **10-100x faster** | **Production (PRIMARY)** | O(log n) with HNSW index | `./setup_postgres.sh` |
| **SQLite** | Baseline | Development/Testing (BACKUP) | O(n) Python-based | Auto-created |

**Why PostgreSQL?**
- **50x faster** vector search for large document collections (100K+ chunks)
- Native pgvector extension with HNSW (Hierarchical Navigable Small World) indexing
- Scales to millions of documents without performance degradation
- Production-ready with connection pooling and optimization

**When to use SQLite?**
- Quick local development and testing
- Small document collections (<1000 chunks)
- No setup required (auto-created on first run)

**Migration**: Easily switch between databases using `.env` files:
```bash
# Use PostgreSQL (production)
cp .env .env.backup

# Use SQLite (development)
cp .env.dev .env

# Migrate data
python migrate_sqlite_to_postgres.py
```

See [webapp/backend/VECTOR_SEARCH_OPTIMIZATION.md](webapp/backend/VECTOR_SEARCH_OPTIMIZATION.md) for performance benchmarks and tuning guide.

## 🎯 Core Components

### 1. Web Scraping System
- **Synchronous Scraper** (`src/web_scraper.py`): Reliable, debuggable scraping
- **Async Scraper** (`src/async_web_scraper.py`): High-performance concurrent processing
- Works with **any website** automatically
- Preserves HTML hierarchy and document structure
- Respects robots.txt and implements polite crawling
- Creates semantic chunks based on content sections
- Smart domain filtering and depth control

### 2. RAG System (`src/rag_system.py`)
- Advanced TF-IDF with trigrams and sublinear scaling
- Intelligent caching system for scraped data
- Boosted scoring for different content types
- Rich metadata tracking (page, section, content type, domain)
- Integrates with local Ollama API for text generation

### 3. Interactive Interface (`notebooks/RAG_HTML.ipynb`)
- Jupyter notebook for experimentation with any website
- Visual exploration of retrieval results
- Easy testing of different queries and websites
- Complete pipeline demonstration

## 📊 Performance

- **Python 3.12 Benefits**: 10-15% faster than Python 3.10, improved memory efficiency
- **Similarity Scores**: 0.6+ (2x improvement over legacy systems)
- **Scraping Speed**: 3-5x faster with async scraper vs synchronous
- **Cache Performance**: 40-60% hit rate for repeated scraping operations
- **Context Quality**: Complete technical explanations with proper code examples
- **Processing Speed**: Optimized with smart caching and concurrent processing
- **Answer Quality**: Relevant, complete, and technically accurate responses

## 🧪 Testing

### Run Core RAG Tests
```bash
# Run all core RAG tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_rag_system.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**Test Results** (27 tests):
- ✅ 23 passed - Core RAG functionality working perfectly
- ⚠️ 4 async tests require `pytest-asyncio` (optional)

### Run Examples
```bash
# Basic usage (recommended first test)
python examples/basic_usage.py

# Advanced features
python examples/advanced_usage.py

# Performance benchmarking
python examples/benchmarking.py

# Generic system test
python examples/generic_usage.py
```

### Quick Functionality Test
```bash
# Test core imports and basic functionality
python -c "
from src.rag_system import RAGSystem
from src.web_scraper import WebScraper
from src.async_web_scraper import AsyncWebScraper

rag = RAGSystem()
scraper = WebScraper()
print('✅ All core modules imported successfully')
"
```

## 🔧 Configuration

The system works in two modes:

1. **Standalone (retrieval only)**: Use `demo_query()` for testing retrieval
2. **With Ollama**: Start `ollama serve` and use `rag_query()` for full answers

Adjust retrieval parameters:
- `top_k`: Number of results (recommended: 3-7)
- Model selection for Ollama: `mistral`, `llama2`, etc.

## 📖 Usage Examples

### Local Documentation Processing
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper

async def process_local_documentation():
    # Find HTML files in your documentation directory
    scraper = AsyncWebScraper()
    html_files = scraper.find_html_files("./documentation", "**/*.html")

    # Process with high-performance async method
    results = await AsyncWebScraper.process_local_files_fast(
        file_paths=html_files,
        output_file="data/local_docs.json",
        concurrent_limit=6  # Adjust based on your system
    )

    print(f"✅ Processed {results['metadata']['total_files']} files")
    print(f"📊 Created {results['metadata']['total_chunks']} chunks")

# Run local processing
asyncio.run(process_local_documentation())
```

### Work with Any Website
```python
from src.rag_system import RAGSystem

# Initialize system
rag_system = RAGSystem()

# Scrape different types of websites
websites = [
    "https://docs.python.org/3/",      # Documentation
    "https://fastapi.tiangolo.com/",   # API docs
    "https://nodejs.org/en/docs/",     # Different tech stack
    "https://reactjs.org/docs/"        # Frontend framework
]

for url in websites:
    success = rag_system.scrape_and_process_website([url], max_pages=10)
    if success:
        result = rag_system.demo_query("How to get started?", top_k=3)
        print(f"Results from {url}: {result}")
```

### Comprehensive Knowledge Base (Web + Local)
```python
from src.web_scraper import WebScraper

# Create comprehensive knowledge base from multiple sources
scraper = WebScraper()

# Process mixed sources in one operation
results = scraper.process_mixed_sources(
    web_urls=[
        "https://docs.python.org/3/tutorial/",
        "https://fastapi.tiangolo.com/"
    ],
    local_files=[
        "./docs/internal-guide.html",
        "./docs/custom-apis.html",
        "./docs/deployment.html"
    ],
    output_file="data/comprehensive_kb.json",
    max_pages=30
)

# Load into RAG system for querying
from src.rag_system import RAGSystem
rag = RAGSystem()
rag.load_data("data/comprehensive_kb.json")

# Query across all sources
answer = rag.demo_query("Deployment and configuration best practices", top_k=5)
print(answer)
```

### High-Performance Async Pipeline
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
from src.rag_system import RAGSystem

async def build_fast_knowledge_base():
    # Configure for maximum performance
    config = ScrapingConfig(
        concurrent_limit=8,
        max_pages=100,
        requests_per_second=12.0
    )

    # Process multiple sources concurrently
    tasks = []

    # Web scraping task
    async with AsyncWebScraper(config) as scraper:
        web_task = scraper.scrape_website_async([
            "https://docs.python.org/3/"
        ])
        tasks.append(web_task)

    # Local file processing task (can run in parallel)
    local_task = AsyncWebScraper.process_local_files_fast(
        file_paths=["./docs/guide1.html", "./docs/guide2.html"],
        concurrent_limit=6
    )
    tasks.append(local_task)

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks)

    print("✅ All processing completed!")
    return results

# Build knowledge base fast
results = asyncio.run(build_fast_knowledge_base())
```

### Full Generation with Context
```python
# Generate complete answers with any website content
answer = rag_system.rag_query(
    query="How to install and set up the framework?",
    top_k=5,
    model="mistral"
)
print(answer)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. See the LICENSE file for details.

## 🙏 Acknowledgments

- Universal design works with any website or documentation
- Enhanced with modern RAG techniques and intelligent caching
- Integrates with Ollama for local LLM capabilities
- Respects website policies and implements ethical web scraping