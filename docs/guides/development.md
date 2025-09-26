# Development Guide

This guide covers setting up a development environment and contributing to the Universal RAG System.

## Prerequisites

- Python 3.10 or higher
- Git
- (Optional) Ollama for full text generation capabilities

## Development Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black isort mypy
```

### 2. Project Structure

```
├── docs/                    # Documentation
│   ├── api/                # API documentation
│   ├── guides/             # User guides
│   └── examples/           # Example documentation
├── src/                    # Source code
│   ├── __init__.py
│   ├── rag_system.py       # Main RAG system
│   ├── web_scraper.py      # Sync web scraper
│   └── async_web_scraper.py # Async web scraper
├── tests/                  # Test files
├── examples/               # Usage examples
├── notebooks/              # Jupyter notebooks
└── data/                   # Data files (generated)
```

### 3. Development Workflow

#### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_rag_system.py

# Run with coverage
python -m pytest --cov=src tests/
```

#### Code Formatting

```bash
# Format code with black
black src/ tests/ examples/

# Sort imports with isort
isort src/ tests/ examples/

# Type checking with mypy
mypy src/
```

#### Running Examples

```bash
# Basic usage example
python examples/basic_usage.py

# Advanced features
python examples/advanced_usage.py

# Performance benchmarking
python examples/benchmarking.py
```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Use descriptive variable names
- Maximum line length: 88 characters (Black default)

### Docstring Format

Use Google-style docstrings:

```python
def scrape_website(start_urls: List[str], max_pages: int = 30) -> bool:
    """Scrape a website for RAG processing.

    Args:
        start_urls: List of URLs to start scraping from
        max_pages: Maximum number of pages to scrape

    Returns:
        True if scraping was successful, False otherwise

    Raises:
        ValueError: If start_urls is empty
        NetworkError: If unable to connect to any URLs
    """
```

### Testing Guidelines

- Write tests for all new functionality
- Aim for >90% test coverage
- Use descriptive test names
- Include both unit tests and integration tests

Example test structure:

```python
import pytest
from src.rag_system import RAGSystem

class TestRAGSystem:
    def test_initialization(self):
        """Test RAG system initializes correctly."""
        rag = RAGSystem()
        assert rag.data_dir == "data"
        assert rag.cache_enabled is True

    def test_invalid_input_handling(self):
        """Test system handles invalid inputs gracefully."""
        rag = RAGSystem()
        with pytest.raises(ValueError):
            rag.scrape_and_process_website([])
```

### Adding New Features

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement feature with tests**:
   - Add functionality to appropriate module
   - Write comprehensive tests
   - Update documentation

3. **Run quality checks**:
   ```bash
   # Run tests
   python -m pytest tests/

   # Format code
   black src/ tests/
   isort src/ tests/

   # Type checking
   mypy src/
   ```

4. **Update documentation**:
   - Update API documentation if needed
   - Add examples for new features
   - Update relevant guides

5. **Submit pull request**:
   - Clear description of changes
   - Reference any related issues
   - Ensure CI passes

## Working with Components

### RAG System Development

The `RAGSystem` class is the main interface. Key areas for development:

- **Retrieval improvements**: Enhance TF-IDF scoring, add new similarity metrics
- **Generation improvements**: Better prompt engineering, model integration
- **Performance**: Caching strategies, batch processing
- **Features**: New content types, metadata extraction

### Web Scraper Development

Two scraper implementations available:

1. **Synchronous** (`web_scraper.py`): Reliable, simpler debugging
2. **Asynchronous** (`async_web_scraper.py`): High performance, complex

Key development areas:

- **Content extraction**: Better HTML parsing, new content types
- **Performance**: Caching, rate limiting, concurrent processing
- **Robustness**: Error handling, retry logic, edge cases
- **Features**: New metadata types, content filtering

### Testing Strategies

#### Unit Tests
Test individual functions and classes in isolation:

```python
def test_extract_content():
    scraper = WebScraper()
    html = "<h1>Title</h1><p>Content</p>"
    soup = BeautifulSoup(html, 'html.parser')

    content = scraper.extract_content(soup, "http://example.com")

    assert len(content) > 0
    assert content[0]['content_type'] == 'heading'
```

#### Integration Tests
Test component interactions:

```python
def test_full_rag_pipeline():
    rag = RAGSystem()

    # Mock website data
    success = rag.scrape_and_process_website(["http://example.com"])
    assert success

    # Test query
    result = rag.demo_query("test query")
    assert 'chunks' in result
```

#### Performance Tests
Monitor performance regressions:

```python
import time

def test_scraping_performance():
    start_time = time.time()

    scraper = AsyncWebScraper()
    success, metrics = asyncio.run(
        scraper.scrape_website(["http://example.com"])
    )

    elapsed = time.time() - start_time
    assert elapsed < 60  # Should complete within 1 minute
```

## Debugging Tips

### Common Issues

1. **Import errors**: Check PYTHONPATH includes project root
2. **Async errors**: Ensure proper await/async usage
3. **Network timeouts**: Adjust timeout settings for slow connections
4. **Memory issues**: Use chunked processing for large websites

### Debugging Tools

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Profile performance
import cProfile
cProfile.run('your_function()')
```

### Testing with Local HTML

For development/testing without network requests:

```python
# Create test HTML files
html_content = """
<html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Heading</h1>
        <p>Test content</p>
    </body>
</html>
"""

with open("test.html", "w") as f:
    f.write(html_content)

# Test with local file
from pathlib import Path
test_file = f"file://{Path('test.html').absolute()}"
```

## Contributing

### Before Submitting

1. Ensure all tests pass
2. Update documentation
3. Follow code style guidelines
4. Add appropriate logging
5. Handle edge cases gracefully

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: What changes were made and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant docs
- **Breaking changes**: Clearly marked and justified

### Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release notes
4. Tag release in Git
5. Update documentation

## Getting Help

- Check existing issues on GitHub
- Review documentation in `/docs`
- Run examples to understand usage patterns
- Use debugging tools and logging for troubleshooting