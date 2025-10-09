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
    start_time: float = field(default_factory=time.time)
    urls_discovered: int = 0
    urls_processed: int = 0
    urls_failed: int = 0
    total_requests: int = 0
    cache_hits: int = 0

    def duration(self) -> float
    def requests_per_second(self) -> float
    def success_rate(self) -> float
```

Tracks comprehensive performance metrics during scraping operations.

**Calculated Properties:**
- `duration()`: Total elapsed time in seconds
- `requests_per_second()`: Average request rate
- `success_rate()`: Success percentage (0-100)

**Usage:**
```python
async with AsyncWebScraper(config) as scraper:
    results = await scraper.scrape_website_async([url])

    # Access metrics from scraper instance
    metrics = scraper.metrics

    print(f"⏱️  Duration: {metrics.duration():.1f}s")
    print(f"📄 Pages processed: {metrics.urls_processed}")
    print(f"🚀 Rate: {metrics.requests_per_second():.1f} requests/sec")
    print(f"✅ Success rate: {metrics.success_rate():.1f}%")
    print(f"💾 Cache hits: {metrics.cache_hits}/{metrics.total_requests}")

# Performance analysis
if metrics.success_rate() < 80:
    print("⚠️  High failure rate - consider reducing concurrency")

if metrics.requests_per_second() < 2:
    print("🐌 Low request rate - may need configuration tuning")
```

## Advanced Content Processing

### Content Extraction Features

The async scraper includes advanced content processing capabilities:

**Enhanced Content Detection:**
- **Code Examples**: Automatically detects and labels `<pre>` and `<code>` blocks
- **Tables**: Extracts structured table data with proper formatting
- **Lists**: Processes ordered and unordered lists with hierarchy
- **Quotes**: Identifies and formats blockquotes and citations

**Semantic Chunking:**
- **Structure-Aware**: Respects HTML heading hierarchy (h1-h6)
- **Content-Type Labeling**: Labels chunks by content type for better retrieval
- **Smart Splitting**: Maintains semantic coherence when splitting large sections
- **Metadata Preservation**: Keeps page titles, URLs, and section information

**Example of Enhanced Processing:**
```python
async with AsyncWebScraper() as scraper:
    results = await scraper.scrape_website_async([
        "https://docs.python.org/3/tutorial/"
    ])

    # Analyze content types in results
    content_types = {}
    for doc in results["documents"]:
        for section in doc["sections"]:
            for content_item in section.get("content", []):
                if content_item.startswith("Code example:"):
                    content_types["code"] = content_types.get("code", 0) + 1
                elif content_item.startswith("Table:"):
                    content_types["table"] = content_types.get("table", 0) + 1
                elif content_item.startswith("List:"):
                    content_types["list"] = content_types.get("list", 0) + 1

    print("📊 Content type distribution:")
    for ctype, count in content_types.items():
        print(f"  {ctype}: {count}")
```

### Smart Caching System

The async scraper implements intelligent caching for optimal performance:

**Domain Caching:**
- Caches domain information for URL processing
- Reduces DNS lookups and URL parsing overhead

**Robots.txt Caching:**
- Caches robots.txt files per domain
- Avoids repeated robots.txt requests

**Content Deduplication:**
- Tracks visited URLs to prevent reprocessing
- Uses URL normalization for effective deduplication

**Cache Performance:**
```python
async with AsyncWebScraper(config) as scraper:
    # First run - cold cache
    start_time = time.time()
    results1 = await scraper.scrape_website_async(["https://example.com"])
    cold_time = time.time() - start_time

    # Second run - warm cache (if overlapping URLs)
    start_time = time.time()
    results2 = await scraper.scrape_website_async(["https://example.com/docs"])
    warm_time = time.time() - start_time

    cache_efficiency = scraper.metrics.cache_hits / scraper.metrics.total_requests
    print(f"🚀 Cache efficiency: {cache_efficiency:.1%}")
    print(f"⚡ Speed improvement: {cold_time/warm_time:.1f}x")
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

Save scraping results asynchronously to both JSON and TXT formats.

**Parameters:**
- `results` (Dict): Results from `scrape_website_async()` or `process_local_files_async()`
- `output_file` (str): Output file path (creates both .json and .txt versions)

**Features:**
- Creates directory structure if it doesn't exist
- Saves structured JSON with metadata and semantic chunks
- Creates text file with formatted content for compatibility
- Fully asynchronous file operations using aiofiles

**Example:**
```python
async def save_scraping_results():
    scraper = AsyncWebScraper()
    results = await scraper.scrape_website_async(["https://example.com"])

    # Save to both JSON and TXT formats
    await scraper.save_results_async(results, "data/example_docs.json")
    # Creates: data/example_docs.json and data/example_docs.txt

    print("💾 Results saved to both JSON and text formats")

# Save local file processing results
async def save_local_results():
    results = await AsyncWebScraper.process_local_files_fast([
        "docs/page1.html", "docs/page2.html"
    ])

    await scraper.save_results_async(results, "data/local_docs.json")
```

## Local File Processing

### process_local_files_fast() - Static Method

```python
@staticmethod
async def process_local_files_fast(
    file_paths: List[str],
    output_file: str = "data/fast_local_docs.json",
    concurrent_limit: int = 6
) -> Dict
```

High-level async local HTML file processing function as a static method.

**Parameters:**
- `file_paths` (List[str]): List of HTML file paths to process
- `output_file` (str, optional): Output file path. Defaults to "data/fast_local_docs.json".
- `concurrent_limit` (int, optional): Number of files to process concurrently. Defaults to 6.

**Returns:**
- `Dict`: Processing results with metadata and semantic chunks

**Example:**
```python
import asyncio
from src.async_web_scraper import AsyncWebScraper

async def process_html_files():
    # Process local HTML files with high performance
    results = await AsyncWebScraper.process_local_files_fast(
        file_paths=[
            "/path/to/docs/page1.html",
            "/path/to/docs/page2.html",
            "/path/to/docs/page3.html"
        ],
        output_file="data/local_docs.json",
        concurrent_limit=4
    )

    metadata = results["metadata"]
    print(f"✅ Processed {metadata['total_files']} files")
    print(f"📊 Created {metadata['total_chunks']} semantic chunks")
    print(f"⚡ Processing rate: {metadata['files_per_second']:.1f} files/sec")

    return results

# Run local file processing
results = asyncio.run(process_html_files())
```

### process_local_files_async()

```python
async def process_local_files_async(
    self,
    file_paths: List[str],
    output_file: str = "data/local_docs_async.json",
    concurrent_limit: int = None
) -> Dict
```

Process multiple local HTML files concurrently with async performance.

**Parameters:**
- `file_paths` (List[str]): List of HTML file paths to process
- `output_file` (str, optional): Output file path. Defaults to "data/local_docs_async.json".
- `concurrent_limit` (int, optional): Concurrent processing limit. Uses config value if None.

**Returns:**
- `Dict`: Processing results with metadata, documents, and semantic chunks

**Example:**
```python
async def process_documentation_folder():
    config = ScrapingConfig(concurrent_limit=8)

    async with AsyncWebScraper(config) as scraper:
        # Find HTML files
        html_files = scraper.find_html_files("./documentation", "**/*.html")

        # Process with custom concurrency
        results = await scraper.process_local_files_async(
            file_paths=html_files,
            output_file="data/documentation.json",
            concurrent_limit=6
        )

        print(f"Processed {len(results['documents'])} documents")
        print(f"Generated {len(results['semantic_chunks'])} chunks")

        return results

results = asyncio.run(process_documentation_folder())
```

### extract_from_local_file_async()

```python
async def extract_from_local_file_async(self, file_path: str) -> Optional[Dict]
```

Async version of extract_from_local_file for processing local HTML files.

**Parameters:**
- `file_path` (str): Path to the HTML file

**Returns:**
- `Optional[Dict]`: Extracted document structure or None if failed

**Example:**
```python
async def process_single_file():
    async with AsyncWebScraper() as scraper:
        doc_structure = await scraper.extract_from_local_file_async(
            "documentation/api-guide.html"
        )

        if doc_structure:
            print(f"Title: {doc_structure['page_title']}")
            print(f"Sections: {len(doc_structure['sections'])}")
            return doc_structure
        else:
            print("Failed to extract content")
            return None

doc = asyncio.run(process_single_file())
```

### find_html_files()

```python
def find_html_files(self, directory: str, pattern: str = "*.html") -> List[str]
```

Find HTML files in a directory with support for glob patterns.

**Parameters:**
- `directory` (str): Directory to search in
- `pattern` (str, optional): Glob pattern. Defaults to "*.html".

**Returns:**
- `List[str]`: List of HTML file paths found

**Example:**
```python
scraper = AsyncWebScraper()

# Find all HTML files in current directory
html_files = scraper.find_html_files("./docs")

# Find HTML files recursively
all_html = scraper.find_html_files("./docs", "**/*.html")

# Find both .html and .htm files
htm_files = scraper.find_html_files("./docs", "*.htm")

print(f"Found {len(html_files)} HTML files")
for file_path in html_files[:5]:  # Show first 5
    print(f"  - {file_path}")
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

### Local File + Web Integration

```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
from src.rag_system import RAGSystem

async def mixed_content_processing():
    """Process both local HTML files and web content together."""

    config = ScrapingConfig(concurrent_limit=6, max_pages=30)

    async with AsyncWebScraper(config) as scraper:
        # Step 1: Process local documentation files
        local_html_files = scraper.find_html_files("./docs", "**/*.html")

        if local_html_files:
            local_results = await scraper.process_local_files_async(
                file_paths=local_html_files,
                output_file="data/local_docs.json"
            )
            print(f"📂 Processed {len(local_results['documents'])} local files")

        # Step 2: Scrape related web content
        web_results = await scraper.scrape_website_async([
            "https://docs.python.org/3/tutorial/"
        ])
        await scraper.save_results_async(web_results, "data/web_docs.json")
        print(f"🌐 Scraped {len(web_results['documents'])} web pages")

        # Step 3: Combine for comprehensive knowledge base
        all_chunks = []
        if local_html_files:
            all_chunks.extend(local_results['semantic_chunks'])
        all_chunks.extend(web_results['semantic_chunks'])

        combined_data = {
            "metadata": {
                "total_sources": len(local_html_files) + len(web_results['documents']),
                "local_files": len(local_html_files) if local_html_files else 0,
                "web_pages": len(web_results['documents']),
                "total_chunks": len(all_chunks)
            },
            "semantic_chunks": all_chunks
        }

        # Save combined results
        await scraper.save_results_async(combined_data, "data/combined_docs.json")

        return combined_data

# Run mixed processing
combined_results = asyncio.run(mixed_content_processing())
```

### High-Performance Local File Processing

```python
async def batch_process_documentation_sites():
    """Process multiple documentation directories with high performance."""

    # Configuration for local file processing
    config = ScrapingConfig(concurrent_limit=8)  # Higher for local files

    documentation_dirs = [
        "./project_docs",
        "./api_docs",
        "./user_guides",
        "./tutorials"
    ]

    all_results = []

    for doc_dir in documentation_dirs:
        if not os.path.exists(doc_dir):
            print(f"⚠️  Directory not found: {doc_dir}")
            continue

        print(f"📁 Processing directory: {doc_dir}")

        # Use static method for high-performance processing
        results = await AsyncWebScraper.process_local_files_fast(
            file_paths=AsyncWebScraper().find_html_files(doc_dir, "**/*.html"),
            output_file=f"data/{os.path.basename(doc_dir)}_docs.json",
            concurrent_limit=6
        )

        all_results.append({
            "directory": doc_dir,
            "files_processed": results["metadata"]["total_files"],
            "chunks_created": results["metadata"]["total_chunks"],
            "processing_time": results["metadata"]["processing_time"]
        })

    # Summary report
    total_files = sum(r["files_processed"] for r in all_results)
    total_chunks = sum(r["chunks_created"] for r in all_results)
    total_time = sum(r["processing_time"] for r in all_results)

    print(f"\n📊 Batch Processing Summary:")
    print(f"  Total files: {total_files}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Average rate: {total_files/total_time:.1f} files/sec")

    return all_results

# Process all documentation
results = asyncio.run(batch_process_documentation_sites())
```

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

    async with AsyncWebScraper(config) as scraper:
        results = await scraper.scrape_website_async([
            "https://fastapi.tiangolo.com/"
        ])
        await scraper.save_results_async(results, "data/fastapi_docs.json")

        print(f"⚡ Scraped {len(results['documents'])} pages")
        print(f"📊 Generated {len(results['semantic_chunks'])} chunks")

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

        if result['chunks']:
            best_score = result['chunks'][0]['score']
            print(f"Query: '{query}' - Score: {best_score:.3f}")

    return rag, results

# Run complete pipeline
rag_system, query_results = asyncio.run(fast_rag_setup())
```

### Real-Time Documentation Processing

```python
async def watch_and_process_files():
    """Example of processing files as they're updated (conceptual)."""

    import asyncio
    from pathlib import Path

    docs_dir = Path("./live_docs")
    processed_files = set()

    while True:
        # Find new or modified HTML files
        current_files = set(docs_dir.glob("**/*.html"))
        new_files = current_files - processed_files

        if new_files:
            print(f"📁 Found {len(new_files)} new/updated files")

            # Process new files
            results = await AsyncWebScraper.process_local_files_fast(
                file_paths=[str(f) for f in new_files],
                output_file="data/live_docs.json",
                concurrent_limit=4
            )

            print(f"✅ Processed {results['metadata']['total_files']} files")
            processed_files.update(new_files)

        # Wait before checking again
        await asyncio.sleep(5)

# Run file watcher (use with caution - infinite loop)
# asyncio.run(watch_and_process_files())
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