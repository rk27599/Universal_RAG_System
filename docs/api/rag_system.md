# RAG System API

The `RAGSystem` class provides the main interface for the Universal RAG System, combining web scraping, document processing, and retrieval-augmented generation.

## Class: RAGSystem

High-level interface for website scraping, document processing, and query answering.

### Constructor

```python
RAGSystem(chunk_size: int = 1200, overlap: int = 100, use_async: bool = False)
```

**Parameters:**
- `chunk_size` (int, optional): Size of text chunks for processing. Defaults to 1200.
- `overlap` (int, optional): Overlap between chunks. Defaults to 100.
- `use_async` (bool, optional): Whether to use async scraping. Defaults to False.

**Example:**
```python
from src.rag_system import RAGSystem

# Default configuration
rag = RAGSystem()

# Custom configuration
rag = RAGSystem(
    chunk_size=1500,
    overlap=150,
    use_async=True
)
```

## Core Methods

### scrape_and_process_website()

```python
scrape_and_process_website(
    start_urls: List[str],
    max_pages: int = 30,
    output_file: str = "data/website_docs.json",
    same_domain_only: bool = True,
    max_depth: int = 2,
    use_cache: bool = True
) -> bool
```

Scrape and process a website for RAG queries.

**Parameters:**
- `start_urls` (List[str]): List of URLs to start scraping from
- `max_pages` (int, optional): Maximum number of pages to scrape. Defaults to 30.
- `output_file` (str, optional): Output file path. Defaults to "data/website_docs.json".
- `same_domain_only` (bool, optional): Stay within the starting domain. Defaults to True.
- `max_depth` (int, optional): Maximum crawling depth. Defaults to 2.
- `use_cache` (bool, optional): Enable caching for performance. Defaults to True.

**Returns:**
- `bool`: True if scraping was successful, False otherwise

**Example:**
```python
rag = RAGSystem()

# Basic usage
success = rag.scrape_and_process_website([
    "https://docs.python.org/3/"
])

# Advanced configuration
success = rag.scrape_and_process_website(
    start_urls=["https://fastapi.tiangolo.com/"],
    max_pages=50,
    max_depth=3,
    same_domain_only=True,
    output_file="data/fastapi_docs.json"
)

if success:
    print("✅ Website scraped and processed successfully!")
else:
    print("❌ Scraping failed - check logs for details")
```

### demo_query()

```python
demo_query(query: str, top_k: int = 5) -> str
```

Perform a retrieval-only query with detailed formatted output.

**Parameters:**
- `query` (str): The query string
- `top_k` (int, optional): Number of top results to return. Defaults to 5.

**Returns:**
- `str`: Formatted string with query results and similarity scores

**Example:**
```python
# Simple query
result = rag.demo_query("How to define functions in Python?")
print(result)  # Prints formatted results with scores and content

# Query with more results
result = rag.demo_query("How to create API endpoints?", top_k=7)
print(result)  # Shows top 7 results with detailed information
```

**Example Output:**
```
🔍 Query: "How to define functions in Python?"

📊 Results (showing top 5 of 5 matches):

--- Result 1: Score 0.756 ---
📄 Page: Python Functions Tutorial
🏷️  Type: paragraph
📝 Content: To define a function in Python, use the def keyword followed by the function name...

--- Result 2: Score 0.634 ---
📄 Page: Python Basics
🏷️  Type: code
📝 Content: def my_function(): return "Hello World"...
```

### rag_query()

```python
rag_query(
    query: str,
    top_k: int = 5,
    model: str = "llama2",
    ollama_url: str = "http://localhost:11434"
) -> str
```

Perform full RAG query with text generation using Ollama.

**Parameters:**
- `query` (str): The query string
- `top_k` (int, optional): Number of context chunks to use. Defaults to 5.
- `model` (str, optional): Ollama model to use. Defaults to "llama2".
- `ollama_url` (str, optional): Ollama API URL. Defaults to "http://localhost:11434".

**Returns:**
- `str`: Generated answer based on retrieved context

**Requirements:**
- Ollama must be running (`ollama serve`)
- Specified model must be available (`ollama pull mistral`)

**Example:**
```python
# Basic generation
answer = rag.rag_query("How to define functions in Python?")
print(answer)

# Advanced configuration
answer = rag.rag_query(
    "How to create REST API endpoints?",
    top_k=5,
    model="llama2",
    temperature=0.3  # More focused responses
)

# Handle errors gracefully
try:
    answer = rag.rag_query("Your question here", model="mistral")
    print(answer)
except Exception as e:
    print(f"Generation failed: {e}")
    # Fall back to retrieval only
    result = rag.demo_query("Your question here")
```

### load_data()

```python
load_data(file_path: str) -> bool
```

Load preprocessed data from a file.

**Parameters:**
- `file_path` (str): Path to the data file (JSON or TXT format)

**Returns:**
- `bool`: True if data was loaded successfully

**Example:**
```python
# Load from JSON file
success = rag.load_data("data/website_docs.json")

# Load from text file
success = rag.load_data("data/website_docs.txt")

if success:
    print(f"✅ Data loaded successfully")
else:
    print("❌ Failed to load data")
```

## Async Processing Methods

### scrape_and_process_website_async()

```python
async def scrape_and_process_website_async(
    self,
    start_urls: List[str],
    max_pages: int = 30,
    output_file: str = "data/website_docs_async.json",
    same_domain_only: bool = True,
    max_depth: int = 2,
    concurrent_limit: int = 6,
    requests_per_second: float = 8.0
) -> bool
```

Asynchronous version of website scraping and processing with high performance.

**Parameters:**
- `start_urls` (List[str]): List of URLs to start scraping from
- `max_pages` (int, optional): Maximum number of pages to scrape. Defaults to 30.
- `output_file` (str, optional): Output file path. Defaults to "data/website_docs_async.json".
- `same_domain_only` (bool, optional): Stay within the starting domain. Defaults to True.
- `max_depth` (int, optional): Maximum crawling depth. Defaults to 2.
- `concurrent_limit` (int, optional): Number of concurrent requests. Defaults to 6.
- `requests_per_second` (float, optional): Rate limiting. Defaults to 8.0.

**Returns:**
- `bool`: True if scraping was successful, False otherwise

**Example:**
```python
import asyncio

async def async_scraping_pipeline():
    rag = RAGSystem(use_async=True)

    # High-performance async scraping
    success = await rag.scrape_and_process_website_async(
        start_urls=["https://docs.python.org/3/"],
        max_pages=50,
        concurrent_limit=8,
        requests_per_second=10.0,
        output_file="data/python_docs_async.json"
    )

    if success:
        print("✅ Async scraping completed successfully!")

        # Test queries immediately
        result = rag.demo_query("Python data types", top_k=3)
        best_score = result['chunks'][0]['score'] if result['chunks'] else 0
        print(f"Best relevance score: {best_score:.3f}")

        return rag
    else:
        print("❌ Async scraping failed")
        return None

# Run async scraping
rag_system = asyncio.run(async_scraping_pipeline())
```

### process_local_files_async()

```python
async def process_local_files_async(
    self,
    file_paths: List[str],
    output_file: str = "data/local_docs_async.json",
    concurrent_limit: int = 6
) -> bool
```

Process local HTML files asynchronously with high performance.

**Parameters:**
- `file_paths` (List[str]): List of HTML file paths to process
- `output_file` (str, optional): Output file path. Defaults to "data/local_docs_async.json".
- `concurrent_limit` (int, optional): Number of files to process concurrently. Defaults to 6.

**Returns:**
- `bool`: True if processing was successful, False otherwise

**Example:**
```python
import asyncio
from pathlib import Path

async def process_documentation_async():
    rag = RAGSystem(use_async=True)

    # Find all HTML files in documentation
    docs_dir = Path("./documentation")
    html_files = list(docs_dir.glob("**/*.html"))
    html_file_paths = [str(f) for f in html_files]

    if html_files:
        print(f"📁 Found {len(html_files)} HTML files")

        # Process asynchronously
        success = await rag.process_local_files_async(
            file_paths=html_file_paths,
            output_file="data/local_docs_fast.json",
            concurrent_limit=8
        )

        if success:
            print("✅ Local files processed successfully!")

            # Test documentation queries
            queries = [
                "installation instructions",
                "configuration options",
                "API reference"
            ]

            for query in queries:
                result = rag.demo_query(query, top_k=3)
                if result['chunks']:
                    score = result['chunks'][0]['score']
                    print(f"'{query}': {score:.3f}")

        return rag
    else:
        print("❌ No HTML files found")
        return None

# Process local documentation
rag_system = asyncio.run(process_documentation_async())
```

### process_mixed_sources_async()

```python
async def process_mixed_sources_async(
    self,
    web_urls: List[str] = None,
    local_files: List[str] = None,
    output_file: str = "data/mixed_docs_async.json",
    max_pages: int = 30,
    same_domain_only: bool = True,
    max_depth: int = 2,
    concurrent_limit: int = 6
) -> bool
```

Process both web URLs and local files asynchronously in a unified pipeline.

**Parameters:**
- `web_urls` (List[str], optional): URLs to scrape from the web
- `local_files` (List[str], optional): Local HTML files to process
- `output_file` (str, optional): Output file path. Defaults to "data/mixed_docs_async.json".
- `max_pages` (int, optional): Maximum pages for web scraping. Defaults to 30.
- `same_domain_only` (bool, optional): Domain restriction for web scraping. Defaults to True.
- `max_depth` (int, optional): Maximum depth for web scraping. Defaults to 2.
- `concurrent_limit` (int, optional): Concurrent processing limit. Defaults to 6.

**Returns:**
- `bool`: True if processing was successful, False otherwise

**Example:**
```python
import asyncio

async def comprehensive_knowledge_base():
    rag = RAGSystem(use_async=True)

    # Combine web and local sources
    success = await rag.process_mixed_sources_async(
        web_urls=[
            "https://docs.python.org/3/tutorial/",
            "https://fastapi.tiangolo.com/"
        ],
        local_files=[
            "./docs/custom-guide.html",
            "./docs/internal-apis.html"
        ],
        output_file="data/comprehensive_kb.json",
        max_pages=40,
        concurrent_limit=8
    )

    if success:
        print("✅ Comprehensive knowledge base created!")

        # Test cross-source queries
        cross_queries = [
            "Python web development frameworks",
            "API design best practices",
            "Custom implementation details"
        ]

        for query in cross_queries:
            result = rag.demo_query(query, top_k=5)
            if result['chunks']:
                # Analyze source diversity
                sources = set()
                for chunk in result['chunks']:
                    if 'url' in chunk:
                        if chunk['url'].startswith('file://'):
                            sources.add('local')
                        else:
                            sources.add('web')

                best_score = result['chunks'][0]['score']
                print(f"'{query}':")
                print(f"  Score: {best_score:.3f}")
                print(f"  Sources: {', '.join(sources)}")

        return rag

    return None

# Create comprehensive knowledge base
kb_system = asyncio.run(comprehensive_knowledge_base())
```

## Data Management Methods

### clear_cache()

```python
clear_cache(output_file: str = "data/website_docs.json") -> bool
```

Clear cached data and reset the system for fresh processing.

**Parameters:**
- `output_file` (str, optional): Output file to clear cache for. Defaults to "data/website_docs.json".

**Returns:**
- `bool`: True if cache was cleared successfully

**Example:**
```python
rag = RAGSystem()

# Clear cache before processing new data
success = rag.clear_cache("data/website_docs.json")

if success:
    print("✅ Cache cleared successfully")

    # Now scrape fresh data
    success = rag.scrape_and_process_website([
        "https://docs.python.org/3/"
    ])
else:
    print("❌ Failed to clear cache")
```

### load_structured_data()

```python
load_structured_data(file_path: str) -> bool
```

Load and process structured data from previously processed files.

**Parameters:**
- `file_path` (str): Path to structured data file

**Returns:**
- `bool`: True if data was loaded and processed successfully

**Example:**
```python
rag = RAGSystem()

# Load pre-processed structured data
success = rag.load_structured_data("data/processed_docs.json")

if success:
    print("✅ Structured data loaded successfully")

    # Verify data quality
    result = rag.demo_query("test query", top_k=1)
    if result['chunks']:
        print(f"Data verification: {result['chunks'][0]['score']:.3f}")
else:
    print("❌ Failed to load structured data")
```

### process_structured_documents()

```python
process_structured_documents(file_path: str = None) -> bool
```

Process structured documents that are already loaded in memory.

**Parameters:**
- `file_path` (str, optional): Optional file path for additional processing

**Returns:**
- `bool`: True if processing was successful

**Example:**
```python
rag = RAGSystem()

# Load data first
rag.load_data("data/website_docs.json")

# Process the loaded documents
success = rag.process_structured_documents()

if success:
    print("✅ Documents processed successfully")

    # Test improved processing
    result = rag.demo_query("comprehensive test", top_k=3)
    print(f"Processing quality: {len(result['chunks'])} chunks found")
else:
    print("❌ Document processing failed")
```

## Query Processing Methods

### preprocess_query()

```python
preprocess_query(query: str) -> str
```

Preprocess and enhance queries for better retrieval performance.

**Parameters:**
- `query` (str): Raw query string

**Returns:**
- `str`: Processed and enhanced query

**Features:**
- Query normalization and cleaning
- Synonym expansion for technical terms
- Context enhancement for better matching

**Example:**
```python
rag = RAGSystem()

# Test query preprocessing
raw_queries = [
    "how to create functions?",
    "API authentication",
    "error handling best practices"
]

for raw_query in raw_queries:
    processed = rag.preprocess_query(raw_query)
    print(f"Raw: '{raw_query}'")
    print(f"Processed: '{processed}'")

    # Use processed query for better results
    result = rag.demo_query(processed, top_k=3)
    if result['chunks']:
        score = result['chunks'][0]['score']
        print(f"Score with processing: {score:.3f}")
    print("-" * 50)
```

### retrieve_context()

```python
retrieve_context(query: str, top_k: int = 5) -> Tuple[List[str], List[Dict]]
```

Retrieve context chunks with detailed scoring and metadata.

**Parameters:**
- `query` (str): Query string
- `top_k` (int, optional): Number of top results to return. Defaults to 5.

**Returns:**
- `Tuple[List[str], List[Dict]]`: Tuple of (context_texts, chunk_metadata)

**Example:**
```python
rag = RAGSystem()
rag.load_data("data/website_docs.json")

# Retrieve context with detailed analysis
query = "Python function definitions"
context_texts, chunk_metadata = rag.retrieve_context(query, top_k=5)

print(f"📋 Retrieved {len(context_texts)} context chunks:")

for i, (text, metadata) in enumerate(zip(context_texts, chunk_metadata)):
    print(f"\n--- Chunk {i+1} ---")
    print(f"Score: {metadata.get('score', 0):.3f}")
    print(f"Source: {metadata.get('url', 'unknown')}")
    print(f"Title: {metadata.get('title', 'unknown')}")
    print(f"Content: {text[:150]}...")

# Use context for custom processing
combined_context = "\n\n".join(context_texts)
print(f"\n📊 Total context length: {len(combined_context)} characters")
```


## Advanced Usage

### Batch Processing Multiple Websites

```python
websites = [
    "https://docs.python.org/3/",
    "https://fastapi.tiangolo.com/",
    "https://flask.palletsprojects.com/"
]

rag = RAGSystem()

for i, url in enumerate(websites):
    print(f"Processing {url} ({i+1}/{len(websites)})...")

    success = rag.scrape_and_process_website(
        [url],
        max_pages=20,
        output_file=f"data/site_{i}.json"
    )

    if success:
        print(f"✅ Processed {url}")
    else:
        print(f"❌ Failed to process {url}")

# Query across all processed websites
result = rag.demo_query("Compare Python web frameworks", top_k=7)
```

### Custom Data Processing Pipeline

```python
rag = RAGSystem(data_dir="custom_data")

# Step 1: Scrape with custom settings
success = rag.scrape_and_process_website(
    start_urls=["https://api-docs.example.com/"],
    max_pages=100,
    max_depth=3,
    output_file="custom_data/api_docs.json"
)

if success:
    print(f"✅ Website scraped and processed successfully")

    # Step 3: Test retrieval quality
    test_queries = [
        "How to authenticate API requests?",
        "Rate limiting policies",
        "Error response codes"
    ]

    for query in test_queries:
        result = rag.demo_query(query, top_k=3)
        best_score = result['chunks'][0]['score'] if result['chunks'] else 0
        print(f"Query: '{query}' - Best score: {best_score:.3f}")
```

### Integration with Custom Models

```python
# Test different models for generation quality
models_to_test = ["mistral", "llama2", "codellama"]
query = "How to implement error handling in APIs?"

for model in models_to_test:
    try:
        print(f"\n--- Testing {model} ---")
        answer = rag.rag_query(query, model=model, temperature=0.5)
        print(f"Answer length: {len(answer)} characters")
        print(f"Answer preview: {answer[:200]}...")
    except Exception as e:
        print(f"Model {model} failed: {e}")
```

## Error Handling

The RAGSystem handles common errors gracefully:

### Network Errors
```python
try:
    success = rag.scrape_and_process_website(["https://unreachable-site.com/"])
    if not success:
        print("Check internet connection and URL accessibility")
except Exception as e:
    print(f"Network error: {e}")
```

### File I/O Errors
```python
try:
    rag.load_data("non_existent_file.json")
except FileNotFoundError:
    print("Data file not found - need to scrape first")
except Exception as e:
    print(f"File error: {e}")
```

### Ollama Connection Errors
```python
try:
    answer = rag.rag_query("test query")
except ConnectionError:
    print("Ollama not running - start with 'ollama serve'")
    # Fall back to retrieval only
    result = rag.demo_query("test query")
```

## Performance Tips

### Optimization Strategies

1. **Enable Caching**: Default behavior, significantly speeds up repeated operations
2. **Batch Processing**: Process multiple sites in the same session
3. **Optimal top_k**: Use 3-7 for best relevance vs. speed balance
4. **Progressive Processing**: Start with small max_pages, increase as needed

### Memory Management

```python
# For large websites, process in chunks
def process_large_site(base_url, total_pages=200):
    rag = RAGSystem()
    chunk_size = 50

    for i in range(0, total_pages, chunk_size):
        success = rag.scrape_and_process_website(
            [base_url],
            max_pages=min(chunk_size, total_pages - i),
            output_file=f"data/chunk_{i}.json"
        )

        if success:
            print(f"Processed chunk {i}-{i+chunk_size}")

        # Data accumulates across calls

    return rag
```

## Integration Examples

### With Web Frameworks

```python
from flask import Flask, jsonify, request

app = Flask(__name__)
rag = RAGSystem()

# Load data once on startup
rag.load_data("data/website_docs.json")

@app.route('/query', methods=['POST'])
def query_endpoint():
    data = request.json
    query = data.get('query', '')
    top_k = data.get('top_k', 3)

    result = rag.demo_query(query, top_k=top_k)
    return jsonify(result)

@app.route('/generate', methods=['POST'])
def generate_endpoint():
    data = request.json
    query = data.get('query', '')
    model = data.get('model', 'mistral')

    try:
        answer = rag.rag_query(query, model=model)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### With Async Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncRAGSystem:
    def __init__(self):
        self.rag = RAGSystem()
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def async_demo_query(self, query: str, top_k: int = 3):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.rag.demo_query,
            query,
            top_k
        )

    async def async_rag_query(self, query: str, model: str = "mistral"):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.rag.rag_query,
            query,
            3,
            model
        )

# Usage
async def main():
    async_rag = AsyncRAGSystem()
    async_rag.rag.load_data("data/website_docs.json")

    # Process multiple queries concurrently
    queries = [
        "How to create functions?",
        "Error handling best practices",
        "API authentication methods"
    ]

    tasks = [async_rag.async_demo_query(q) for q in queries]
    results = await asyncio.gather(*tasks)

    for query, result in zip(queries, results):
        print(f"Query: {query}")
        print(f"Best score: {result['chunks'][0]['score']:.3f}")

asyncio.run(main())
```

---

*For complete usage examples, see the [Getting Started Guide](../guides/getting-started.md) and [Examples Directory](../../examples/).*