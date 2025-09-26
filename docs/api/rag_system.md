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