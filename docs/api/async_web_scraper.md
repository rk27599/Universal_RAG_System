# Async Web Scraper API

High-performance asynchronous web scraper optimized for speed and efficiency with concurrent processing capabilities.

## Class: AsyncWebScraper

Asynchronous web scraper with concurrent processing, smart caching, and performance optimization.

### Constructor

```python
AsyncWebScraper(config: Optional[ScrapingConfig] = None)
```

**Parameters:**
- `config` (ScrapingConfig, optional): Configuration object. Uses defaults if None.

**Example:**
```python
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

# Default configuration
scraper = AsyncWebScraper()

# Custom configuration
config = ScrapingConfig(
    concurrent_limit=8,
    requests_per_second=10.0,
    max_pages=100
)
scraper = AsyncWebScraper(config)
```

## Configuration Classes

### ScrapingConfig

```python
@dataclass
class ScrapingConfig:
    concurrent_limit: int = 4          # Max concurrent requests
    requests_per_second: float = 6.0   # Rate limiting
    timeout: float = 15.0              # Request timeout in seconds
    max_pages: int = 30                # Maximum pages to scrape
    max_depth: int = 2                 # Maximum crawling depth
    same_domain_only: bool = True      # Stay within domain
    respect_robots_txt: bool = True    # Honor robots.txt
    user_agent: str = "..."            # User agent string
    retry_attempts: int = 3            # Retry failed requests
    retry_delay: float = 1.0           # Delay between retries
```

**Example:**
```python
# High-performance configuration
config = ScrapingConfig(
    concurrent_limit=8,        # More concurrent requests
    requests_per_second=12.0,  # Higher rate limit
    max_pages=100,             # More pages
    timeout=20.0,              # Longer timeout
    retry_attempts=5,          # More retries
    max_depth=3                # Deeper crawling
)

# Conservative configuration
config = ScrapingConfig(
    concurrent_limit=2,        # Fewer concurrent requests
    requests_per_second=3.0,   # Lower rate limit
    max_pages=20,              # Fewer pages
    timeout=10.0,              # Shorter timeout
    retry_attempts=2           # Fewer retries
)
```

### PerformanceMetrics

```python
@dataclass
class PerformanceMetrics:
    start_time: float
    urls_discovered: int = 0
    urls_processed: int = 0
    urls_failed: int = 0
    total_requests: int = 0
    cache_hits: int = 0
    total_bytes_downloaded: int = 0
    elapsed_time: float = 0
```

**Usage:**
```python
success, metrics = await scraper.scrape_website([url])

print(f"Processing time: {metrics.elapsed_time:.1f}s")
print(f"Pages processed: {metrics.urls_processed}")
print(f"Cache efficiency: {metrics.cache_hits/metrics.total_requests:.1%}")
print(f"Data downloaded: {metrics.total_bytes_downloaded:,} bytes")
```

## Core Methods

### scrape_website_async()

```python
async def scrape_website_async(self, start_urls: List[str]) -> Dict
```

Main asynchronous scraping method with concurrent processing.

**Parameters:**
- `start_urls` (List[str]): List of starting URLs

**Returns:**
- `Dict`: Dictionary containing scraped results with structure:
  ```python
  {
      "results": List[Dict],  # Structured document data
      "metrics": PerformanceMetrics,
      "failed_urls": List[Tuple[str, str]]
  }
  ```

**Example:**
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

async def scrape_documentation():
    # Configure for documentation scraping
    config = ScrapingConfig(
        concurrent_limit=6,
        max_pages=75,
        requests_per_second=8.0,
        timeout=20.0
    )

    async with AsyncWebScraper(config) as scraper:
        # Scrape the website
        results = await scraper.scrape_website_async(
            start_urls=["https://docs.python.org/3/"]
        )

        # Save results to file
        await scraper.save_results_async(results, "data/python_docs.json")

        # Access metrics
        metrics = results["metrics"]
        print(f"✅ Successfully scraped {metrics.urls_processed} pages")
        print(f"⚡ Total time: {metrics.elapsed_time:.1f} seconds")
        print(f"📊 Cache hits: {metrics.cache_hits} ({metrics.cache_hits/metrics.total_requests:.1%})")
        print(f"💾 Data size: {metrics.total_bytes_downloaded:,} bytes")

        return results

# Run the scraper
results = asyncio.run(scrape_documentation())
```

### save_results_async()

```python
async def save_results_async(self, results: Dict, output_file: str) -> None
```

Save scraping results to both JSON and TXT formats.

**Parameters:**
- `results` (Dict): Results from `scrape_website_async()`
- `output_file` (str): Output file path (creates both .json and .txt versions)

**Example:**
```python
async def save_scraping_results():
    scraper = AsyncWebScraper()
    results = await scraper.scrape_website_async(["https://example.com"])

    # Save to both JSON and TXT formats
    await scraper.save_results_async(results, "data/example_docs.json")
    # Creates: data/example_docs.json and data/example_docs.txt
```

## Standalone Functions

### scrape_website_fast()

```python
async def scrape_website_fast(
    start_urls: List[str],
    max_pages: int = 30,
    concurrent_limit: int = 8,
    requests_per_second: float = 10.0,
    output_file: str = "data/fast_scraped_docs.json"
) -> Dict
```

High-level async scraping function with automatic configuration and file saving.

**Parameters:**
- `start_urls` (List[str]): URLs to start scraping from
- `max_pages` (int, optional): Maximum pages to scrape. Defaults to 30.
- `concurrent_limit` (int, optional): Max concurrent requests. Defaults to 8.
- `requests_per_second` (float, optional): Rate limiting. Defaults to 10.0.
- `output_file` (str, optional): Output file path. Defaults to "data/fast_scraped_docs.json".

**Returns:**
- `Dict`: Results dictionary with metrics and scraped data

**Example:**
```python
import asyncio
from src.async_web_scraper import scrape_website_fast

async def quick_scrape():
    # High-performance scraping with minimal setup
    results = await scrape_website_fast(
        start_urls=["https://docs.python.org/3/"],
        max_pages=50,
        concurrent_limit=6,
        requests_per_second=8.0,
        output_file="data/python_docs.json"
    )

    metrics = results["metrics"]
    print(f"✅ Scraped {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")
    return results

# Single line execution
results = asyncio.run(quick_scrape())
```

## Advanced Usage

### High-Performance Batch Processing

```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

async def process_multiple_sites():
    """Process multiple websites concurrently for maximum performance."""

    sites = [
        ("https://docs.python.org/", "python_docs.json"),
        ("https://fastapi.tiangolo.com/", "fastapi_docs.json"),
        ("https://flask.palletsprojects.com/", "flask_docs.json")
    ]

    # High-performance configuration
    config = ScrapingConfig(
        concurrent_limit=8,
        requests_per_second=15.0,
        max_pages=60,
        timeout=25.0,
        retry_attempts=4
    )

    scraper = AsyncWebScraper(config)
    results = []

    # Process all sites concurrently
    tasks = [
        scraper.scrape_website([url], f"data/{filename}")
        for url, filename in sites
    ]

    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

    for (url, filename), result in zip(sites, batch_results):
        if isinstance(result, Exception):
            print(f"❌ {url} failed: {result}")
        else:
            success, metrics = result
            if success:
                print(f"✅ {url}: {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")
                results.append((url, metrics))
            else:
                print(f"⚠️  {url}: Partial success - {metrics.urls_processed} pages")

    return results

# Run batch processing
results = asyncio.run(process_multiple_sites())
```

### Custom Content Filtering

```python
class CustomAsyncWebScraper(AsyncWebScraper):
    """Extended scraper with custom content filtering."""

    def __init__(self, config=None):
        super().__init__(config)
        self.content_filters = {
            'min_content_length': 100,
            'exclude_patterns': [r'cookie', r'privacy policy'],
            'include_patterns': [r'tutorial', r'guide', r'documentation']
        }

    def extract_content(self, soup, url):
        """Override content extraction with custom filtering."""
        content_chunks = super().extract_content(soup, url)

        # Apply custom filters
        filtered_chunks = []
        for chunk in content_chunks:
            # Length filter
            if len(chunk['content']) < self.content_filters['min_content_length']:
                continue

            # Pattern filters
            content_lower = chunk['content'].lower()

            # Skip excluded patterns
            if any(re.search(pattern, content_lower) for pattern in self.content_filters['exclude_patterns']):
                continue

            # Include relevant patterns (if specified)
            if self.content_filters['include_patterns']:
                if any(re.search(pattern, content_lower) for pattern in self.content_filters['include_patterns']):
                    chunk['metadata']['relevance_boost'] = True

            filtered_chunks.append(chunk)

        return filtered_chunks

# Usage
async def scrape_with_filtering():
    config = ScrapingConfig(concurrent_limit=6, max_pages=40)
    scraper = CustomAsyncWebScraper(config)

    success, metrics = await scraper.scrape_website([
        "https://docs.python.org/3/tutorial/"
    ])

    return success, metrics
```

### Performance Monitoring and Optimization

```python
import asyncio
import time
from dataclasses import asdict

async def benchmark_scraping_performance():
    """Benchmark different configurations for optimal performance."""

    test_url = "https://docs.python.org/3/"
    configurations = [
        ("Conservative", ScrapingConfig(concurrent_limit=2, requests_per_second=3.0, max_pages=20)),
        ("Balanced", ScrapingConfig(concurrent_limit=4, requests_per_second=6.0, max_pages=20)),
        ("Aggressive", ScrapingConfig(concurrent_limit=8, requests_per_second=12.0, max_pages=20)),
    ]

    results = []

    for name, config in configurations:
        print(f"\n--- Testing {name} Configuration ---")

        scraper = AsyncWebScraper(config)
        start_time = time.time()

        success, metrics = await scraper.scrape_website([test_url])

        if success:
            pages_per_second = metrics.urls_processed / metrics.elapsed_time
            print(f"✅ Processed {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")
            print(f"📈 Rate: {pages_per_second:.2f} pages/second")
            print(f"💾 Cache efficiency: {metrics.cache_hits}/{metrics.total_requests} ({metrics.cache_hits/metrics.total_requests:.1%})")

            results.append({
                'name': name,
                'config': asdict(config),
                'metrics': asdict(metrics),
                'pages_per_second': pages_per_second
            })
        else:
            print(f"❌ Configuration {name} failed")

    # Find optimal configuration
    if results:
        best = max(results, key=lambda x: x['pages_per_second'])
        print(f"\n🏆 Best performing configuration: {best['name']}")
        print(f"Rate: {best['pages_per_second']:.2f} pages/second")

    return results

# Run benchmark
benchmark_results = asyncio.run(benchmark_scraping_performance())
```

## Error Handling and Resilience

### Comprehensive Error Handling

```python
import asyncio
import logging
from aiohttp import ClientError, ServerTimeoutError

logging.basicConfig(level=logging.INFO)

async def robust_scraping():
    """Example of robust scraping with comprehensive error handling."""

    config = ScrapingConfig(
        concurrent_limit=6,
        max_pages=50,
        retry_attempts=5,
        retry_delay=2.0,
        timeout=30.0
    )

    scraper = AsyncWebScraper(config)

    try:
        success, metrics = await scraper.scrape_website([
            "https://docs.python.org/3/"
        ])

        if success:
            print(f"✅ Scraping completed successfully")
            print(f"📊 Processed: {metrics.urls_processed}/{metrics.urls_discovered} pages")
            print(f"⚠️  Failed: {metrics.urls_failed} pages")
            print(f"⚡ Performance: {metrics.urls_processed/metrics.elapsed_time:.2f} pages/second")

            # Check for warnings
            failure_rate = metrics.urls_failed / (metrics.urls_processed + metrics.urls_failed)
            if failure_rate > 0.1:
                print(f"⚠️  High failure rate: {failure_rate:.1%} - consider adjusting settings")

        else:
            print(f"❌ Scraping failed - processed {metrics.urls_processed} pages before failure")
            print("Check logs for detailed error information")

    except ClientError as e:
        print(f"❌ Network error: {e}")
        print("Check internet connection and target website accessibility")

    except ServerTimeoutError as e:
        print(f"❌ Timeout error: {e}")
        print("Consider increasing timeout or reducing concurrent requests")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logging.exception("Detailed error information:")

    return success if 'success' in locals() else False

# Run with error handling
result = asyncio.run(robust_scraping())
```

### Recovery Strategies

```python
async def scrape_with_recovery():
    """Scraping with automatic recovery and fallback strategies."""

    primary_config = ScrapingConfig(
        concurrent_limit=8,
        requests_per_second=10.0,
        max_pages=100
    )

    fallback_config = ScrapingConfig(
        concurrent_limit=2,
        requests_per_second=3.0,
        max_pages=50
    )

    url = "https://docs.python.org/3/"

    # Try primary configuration
    scraper = AsyncWebScraper(primary_config)
    success, metrics = await scraper.scrape_website([url])

    if not success or metrics.urls_failed > metrics.urls_processed * 0.3:
        print("⚠️  Primary configuration had issues, trying fallback...")

        # Try fallback configuration
        scraper = AsyncWebScraper(fallback_config)
        success, metrics = await scraper.scrape_website([url], "data/fallback_docs.json")

        if success:
            print("✅ Fallback configuration successful")
        else:
            print("❌ Both configurations failed")

    return success, metrics

result = asyncio.run(scrape_with_recovery())
```

## Integration Examples

### Integration with RAG System

```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
from src.rag_system import RAGSystem

async def fast_rag_setup():
    """Complete pipeline: fast scraping → RAG processing → querying."""

    # Step 1: Fast scraping with async scraper
    config = ScrapingConfig(
        concurrent_limit=6,
        max_pages=75,
        requests_per_second=8.0
    )

    scraper = AsyncWebScraper(config)
    success, metrics = await scraper.scrape_website(
        ["https://fastapi.tiangolo.com/"],
        "data/fastapi_docs.json"
    )

    if not success:
        return None

    print(f"⚡ Scraped {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")

    # Step 2: Load into RAG system
    rag = RAGSystem()
    loaded = rag.load_data("data/fastapi_docs.json")

    if not loaded:
        return None

    # Step 3: Test queries
    test_queries = [
        "How to create a FastAPI application?",
        "Path parameters and query parameters",
        "Request body and response models"
    ]

    results = {}
    for query in test_queries:
        result = rag.demo_query(query, top_k=3)
        results[query] = result
        print(f"Query: {query}")
        print(f"Best score: {result['chunks'][0]['score']:.3f}")

    return rag, results

# Run complete pipeline
rag_system, query_results = asyncio.run(fast_rag_setup())
```

### Web Service Integration

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio

app = FastAPI()

class ScrapeRequest(BaseModel):
    urls: List[str]
    max_pages: int = 30
    concurrent_limit: int = 4

class ScrapeStatus(BaseModel):
    task_id: str
    status: str  # "running", "completed", "failed"
    progress: Dict[str, Any]

# In-memory task storage (use Redis/database in production)
scraping_tasks = {}

@app.post("/scrape")
async def start_scraping(request: ScrapeRequest, background_tasks: BackgroundTasks):
    task_id = f"task_{int(time.time())}"

    config = ScrapingConfig(
        concurrent_limit=request.concurrent_limit,
        max_pages=request.max_pages
    )

    background_tasks.add_task(run_scraping_task, task_id, request.urls, config)

    scraping_tasks[task_id] = {
        "status": "running",
        "urls": request.urls,
        "progress": {"pages_processed": 0, "start_time": time.time()}
    }

    return {"task_id": task_id, "status": "started"}

async def run_scraping_task(task_id: str, urls: List[str], config: ScrapingConfig):
    try:
        scraper = AsyncWebScraper(config)
        success, metrics = await scraper.scrape_website(urls)

        scraping_tasks[task_id].update({
            "status": "completed" if success else "failed",
            "progress": {
                "pages_processed": metrics.urls_processed,
                "pages_failed": metrics.urls_failed,
                "elapsed_time": metrics.elapsed_time,
                "cache_hits": metrics.cache_hits
            }
        })

    except Exception as e:
        scraping_tasks[task_id].update({
            "status": "failed",
            "error": str(e)
        })

@app.get("/scrape/{task_id}/status")
async def get_scrape_status(task_id: str):
    if task_id not in scraping_tasks:
        return {"error": "Task not found"}, 404

    return scraping_tasks[task_id]
```

## Performance Optimization

### Best Practices

1. **Concurrency Tuning**: Start with 4-6 concurrent requests, adjust based on target site
2. **Rate Limiting**: Respect server limits (6-10 requests/second typical)
3. **Timeout Settings**: Use 15-30 seconds for reliable connections
4. **Retry Strategy**: Configure 3-5 retry attempts with exponential backoff
5. **Caching**: Enable for repeated scraping operations
6. **Memory Management**: Monitor memory usage for large-scale operations

### Configuration Guidelines

```python
# For documentation sites
docs_config = ScrapingConfig(
    concurrent_limit=6,
    requests_per_second=8.0,
    max_pages=100,
    timeout=20.0,
    retry_attempts=4
)

# For e-commerce sites (more conservative)
ecommerce_config = ScrapingConfig(
    concurrent_limit=3,
    requests_per_second=4.0,
    max_pages=50,
    timeout=15.0,
    retry_attempts=5
)

# For news sites (balanced)
news_config = ScrapingConfig(
    concurrent_limit=5,
    requests_per_second=7.0,
    max_pages=75,
    timeout=18.0,
    retry_attempts=3
)
```

---

*For complete implementation examples and integration patterns, see the [Getting Started Guide](../guides/getting-started.md) and [Performance Guide](../guides/performance.md).*