# RAG System API

The `RAGSystem` class provides the main interface for the Universal RAG System.

## Class: RAGSystem

High-level interface for website scraping, document processing, and retrieval-augmented generation.

### Constructor

```python
RAGSystem(data_dir: str = "data", cache_enabled: bool = True)
```

**Parameters:**
- `data_dir` (str, optional): Directory to store data files. Defaults to "data".
- `cache_enabled` (bool, optional): Enable intelligent caching. Defaults to True.

### Methods

#### scrape_and_process_website()

```python
scrape_and_process_website(
    start_urls: List[str],
    max_pages: int = 30,
    max_depth: int = 2,
    same_domain_only: bool = True,
    output_file: Optional[str] = None
) -> bool
```

Scrape and process a website for RAG queries.

**Parameters:**
- `start_urls` (List[str]): List of URLs to start scraping from
- `max_pages` (int, optional): Maximum number of pages to scrape. Defaults to 30.
- `max_depth` (int, optional): Maximum crawling depth. Defaults to 2.
- `same_domain_only` (bool, optional): Stay within the starting domain. Defaults to True.
- `output_file` (str, optional): Custom output file path. Auto-generated if None.

**Returns:**
- `bool`: True if scraping was successful, False otherwise

**Example:**
```python
rag = RAGSystem()
success = rag.scrape_and_process_website(
    start_urls=["https://docs.python.org/3/"],
    max_pages=20,
    max_depth=2
)
```

#### demo_query()

```python
demo_query(query: str, top_k: int = 3) -> Dict[str, Any]
```

Perform a retrieval-only query (no text generation).

**Parameters:**
- `query` (str): The query string
- `top_k` (int, optional): Number of top results to return. Defaults to 3.

**Returns:**
- `Dict[str, Any]`: Dictionary containing query results with metadata

**Example:**
```python
result = rag.demo_query("How to define functions in Python?", top_k=5)
print(f"Found {len(result['chunks'])} relevant chunks")
for chunk in result['chunks']:
    print(f"Score: {chunk['score']:.3f}")
    print(f"Content: {chunk['content'][:200]}...")
```

#### rag_query()

```python
rag_query(
    query: str,
    top_k: int = 3,
    model: str = "mistral",
    temperature: float = 0.7
) -> str
```

Perform full RAG query with text generation using Ollama.

**Parameters:**
- `query` (str): The query string
- `top_k` (int, optional): Number of context chunks to use. Defaults to 3.
- `model` (str, optional): Ollama model to use. Defaults to "mistral".
- `temperature` (float, optional): Generation temperature. Defaults to 0.7.

**Returns:**
- `str`: Generated answer based on retrieved context

**Requirements:**
- Ollama must be running (`ollama serve`)
- Specified model must be available (`ollama pull mistral`)

**Example:**
```python
# Start Ollama first: ollama serve
answer = rag.rag_query(
    "How to define functions in Python?",
    top_k=5,
    model="mistral"
)
print(answer)
```

#### load_data()

```python
load_data(file_path: str) -> bool
```

Load preprocessed data from a file.

**Parameters:**
- `file_path` (str): Path to the data file (JSON or TXT format)

**Returns:**
- `bool`: True if data was loaded successfully

#### get_stats()

```python
get_stats() -> Dict[str, Any]
```

Get statistics about the loaded data.

**Returns:**
- `Dict[str, Any]`: Dictionary containing data statistics

## Error Handling

The RAGSystem handles common errors gracefully:

- **Network errors**: Retries with exponential backoff
- **Parsing errors**: Skips problematic pages and continues
- **File I/O errors**: Creates directories as needed
- **Ollama connection errors**: Returns error message instead of crashing

## Performance Tips

1. **Caching**: Enable caching (default) for faster subsequent runs
2. **Batch processing**: Process multiple websites in the same session
3. **Optimal top_k**: Use 3-7 for best relevance vs. speed balance
4. **Memory usage**: Large websites may require chunked processing

## Example Workflows

### Basic Website Processing
```python
from src.rag_system import RAGSystem

rag = RAGSystem()

# Scrape documentation
success = rag.scrape_and_process_website([
    "https://fastapi.tiangolo.com/"
], max_pages=25)

if success:
    # Test retrieval
    result = rag.demo_query("How to create an API endpoint?")

    # Generate full answer
    answer = rag.rag_query("How to create an API endpoint?")
    print(answer)
```

### Multi-Website Processing
```python
websites = [
    "https://docs.python.org/3/",
    "https://fastapi.tiangolo.com/",
    "https://flask.palletsprojects.com/"
]

for url in websites:
    rag.scrape_and_process_website([url], max_pages=15)

# Query across all websites
answer = rag.rag_query("Compare Flask and FastAPI")
```