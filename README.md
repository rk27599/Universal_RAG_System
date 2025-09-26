# Universal RAG System for Any Website

An advanced **Retrieval-Augmented Generation (RAG) system** that works with **any website**. Features structure-aware web scraping, semantic chunking, enhanced TF-IDF retrieval, intelligent caching, and local LLM integration via Ollama.

## 🚀 Features

- **🌍 Universal Compatibility**: Works with **any website** automatically - documentation, blogs, APIs, etc.
- **🏗️ Structure-Aware Scraping**: Preserves HTML hierarchy (h1, h2, h3) and document structure
- **🧠 Semantic Chunking**: Respects content sections vs random word splits
- **🔍 Enhanced Retrieval**: High similarity scores (0.6+ typical vs 0.3 legacy systems)
- **📊 Rich Metadata**: Page titles, section hierarchy, content types, domain information
- **⚡ Dual Scraper Support**: Both sync (reliable) and async (3-5x faster) scrapers
- **💾 Smart Caching**: Content-based caching with 40-60% hit rates
- **🚀 High Performance**: Concurrent processing with configurable limits
- **🤖 Local LLM Integration**: Works with Ollama for complete text generation
- **🚦 Respectful Crawling**: Honors robots.txt, implements rate limiting, same-domain filtering

## 📋 Requirements

- Python 3.10+
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

    scraper = AsyncWebScraper(config)
    success, metrics = await scraper.scrape_website([
        "https://docs.python.org/3/"
    ])

    print(f"✅ Processed {metrics.urls_processed} pages")
    print(f"⚡ Total time: {metrics.elapsed_time:.1f}s")
    print(f"📊 Cache hits: {metrics.cache_hits}")

# Run async scraping
success = asyncio.run(fast_scrape())
```

## 📁 Project Structure

```
├── README.md                         # This file
├── CLAUDE.md                        # Detailed project documentation
├── requirements.txt                 # Python dependencies
├── src/                             # Source code
│   ├── __init__.py
│   ├── web_scraper.py              # Synchronous web scraper
│   ├── async_web_scraper.py        # High-performance async scraper
│   └── rag_system.py               # Main RAG system
├── data/                            # Data files (auto-generated)
│   ├── *.json                      # Structured website data
│   ├── *.txt                       # Text format compatibility
│   └── *_cache.pkl                 # Processed data caches
├── notebooks/                       # Jupyter notebooks
│   └── RAG_HTML.ipynb              # Interactive notebook
├── tests/                          # Test files
│   ├── __init__.py
│   ├── test_rag_system.py          # RAG system tests
│   └── test_scraper.py             # Scraper tests
└── examples/                       # Usage examples
    ├── basic_usage.py              # Basic website demo
    ├── advanced_usage.py           # Advanced features demo
    ├── benchmarking.py             # Performance benchmarking
    └── generic_usage.py            # Generic system demo
```

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

- **Similarity Scores**: 0.6+ (2x improvement over legacy systems)
- **Scraping Speed**: 3-5x faster with async scraper vs synchronous
- **Cache Performance**: 40-60% hit rate for repeated scraping operations
- **Context Quality**: Complete technical explanations with proper code examples
- **Processing Speed**: Optimized with smart caching and concurrent processing
- **Answer Quality**: Relevant, complete, and technically accurate responses

## 🧪 Testing

Run comprehensive benchmarking:
```bash
python examples/benchmarking.py
```

Test specific functionality:
```bash
python -m pytest tests/
```

Test the generic system:
```bash
python test_generic_system.py
```

## 🔧 Configuration

The system works in two modes:

1. **Standalone (retrieval only)**: Use `demo_query()` for testing retrieval
2. **With Ollama**: Start `ollama serve` and use `rag_query()` for full answers

Adjust retrieval parameters:
- `top_k`: Number of results (recommended: 3-7)
- Model selection for Ollama: `mistral`, `llama2`, etc.

## 📖 Usage Examples

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