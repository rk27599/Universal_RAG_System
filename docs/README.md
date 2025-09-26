# Documentation

Comprehensive documentation for the Universal RAG System.

## 📖 Quick Navigation

### 🚀 Getting Started
- [Getting Started Guide](./guides/getting-started.md) - Quick start and basic usage
- [Installation](./guides/getting-started.md#quick-installation) - Setup instructions

### 📚 API Reference
- [API Overview](./api/README.md) - Complete API documentation
- [RAG System API](./api/rag_system.md) - Main system interface
- [Async Web Scraper API](./api/async_web_scraper.md) - High-performance scraping

### 👨‍💻 Development
- [Development Guide](./guides/development.md) - Setup dev environment
- [Architecture Overview](./architecture.md) - System design and components

### 📋 Guides
- [Performance Optimization](./guides/performance.md) - Tips for optimal performance
- [Troubleshooting](./guides/troubleshooting.md) - Common issues and solutions
- [Deployment](./guides/deployment.md) - Production deployment

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
- **⚡ High Performance**: Async scraping with intelligent caching
- **🧠 Smart Retrieval**: Enhanced TF-IDF with semantic chunking
- **🤖 Local LLMs**: Integration with Ollama for text generation
- **📊 Rich Metadata**: Page titles, sections, content types, domains

## 📊 Performance Benchmarks

| Feature | Performance |
|---------|-------------|
| Similarity Scores | 0.6+ (2x improvement) |
| Processing Speed | 3-5x faster with async |
| Cache Hit Rate | 40-60% for repeated scraping |
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
│   └── async_web_scraper.md
├── guides/                   # User guides
│   ├── README.md
│   ├── getting-started.md
│   ├── development.md
│   ├── performance.md
│   ├── troubleshooting.md
│   └── deployment.md
└── examples/                 # Example documentation
    └── README.md
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
- Use clear headings with emoji prefixes
- Include code examples with syntax highlighting
- Provide both basic and advanced usage examples
- Link between related documentation sections

### Content Guidelines
- Explain the "why" not just the "how"
- Include common use cases and patterns
- Provide troubleshooting information
- Keep examples up-to-date with current API

## 🔍 Finding Information

### For Beginners
Start with the [Getting Started Guide](./guides/getting-started.md) for a comprehensive introduction.

### For API Usage
Check the [API Reference](./api/README.md) for detailed method documentation.

### For Developers
Review the [Development Guide](./guides/development.md) for contribution guidelines.

### For Troubleshooting
Visit [Troubleshooting](./guides/troubleshooting.md) for common issues and solutions.

## 📝 Recent Updates

- **API Documentation**: Complete API reference with examples
- **Architecture Overview**: System design and component interaction
- **Performance Guide**: Optimization tips and benchmarks
- **Development Guide**: Comprehensive development setup
- **Getting Started**: Step-by-step beginner guide

## 💡 Need Help?

- 📖 **Documentation**: Browse these docs for comprehensive information
- 🐛 **Issues**: Report bugs on GitHub
- 💬 **Discussions**: Ask questions in GitHub discussions
- 📧 **Contact**: Reach out to maintainers for support

---

*Last updated: September 2024*