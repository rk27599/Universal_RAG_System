# Web Scraper API

Synchronous web scraper optimized for reliability and detailed debugging. Ideal for development, testing, and scenarios where step-by-step processing visibility is important.

## Class: WebScraper

Synchronous web scraper with comprehensive error reporting and debugging capabilities.

### Constructor

```python
WebScraper()
```

Simple constructor with no configuration parameters. All settings are passed to individual methods.

**Example:**
```python
from src.web_scraper import WebScraper

# Initialize scraper
scraper = WebScraper()
```

## Core Methods

### scrape_website()

```python
scrape_website(
    start_urls: List[str],
    output_file: str,
    max_pages: int = 30,
    max_depth: int = 2,
    same_domain_only: bool = True
) -> bool
```

Scrape a website with synchronous processing and detailed logging.

**Parameters:**
- `start_urls` (List[str]): List of URLs to start scraping from
- `output_file` (str): Output file path for scraped data
- `max_pages` (int, optional): Maximum number of pages to scrape. Defaults to 30.
- `max_depth` (int, optional): Maximum crawling depth. Defaults to 2.
- `same_domain_only` (bool, optional): Stay within the starting domain. Defaults to True.

**Returns:**
- `bool`: True if scraping was successful, False otherwise

**Example:**
```python
from src.web_scraper import WebScraper
import logging

# Enable detailed logging for debugging
logging.basicConfig(level=logging.INFO)

scraper = WebScraper()

# Basic usage
success = scraper.scrape_website(
    start_urls=["https://docs.python.org/3/"],
    output_file="data/python_docs.json"
)

if success:
    print("✅ Scraping completed successfully")
else:
    print("❌ Scraping failed - check logs for details")

# Advanced configuration
success = scraper.scrape_website(
    start_urls=["https://fastapi.tiangolo.com/"],
    output_file="data/fastapi_docs.json",
    max_pages=50,
    max_depth=3,
    same_domain_only=True
)
```

### scrape_page()

```python
scrape_page(url: str) -> Optional[Dict[str, Any]]
```

Scrape a single page with detailed error reporting.

**Parameters:**
- `url` (str): URL to scrape

**Returns:**
- `Optional[Dict[str, Any]]`: Page data with content and metadata, or None if failed

**Example:**
```python
scraper = WebScraper()

# Scrape single page
page_data = scraper.scrape_page("https://docs.python.org/3/tutorial/")

if page_data:
    print(f"Page title: {page_data['title']}")
    print(f"Content chunks: {len(page_data['content'])}")
    print(f"Links found: {len(page_data.get('links', []))}")
else:
    print("Failed to scrape page")
```

### extract_content()

```python
extract_content(soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]
```

Extract structured content from parsed HTML.

**Parameters:**
- `soup` (BeautifulSoup): Parsed HTML content
- `url` (str): Source URL for metadata

**Returns:**
- `List[Dict[str, Any]]`: List of content chunks with metadata

**Example:**
```python
from bs4 import BeautifulSoup
import requests

scraper = WebScraper()

# Manual content extraction
response = requests.get("https://example.com/")
soup = BeautifulSoup(response.content, 'html.parser')

content_chunks = scraper.extract_content(soup, "https://example.com/")

for chunk in content_chunks:
    print(f"Type: {chunk['content_type']}")
    print(f"Content: {chunk['content'][:100]}...")
    print(f"Metadata: {chunk['metadata']}")
    print("-" * 50)
```

### discover_urls()

```python
discover_urls(soup: BeautifulSoup, base_url: str, current_depth: int) -> Set[str]
```

Discover new URLs from page content with depth and domain filtering.

**Parameters:**
- `soup` (BeautifulSoup): Parsed HTML content
- `base_url` (str): Base URL for resolving relative links
- `current_depth` (int): Current crawling depth

**Returns:**
- `Set[str]`: Set of discovered URLs

**Example:**
```python
scraper = WebScraper()

# Manual URL discovery
response = requests.get("https://docs.python.org/3/")
soup = BeautifulSoup(response.content, 'html.parser')

discovered_urls = scraper.discover_urls(
    soup,
    "https://docs.python.org/3/",
    current_depth=1
)

print(f"Found {len(discovered_urls)} URLs:")
for url in list(discovered_urls)[:5]:
    print(f"  - {url}")
```

## Advanced Usage

### Debugging and Development

```python
import logging
from src.web_scraper import WebScraper

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_scraping():
    """Example of using sync scraper for debugging."""

    scraper = WebScraper()

    # Start with a single page
    test_url = "https://docs.python.org/3/tutorial/introduction.html"
    page_data = scraper.scrape_page(test_url)

    if page_data:
        print(f"Successfully scraped: {page_data['title']}")
        print(f"Content chunks: {len(page_data['content'])}")

        # Examine content types
        content_types = {}
        for chunk in page_data['content']:
            ctype = chunk['content_type']
            content_types[ctype] = content_types.get(ctype, 0) + 1

        print(f"Content distribution: {content_types}")

        # Check for issues
        empty_chunks = [c for c in page_data['content'] if not c['content'].strip()]
        if empty_chunks:
            print(f"Warning: {len(empty_chunks)} empty content chunks found")

    else:
        print("Failed to scrape page - check logs for details")

debug_scraping()
```

### Step-by-Step Processing

```python
from src.web_scraper import WebScraper
import json
import time

def process_with_monitoring():
    """Monitor scraping progress with detailed feedback."""

    scraper = WebScraper()
    start_urls = ["https://docs.python.org/3/tutorial/"]

    print("🚀 Starting synchronous scraping...")
    start_time = time.time()

    # Process with monitoring
    success = scraper.scrape_website(
        start_urls=start_urls,
        output_file="data/tutorial_docs.json",
        max_pages=25,
        max_depth=2
    )

    elapsed = time.time() - start_time

    if success:
        # Analyze results
        with open("data/tutorial_docs.json", 'r') as f:
            data = json.load(f)

        pages = len(set(doc['metadata']['url'] for doc in data))
        chunks = len(data)

        print(f"✅ Scraping completed in {elapsed:.1f} seconds")
        print(f"📄 Processed {pages} pages into {chunks} chunks")
        print(f"📊 Average chunks per page: {chunks/pages:.1f}")
        print(f"⏱️  Average time per page: {elapsed/pages:.2f} seconds")

        # Content quality analysis
        avg_length = sum(len(doc['content']) for doc in data) / len(data)
        print(f"📝 Average chunk length: {avg_length:.0f} characters")

    else:
        print(f"❌ Scraping failed after {elapsed:.1f} seconds")

process_with_monitoring()
```

### Custom Content Processing

```python
class CustomWebScraper(WebScraper):
    """Extended scraper with custom processing logic."""

    def __init__(self):
        super().__init__()
        self.processing_stats = {
            'pages_processed': 0,
            'content_chunks': 0,
            'errors': []
        }

    def scrape_page(self, url):
        """Override with custom processing and statistics."""
        try:
            page_data = super().scrape_page(url)

            if page_data:
                self.processing_stats['pages_processed'] += 1
                self.processing_stats['content_chunks'] += len(page_data['content'])

                # Custom content filtering
                filtered_content = self._filter_content(page_data['content'])
                page_data['content'] = filtered_content

                print(f"✅ Processed: {url} ({len(filtered_content)} chunks)")
            else:
                self.processing_stats['errors'].append(url)
                print(f"❌ Failed: {url}")

            return page_data

        except Exception as e:
            self.processing_stats['errors'].append(f"{url}: {str(e)}")
            print(f"💥 Error processing {url}: {e}")
            return None

    def _filter_content(self, content_chunks):
        """Apply custom filtering to content chunks."""
        filtered = []

        for chunk in content_chunks:
            # Skip very short content
            if len(chunk['content']) < 50:
                continue

            # Skip navigation and footer content
            if chunk['content_type'] in ['nav', 'footer']:
                continue

            # Enhance metadata
            chunk['metadata']['processed_by'] = 'CustomWebScraper'
            chunk['metadata']['word_count'] = len(chunk['content'].split())

            filtered.append(chunk)

        return filtered

    def get_statistics(self):
        """Get processing statistics."""
        return self.processing_stats

# Usage
def run_custom_scraping():
    scraper = CustomWebScraper()

    success = scraper.scrape_website(
        start_urls=["https://docs.python.org/3/library/"],
        output_file="data/library_docs.json",
        max_pages=20
    )

    stats = scraper.get_statistics()
    print(f"\n📊 Processing Statistics:")
    print(f"Pages processed: {stats['pages_processed']}")
    print(f"Content chunks: {stats['content_chunks']}")
    print(f"Errors: {len(stats['errors'])}")

    if stats['errors']:
        print("\nErrors encountered:")
        for error in stats['errors']:
            print(f"  - {error}")

run_custom_scraping()
```

### Content Quality Analysis

```python
import json
from collections import defaultdict
from src.web_scraper import WebScraper

def analyze_content_quality():
    """Analyze scraped content for quality and completeness."""

    scraper = WebScraper()

    # Scrape test content
    success = scraper.scrape_website(
        start_urls=["https://docs.python.org/3/tutorial/"],
        output_file="data/quality_test.json",
        max_pages=15
    )

    if not success:
        print("Scraping failed")
        return

    # Load and analyze
    with open("data/quality_test.json", 'r') as f:
        data = json.load(f)

    print(f"📊 Content Quality Analysis")
    print(f"Total chunks: {len(data)}")

    # Content type distribution
    content_types = defaultdict(int)
    content_lengths = []

    for doc in data:
        content_types[doc['content_type']] += 1
        content_lengths.append(len(doc['content']))

    print(f"\n📋 Content Types:")
    for ctype, count in sorted(content_types.items()):
        print(f"  {ctype}: {count}")

    # Length analysis
    avg_length = sum(content_lengths) / len(content_lengths)
    min_length = min(content_lengths)
    max_length = max(content_lengths)

    print(f"\n📏 Content Length Analysis:")
    print(f"  Average: {avg_length:.0f} characters")
    print(f"  Range: {min_length} - {max_length} characters")

    # Quality indicators
    empty_content = sum(1 for doc in data if not doc['content'].strip())
    short_content = sum(1 for length in content_lengths if length < 100)

    print(f"\n⚠️  Quality Issues:")
    print(f"  Empty chunks: {empty_content}")
    print(f"  Short chunks (<100 chars): {short_content}")

    # Page coverage
    unique_pages = len(set(doc['metadata']['url'] for doc in data))
    print(f"\n📄 Page Coverage:")
    print(f"  Unique pages: {unique_pages}")
    print(f"  Chunks per page: {len(data)/unique_pages:.1f}")

analyze_content_quality()
```

## Error Handling and Troubleshooting

### Comprehensive Error Handling

```python
import logging
import traceback
from src.web_scraper import WebScraper

def robust_scraping_with_recovery():
    """Example of robust scraping with error recovery."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scraper = WebScraper()
    test_urls = [
        "https://docs.python.org/3/tutorial/",
        "https://docs.python.org/3/library/",
        "https://docs.python.org/3/reference/"
    ]

    results = {}

    for i, url in enumerate(test_urls):
        print(f"\n--- Processing URL {i+1}/{len(test_urls)}: {url} ---")

        try:
            output_file = f"data/docs_part_{i+1}.json"

            success = scraper.scrape_website(
                start_urls=[url],
                output_file=output_file,
                max_pages=20,
                max_depth=2
            )

            if success:
                print(f"✅ Successfully processed {url}")
                results[url] = {"status": "success", "file": output_file}
            else:
                print(f"⚠️  Partial processing for {url}")
                results[url] = {"status": "partial", "file": output_file}

        except Exception as e:
            print(f"❌ Failed to process {url}: {e}")
            results[url] = {"status": "failed", "error": str(e)}

            # Log detailed error
            logging.error(f"Error processing {url}:")
            logging.error(traceback.format_exc())

    # Summary
    print(f"\n📊 Processing Summary:")
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    partial_count = sum(1 for r in results.values() if r['status'] == 'partial')
    failed_count = sum(1 for r in results.values() if r['status'] == 'failed')

    print(f"Successful: {success_count}/{len(test_urls)}")
    print(f"Partial: {partial_count}/{len(test_urls)}")
    print(f"Failed: {failed_count}/{len(test_urls)}")

    return results

results = robust_scraping_with_recovery()
```

### Debugging Common Issues

```python
def diagnose_scraping_issues():
    """Diagnose common scraping problems."""

    scraper = WebScraper()
    test_url = "https://docs.python.org/3/"

    print("🔍 Diagnosing scraping issues...")

    # Test single page access
    print("\n1. Testing single page access...")
    page_data = scraper.scrape_page(test_url)

    if not page_data:
        print("❌ Cannot access single page - check network/URL")
        return
    else:
        print(f"✅ Single page access OK - got {len(page_data['content'])} chunks")

    # Test content extraction
    print("\n2. Testing content extraction...")
    if not page_data['content']:
        print("❌ No content extracted - check HTML parsing")
    else:
        content_types = set(chunk['content_type'] for chunk in page_data['content'])
        print(f"✅ Content extraction OK - types: {content_types}")

    # Test URL discovery
    print("\n3. Testing URL discovery...")
    from bs4 import BeautifulSoup
    import requests

    response = requests.get(test_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    discovered_urls = scraper.discover_urls(soup, test_url, current_depth=1)

    if not discovered_urls:
        print("❌ No URLs discovered - check link extraction logic")
    else:
        print(f"✅ URL discovery OK - found {len(discovered_urls)} URLs")

    # Test full scraping with minimal settings
    print("\n4. Testing full scraping (minimal)...")
    success = scraper.scrape_website(
        start_urls=[test_url],
        output_file="data/diagnostic_test.json",
        max_pages=5,
        max_depth=1
    )

    if success:
        print("✅ Full scraping OK")
    else:
        print("❌ Full scraping failed - check logs")

diagnose_scraping_issues()
```

## Integration with RAG System

### Direct Integration

```python
from src.web_scraper import WebScraper
from src.rag_system import RAGSystem

def sync_scraping_rag_pipeline():
    """Complete pipeline using sync scraper for reliable processing."""

    print("🔄 Starting sync scraping → RAG pipeline...")

    # Step 1: Reliable scraping
    scraper = WebScraper()
    success = scraper.scrape_website(
        start_urls=["https://docs.python.org/3/tutorial/"],
        output_file="data/reliable_docs.json",
        max_pages=30,
        max_depth=2
    )

    if not success:
        print("❌ Scraping failed")
        return None

    print("✅ Scraping completed successfully")

    # Step 2: Load into RAG system
    rag = RAGSystem()
    loaded = rag.load_data("data/reliable_docs.json")

    if not loaded:
        print("❌ Failed to load data into RAG system")
        return None

    print("✅ Data loaded into RAG system")

    # Step 3: Quality testing
    test_queries = [
        "How to define functions in Python?",
        "What are Python data types?",
        "How to use loops in Python?"
    ]

    print("\n🧪 Testing query quality...")
    for query in test_queries:
        result = rag.demo_query(query, top_k=3)

        if result['chunks']:
            best_score = result['chunks'][0]['score']
            print(f"Query: '{query}' - Score: {best_score:.3f}")

            if best_score < 0.3:
                print(f"  ⚠️  Low relevance score for this query")
        else:
            print(f"Query: '{query}' - No results found")

    return rag

# Run pipeline
rag_system = sync_scraping_rag_pipeline()
```

### Comparison with Async Scraper

```python
import time
from src.web_scraper import WebScraper
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
import asyncio

def compare_scraping_approaches():
    """Compare sync vs async scraping performance and reliability."""

    test_url = "https://docs.python.org/3/library/"
    max_pages = 20

    print("⚖️  Comparing Sync vs Async Scraping...")

    # Test sync scraper
    print("\n--- Sync Scraper Test ---")
    sync_start = time.time()

    sync_scraper = WebScraper()
    sync_success = sync_scraper.scrape_website(
        start_urls=[test_url],
        output_file="data/sync_test.json",
        max_pages=max_pages,
        max_depth=1
    )

    sync_time = time.time() - sync_start

    if sync_success:
        print(f"✅ Sync scraping: {sync_time:.1f} seconds")
    else:
        print(f"❌ Sync scraping failed after {sync_time:.1f} seconds")

    # Test async scraper
    print("\n--- Async Scraper Test ---")

    async def run_async_test():
        config = ScrapingConfig(
            concurrent_limit=4,
            max_pages=max_pages,
            requests_per_second=6.0
        )

        async_scraper = AsyncWebScraper(config)
        success, metrics = await async_scraper.scrape_website(
            [test_url],
            "data/async_test.json"
        )

        return success, metrics

    async_start = time.time()
    async_success, async_metrics = asyncio.run(run_async_test())
    async_time = time.time() - async_start

    if async_success:
        print(f"✅ Async scraping: {async_time:.1f} seconds")
        print(f"   Pages processed: {async_metrics.urls_processed}")
    else:
        print(f"❌ Async scraping failed after {async_time:.1f} seconds")

    # Comparison
    if sync_success and async_success:
        speedup = sync_time / async_time
        print(f"\n📈 Performance Comparison:")
        print(f"   Sync time: {sync_time:.1f}s")
        print(f"   Async time: {async_time:.1f}s")
        print(f"   Speedup: {speedup:.1f}x")

        if speedup > 2:
            print("   🚀 Async provides significant speedup")
        elif speedup > 1.2:
            print("   ⚡ Async provides moderate speedup")
        else:
            print("   🐌 Similar performance (site may be rate-limited)")

compare_scraping_approaches()
```

## Best Practices

### Development and Testing

1. **Start Small**: Begin with single pages and small max_pages values
2. **Enable Logging**: Use detailed logging for debugging
3. **Check Content Quality**: Analyze extracted content for completeness
4. **Handle Errors Gracefully**: Implement comprehensive error handling
5. **Monitor Progress**: Use step-by-step processing for visibility

### When to Use Sync Scraper

- **Development and debugging** - easier to trace issues
- **Small to medium websites** - performance difference is minimal
- **Content quality analysis** - step-by-step processing visibility
- **Error diagnosis** - detailed error reporting and logging
- **Learning and exploration** - understanding scraping mechanics

### Configuration Guidelines

```python
# Development/debugging
scraper.scrape_website(
    start_urls=[url],
    max_pages=10,     # Small for testing
    max_depth=1,      # Shallow for quick feedback
    output_file="debug.json"
)

# Production (reliable)
scraper.scrape_website(
    start_urls=[url],
    max_pages=50,     # Reasonable size
    max_depth=2,      # Standard depth
    output_file="production.json"
)

# Quality analysis
scraper.scrape_website(
    start_urls=[url],
    max_pages=25,     # Medium size
    max_depth=3,      # Deeper analysis
    output_file="analysis.json"
)
```

---

*For high-performance scraping needs, see the [Async Web Scraper API](./async_web_scraper.md). For complete usage examples, check the [Getting Started Guide](../guides/getting-started.md).*