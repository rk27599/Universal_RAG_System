# Getting Started

Welcome to the Universal RAG System! This guide will help you get up and running quickly.

## What is the Universal RAG System?

The Universal RAG System is an advanced **Retrieval-Augmented Generation** system that can work with **any website**. It combines intelligent web scraping, semantic chunking, enhanced retrieval, and optional text generation via local LLMs.

### Key Features

- 🌍 **Works with any website** - Documentation, blogs, APIs, wikis
- 🏗️ **Structure-aware** - Preserves HTML hierarchy and document structure
- 🧠 **Semantic chunking** - Respects content sections vs random splits
- 🔍 **Enhanced retrieval** - High similarity scores with intelligent boosting
- ⚡ **High performance** - Async scraping and intelligent caching
- 🤖 **Local LLM integration** - Works with Ollama for text generation

## Quick Installation

### Prerequisites

- Python 3.10 or higher
- Internet connection for web scraping

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG

# Install required packages
pip install -r requirements.txt
```

### Optional: Install Ollama for Text Generation

```bash
# Install Ollama (visit https://ollama.ai for installation)
# Then pull a model:
ollama pull mistral
```

## Your First RAG Query

Let's start with a simple example using FastAPI documentation:

```python
from src.rag_system import RAGSystem

# Initialize the system
rag = RAGSystem()

# Scrape and process FastAPI documentation
success = rag.scrape_and_process_website(
    start_urls=["https://fastapi.tiangolo.com/"],
    max_pages=20  # Start small for testing
)

if success:
    print("✅ Website scraped successfully!")

    # Test retrieval (no text generation)
    result = rag.demo_query("How to create an API endpoint?", top_k=3)

    print(f"Found {len(result['chunks'])} relevant chunks:")
    for i, chunk in enumerate(result['chunks'][:2]):
        print(f"\n--- Result {i+1} (Score: {chunk['score']:.3f}) ---")
        print(f"Page: {chunk['metadata']['page_title']}")
        print(f"Content: {chunk['content'][:200]}...")
```

## Understanding the Results

The `demo_query()` method returns a dictionary with:

```python
{
    'query': 'Your original query',
    'chunks': [
        {
            'content': 'Relevant text content',
            'score': 0.756,  # Similarity score (higher = more relevant)
            'metadata': {
                'page_title': 'Page Title',
                'section_hierarchy': ['Main', 'Sub-section'],
                'content_type': 'paragraph',
                'domain': 'fastapi.tiangolo.com',
                'url': 'https://...'
            }
        }
    ]
}
```

## Using with Text Generation

If you have Ollama installed and running:

```bash
# Start Ollama server (in another terminal)
ollama serve

# Make sure you have a model installed
ollama pull mistral
```

Then use full RAG generation:

```python
# Full text generation with context
answer = rag.rag_query(
    "How to create an API endpoint in FastAPI?",
    top_k=5,
    model="mistral"
)

print("Generated Answer:")
print(answer)
```

This will:
1. Find the top 5 most relevant chunks
2. Use them as context for the LLM
3. Generate a complete answer based on the documentation

## Working with Different Websites

The system works with any website. Here are some examples:

### Python Documentation
```python
rag.scrape_and_process_website([
    "https://docs.python.org/3/"
], max_pages=30)

result = rag.demo_query("How to define functions?")
```

### React Documentation
```python
rag.scrape_and_process_website([
    "https://reactjs.org/docs/"
], max_pages=25)

result = rag.demo_query("How to use hooks?")
```

### Node.js Documentation
```python
rag.scrape_and_process_website([
    "https://nodejs.org/en/docs/"
], max_pages=20)

result = rag.demo_query("How to create HTTP servers?")
```

## Configuration Options

### Scraping Configuration

```python
# Customize scraping behavior
success = rag.scrape_and_process_website(
    start_urls=["https://your-website.com/"],
    max_pages=50,           # More pages
    max_depth=3,            # Deeper crawling
    same_domain_only=True,  # Stay within domain
    output_file="data/custom_docs.json"  # Custom file name
)
```

### Query Configuration

```python
# Adjust retrieval parameters
result = rag.demo_query(
    "Your question",
    top_k=7  # More context chunks
)

# Adjust generation parameters
answer = rag.rag_query(
    "Your question",
    top_k=5,
    model="llama2",      # Different model
    temperature=0.3      # More focused responses
)
```

## Interactive Notebook

For experimentation, try the Jupyter notebook:

```bash
# Start Jupyter
jupyter notebook notebooks/RAG_HTML.ipynb

# Or Jupyter Lab
jupyter lab notebooks/RAG_HTML.ipynb
```

The notebook provides an interactive interface to:
- Scrape websites
- Test queries
- Explore results
- Visualize similarity scores

## Running Examples

The project includes several example scripts:

```bash
# Basic usage with FastAPI docs
python examples/basic_usage.py

# Advanced features demonstration
python examples/advanced_usage.py

# Interactive demo with multiple websites
python examples/generic_usage.py

# Performance benchmarking
python examples/benchmarking.py
```

## Common Use Cases

### 1. Technical Documentation Q&A
```python
# Process documentation
rag.scrape_and_process_website(["https://docs.framework.com/"])

# Ask technical questions
answer = rag.rag_query("How to configure authentication?")
```

### 2. API Reference Assistant
```python
# Process API docs
rag.scrape_and_process_website(["https://api.service.com/docs/"])

# Get API usage examples
result = rag.demo_query("POST request examples")
```

### 3. Learning Assistant
```python
# Process educational content
rag.scrape_and_process_website(["https://tutorial-site.com/"])

# Ask learning questions
answer = rag.rag_query("Explain concepts with examples")
```

## Performance Tips

### Start Small
Begin with `max_pages=10-20` to test, then increase for production use.

### Use Caching
The system automatically caches processed data. Repeated queries are much faster.

### Optimal top_k Values
- `top_k=3`: Quick, focused answers
- `top_k=5-7`: Balanced context and performance
- `top_k=10+`: Comprehensive but slower

### Async for Speed
For large websites, consider the async scraper:

```python
import asyncio
from src.async_web_scraper import AsyncWebScraper

async def fast_scrape():
    scraper = AsyncWebScraper()
    success, metrics = await scraper.scrape_website([
        "https://docs.python.org/"
    ])
    print(f"Processed {metrics.urls_processed} pages")

asyncio.run(fast_scrape())
```

## Troubleshooting

### Common Issues

1. **Low similarity scores** (< 0.3): Try different query phrasing
2. **No results**: Check if website was scraped successfully
3. **Ollama connection error**: Ensure `ollama serve` is running
4. **Memory issues**: Reduce `max_pages` or use chunked processing

### Getting Help

- Check the [Troubleshooting Guide](./troubleshooting.md)
- Review [API Documentation](../api/README.md)
- Run example scripts to see expected behavior
- Enable debug logging for detailed information

## Next Steps

Once you're comfortable with the basics:

1. **Explore Advanced Features**: Check out `examples/advanced_usage.py`
2. **Customize for Your Needs**: Review the [Development Guide](./development.md)
3. **Optimize Performance**: See the [Performance Guide](./performance.md)
4. **Deploy to Production**: Follow the [Deployment Guide](./deployment.md)

Happy querying! 🚀