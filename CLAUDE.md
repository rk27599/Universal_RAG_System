# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **advanced RAG (Retrieval-Augmented Generation) system** that works with **any website**. It features intelligent web scraping, structure-aware content extraction, semantic chunking, enhanced TF-IDF retrieval, and local LLM integration via Ollama.

## Architecture

### Core Components

1. **Web Scraping System**:
   - **Synchronous Scraper** (`web_scraper.py`): Reliable, debuggable scraping
   - **Async Scraper** (`async_web_scraper.py`): High-performance concurrent processing
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
   - Intelligent caching for performance optimization

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

# Performance benchmarking and comparison
python examples/benchmarking.py
python examples/performance_comparison.py

# Interactive multi-website demo
python examples/generic_usage.py

# Quick test with any URL
python tests/test_generic_system.py
```

### Async vs Sync Scraper Usage
```bash
# For high-performance scraping (recommended for large websites)
# Use async scraper through RAG system or directly

# For development and debugging (easier to troubleshoot)
# Use sync scraper (default in most examples)
```

### Running the Interactive Notebook
```bash
jupyter notebook notebooks/RAG_HTML.ipynb
# or
jupyter lab notebooks/RAG_HTML.ipynb
```

### Python Environment
- Python 3.10+
- Core dependencies: requests, sklearn, beautifulsoup4, numpy, pickle
- Optional: Ollama for full text generation

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

### High-Performance Async Scraping
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

async def fast_scrape():
    config = ScrapingConfig(
        concurrent_limit=6,
        max_pages=50,
        requests_per_second=8.0
    )

    scraper = AsyncWebScraper(config)
    success, metrics = await scraper.scrape_website([
        "https://docs.python.org/"
    ])

    print(f"Processed {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")
    return success

# Run async scraping
success = asyncio.run(fast_scrape())
```

## Key Features

- **🌐 Universal Web Scraping**: Works with any website automatically
- **🏗️ Structure-Aware**: Preserves document hierarchy and context
- **🧠 Semantic Chunking**: Respects website sections vs random word splits
- **🔍 Enhanced Retrieval**: High similarity scores with intelligent boosting
- **📊 Rich Metadata**: Page titles, section hierarchy, content types, domains
- **⚡ High Performance**: Async scraping with concurrent processing
- **🔧 Dual Scraper Support**: Both sync (reliable) and async (fast) scrapers
- **💾 Smart Caching**: Content-based caching for performance optimization
- **📚 Comprehensive Documentation**: Complete API docs and user guides
- **🤖 Ethics**: Respects robots.txt and implements polite crawling

## File Structure

```
docs/                       # Comprehensive documentation
├── README.md              # Documentation overview
├── architecture.md        # System architecture
├── api/                   # API documentation
│   ├── README.md
│   ├── rag_system.md
│   └── async_web_scraper.md
└── guides/                # User guides
    ├── README.md
    ├── getting-started.md
    ├── development.md
    └── troubleshooting.md

src/
├── web_scraper.py         # Synchronous web scraper
├── async_web_scraper.py   # High-performance async scraper
├── rag_system.py          # Complete RAG system
└── __init__.py            # Package init

examples/
├── basic_usage.py         # Simple demo
├── generic_usage.py       # Interactive multi-website demo
├── advanced_usage.py      # Advanced features demo
├── benchmarking.py        # Performance testing
└── performance_comparison.py # Performance analysis

tests/
├── test_scraper.py        # Web scraper tests
├── test_rag_system.py     # RAG system tests
├── test_generic_system.py # Generic system tests
└── test_local_html.py     # Local HTML tests

notebooks/
└── RAG_HTML.ipynb         # Interactive Jupyter notebook

data/                      # Generated data directory
├── website_docs.json      # Structured website data
├── website_docs.txt       # Text format for compatibility
└── *_cache.pkl           # Processed data caches
```

## Usage Patterns

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

## Performance Expectations

- **Similarity Scores**: 0.6+ for excellent matches (2x improvement over legacy systems)
- **Context Quality**: Complete sections with proper metadata
- **Processing Speed**: 3-5x faster with async scraper and smart caching
- **Cache Hit Rate**: 40-60% for repeated scraping operations
- **Answer Quality**: Relevant, complete, and domain-aware responses
- **Website Coverage**: Works with documentation sites, blogs, wikis, APIs, etc.
- **Memory Efficiency**: Optimized for large-scale website processing

## Configuration Options

- **max_pages**: Number of pages to scrape (default: 30)
- **max_depth**: How deep to crawl (default: 2)
- **same_domain_only**: Stay within starting domain (default: True)
- **top_k**: Number of results to retrieve (3-7 recommended)

## Documentation & Getting Started

### Quick Start
1. **New users**: Start with [`docs/guides/getting-started.md`](./docs/guides/getting-started.md)
2. **API Reference**: See [`docs/api/README.md`](./docs/api/README.md) for detailed API docs
3. **Development**: Check [`docs/guides/development.md`](./docs/guides/development.md) for setup
4. **Architecture**: Review [`docs/architecture.md`](./docs/architecture.md) for system design

### Examples & Testing
1. Run `python examples/basic_usage.py` to test with FastAPI docs
2. Try `python examples/generic_usage.py` for interactive demo
3. Use `python examples/performance_comparison.py` for benchmarking
4. Use with Ollama (`ollama serve` + `ollama pull mistral`) for full generation
5. Adjust parameters based on your website and needs

### Troubleshooting
- Check [`docs/guides/troubleshooting.md`](./docs/guides/troubleshooting.md) for common issues
- Enable debug logging for detailed error information
- Start with small `max_pages` values for testing

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