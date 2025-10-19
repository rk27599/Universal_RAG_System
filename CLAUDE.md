# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **advanced RAG (Retrieval-Augmented Generation) system** that works with **any website and PDF documents**. It features intelligent web scraping, PDF processing with table/image extraction, structure-aware content extraction, semantic chunking, enhanced TF-IDF retrieval, and local LLM integration via Ollama.

## Architecture

### Core Components

1. **Web Scraper** (`web_scraper.py`):
   - Respects robots.txt and implements polite crawling
   - Preserves HTML hierarchy and document structure
   - Extracts clean content while maintaining context
   - Creates semantic chunks based on website sections
   - Works with any website automatically

2. **PDF Processor** (`webapp/backend/services/pdf_processor.py`):
   - Hybrid approach: PyMuPDF for text + pdfplumber for tables
   - Intelligent table detection with markdown formatting
   - Image extraction per page with configurable resolution
   - Font-based heading detection
   - Semantic chunking respecting document structure
   - Supports configuration profiles (fast, balanced, quality, large_files)

3. **RAG System** (`rag_system.py`):
   - Advanced TF-IDF with trigrams and sublinear scaling
   - Boosted scoring for code examples and technical content
   - Rich metadata tracking (page, section, content type, domain)
   - Integrates with local Ollama API for text generation
   - Generic query enhancement for any domain

4. **Data Files**:
   - `data/website_docs.json`: Structured website documentation with metadata
   - `data/website_docs.txt`: Compatible text format
   - `data/*_cache.pkl`: Processed chunks and vectors cache
   - `data/uploads/`: Uploaded PDF and document files

## Development Commands

### Running Examples
```bash
# Basic usage with FastAPI docs demo
python examples/basic_usage.py

# Advanced features with Ollama integration
python examples/advanced_usage.py

# Performance benchmarking
python examples/benchmarking.py

# Interactive demo with any website
python examples/generic_usage.py
```

### Local File Processing
```bash
# Process local HTML files with async performance
python -c "
import asyncio
from src.async_web_scraper import AsyncWebScraper

async def main():
    results = await AsyncWebScraper.process_local_files_fast(
        file_paths=['data/temp.html', 'data/temp2.html'],
        output_file='data/local_docs.json',
        concurrent_limit=4
    )
    print(f'Processed {results[\"metadata\"][\"total_files\"]} files')

asyncio.run(main())
"
```

### Running the Interactive Notebook
```bash
jupyter notebook notebooks/RAG_HTML.ipynb
# or
jupyter lab notebooks/RAG_HTML.ipynb
```

### Python Environment
- Python 3.12+ (✅ Migrated from 3.10 - October 2024)
- PyTorch 2.6.0+cu124 (✅ Required for BGE-M3 embeddings)
- CUDA 12.4+ (for GPU acceleration)
- Core dependencies: requests, sklearn, beautifulsoup4, numpy, pickle
- PDF dependencies: PyMuPDF, pdfplumber, Pillow, nltk
- Embedding: FlagEmbedding 1.3.5 (BGE-M3 model)
- Optional: Ollama for full text generation
- Performance: ~10-15% faster than Python 3.10

### Installing Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install PyTorch 2.6.0 with CUDA 12.4 support (Required for BGE-M3)
pip install torch==2.6.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install BGE-M3 embedding model
pip install FlagEmbedding==1.3.5

# Install PDF processing dependencies
pip install PyMuPDF pdfplumber Pillow nltk

# Install dev/testing dependencies (optional)
pip install -r webapp/requirements.txt

# Install backend production dependencies
pip install -r webapp/backend/requirements.txt

# Download NLTK data for sentence tokenization
python -c "import nltk; nltk.download('punkt_tab')"
```

## Embedding Models

### BGE-M3 (Current - Default)
The system uses **BGE-M3** for high-quality semantic embeddings:

| Feature | BGE-M3 (Current) | MiniLM (Old) |
|---------|------------------|--------------|
| **Dimensions** | 1024 | 384 |
| **Context Window** | 8,192 tokens | 512 tokens |
| **Languages** | 100+ | English only |
| **Quality** | State-of-the-art MTEB | Good |
| **Model** | BAAI/bge-m3 | sentence-transformers/all-MiniLM-L6-v2 |

### Migration Complete ✅
- **10,366 chunks** re-embedded with BGE-M3
- **Processing time:** 12.4 minutes
- **Quality:** 2.7x larger embedding space, 16x context window
- **Backward compatible:** Old embeddings preserved

## Material Studio Expert System Prompt

The system includes a **configurable expert prompt** that ensures accurate, citation-based responses for Material Studio queries.

### Features
- **Default ON** for all RAG queries with document context
- **Cites sources** - Forces LLM to reference specific documentation sections
- **Acknowledges limitations** - Clearly states when context is insufficient
- **User customizable** - Toggle on/off or write custom prompts via Settings UI
- **Persisted settings** - Saved to localStorage across sessions

### How It Works
```
User Query → BGE-M3 Embedding (1024-dim) →
Vector Search (HNSW index) → Retrieve 20 chunks (70%+ similarity) →
Apply Expert Prompt → Ollama generates grounded response →
User receives citation-based answer
```

### Configuration
Access via **Settings → Model Settings → System Prompt Settings**:
- Toggle expert prompt on/off
- View/edit custom system prompt
- Reset to default Material Studio expert prompt
- Settings persist across page reloads

### Expert Prompt Guidelines
The default prompt enforces:
- **Accuracy:** Only use retrieved documentation
- **Citation:** Reference specific sources (e.g., "According to the Forcite Module API documentation...")
- **Transparency:** Acknowledge when information is missing
- **Professional:** Clear, concise technical explanations
- **Scope:** Stay within Material Studio documentation

### Working with the RAG System

The system works with any website and can operate standalone or with Ollama:

1. **Standalone (retrieval only)**: Use `demo_query()` for testing
2. **With Ollama**: Start `ollama serve` and use `rag_query()` for full answers

Example usage:
```python
from src.rag_system import RAGSystem

# Initialize system
rag_system = RAGSystem()

# Scrape and process any website
rag_system.scrape_and_process_website(
    start_urls=["https://docs.python.org/"],
    max_pages=20,
    output_file="data/python_docs.json"
)

# Test retrieval
result = rag_system.demo_query("What are Python data types?", top_k=3)

# Full generation (requires Ollama)
answer = rag_system.rag_query("What are Python data types?", top_k=3, model="mistral")
```

### Local File Processing Usage:
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper

# Process local HTML files with high performance
async def process_local_files():
    results = await AsyncWebScraper.process_local_files_fast(
        file_paths=["data/temp.html", "data/temp2.html"],
        output_file="data/local_docs.json",
        concurrent_limit=4
    )

    print(f"✅ Processed {results['metadata']['total_files']} files")
    print(f"📊 Created {results['metadata']['total_chunks']} chunks")

    return results

# Run local file processing
results = asyncio.run(process_local_files())

# Load into RAG system
rag_system = RAGSystem()
rag_system.load_data("data/local_docs.json")

# Query local documentation
result = rag_system.demo_query("specific topic from local docs", top_k=3)
```

### PDF Processing Usage:
```python
from webapp.backend.services.pdf_processor import PDFProcessor
from webapp.backend.config.pdf_config import get_config
import asyncio

# Basic PDF processing
async def process_pdf():
    processor = PDFProcessor(chunk_size=1000, overlap=200)
    result = await processor.process_pdf("path/to/document.pdf", document_id=1)

    if result:
        print(f"Title: {result['page_title']}")
        print(f"Pages: {result['metadata']['total_pages']}")
        print(f"Sections: {result['total_sections']}")
        print(f"Images: {result['metadata']['image_count']}")
        print(f"Tables: {result['metadata']['table_count']}")

# Advanced PDF processing with custom config
async def process_pdf_advanced():
    # Use quality profile for best results
    config = get_config("quality")
    processor = PDFProcessor(config=config)
    result = await processor.process_pdf("technical_doc.pdf", document_id=1)

    # Sections with semantic chunks
    for section in result['sections']:
        print(f"{section['title']}: {section['word_count']} words")

# Available config profiles:
# - "default": Balanced settings
# - "fast": Quick processing, no images
# - "balanced": Standard quality (recommended)
# - "quality": Maximum quality, high-res images
# - "large_files": Optimized for large PDFs (>50MB)

asyncio.run(process_pdf())
```

## Key Features

- **🌐 Universal Web Scraping**: Works with any website automatically
- **📄 PDF Processing**: Hybrid PyMuPDF + pdfplumber for comprehensive extraction
- **📊 Table Detection**: Intelligent detection and markdown formatting
- **🖼️ Image Extraction**: Per-page image extraction with configurable resolution
- **📂 Local File Processing**: High-performance async processing of local HTML files
- **🏗️ Structure-Aware**: Preserves document hierarchy and context
- **🧠 Semantic Chunking**: Respects document sections vs random word splits
- **🔍 Enhanced Retrieval**: High similarity scores with intelligent boosting
- **📈 Rich Metadata**: Page titles, section hierarchy, content types, domains
- **🔄 Mixed Source Processing**: Combines web scraping + local files + PDFs seamlessly
- **⚡ Performance**: TF-IDF with trigrams, boosted scoring, smart caching
- **🤖 Ethics**: Respects robots.txt and implements polite crawling

## File Structure

**ROOT DIRECTORY (Clean - Only Essential Files)**
```
/home/rkpatel/RAG/
├── README.md            # Main project overview
├── CLAUDE.md            # This file - Claude Code instructions
├── LICENSE              # License file
├── .gitignore           # Git ignore rules
├── logs/                # Application logs (gitignored)
├── data/                # Data files (gitignored)
├── archive/             # Old RAG system (reference)
├── venv/                # Python virtual environment
└── webapp/              # 🎯 ALL APPLICATION CODE & DOCS HERE
```

**WEBAPP DIRECTORY (All Code, Tests, Docs, Scripts)**
```
webapp/
├── requirements.txt                 # Dev/testing dependencies
├── README.md                        # Webapp overview
├── INSTALLATION_GUIDE.md            # Setup instructions
│
├── tests/                           # ALL test files
│   ├── test_enhanced_rag_e2e.py    # End-to-end RAG tests
│   ├── test_pdf_sample.py          # PDF processing tests
│   ├── test_phase3_integration.py  # Phase 3 integration
│   └── validate_phases_1_2.py      # Phase 1 & 2 validation
│
├── backend/                         # FastAPI Backend (Python)
│   ├── api/                        # REST API endpoints
│   │   ├── auth.py                # Authentication
│   │   ├── chat.py                # WebSocket chat + Redis
│   │   ├── documents.py           # Document upload/management
│   │   └── models.py              # Ollama model info
│   │
│   ├── core/                       # Core configuration
│   │   ├── config.py              # Settings + Redis config
│   │   ├── database.py            # SQLAlchemy setup
│   │   └── security.py            # JWT & password hashing
│   │
│   ├── models/                     # Database models
│   │   ├── user.py                # User model
│   │   ├── document.py            # Document & Chunk (progress tracking)
│   │   └── conversation.py        # Chat models
│   │
│   ├── services/                   # Business logic
│   │   ├── document_service.py          # Document processing w/ progress
│   │   ├── embedding_service_bge.py     # BGE-M3 embeddings (1024-dim)
│   │   ├── pdf_processor.py             # Advanced PDF processing
│   │   ├── redis_service.py             # Redis WebSocket session management
│   │   ├── enhanced_search_service.py   # 🆕 Unified enhanced RAG
│   │   ├── reranker_service.py          # 🆕 Cross-encoder reranking
│   │   ├── bm25_retriever.py            # 🆕 BM25 keyword search
│   │   ├── ensemble_retriever.py        # 🆕 Hybrid search orchestration
│   │   ├── query_expander.py            # 🆕 Multi-query generation
│   │   ├── corrective_rag.py            # 🆕 Self-grading RAG
│   │   ├── web_search_fallback.py       # 🆕 External knowledge fallback
│   │   ├── document_recovery_service.py # 🆕 Document repair/recovery
│   │   ├── rag_service.py               # RAG retrieval orchestration
│   │   └── ollama_service.py            # LLM integration
│   │
│   ├── utils/                      # Utility modules
│   │   ├── async_web_scraper.py   # HTML content extraction
│   │   └── memory_manager.py      # 🆕 RAM/swap monitoring, adaptive batching
│   │
│   ├── prompts/                    # 🆕 LLM Prompt Templates
│   │   ├── citation_template.py   # Citation-enforcing prompts
│   │   ├── cot_template.py        # Chain-of-thought prompts
│   │   └── extractive_template.py # Extractive QA prompts
│   │
│   ├── scripts/                    # Backend scripts
│   │   ├── reembed_with_bge_m3.py # BGE-M3 migration script
│   │   ├── setup_postgres.sh      # Database setup
│   │   ├── redis_health.py        # Redis monitoring
│   │   └── migrate_*.py           # Database migrations
│   │
│   ├── docs/                       # Backend documentation
│   │   ├── ENHANCED_SEARCH_INTEGRATION.md  # RAG features guide
│   │   ├── README_ENHANCED_SEARCH.md       # Enhanced search overview
│   │   ├── TESTING_GUIDE.md                # Testing documentation
│   │   ├── VECTOR_SEARCH_OPTIMIZATION.md   # Performance tuning
│   │   └── redis/                          # Redis-specific docs
│   │       ├── REDIS_DEPLOYMENT_STEPS.md
│   │       ├── REDIS_FIX_SUMMARY.md
│   │       └── FIX_REDIS_PUBSUB.md
│   │
│   ├── tests/                      # Backend tests
│   │   └── test_enhanced_search_integration.py
│   │
│   ├── main.py                     # FastAPI application entry
│   ├── init_db.py                  # Database initialization
│   └── requirements.txt            # Backend dependencies
│
├── frontend/                        # React Frontend (TypeScript)
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── Auth/              # Login, Register
│   │   │   ├── Chat/              # Chat interface
│   │   │   ├── Documents/         # Upload, list (🆕 progress tracking)
│   │   │   ├── Layout/            # App layout, sidebar
│   │   │   └── Settings/          # Model settings (🆕 system prompt)
│   │   │
│   │   ├── contexts/               # React contexts
│   │   │   ├── AuthContext.tsx    # Auth state
│   │   │   └── ChatContext.tsx    # Chat state + WebSocket
│   │   │
│   │   ├── services/               # API services
│   │   │   └── api.ts             # Axios API client
│   │   │
│   │   ├── config/                 # Configuration
│   │   │   └── config.ts          # App settings
│   │   │
│   │   ├── App.tsx                 # Main app component
│   │   └── index.tsx               # React entry point
│   │
│   ├── public/                     # Static assets
│   ├── package.json                # Node dependencies
│   └── README.md                   # Frontend documentation
│
├── docs/                            # 📚 ALL PROJECT DOCUMENTATION
│   ├── README.md                   # Docs index
│   ├── README_ROOT.md              # Root docs overview
│   ├── BGE_M3_MIGRATION_GUIDE.md   # 🆕 BGE-M3 migration guide
│   ├── FEATURES_GUIDE.md           # 🆕 Complete features guide (consolidated)
│   ├── NETWORK_SETUP.md            # Network/LAN configuration
│   ├── PRODUCTION_DEPLOYMENT.md    # Production deployment
│   ├── REDIS_COMPLETE_GUIDE.md     # 🆕 Redis setup & troubleshooting
│   ├── ADMIN_GUIDE.md              # Admin operations
│   ├── USER_GUIDE.md               # User manual
│   ├── DEPLOYMENT_GUIDE.md         # Docker deployment
│   ├── HANDOVER_DOCUMENT.md        # Project handover
│   └── architecture/               # Architecture decisions
│
└── scripts/                         # Webapp utility scripts
    ├── deploy.sh                   # Deployment automation
    ├── backup.sh                   # Database backup
    ├── setup_ollama.sh             # Ollama setup
    └── security_validator.py       # Security checks
```

**Key Organization Principles (October 2024)**:
- **Root**: Only README.md, CLAUDE.md, LICENSE, .gitignore + gitignored folders
- **webapp/**: ALL code, tests, documentation, and scripts
- **webapp/docs/**: Centralized documentation for entire project
- **webapp/backend/**: Backend code, services, scripts, backend-specific docs
- **webapp/tests/**: ALL test files (root + backend + integration)
- **Clean separation**: Dev dependencies in webapp/requirements.txt, backend production in webapp/backend/requirements.txt

## Usage Patterns

### Quick Start with Web Content
```python
# Quick start with any website:
python examples/basic_usage.py

# Custom website scraping:
from src.rag_system import RAGSystem
rag_system = RAGSystem()
rag_system.scrape_and_process_website(["https://your-website.com/"])

# Test retrieval performance:
result = rag_system.demo_query("Your question here", top_k=3)

# Generate full answers with Ollama:
answer = rag_system.rag_query("Your question here", top_k=3)
```

### Local File Processing Patterns
```python
# High-performance local file processing
import asyncio
from src.async_web_scraper import AsyncWebScraper

# Pattern 1: Static method for simple usage
results = await AsyncWebScraper.process_local_files_fast(
    file_paths=["docs/guide.html", "docs/api.html"],
    output_file="data/local_docs.json",
    concurrent_limit=6
)

# Pattern 2: Instance method for advanced control
async with AsyncWebScraper() as scraper:
    html_files = scraper.find_html_files("./documentation", "**/*.html")
    results = await scraper.process_local_files_async(
        file_paths=html_files,
        output_file="data/comprehensive_docs.json"
    )

# Pattern 3: Mixed source processing
from src.web_scraper import WebScraper
scraper = WebScraper()
results = scraper.process_mixed_sources(
    web_urls=["https://docs.example.com/"],
    local_files=["./internal/custom-docs.html"],
    output_file="data/mixed_knowledge_base.json"
)
```

### Integration Patterns
```python
# Pattern 1: Async pipeline with RAG
async def async_knowledge_pipeline():
    # Process sources
    results = await AsyncWebScraper.process_local_files_fast(
        file_paths=["docs/*.html"],
        output_file="data/knowledge.json"
    )

    # Load into RAG
    rag = RAGSystem()
    rag.load_data("data/knowledge.json")

    # Query immediately
    return rag.demo_query("your question", top_k=5)

# Pattern 2: Batch processing multiple directories
async def batch_process_documentation():
    directories = ["./api_docs", "./user_guides", "./tutorials"]

    for i, doc_dir in enumerate(directories):
        results = await AsyncWebScraper.process_local_files_fast(
            file_paths=AsyncWebScraper().find_html_files(doc_dir, "**/*.html"),
            output_file=f"data/docs_batch_{i}.json"
        )
        print(f"Processed {doc_dir}: {results['metadata']['total_files']} files")

# Pattern 3: Real-time processing pipeline
def setup_comprehensive_rag():
    rag = RAGSystem()

    # Load multiple processed sources
    for data_file in ["data/web_docs.json", "data/local_docs.json", "data/mixed_docs.json"]:
        if os.path.exists(data_file):
            rag.load_data(data_file)

    return rag
```

## Performance Expectations

### General Performance
- **Similarity Scores**: 0.4+ for good matches (varies by content)
- **Context Quality**: Complete sections with proper metadata
- **Processing Speed**: Fast with smart caching
- **Answer Quality**: Relevant, complete, and domain-aware responses
- **Website Coverage**: Works with documentation sites, blogs, wikis, etc.

### PDF Processing Performance
- **Processing Speed**:
  - Small PDFs (<10MB, <50 pages): 5-15 seconds
  - Medium PDFs (10-30MB, 50-200 pages): 15-60 seconds
  - Large PDFs (>30MB, >200 pages): 1-5 minutes
- **Memory Usage**: ~100-500MB depending on PDF complexity
- **Quality**:
  - Text extraction: Excellent with PyMuPDF
  - Table detection: 70-90% accuracy with pdfplumber
  - Image extraction: High quality, configurable resolution
- **Supported PDFs**:
  - ✅ Text-based PDFs (digital documents)
  - ✅ PDFs with tables and images
  - ✅ Technical documentation
  - ⚠️ Scanned PDFs (limited quality, consider OCR preprocessing)
  - ❌ Password-protected PDFs (not supported)

## Configuration Options

### Web Scraping
- **max_pages**: Number of pages to scrape (default: 30)
- **max_depth**: How deep to crawl (default: 2)
- **same_domain_only**: Stay within starting domain (default: True)
- **top_k**: Number of results to retrieve (3-7 recommended)

### PDF Processing (see `webapp/backend/config/pdf_config.py`)
- **chunk_size**: Words per chunk (default: 1000, range: 500-5000)
- **overlap**: Overlap between chunks (default: 200 words)
- **table_detection_threshold**: Sensitivity (default: 0.7)
- **image_resolution**: DPI for extracted images (default: 150)
- **max_file_size_mb**: Maximum file size warning (default: 50MB)

Use configuration profiles:
```python
from webapp.backend.config.pdf_config import get_config

config = get_config("quality")  # Options: default, fast, balanced, quality, large_files
processor = PDFProcessor(config=config)
```

## Next Steps

1. **Install dependencies**:
   - Dev/testing: `pip install -r webapp/requirements.txt`
   - Backend production: `pip install -r webapp/backend/requirements.txt`
2. **Download NLTK data**: `python -c "import nltk; nltk.download('punkt_tab')"`
3. **Setup backend**: Follow `webapp/INSTALLATION_GUIDE.md`
4. **Start application**:
   - Backend: `cd webapp/backend && python main.py`
   - Frontend: `cd webapp/frontend && npm start`
5. Upload PDFs via the web interface to test PDF processing
6. Use with Ollama (`ollama serve` + `ollama pull mistral`) for full generation
7. Enable enhanced RAG features via Settings UI (reranker, hybrid search, query expansion)
8. Experiment with different domains, PDFs, and content types

## Important Notes

### Web Scraping
- Always respect website terms of service and robots.txt
- Start with small max_pages values for testing
- Some websites may block automated scraping
- The system works best with well-structured documentation sites
- Performance varies based on website structure and content quality

### PDF Processing
- **Supported formats**: Text-based PDFs work best
- **File size limits**: Default warning at 50MB (configurable)
- **Password-protected PDFs**: Not supported - remove password first
- **Scanned PDFs**: Limited quality - consider using OCR preprocessing
- **Complex layouts**: Table detection is ~70-90% accurate
- **Memory usage**: Large PDFs (>100MB) may require 1-2GB RAM
- **Processing time**: Varies with file size and complexity
- **Dependencies**: Ensure PyMuPDF, pdfplumber, Pillow, nltk are installed

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.