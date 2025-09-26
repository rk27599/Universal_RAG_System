# Troubleshooting Guide

Common issues and solutions for the Universal RAG System.

## 🚨 Common Issues

### Installation and Setup Issues

#### Issue: ModuleNotFoundError
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Ensure you're in the project root directory
cd Python_RAG

# Install dependencies
pip install -r requirements.txt

# Add project to Python path (temporary)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
python -m src.rag_system
```

#### Issue: Requirements Installation Fails
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solution:**
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Update pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Web Scraping Issues

#### Issue: Low Similarity Scores (< 0.3)
**Symptoms**: Query results have very low similarity scores

**Causes & Solutions:**
1. **Query phrasing**: Try rephrasing your query with different terms
2. **Limited content**: Increase `max_pages` parameter
3. **Wrong domain**: Ensure you're scraping relevant content

```python
# Try different query variations
queries = [
    "How to create functions?",
    "Function definition syntax",
    "Define Python functions"
]

for query in queries:
    result = rag.demo_query(query, top_k=5)
    print(f"Query: {query}, Best score: {result['chunks'][0]['score']:.3f}")
```

#### Issue: No Results Found
**Symptoms**: Empty results or error messages

**Solutions:**
```python
# Check if data was loaded successfully
rag = RAGSystem()
stats = rag.get_stats()
print(f"Loaded {stats.get('total_chunks', 0)} chunks")

# Try broader queries
result = rag.demo_query("python", top_k=10)  # Very general query

# Check data file exists
import os
if not os.path.exists("data/website_docs.json"):
    print("No data file found - need to scrape first")
```

#### Issue: Scraping Fails
**Symptoms**: `scrape_and_process_website()` returns `False`

**Debugging Steps:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
rag = RAGSystem()
success = rag.scrape_and_process_website([
    "https://docs.python.org/"
], max_pages=5)  # Start small

# Check common issues:
# 1. Network connectivity
# 2. Website blocks automated requests
# 3. robots.txt restrictions
# 4. SSL certificate issues
```

### Performance Issues

#### Issue: Slow Scraping Performance
**Symptoms**: Scraping takes very long time

**Solutions:**
```python
# Use async scraper for better performance
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

async def fast_scrape():
    config = ScrapingConfig(
        concurrent_limit=6,
        requests_per_second=8.0
    )

    scraper = AsyncWebScraper(config)
    success, metrics = await scraper.scrape_website([
        "https://docs.python.org/"
    ])

    print(f"Processed {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")

asyncio.run(fast_scrape())
```

#### Issue: High Memory Usage
**Symptoms**: System runs out of memory with large websites

**Solutions:**
```python
# Reduce max_pages
rag.scrape_and_process_website([url], max_pages=20)  # Instead of 100

# Process in batches
urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
for url in urls:
    rag.scrape_and_process_website([url], max_pages=15)
    # Data accumulates across calls
```

### Ollama Integration Issues

#### Issue: Ollama Connection Error
```
ConnectionError: Failed to connect to Ollama API
```

**Solutions:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama server
ollama serve

# In another terminal, check available models
ollama list

# Pull required model if not available
ollama pull mistral
```

#### Issue: Slow Generation Performance
**Symptoms**: `rag_query()` takes very long time

**Solutions:**
```python
# Use smaller, faster models
answer = rag.rag_query("query", model="tinyllama")  # Faster but less capable

# Reduce context size
answer = rag.rag_query("query", top_k=3)  # Instead of top_k=10

# Adjust temperature for faster generation
answer = rag.rag_query("query", temperature=0.1)  # More deterministic
```

#### Issue: Poor Generation Quality
**Symptoms**: Generated answers are irrelevant or incorrect

**Solutions:**
```python
# Increase context size
answer = rag.rag_query("query", top_k=7)  # More context

# Try different models
models_to_try = ["mistral", "llama2", "codellama"]
for model in models_to_try:
    try:
        answer = rag.rag_query("query", model=model)
        print(f"Model {model}: {answer[:100]}...")
    except Exception as e:
        print(f"Model {model} failed: {e}")

# Check retrieval quality first
result = rag.demo_query("query", top_k=5)
for i, chunk in enumerate(result['chunks']):
    print(f"Chunk {i}: Score={chunk['score']:.3f}")
    print(f"Content: {chunk['content'][:150]}...")
```

## 🔧 Debugging Techniques

### Enable Debug Logging
```python
import logging

# Enable debug logging for all components
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or specific components
logger = logging.getLogger('src.rag_system')
logger.setLevel(logging.DEBUG)
```

### Inspect Data Files
```python
import json

# Check scraped data
with open('data/website_docs.json', 'r') as f:
    data = json.load(f)

print(f"Total documents: {len(data)}")
print(f"First document keys: {list(data[0].keys())}")
print(f"Content types: {set(doc['content_type'] for doc in data)}")
```

### Test Individual Components
```python
# Test scraper only
from src.web_scraper import WebScraper
scraper = WebScraper()
success = scraper.scrape_website(["https://example.com"], "test_output.json")

# Test RAG system with existing data
rag = RAGSystem()
rag.load_data("data/website_docs.json")
result = rag.demo_query("test query")
```

## 🔍 Performance Analysis

### Profiling Scraping Performance
```python
import time
import cProfile

def profile_scraping():
    start_time = time.time()

    rag = RAGSystem()
    success = rag.scrape_and_process_website([
        "https://docs.python.org/"
    ], max_pages=10)

    elapsed = time.time() - start_time
    print(f"Scraping took {elapsed:.1f} seconds")

    return success

# Profile the function
cProfile.run('profile_scraping()')
```

### Monitoring Resource Usage
```python
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")

# Monitor during scraping
monitor_memory()
rag.scrape_and_process_website([url])
monitor_memory()
```

## 📞 Getting Additional Help

### Before Asking for Help

1. **Check logs**: Enable debug logging and review error messages
2. **Verify setup**: Ensure all dependencies are installed correctly
3. **Test with examples**: Run provided example scripts
4. **Check network**: Verify internet connectivity and website accessibility
5. **Try different websites**: Some sites may block automated requests

### Information to Include

When reporting issues, please include:

- **Python version**: `python --version`
- **Operating system**: Windows/macOS/Linux
- **Error messages**: Complete error traceback
- **Code snippet**: Minimal example that reproduces the issue
- **Expected vs actual behavior**: What should happen vs what happens

### Useful Diagnostic Commands

```bash
# System information
python --version
pip list | grep -E "(beautifulsoup4|requests|scikit-learn|numpy)"

# Network connectivity
ping google.com
curl -I https://docs.python.org/

# File system
ls -la data/
du -sh data/

# Ollama (if used)
ollama list
curl http://localhost:11434/api/version
```

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check the `/docs` directory for detailed guides
- **Examples**: Review `/examples` for working code patterns
- **Tests**: Look at `/tests` for usage patterns and edge cases

## 🐛 Known Issues

### Website-Specific Issues

1. **JavaScript-heavy sites**: May not scrape dynamic content properly
2. **Rate limiting**: Some sites aggressively limit automated requests
3. **Authentication**: Cannot access login-protected content
4. **Dynamic content**: SPAs and AJAX-loaded content may be missed

### Workarounds

```python
# For JavaScript sites, try different starting URLs
# Look for direct documentation links that serve static HTML

# For rate limiting, reduce concurrent requests
config = ScrapingConfig(
    concurrent_limit=2,
    requests_per_second=2.0
)

# For authentication, scrape public documentation instead
```

### System Limitations

1. **Memory usage**: Large websites may consume significant memory
2. **Processing time**: Initial scraping can be time-consuming
3. **Storage space**: Cached data files can become large

Remember: Most issues can be resolved by starting with small test cases and gradually scaling up! 🚀