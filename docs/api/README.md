# API Documentation

This directory contains detailed API documentation for the Universal RAG System.

## Quick Links

- [RAG System API](./rag_system.md) - Main RAG system interface
- [Web Scraper API](./web_scraper.md) - Web scraping functionality
- [Async Web Scraper API](./async_web_scraper.md) - High-performance async scraping
- [Configuration](./configuration.md) - System configuration options

## Overview

The Universal RAG System provides three main APIs:

1. **RAG System** - High-level interface for retrieval and generation
2. **Web Scraper** - Synchronous web scraping with structure preservation
3. **Async Web Scraper** - High-performance async web scraping

## Getting Started

```python
from src.rag_system import RAGSystem

# Initialize the system
rag = RAGSystem()

# Scrape and process a website
success = rag.scrape_and_process_website(
    start_urls=["https://docs.python.org/"],
    max_pages=20
)

# Query the system
result = rag.demo_query("How to define functions?", top_k=3)
```

See individual API documentation for detailed usage examples.