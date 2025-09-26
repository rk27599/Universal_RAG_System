# Web Scraper API

Synchronous web scraper optimized for reliability and detailed debugging. Ideal for development, testing, and scenarios where step-by-step processing visibility is important.

## Class: WebScraper

Synchronous web scraper with comprehensive error reporting and debugging capabilities.

### Constructor

```python
WebScraper(base_url: str = None, respect_robots_txt: bool = True, local_mode: bool = False)
```

Initialize web scraper with optional configuration.

**Parameters:**
- `base_url` (str, optional): Base URL for the website to scrape. Used for robots.txt validation.
- `respect_robots_txt` (bool, optional): Whether to respect robots.txt rules. Defaults to True.
- `local_mode` (bool, optional): Enable local-only mode for processing HTML files. Defaults to False.

**Example:**
```python
from src.web_scraper import WebScraper

# Basic scraper for web content
scraper = WebScraper()

# Scraper for specific website with robots.txt
scraper = WebScraper(
    base_url="https://docs.python.org/",
    respect_robots_txt=True
)

# Local-only mode for processing HTML files
local_scraper = WebScraper(local_mode=True)
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
discover_urls(
    start_urls: List[str],
    max_pages: int = 50,
    same_domain_only: bool = True,
    max_depth: int = 2
) -> List[str]
```

Discover URLs starting from given URLs with intelligent filtering.

**Parameters:**
- `start_urls` (List[str]): List of URLs to start discovery from
- `max_pages` (int, optional): Maximum number of URLs to discover. Defaults to 50.
- `same_domain_only` (bool, optional): Stay within the starting domain. Defaults to True.
- `max_depth` (int, optional): Maximum crawling depth. Defaults to 2.

**Returns:**
- `List[str]`: List of discovered URLs

**Example:**
```python
scraper = WebScraper()

# Discover URLs from starting points
discovered_urls = scraper.discover_urls(
    start_urls=["https://docs.python.org/3/"],
    max_pages=30,
    same_domain_only=True,
    max_depth=2
)

print(f"Found {len(discovered_urls)} URLs:")
for url in discovered_urls[:5]:
    print(f"  - {url}")
```

## Local File Processing

### extract_from_local_file()

```python
extract_from_local_file(file_path: str) -> Optional[Dict]
```

Extract structured content from a local HTML file.

**Parameters:**
- `file_path` (str): Path to the HTML file to process

**Returns:**
- `Optional[Dict]`: Extracted document structure or None if failed

**Features:**
- Supports both .html and .htm files
- Extracts page title, sections, and content hierarchy
- Creates file:// URLs for consistency
- Handles encoding issues gracefully

**Example:**
```python
scraper = WebScraper(local_mode=True)

# Process a single HTML file
doc_structure = scraper.extract_from_local_file("docs/user-guide.html")

if doc_structure:
    print(f"Title: {doc_structure['page_title']}")
    print(f"Sections: {len(doc_structure['sections'])}")
    print(f"Domain: {doc_structure['domain']}")  # Will be 'local'

    # Examine sections
    for section in doc_structure['sections']:
        print(f"  - {section['title']} ({section['word_count']} words)")
else:
    print("Failed to extract content from file")
```

### process_local_files()

```python
process_local_files(
    file_paths: List[str],
    output_file: str = "data/local_docs_structured.json"
) -> Dict
```

Process multiple local HTML files with detailed progress reporting.

**Parameters:**
- `file_paths` (List[str]): List of HTML file paths to process
- `output_file` (str, optional): Output file path. Defaults to "data/local_docs_structured.json".

**Returns:**
- `Dict`: Processing results with metadata, documents, and semantic chunks

**Features:**
- Processes files sequentially with detailed logging
- Creates both JSON and TXT output formats
- Generates semantic chunks with proper metadata
- Provides comprehensive statistics and error reporting

**Example:**
```python
scraper = WebScraper(local_mode=True)

# Find HTML files in directory
html_files = scraper.find_html_files("./documentation", "*.html")

# Process all files
results = scraper.process_local_files(
    file_paths=html_files,
    output_file="data/documentation.json"
)

print(f"✅ Processed {results['metadata']['total_files']} files")
print(f"📊 Created {results['metadata']['total_chunks']} semantic chunks")

# Access processed documents
for doc in results['documents']:
    print(f"📄 {doc['page_title']}: {doc['total_sections']} sections")
```

### process_mixed_sources()

```python
process_mixed_sources(
    web_urls: List[str] = None,
    local_files: List[str] = None,
    output_file: str = "data/mixed_docs_structured.json",
    max_pages: int = 30,
    same_domain_only: bool = True,
    max_depth: int = 2
) -> Dict
```

Process both web URLs and local HTML files in a single operation.

**Parameters:**
- `web_urls` (List[str], optional): URLs to scrape from the web
- `local_files` (List[str], optional): Local HTML files to process
- `output_file` (str, optional): Output file path. Defaults to "data/mixed_docs_structured.json".
- `max_pages` (int, optional): Maximum pages for web scraping. Defaults to 30.
- `same_domain_only` (bool, optional): Domain restriction for web scraping. Defaults to True.
- `max_depth` (int, optional): Maximum depth for web scraping. Defaults to 2.

**Returns:**
- `Dict`: Combined processing results

**Example:**
```python
scraper = WebScraper()

# Process both web and local sources
results = scraper.process_mixed_sources(
    web_urls=["https://docs.python.org/3/tutorial/"],
    local_files=["./docs/custom-guide.html", "./docs/api-reference.html"],
    output_file="data/comprehensive_docs.json",
    max_pages=20
)

metadata = results['metadata']
print(f"📊 Mixed Processing Results:")
print(f"  Web URLs processed: {len(metadata['web_urls'])}")
print(f"  Local files processed: {len(metadata['local_files'])}")
print(f"  Total documents: {metadata['total_documents']}")
print(f"  Total chunks: {metadata['total_chunks']}")
print(f"  Domains covered: {len(metadata['domains'])}")
```

### find_html_files()

```python
find_html_files(directory: str, pattern: str = "*.html") -> List[str]
```

Find HTML files in a directory with glob pattern support.

**Parameters:**
- `directory` (str): Directory to search in
- `pattern` (str, optional): Glob pattern for file matching. Defaults to "*.html".

**Returns:**
- `List[str]`: Sorted list of HTML file paths found

**Features:**
- Supports both .html and .htm files automatically
- Recursive search with ** patterns
- Removes duplicates and sorts results
- Cross-platform path handling

**Example:**
```python
scraper = WebScraper()

# Find HTML files in current directory
html_files = scraper.find_html_files("./docs")

# Find HTML files recursively
all_html = scraper.find_html_files("./docs", "**/*.html")

# Find both HTML and HTM files
all_files = []
all_files.extend(scraper.find_html_files("./docs", "*.html"))
all_files.extend(scraper.find_html_files("./docs", "*.htm"))

print(f"Found {len(html_files)} HTML files:")
for file_path in html_files:
    print(f"  - {file_path}")
```

## Content Processing Methods

### extract_sections()

```python
extract_sections(content_soup: BeautifulSoup, url: str, page_title: str) -> List[Dict]
```

Extract sections with hierarchy and context from HTML content.

**Parameters:**
- `content_soup` (BeautifulSoup): Cleaned HTML content
- `url` (str): Source URL for metadata
- `page_title` (str): Page title for context

**Returns:**
- `List[Dict]`: List of section dictionaries with content and metadata

**Features:**
- Respects HTML heading hierarchy (h1-h6)
- Processes various content types (paragraphs, code, lists, tables)
- Labels content by type for better organization
- Maintains section relationships and word counts

**Example:**
```python
from bs4 import BeautifulSoup

scraper = WebScraper()

# Process HTML content manually
with open("example.html", 'r') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')
soup = scraper.clean_content(soup)

sections = scraper.extract_sections(soup, "file://example.html", "Example Page")

for section in sections:
    print(f"Section: {section['title']} (Level {section['level']})")
    print(f"  Content items: {len(section['content'])}")
    print(f"  Word count: {section['word_count']}")
```

### extract_table_text()

```python
extract_table_text(table_element) -> str
```

Extract structured text from HTML table elements.

**Parameters:**
- `table_element`: BeautifulSoup table element

**Returns:**
- `str`: Formatted table text with pipe separators

**Example:**
```python
scraper = WebScraper()

# Extract table from HTML
soup = BeautifulSoup(html_content, 'html.parser')
table = soup.find('table')

if table:
    table_text = scraper.extract_table_text(table)
    print("Table content:")
    print(table_text)
```

### create_semantic_chunks()

```python
create_semantic_chunks(
    structured_docs: List[Dict],
    max_chunk_size: int = 1200
) -> List[Dict]
```

Create semantically meaningful chunks from structured documents.

**Parameters:**
- `structured_docs` (List[Dict]): List of structured document dictionaries
- `max_chunk_size` (int, optional): Maximum size per chunk. Defaults to 1200.

**Returns:**
- `List[Dict]`: List of semantic chunks with rich metadata

**Features:**
- Maintains semantic coherence across chunks
- Smart splitting for large sections using paragraph boundaries
- Rich metadata including page titles, section titles, URLs
- Content type classification and word counts

**Example:**
```python
scraper = WebScraper()

# Process files and create chunks
results = scraper.process_local_files(["doc1.html", "doc2.html"])
documents = results['documents']

# Create custom chunks with different size
chunks = scraper.create_semantic_chunks(documents, max_chunk_size=800)

print(f"Created {len(chunks)} semantic chunks")

for chunk in chunks[:3]:  # Show first 3
    print(f"Title: {chunk['title']}")
    print(f"Type: {chunk.get('type', 'unknown')}")
    print(f"Words: {chunk['word_count']}")
    print(f"Content: {chunk['text'][:100]}...")
    print("-" * 50)
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

### Local File Processing Pipeline

```python
from src.web_scraper import WebScraper
from src.rag_system import RAGSystem

def local_file_rag_pipeline():
    """Complete pipeline for processing local HTML documentation."""

    print("📂 Starting local file → RAG pipeline...")

    # Step 1: Process local HTML files
    scraper = WebScraper(local_mode=True)

    # Find all HTML documentation files
    html_files = scraper.find_html_files("./documentation", "**/*.html")

    if not html_files:
        print("❌ No HTML files found in documentation directory")
        return None

    print(f"📄 Found {len(html_files)} HTML files")

    # Process all local files
    results = scraper.process_local_files(
        file_paths=html_files,
        output_file="data/local_documentation.json"
    )

    print(f"✅ Processed {results['metadata']['total_files']} files")
    print(f"📊 Created {results['metadata']['total_chunks']} semantic chunks")

    # Step 2: Load into RAG system
    rag = RAGSystem()
    loaded = rag.load_data("data/local_documentation.json")

    if not loaded:
        print("❌ Failed to load data into RAG system")
        return None

    print("✅ Data loaded into RAG system")

    # Step 3: Test with documentation-specific queries
    test_queries = [
        "How to install the software?",
        "API authentication methods",
        "Configuration file format",
        "Troubleshooting common issues"
    ]

    print("\n🧪 Testing documentation queries...")
    for query in test_queries:
        result = rag.demo_query(query, top_k=3)

        if result['chunks']:
            best_score = result['chunks'][0]['score']
            print(f"Query: '{query}' - Score: {best_score:.3f}")

            if best_score < 0.3:
                print(f"  ⚠️  Low relevance - may need more specific documentation")
        else:
            print(f"Query: '{query}' - No results found")

    return rag

# Process local documentation
rag_system = local_file_rag_pipeline()
```

### Mixed Source Processing Pipeline

```python
def mixed_source_rag_pipeline():
    """Process both web content and local files together."""

    print("🔄 Starting mixed source → RAG pipeline...")

    scraper = WebScraper()

    # Step 1: Find local HTML files
    local_files = scraper.find_html_files("./docs", "*.html")

    # Step 2: Process mixed sources
    results = scraper.process_mixed_sources(
        web_urls=["https://docs.python.org/3/tutorial/"],
        local_files=local_files,
        output_file="data/mixed_comprehensive.json",
        max_pages=25
    )

    metadata = results['metadata']
    print(f"📊 Mixed Processing Complete:")
    print(f"  Web pages: {len(metadata.get('web_urls', []))}")
    print(f"  Local files: {len(metadata.get('local_files', []))}")
    print(f"  Total documents: {metadata['total_documents']}")
    print(f"  Total chunks: {metadata['total_chunks']}")

    # Step 3: Load into RAG system
    rag = RAGSystem()
    loaded = rag.load_data("data/mixed_comprehensive.json")

    if loaded:
        print("✅ Mixed source data loaded successfully")

        # Test comprehensive queries
        comprehensive_queries = [
            "Python basics and fundamentals",
            "Local setup and configuration",
            "Advanced programming concepts"
        ]

        for query in comprehensive_queries:
            result = rag.demo_query(query, top_k=5)
            if result['chunks']:
                sources = set(chunk.get('domain', 'unknown') for chunk in result['chunks'])
                best_score = result['chunks'][0]['score']
                print(f"Query: '{query}'")
                print(f"  Score: {best_score:.3f}")
                print(f"  Sources: {', '.join(sources)}")

    return rag

# Process mixed sources
mixed_rag = mixed_source_rag_pipeline()
```

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