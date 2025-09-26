# Documentation

Comprehensive documentation for the Universal RAG System - an advanced Retrieval-Augmented Generation system that works with any website.

## 📖 Quick Navigation

### 🚀 Getting Started
- [Getting Started Guide](./guides/getting-started.md) - Complete beginner tutorial
- [Installation](./guides/getting-started.md#quick-installation) - Setup instructions
- [Quick Examples](./guides/getting-started.md#your-first-rag-query) - Get running in 5 minutes

### 📚 API Reference
- [API Overview](./api/README.md) - Complete API documentation
- [RAG System API](./api/rag_system.md) - Main system interface
- [Async Web Scraper API](./api/async_web_scraper.md) - High-performance scraping
- [Web Scraper API](./api/web_scraper.md) - Synchronous scraping

### 👨‍💻 Development
- [Architecture Overview](./architecture.md) - System design and components

### 📋 User Guides
- [Performance Optimization](./guides/performance.md) - Tips for optimal performance
- [Troubleshooting](./guides/troubleshooting.md) - Common issues and solutions

## 🏗️ System Architecture

The Universal RAG System consists of three main components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Scraper   │───▶│   RAG System     │───▶│  Text Generator │
│                 │    │                  │    │   (Ollama)      │
│ • Async/Sync    │    │ • TF-IDF         │    │ • Local LLMs    │
│ • Structure     │    │ • Semantic       │    │ • Mistral       │
│ • Metadata      │    │ • Caching        │    │ • Llama2        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 Key Features

- **🌍 Universal**: Works with any website automatically
- **🏗️ Structure-Aware**: Preserves HTML hierarchy and document structure
- **⚡ High Performance**: Async scraping with 3-5x speed improvement
- **🧠 Smart Retrieval**: Enhanced TF-IDF with semantic chunking
- **🤖 Local LLMs**: Integration with Ollama for text generation
- **📊 Rich Metadata**: Page titles, sections, content types, domains

## 📊 Performance Benchmarks

| Feature | Performance |
|---------|-------------|
| Similarity Scores | 0.6+ (2x improvement) |
| Scraping Speed | 3-5x faster with async |
| Cache Hit Rate | 40-60% for repeated operations |
| Memory Efficiency | Optimized for large sites |

## 🔧 Quick Example

```python
from src.rag_system import RAGSystem

# Initialize and scrape
rag = RAGSystem()
success = rag.scrape_and_process_website([
    "https://fastapi.tiangolo.com/"
], max_pages=20)

# Query with retrieval only
result = rag.demo_query("How to create API endpoints?", top_k=3)

# Full generation with Ollama
answer = rag.rag_query("How to create API endpoints?", model="mistral")
```

## 📁 Documentation Structure

```
docs/
├── README.md                 # This file
├── architecture.md           # System architecture
├── api/                      # API documentation
│   ├── README.md
│   ├── rag_system.md
│   ├── async_web_scraper.md
│   └── web_scraper.md
└── guides/                   # User guides
    ├── README.md
    ├── getting-started.md
    ├── performance.md
    └── troubleshooting.md
```

## 🤝 Contributing to Documentation

When contributing to documentation:

1. **Follow the existing structure** and formatting
2. **Include code examples** for new features
3. **Update multiple sections** if changes affect various areas
4. **Test examples** to ensure they work
5. **Use clear, concise language** suitable for all skill levels

## 📋 Documentation Standards

### Formatting Guidelines
- Use clear headings with emoji prefixes for visual hierarchy
- Include code examples with syntax highlighting
- Provide both basic and advanced usage examples
- Link between related documentation sections
- Use consistent terminology throughout

### Content Guidelines
- Explain the "why" not just the "how"
- Include common use cases and patterns
- Provide troubleshooting information
- Keep examples up-to-date with current API
- Focus on practical, actionable information

## 🔍 Finding Information

### For Beginners
Start with the [Getting Started Guide](./guides/getting-started.md) for a comprehensive introduction.

### For API Usage
Check the [API Reference](./api/README.md) for detailed method documentation.

### For System Architecture
Review the [Architecture Guide](./architecture.md) for system design details.

### For Performance
See the [Performance Guide](./guides/performance.md) for optimization strategies.

### For Troubleshooting
Visit [Troubleshooting](./guides/troubleshooting.md) for common issues and solutions.

## 📈 Recent Updates

- **Async Scraper**: High-performance concurrent processing
- **Enhanced API Documentation**: Complete with examples and error handling
- **Architecture Overview**: Detailed system design documentation
- **Performance Guide**: Optimization strategies and benchmarks
- **Troubleshooting Guide**: Comprehensive problem-solving resource

## 💡 Need Help?

- 📖 **Documentation**: Browse these docs for comprehensive information
- 🐛 **Issues**: Report bugs on GitHub
- 💬 **Discussions**: Ask questions in GitHub discussions
- 🚀 **Examples**: Check the `/examples` directory for working code
- 📧 **Contact**: Reach out to maintainers for support

## 🔗 Quick Links

| Topic | Link |
|-------|------|
| Getting Started | [guides/getting-started.md](./guides/getting-started.md) |
| API Reference | [api/README.md](./api/README.md) |
| System Architecture | [architecture.md](./architecture.md) |
| Performance Tips | [guides/performance.md](./guides/performance.md) |
| Troubleshooting | [guides/troubleshooting.md](./guides/troubleshooting.md) |

---

*Documentation last updated: December 2024*