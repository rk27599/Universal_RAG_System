# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **advanced RAG (Retrieval-Augmented Generation) system** that works with **any website**. It features intelligent web scraping, structure-aware content extraction, semantic chunking, enhanced TF-IDF retrieval, and local LLM integration via Ollama.

## Architecture

### Core Components

1. **Web Scraper** (`web_scraper.py`):
   - Respects robots.txt and implements polite crawling
   - Preserves HTML hierarchy and document structure
   - Extracts clean content while maintaining context
   - Creates semantic chunks based on website sections
   - Works with any website automatically

2. **RAG System** (`rag_system.py`):
   - Advanced TF-IDF with trigrams and sublinear scaling
   - Boosted scoring for code examples and technical content
   - Rich metadata tracking (page, section, content type, domain)
   - Integrates with local Ollama API for text generation
   - Generic query enhancement for any domain

3. **Data Files**:
   - `data/website_docs.json`: Structured website documentation with metadata
   - `data/website_docs.txt`: Compatible text format
   - `data/*_cache.pkl`: Processed chunks and vectors cache

## Development Commands

### Running Examples
```bash
# Basic usage with FastAPI docs demo
python examples/basic_usage.py

# Advanced features with Ollama integration
python examples/advanced_usage.py

# Performance benchmarking
python examples/benchmarking.py

# Quick test with any URL
python test_generic_system.py
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
- Python 3.12+ (✅ Migrated from 3.10 - October 2025)
- Core dependencies: requests, sklearn, beautifulsoup4, numpy, pickle
- Optional: Ollama for full text generation
- Performance: ~10-15% faster than Python 3.10

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

## Key Features

- **🌐 Universal Web Scraping**: Works with any website automatically
- **📂 Local File Processing**: High-performance async processing of local HTML files
- **🏗️ Structure-Aware**: Preserves document hierarchy and context
- **🧠 Semantic Chunking**: Respects website sections vs random word splits
- **🔍 Enhanced Retrieval**: High similarity scores with intelligent boosting
- **📊 Rich Metadata**: Page titles, section hierarchy, content types, domains
- **🔄 Mixed Source Processing**: Combines web scraping + local files seamlessly
- **⚡ Performance**: TF-IDF with trigrams, boosted scoring, smart caching
- **🤖 Ethics**: Respects robots.txt and implements polite crawling

## File Structure

```
src/
├── web_scraper.py          # Universal web scraper
├── rag_system.py           # Complete RAG system
└── __init__.py             # Package init

examples/
├── basic_usage.py          # Simple demo
├── generic_usage.py        # Interactive multi-website demo
├── advanced_usage.py       # Advanced features demo
└── benchmarking.py         # Performance testing

tests/
├── test_scraper.py         # Web scraper tests
└── test_rag_system.py      # RAG system tests

data/                       # Generated data directory
├── website_docs.json       # Structured website data
├── website_docs.txt        # Text format for compatibility
└── *_cache.pkl            # Processed data caches
```

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

- **Similarity Scores**: 0.4+ for good matches (varies by content)
- **Context Quality**: Complete sections with proper metadata
- **Processing Speed**: Fast with smart caching
- **Answer Quality**: Relevant, complete, and domain-aware responses
- **Website Coverage**: Works with documentation sites, blogs, wikis, etc.

## Configuration Options

- **max_pages**: Number of pages to scrape (default: 30)
- **max_depth**: How deep to crawl (default: 2)
- **same_domain_only**: Stay within starting domain (default: True)
- **top_k**: Number of results to retrieve (3-7 recommended)

## Next Steps

1. Run `python examples/basic_usage.py` to test with FastAPI docs
2. Try `python examples/generic_usage.py` for interactive demo
3. Use with Ollama (`ollama serve` + `ollama pull mistral`) for full generation
4. Adjust parameters based on your website and needs
5. Experiment with different domains and content types

## Important Notes

- Always respect website terms of service and robots.txt
- Start with small max_pages values for testing
- Some websites may block automated scraping
- The system works best with well-structured documentation sites
- Performance varies based on website structure and content quality

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.