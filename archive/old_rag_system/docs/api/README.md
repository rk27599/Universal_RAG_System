# API Documentation

Complete API reference for the Universal RAG System components.

## 📋 Overview

The Universal RAG System provides three main APIs:

1. **[RAG System](./rag_system.md)** - High-level interface for retrieval and generation
2. **[Async Web Scraper](./async_web_scraper.md)** - High-performance concurrent scraping
3. **[Web Scraper](./web_scraper.md)** - Synchronous scraping with detailed debugging

## 🚀 Quick Start

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
print(f"Found {len(result['chunks'])} relevant chunks")
```

## 📚 API Components

### RAG System (`src/rag_system.py`)
The main interface for the Universal RAG System.

**Key Methods:**
- `scrape_and_process_website()` - Scrape and index website content
- `demo_query()` - Retrieval-only queries for testing
- `rag_query()` - Full RAG with text generation via Ollama
- `load_data()` - Load preprocessed data

**[→ Full RAG System API Documentation](./rag_system.md)**

### Async Web Scraper (`src/async_web_scraper.py`)
High-performance asynchronous web scraper with concurrent processing.

**Key Features:**
- 3-5x faster than synchronous scraping
- Configurable concurrency limits
- Smart rate limiting and caching
- Performance metrics tracking

**[→ Full Async Web Scraper API Documentation](./async_web_scraper.md)**

### Web Scraper (`src/web_scraper.py`)
Synchronous web scraper optimized for reliability and debugging.

**Key Features:**
- Detailed error reporting
- Step-by-step processing
- Easier troubleshooting
- Consistent results

**[→ Full Web Scraper API Documentation](./web_scraper.md)**

## 🔧 Configuration

### Environment Setup

```python
# Basic setup
from src.rag_system import RAGSystem

rag = RAGSystem(
    data_dir="data",           # Directory for data files
    cache_enabled=True         # Enable intelligent caching
)
```

### Scraping Configuration

```python
# Sync scraper (via RAG system)
success = rag.scrape_and_process_website(
    start_urls=["https://example.com/"],
    max_pages=30,              # Maximum pages to scrape
    max_depth=2,               # Maximum crawling depth
    same_domain_only=True,     # Stay within domain
    output_file="data/docs.json"  # Custom output file
)

# Async scraper (direct usage)
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

config = ScrapingConfig(
    concurrent_limit=6,        # Concurrent requests
    requests_per_second=8.0,   # Rate limiting
    max_pages=50,              # More pages for async
    timeout=15.0               # Request timeout
)

scraper = AsyncWebScraper(config)
success, metrics = asyncio.run(
    scraper.scrape_website(["https://example.com/"])
)
```

## 🎯 Common Usage Patterns

### 1. Basic Website Processing
```python
from src.rag_system import RAGSystem

rag = RAGSystem()

# Process a documentation site
success = rag.scrape_and_process_website([
    "https://fastapi.tiangolo.com/"
], max_pages=25)

if success:
    # Test retrieval
    result = rag.demo_query("How to create an API?", top_k=3)

    # Generate answer with Ollama
    answer = rag.rag_query("How to create an API?", model="mistral")
    print(answer)
```

### 2. High-Performance Batch Processing
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
from src.rag_system import RAGSystem

async def process_multiple_sites():
    config = ScrapingConfig(concurrent_limit=8, max_pages=40)
    scraper = AsyncWebScraper(config)

    sites = [
        "https://docs.python.org/",
        "https://fastapi.tiangolo.com/",
        "https://flask.palletsprojects.com/"
    ]

    for site in sites:
        success, metrics = await scraper.scrape_website([site])
        print(f"Processed {site}: {metrics.urls_processed} pages")

    # Load all data into RAG system
    rag = RAGSystem()
    rag.load_data("data/website_docs.json")

    return rag

# Use the processed data
rag = asyncio.run(process_multiple_sites())
result = rag.demo_query("Compare Python web frameworks", top_k=7)
```

### 3. Custom Content Processing
```python
from src.web_scraper import WebScraper

# Use sync scraper directly for debugging
scraper = WebScraper()

success = scraper.scrape_website(
    start_urls=["https://example.com/"],
    output_file="custom_output.json",
    max_pages=15,
    max_depth=1
)

if success:
    # Load into RAG system
    rag = RAGSystem()
    rag.load_data("custom_output.json")
```

## ⚡ Performance Considerations

### Choosing the Right Scraper

| Use Case | Recommended Scraper | Reason |
|----------|-------------------|---------|
| Development/Testing | Sync Web Scraper | Easier debugging, detailed logs |
| Production/Large sites | Async Web Scraper | 3-5x faster, concurrent processing |
| Mixed content types | RAG System (auto) | Automatically chooses best approach |
| Debugging issues | Sync Web Scraper | Step-by-step processing visibility |

### Optimization Tips

1. **Start Small**: Begin with `max_pages=10-20` for testing
2. **Use Caching**: Enable caching for repeated scraping
3. **Tune Concurrency**: Adjust `concurrent_limit` based on target site
4. **Monitor Performance**: Check metrics for optimization opportunities

## 🛠️ Error Handling

All APIs include comprehensive error handling:

```python
try:
    rag = RAGSystem()
    success = rag.scrape_and_process_website(["https://example.com/"])

    if not success:
        print("Scraping failed - check logs for details")

    result = rag.demo_query("test query", top_k=3)

except Exception as e:
    print(f"Error: {e}")
    # Check logs for detailed error information
```

## 📊 API Response Formats

### RAG Query Response
```python
{
    'query': 'Your original query',
    'chunks': [
        {
            'content': 'Relevant text content',
            'score': 0.756,  # Similarity score (0-1)
            'metadata': {
                'page_title': 'Page Title',
                'section_hierarchy': ['Main', 'Sub-section'],
                'content_type': 'paragraph',
                'domain': 'example.com',
                'url': 'https://example.com/page'
            }
        }
    ]
}
```

### Scraping Metrics
```python
{
    'urls_discovered': 45,
    'urls_processed': 40,
    'urls_failed': 5,
    'cache_hits': 12,
    'elapsed_time': 23.5,
    'total_bytes_downloaded': 2048576
}
```

## 🔗 Related Documentation

- [Getting Started Guide](../guides/getting-started.md) - Learn the basics
- [Architecture Overview](../architecture.md) - Understand system design
- [Performance Guide](../guides/performance.md) - Optimization strategies
- [Troubleshooting](../guides/troubleshooting.md) - Common issues

---

*For detailed method signatures and advanced usage, see the individual API documentation files.*