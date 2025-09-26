# Troubleshooting Guide

Comprehensive solutions for common issues with the Universal RAG System.

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

# Or run from project root with module syntax
python -m examples.basic_usage
```

#### Issue: Requirements Installation Fails
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solutions:**
```bash
# Use virtual environment (recommended)
python -m venv rag_env
source rag_env/bin/activate  # On Windows: rag_env\Scripts\activate

# Update pip first
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Alternative: Install individually
pip install requests beautifulsoup4 scikit-learn numpy aiohttp aiofiles
```

### Web Scraping Issues

#### Issue: Low Similarity Scores (< 0.3)
**Symptoms**: Query results have very low similarity scores, poor relevance

**Causes & Solutions:**

1. **Query phrasing issues**:
```python
# ❌ Too specific or technical jargon
result = rag.demo_query("instantiate FastAPI middleware for CORS preflight", top_k=3)

# ✅ Use natural language
result = rag.demo_query("how to enable CORS in FastAPI", top_k=3)

# ✅ Try multiple phrasings
queries = [
    "How to create functions?",
    "Function definition syntax",
    "Define Python functions",
    "Creating functions in Python"
]
```

2. **Insufficient content**:
```python
# Check if data was loaded successfully
try:
    result = rag.demo_query("test", top_k=1)
    if "No documents" in result or len(result.strip()) < 50:
        print("⚠️ Low content volume - increase max_pages")
        # Increase scraping scope
        success = rag.scrape_and_process_website([url], max_pages=50)
    else:
        print("✅ Sufficient content available")
except Exception as e:
    print(f"❌ No data loaded: {e}")
```

3. **Wrong domain/content type**:
```python
# Test with a domain-specific query
result = rag.demo_query("python", top_k=1)
if "No documents" in result:
    print("❌ No Python docs found - scrape Python documentation first")
else:
    print("✅ Python documentation appears to be available")
```

#### Issue: No Results Found
**Symptoms**: Empty results or "No relevant content found" messages

**Diagnosis Steps:**
```python
def diagnose_no_results():
    rag = RAGSystem()

    # Step 1: Check if data exists
    try:
        test_result = rag.demo_query("test", top_k=1)
        if "No documents" in test_result or len(test_result.strip()) < 20:
            print("❌ No data loaded - need to scrape or load data first")
            return
        else:
            print("✅ Data appears to be loaded")

    except Exception as e:
        print(f"❌ No data loaded: {e}")
        return

    # Step 2: Test with very broad query
    broad_result = rag.demo_query("python", top_k=10)
    if "No documents" in broad_result or len(broad_result.strip()) < 50:
        print("❌ Even broad queries return nothing - data loading issue")
        return

    # Step 3: Test with specific query
    specific_result = rag.demo_query("your original query here", top_k=10)
    if "No documents" in specific_result or len(specific_result.strip()) < 50:
        print("⚠️ Specific query too narrow - try broader terms")

    print("✅ Diagnosis complete")

diagnose_no_results()
```

**Solutions:**
```python
# 1. Load data if not loaded
# Test if data is loaded by trying a simple query
try:
    test_result = rag.demo_query("test", top_k=1)
    if "No documents" in test_result or not test_result.strip():
        has_data = False
    else:
        has_data = True
except Exception:
    has_data = False

if not has_data:
    rag.load_data("data/website_docs.json")

# 2. Try broader queries first
result = rag.demo_query("API", top_k=10)  # Very general
if "No documents" not in result and result.strip():
    print("✅ Data exists, refine your query")

# 3. Inspect your scraped data manually
# Check the JSON file directly to see what content is available
import json
try:
    with open("data/website_docs.json", 'r') as f:
        data = json.load(f)
    print(f"Available content types: {set(doc['content_type'] for doc in data)}")
    print(f"Sample pages: {list(set(doc['metadata']['page_title'] for doc in data))[:3]}")
except Exception as e:
    print(f"Cannot inspect data file: {e}")
```

#### Issue: Scraping Fails Completely
**Symptoms**: `scrape_and_process_website()` returns `False`

**Debugging Steps:**
```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')

def debug_scraping_failure():
    rag = RAGSystem()

    print("🔍 Debugging scraping failure...")

    # Test with minimal settings first
    test_urls = [
        "https://httpbin.org/html",  # Simple test page
        "https://example.com/",      # Basic page
        "https://docs.python.org/3/" # Your target
    ]

    for url in test_urls:
        print(f"\n--- Testing {url} ---")
        success = rag.scrape_and_process_website(
            [url],
            max_pages=3,  # Minimal
            max_depth=1,  # Shallow
            output_file=f"debug_{url.split('//')[1].split('/')[0]}.json"
        )

        if success:
            print(f"✅ {url} works")
            break
        else:
            print(f"❌ {url} failed")

    # Check common issues
    print("\n🔍 Checking common issues:")

    # Network connectivity
    try:
        import requests
        response = requests.get("https://httpbin.org/ip", timeout=10)
        print(f"✅ Network connectivity OK: {response.status_code}")
    except Exception as e:
        print(f"❌ Network issue: {e}")

    # DNS resolution
    try:
        import socket
        socket.gethostbyname('docs.python.org')
        print("✅ DNS resolution OK")
    except Exception as e:
        print(f"❌ DNS issue: {e}")

debug_scraping_failure()
```

### Performance Issues

#### Issue: Extremely Slow Scraping
**Symptoms**: Scraping takes much longer than expected

**Solutions:**

1. **Use Async Scraper for large sites**:
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

async def faster_scraping():
    config = ScrapingConfig(
        concurrent_limit=6,
        requests_per_second=8.0,
        max_pages=50
    )

    scraper = AsyncWebScraper(config)
    success, metrics = await scraper.scrape_website([url])

    print(f"⚡ Completed in {metrics.elapsed_time:.1f} seconds")
    return success

# Run async version
success = asyncio.run(faster_scraping())
```

2. **Optimize sync scraper settings**:
```python
# Reduce scope for testing
success = rag.scrape_and_process_website(
    [url],
    max_pages=10,    # Smaller scope
    max_depth=1,     # Less depth
    same_domain_only=True  # Stay focused
)
```

3. **Check for site-specific issues**:
```python
def analyze_scraping_speed():
    import time

    test_sites = [
        ("https://httpbin.org/html", "Simple test"),
        ("https://docs.python.org/3/", "Your target site")
    ]

    for url, description in test_sites:
        start_time = time.time()

        rag = RAGSystem()
        success = rag.scrape_and_process_website([url], max_pages=5)

        elapsed = time.time() - start_time

        if success:
            print(f"✅ {description}: {elapsed:.1f}s for 5 pages")
        else:
            print(f"❌ {description}: Failed after {elapsed:.1f}s")

analyze_scraping_speed()
```

#### Issue: High Memory Usage
**Symptoms**: System runs out of memory during scraping

**Solutions:**

1. **Process in smaller batches**:
```python
def memory_efficient_scraping(base_url, total_pages=100):
    rag = RAGSystem()
    batch_size = 20

    for i in range(0, total_pages, batch_size):
        print(f"Processing batch {i//batch_size + 1}...")

        success = rag.scrape_and_process_website(
            [base_url],
            max_pages=min(batch_size, total_pages - i),
            output_file=f"data/batch_{i}.json"
        )

        if success:
            print(f"✅ Batch {i//batch_size + 1} complete")

        # Data accumulates across calls

    return rag

# Use memory-efficient approach
rag = memory_efficient_scraping("https://docs.python.org/", 60)
```

2. **Monitor memory usage**:
```python
import psutil
import os

def monitor_memory_usage():
    process = psutil.Process(os.getpid())

    def get_memory_mb():
        return process.memory_info().rss / 1024 / 1024

    print(f"Initial memory: {get_memory_mb():.1f} MB")

    rag = RAGSystem()
    print(f"After init: {get_memory_mb():.1f} MB")

    success = rag.scrape_and_process_website([url], max_pages=30)
    print(f"After scraping: {get_memory_mb():.1f} MB")

    result = rag.demo_query("test query")
    print(f"After query: {get_memory_mb():.1f} MB")

monitor_memory_usage()
```

### Ollama Integration Issues

#### Issue: Ollama Connection Error
```
ConnectionError: Failed to connect to Ollama API
```

**Diagnosis:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not running, start Ollama
ollama serve
```

**Solutions:**
```python
def test_ollama_connection():
    import requests

    try:
        # Test Ollama API
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")

            # Check available models
            models_response = requests.get("http://localhost:11434/api/tags")
            if models_response.status_code == 200:
                models = models_response.json()
                print(f"📋 Available models: {[m['name'] for m in models.get('models', [])]}")

        else:
            print(f"❌ Ollama API returned {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama - is 'ollama serve' running?")
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")

test_ollama_connection()
```

**Manual Setup:**
```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull a model
ollama pull mistral

# Terminal 3: Test with curl
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Hello, world!"
}'
```

#### Issue: Model Not Found
```
Error: Model 'mistral' not found
```

**Solutions:**
```bash
# List available models
ollama list

# Pull the model you need
ollama pull mistral
ollama pull llama2

# For coding tasks
ollama pull codellama
```

#### Issue: Slow Generation Performance
**Symptoms**: `rag_query()` takes very long time

**Optimization:**
```python
# Use smaller, faster models
fast_models = ["tinyllama", "phi"]

for model in fast_models:
    try:
        start_time = time.time()
        answer = rag.rag_query("test question", model=model, top_k=3)
        elapsed = time.time() - start_time

        print(f"Model {model}: {elapsed:.1f}s")
        print(f"Answer quality: {len(answer)} characters")

    except Exception as e:
        print(f"Model {model} failed: {e}")

# Reduce context size
answer = rag.rag_query("question", top_k=3)  # Instead of top_k=10

# Use lower temperature for faster generation
answer = rag.rag_query("question", temperature=0.1)  # More deterministic
```

## 🔧 Debugging Tools and Techniques

### Enable Debug Logging

```python
import logging

# Enable debug logging for all components
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_debug.log'),
        logging.StreamHandler()
    ]
)

# Or target specific components
logger = logging.getLogger('src.rag_system')
logger.setLevel(logging.DEBUG)
```

### Data Inspection Tools

```python
def inspect_scraped_data(data_file="data/website_docs.json"):
    """Comprehensive data inspection."""
    import json
    from collections import Counter

    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Data file {data_file} not found")
        return

    print(f"📊 Data Inspection Report")
    print(f"Total documents: {len(data)}")

    # Content types
    content_types = Counter(doc['content_type'] for doc in data)
    print(f"\n📋 Content Types:")
    for ctype, count in content_types.most_common():
        print(f"  {ctype}: {count}")

    # Page distribution
    pages = Counter(doc['metadata']['url'] for doc in data)
    print(f"\n📄 Page Distribution (top 5):")
    for url, count in pages.most_common(5):
        print(f"  {count} chunks: {url}")

    # Content length analysis
    lengths = [len(doc['content']) for doc in data]
    avg_length = sum(lengths) / len(lengths)
    print(f"\n📏 Content Analysis:")
    print(f"  Average length: {avg_length:.0f} characters")
    print(f"  Range: {min(lengths)} - {max(lengths)} characters")

    # Quality checks
    empty_content = sum(1 for doc in data if not doc['content'].strip())
    short_content = sum(1 for length in lengths if length < 50)

    print(f"\n⚠️ Quality Issues:")
    print(f"  Empty chunks: {empty_content}")
    print(f"  Very short chunks (<50 chars): {short_content}")

    # Sample content
    print(f"\n📝 Sample Content:")
    for i, doc in enumerate(data[:3]):
        print(f"  Sample {i+1}: {doc['content'][:100]}...")

inspect_scraped_data()
```

### Query Performance Analysis

```python
def analyze_query_performance():
    """Analyze query performance and result quality."""
    rag = RAGSystem()

    # Load data
    try:
        rag.load_data("data/website_docs.json")
    except:
        print("❌ No data loaded - scrape first")
        return

    test_queries = [
        ("python functions", "Should find function definitions"),
        ("api endpoint", "Should find API documentation"),
        ("installation guide", "Should find setup instructions"),
        ("nonexistent topic xyz", "Should return low scores")
    ]

    print("🔍 Query Performance Analysis")

    for query, expected in test_queries:
        start_time = time.time()
        result = rag.demo_query(query, top_k=5)
        elapsed = time.time() - start_time

        best_score = result['chunks'][0]['score'] if result['chunks'] else 0

        print(f"\nQuery: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Best score: {best_score:.3f}")
        print(f"  Results: {len(result['chunks'])}")

        if best_score < 0.3:
            print(f"  ⚠️ Low relevance - consider rephrasing")
        elif best_score > 0.6:
            print(f"  ✅ High relevance")
        else:
            print(f"  📊 Moderate relevance")

analyze_query_performance()
```

## 🎯 Performance Optimization

### Query Optimization

```python
def optimize_queries():
    """Examples of query optimization techniques."""
    rag = RAGSystem()
    rag.load_data("data/website_docs.json")

    # Poor query examples and improvements
    optimizations = [
        {
            "poor": "implement async await coroutine functionality",
            "better": "how to use async and await in Python",
            "reason": "Use natural language instead of technical jargon"
        },
        {
            "poor": "FastAPI middleware CORS",
            "better": "enable CORS in FastAPI application",
            "reason": "Complete sentences work better than keywords"
        },
        {
            "poor": "error",
            "better": "how to handle errors and exceptions",
            "reason": "Specific context improves relevance"
        }
    ]

    for opt in optimizations:
        print(f"\n--- Query Optimization Example ---")
        print(f"Poor: '{opt['poor']}'")
        print(f"Better: '{opt['better']}'")
        print(f"Reason: {opt['reason']}")

        # Test both
        poor_result = rag.demo_query(opt['poor'], top_k=3)
        better_result = rag.demo_query(opt['better'], top_k=3)

        poor_score = poor_result['chunks'][0]['score'] if poor_result['chunks'] else 0
        better_score = better_result['chunks'][0]['score'] if better_result['chunks'] else 0

        print(f"Poor score: {poor_score:.3f}")
        print(f"Better score: {better_score:.3f}")

        if better_score > poor_score:
            print("✅ Optimization improved results")
        else:
            print("⚠️ Results similar - context may matter more")

optimize_queries()
```

### System Health Check

```python
def system_health_check():
    """Comprehensive system health check."""
    print("🏥 RAG System Health Check")

    issues = []

    # 1. Check Python version
    import sys
    if sys.version_info < (3, 10):
        issues.append("❌ Python version too old (need 3.10+)")
    else:
        print("✅ Python version OK")

    # 2. Check dependencies
    required_modules = ['requests', 'beautifulsoup4', 'sklearn', 'numpy']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            issues.append(f"❌ {module} not installed")

    # 3. Check data directory
    import os
    if not os.path.exists('data'):
        issues.append("❌ Data directory missing")
        os.makedirs('data', exist_ok=True)
        print("✅ Created data directory")
    else:
        print("✅ Data directory exists")

    # 4. Test basic functionality
    try:
        rag = RAGSystem()
        print("✅ RAG System initialization OK")
    except Exception as e:
        issues.append(f"❌ RAG System init failed: {e}")

    # 5. Test network connectivity
    try:
        import requests
        response = requests.get("https://httpbin.org/ip", timeout=10)
        if response.status_code == 200:
            print("✅ Network connectivity OK")
        else:
            issues.append(f"⚠️ Network issues: {response.status_code}")
    except Exception as e:
        issues.append(f"❌ Network test failed: {e}")

    # 6. Test Ollama (optional)
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=3)
        if response.status_code == 200:
            print("✅ Ollama available")
        else:
            print("⚠️ Ollama not running (optional)")
    except:
        print("⚠️ Ollama not available (optional)")

    # Summary
    if issues:
        print(f"\n🚨 Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"\n🎉 System Health: All checks passed!")

    return len(issues) == 0

# Run health check
is_healthy = system_health_check()
```

## 📞 Getting Additional Help

### Before Asking for Help

1. **Run the health check** above to identify common issues
2. **Check similarity scores** - low scores often indicate query issues
3. **Enable debug logging** to see detailed error messages
4. **Test with simple examples** from the getting started guide
5. **Verify network connectivity** and website accessibility

### Information to Include When Reporting Issues

```python
def generate_debug_report():
    """Generate comprehensive debug report for issue reporting."""
    import sys
    import platform

    report = []
    report.append("=== RAG System Debug Report ===")
    report.append(f"Python version: {sys.version}")
    report.append(f"Platform: {platform.platform()}")

    # System info
    try:
        import psutil
        memory = psutil.virtual_memory()
        report.append(f"Available memory: {memory.available / (1024**3):.1f} GB")
    except:
        pass

    # Package versions
    packages = ['requests', 'beautifulsoup4', 'scikit-learn', 'numpy', 'aiohttp']
    for pkg in packages:
        try:
            module = __import__(pkg)
            version = getattr(module, '__version__', 'unknown')
            report.append(f"{pkg}: {version}")
        except ImportError:
            report.append(f"{pkg}: NOT INSTALLED")

    # RAG system status
    try:
        rag = RAGSystem()
        # Test if RAG system has data loaded
        test_result = rag.demo_query("test", top_k=1)
        if "No documents" in test_result:
            report.append("Data loaded: No chunks available")
        else:
            report.append("Data loaded: Successfully loaded")
    except Exception as e:
        report.append(f"RAG system error: {e}")

    # Network test
    try:
        import requests
        response = requests.get("https://httpbin.org/ip", timeout=5)
        report.append(f"Network test: {response.status_code}")
    except Exception as e:
        report.append(f"Network test failed: {e}")

    print("\n".join(report))
    return "\n".join(report)

# Generate report for issue submission
debug_info = generate_debug_report()
```

### Community Resources

- **GitHub Issues**: Report bugs and feature requests with debug info
- **Documentation**: Check the [API docs](../api/README.md) for detailed information
- **Examples**: Review working examples in the `/examples` directory
- **Tests**: Look at `/tests` for usage patterns and edge cases

### Quick Diagnostic Commands

```bash
# System information
python --version
pip list | grep -E "(beautifulsoup4|requests|scikit-learn|numpy)"

# Network connectivity
ping -c 3 docs.python.org
curl -I https://docs.python.org/

# File system
ls -la data/
du -sh data/

# Ollama (if used)
ollama list
curl -s http://localhost:11434/api/version
```

## 🎯 Prevention Tips

### Regular Maintenance

```python
def system_maintenance():
    """Regular maintenance tasks."""
    import os
    import glob

    print("🧹 Running system maintenance...")

    # Clean old cache files
    cache_files = glob.glob("data/*_cache.pkl")
    old_count = len(cache_files)

    # Remove caches older than 7 days
    import time
    week_ago = time.time() - (7 * 24 * 60 * 60)

    for cache_file in cache_files:
        if os.path.getmtime(cache_file) < week_ago:
            os.remove(cache_file)
            print(f"Removed old cache: {cache_file}")

    # Check data directory size
    total_size = sum(os.path.getsize(os.path.join("data", f))
                    for f in os.listdir("data")
                    if os.path.isfile(os.path.join("data", f)))

    print(f"Data directory size: {total_size / (1024*1024):.1f} MB")

    if total_size > 100 * 1024 * 1024:  # 100MB
        print("⚠️ Large data directory - consider cleanup")

# Run monthly
system_maintenance()
```

### Best Practices

1. **Start small** - Always test with small `max_pages` values first
2. **Monitor performance** - Keep track of similarity scores and response times
3. **Regular cleanup** - Clean old data files and caches periodically
4. **Version control** - Keep track of configuration changes
5. **Backup important data** - Save successful scraping results

Remember: Most issues can be resolved by starting with small test cases and gradually scaling up! 🚀