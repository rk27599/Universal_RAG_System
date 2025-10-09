# Getting Started with Universal RAG System

Welcome to the Universal RAG System! This comprehensive guide will take you from installation to your first successful RAG query in just a few minutes.

## 🎯 What You'll Learn

- How to install and set up the Universal RAG System
- Understanding the core concepts and components
- Creating your first RAG query
- Working with different types of websites
- Using both sync and async scrapers
- Integrating with Ollama for text generation

## 📋 Prerequisites

- **Python 3.10 or higher** installed on your system
- **Basic Python knowledge** (functions, imports, basic syntax)
- **Internet connection** for web scraping
- **Terminal/Command line** basic familiarity

## 🚀 Quick Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG
```

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Test basic functionality
python -c "from src.rag_system import RAGSystem; print('✅ Installation successful!')"
```

## 🏗️ Understanding the System

The Universal RAG System has three main components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Scraper   │───▶│   RAG System     │───▶│  Text Generator │
│                 │    │                  │    │   (Ollama)      │
│ • Sync/Async    │    │ • TF-IDF         │    │ • Local LLMs    │
│ • Structure     │    │ • Semantic       │    │ • Mistral       │
│ • Metadata      │    │ • Caching        │    │ • Llama2        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

1. **Web Scraper**: Extracts content from websites while preserving structure
2. **RAG System**: Processes content and enables intelligent retrieval
3. **Text Generator** (Optional): Uses Ollama for generating complete answers

## 🎯 Your First RAG Query

Let's start with a simple example using FastAPI documentation:

### Step 1: Basic Setup

```python
# Create a new file: first_rag_example.py
from src.rag_system import RAGSystem

# Initialize the system
rag = RAGSystem()
print("✅ RAG System initialized successfully!")
```

### Step 2: Scrape Your First Website

```python
# Add to your file
print("🌐 Starting to scrape FastAPI documentation...")

# Scrape and process FastAPI documentation
success = rag.scrape_and_process_website(
    start_urls=["https://fastapi.tiangolo.com/"],
    max_pages=20  # Start small for testing
)

if success:
    print("✅ Website scraped successfully!")
else:
    print("❌ Scraping failed - check your internet connection")
```

### Step 3: Your First Query

```python
# Add to your file
print("\n🔍 Testing retrieval with a query...")

# Test retrieval (no text generation yet)
result = rag.demo_query("How to create an API endpoint?", top_k=3)
print(result)  # This prints the formatted results
```

### Step 4: Run Your First Example

```bash
# Run your example
python first_rag_example.py
```

**Expected Output:**
```
✅ RAG System initialized successfully!
🌐 Starting to scrape FastAPI documentation...
✅ Website scraped successfully!

🔍 Testing retrieval with a query...
🔍 Query: "How to create an API endpoint?"

📊 Results (showing top 3 of 3 matches):

--- Result 1: Score 0.742 ---
📄 Page: First Steps - FastAPI
🏷️  Type: paragraph
📝 Content: To create an API endpoint in FastAPI, you use the @app.get(), @app.post(), or other HTTP method decorators...
```

## 🚀 Working with Different Websites

The system works with any website automatically. Let's try different types:

### Documentation Sites

```python
from src.rag_system import RAGSystem

rag = RAGSystem()

# Python official documentation
success = rag.scrape_and_process_website(
    start_urls=["https://docs.python.org/3/tutorial/"],
    max_pages=25,
    output_file="data/python_tutorial.json"
)

if success:
    # Query Python-specific questions
    result = rag.demo_query("How to define functions in Python?", top_k=3)
    print(f"Best match score: {result['chunks'][0]['score']:.3f}")
```

### API Documentation

```python
# React documentation
success = rag.scrape_and_process_website(
    start_urls=["https://reactjs.org/docs/"],
    max_pages=30,
    output_file="data/react_docs.json"
)

if success:
    result = rag.demo_query("How to use React hooks?", top_k=5)
    print(f"Found {len(result['chunks'])} relevant chunks about React hooks")
```

### Framework Documentation

```python
# Django documentation
success = rag.scrape_and_process_website(
    start_urls=["https://docs.djangoproject.com/en/stable/"],
    max_pages=40,
    output_file="data/django_docs.json"
)

if success:
    result = rag.demo_query("How to create Django models?", top_k=4)
    for chunk in result['chunks'][:2]:
        print(f"Score: {chunk['score']:.3f} - {chunk['content'][:100]}...")
```

## ⚡ High-Performance Async Scraping

For larger websites, use the async scraper for 3-5x speed improvement:

```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig
from src.rag_system import RAGSystem

async def fast_scraping_example():
    """Example of high-performance async scraping."""

    # Configure for high performance
    config = ScrapingConfig(
        concurrent_limit=6,        # Process 6 pages simultaneously
        max_pages=50,             # More pages
        requests_per_second=8.0,  # Higher rate limit
        timeout=20.0              # Longer timeout for reliability
    )

    print("🚀 Starting high-performance async scraping...")

    async with AsyncWebScraper(config) as scraper:
        # Scrape the website
        results = await scraper.scrape_website_async(
            start_urls=["https://docs.python.org/3/"]
        )

        # Save results to file
        await scraper.save_results_async(results, "data/python_docs_fast.json")

        # Access metrics
        metrics = results["metrics"]
        print(f"✅ Async scraping completed!")
        print(f"⚡ Processed {metrics.urls_processed} pages in {metrics.elapsed_time:.1f} seconds")
        print(f"📊 Speed: {metrics.urls_processed/metrics.elapsed_time:.1f} pages/second")
        print(f"💾 Cache hits: {metrics.cache_hits} ({metrics.cache_hits/metrics.total_requests:.1%})")

        # Load into RAG system for querying
        rag = RAGSystem()
        rag.load_data("data/python_docs_fast.json")

        # Test query
        result = rag.demo_query("Python data structures", top_k=3)
        # Check if result is meaningful (demo_query returns a formatted string)
        if "No documents" not in result and result.strip():
            print(f"🔍 Query executed successfully")
        else:
            print(f"🔍 Query returned no results")

        return rag

# Run async example
rag_system = asyncio.run(fast_scraping_example())
```

## 🤖 Adding Text Generation with Ollama

To generate complete answers (not just retrieval), you need Ollama:

### 1. Install Ollama

Visit [ollama.ai](https://ollama.ai) and install Ollama for your system.

### 2. Setup Ollama

```bash
# Start Ollama server (in a separate terminal)
ollama serve

# Pull a model (in another terminal)
ollama pull mistral
```

### 3. Generate Complete Answers

```python
from src.rag_system import RAGSystem

# Load previously scraped data
rag = RAGSystem()
rag.load_data("data/fastapi_docs.json")  # From previous examples

print("🤖 Generating complete answer with Ollama...")

# Generate full answer with context
answer = rag.rag_query(
    "How do I create a REST API endpoint in FastAPI?",
    top_k=5,           # Use top 5 chunks for context
    model="mistral"    # Use Mistral model
)

print(f"🎯 Generated Answer:")
print(answer)
```

**Example Output:**
```
🤖 Generating complete answer with Ollama...
🎯 Generated Answer:
To create a REST API endpoint in FastAPI, follow these steps:

1. Import FastAPI and create an app instance:
   ```python
   from fastapi import FastAPI
   app = FastAPI()
   ```

2. Define your endpoint using decorators:
   ```python
   @app.get("/")
   async def read_root():
       return {"message": "Hello World"}
   ```

3. For different HTTP methods, use @app.post(), @app.put(), @app.delete()

4. Run your application with: uvicorn main:app --reload

This creates a simple API endpoint that responds to GET requests at the root path.
```

## 🎛️ Customizing Your Setup

### Adjusting Scraping Parameters

```python
# For small websites (blogs, simple docs)
rag.scrape_and_process_website(
    start_urls=["https://example.com/"],
    max_pages=15,      # Fewer pages
    max_depth=1,       # Shallow scraping
    same_domain_only=True
)

# For large documentation sites
rag.scrape_and_process_website(
    start_urls=["https://docs.framework.com/"],
    max_pages=75,      # More pages
    max_depth=3,       # Deeper scraping
    same_domain_only=True
)
```

### Optimizing Query Parameters

```python
# For quick answers
result = rag.demo_query("your question", top_k=3)

# For comprehensive context
result = rag.demo_query("complex question", top_k=7)

# For generation with different models
answer = rag.rag_query("question", top_k=5, model="llama2")
answer = rag.rag_query("question", top_k=5, model="mistral", temperature=0.3)
```

## 🔍 Understanding Query Results

When you run `demo_query()`, you get formatted text output:

```python
result = rag.demo_query("How to create functions?", top_k=3)

# demo_query() returns a formatted string with results
# Example output:
# ✅ Found 3 relevant chunks:
#
# 📄 Result 1: Python Functions Tutorial - Function Definition
#    Domain: docs.python.org
#    Type: paragraph
#    Relevance: 0.756 (base: 0.680)
#    Words: 342
#    Preview: To define a function in Python...
#
# (Additional results follow...)

print(result)  # Prints the formatted output
```

**Note:** `demo_query()` is designed for quick testing and prints formatted results. For programmatic access to structured data, use `retrieve_context()` method instead:

```python
# For structured data access:
contexts, metadata = rag.retrieve_context("How to create functions?", top_k=3)

# Access individual results
for i, (context, meta) in enumerate(zip(contexts, metadata)):
    score = meta.get('boosted_score', 0)
    page_title = meta.get('page_title', 'Unknown')
    print(f"Result {i+1}: {page_title} (score: {score:.3f})")
    print(f"Content: {context[:200]}...")
```

### Interpreting Similarity Scores

- **0.7+**: Excellent match, highly relevant
- **0.5-0.7**: Good match, relevant content
- **0.3-0.5**: Moderate match, may be useful
- **Below 0.3**: Low relevance, consider rephrasing query

## 🛠️ Interactive Exploration

Use the Jupyter notebook for interactive experimentation:

```bash
# Start Jupyter
jupyter lab notebooks/RAG_HTML.ipynb
```

The notebook provides an interactive interface to:
- Test different websites
- Experiment with query parameters
- Visualize similarity scores
- Compare different approaches

## 📊 Monitoring Performance

Keep track of your system's performance:

```python
import time

def benchmark_query_performance():
    rag = RAGSystem()
    rag.load_data("data/website_docs.json")

    queries = [
        "How to create functions?",
        "Error handling best practices",
        "API authentication methods"
    ]

    for query in queries:
        start_time = time.time()
        result = rag.demo_query(query, top_k=3)
        elapsed = time.time() - start_time

        best_score = result['chunks'][0]['score'] if result['chunks'] else 0
        print(f"Query: '{query}'")
        print(f"  Time: {elapsed:.3f}s, Best Score: {best_score:.3f}")

benchmark_query_performance()
```

## 🚨 Common Beginner Mistakes

### 1. Starting Too Big
```python
# ❌ Don't start with huge websites
rag.scrape_and_process_website([url], max_pages=500)  # Too many!

# ✅ Start small and scale up
rag.scrape_and_process_website([url], max_pages=20)   # Perfect for testing
```

### 2. Ignoring Similarity Scores
```python
# ❌ Using results without checking quality
result = rag.demo_query("question")
answer = result['chunks'][0]['content']  # Might be irrelevant!

# ✅ Check scores first
result = rag.demo_query("question")
if result['chunks'] and result['chunks'][0]['score'] > 0.5:
    answer = result['chunks'][0]['content']
else:
    print("Low quality results - try rephrasing your query")
```

### 3. Not Using Appropriate top_k
```python
# ❌ Always using default
result = rag.demo_query("complex question")  # Only gets top 3

# ✅ Adjust based on question complexity
simple_result = rag.demo_query("simple question", top_k=3)
complex_result = rag.demo_query("complex question", top_k=7)
```

## 🎯 Next Steps

Now that you've mastered the basics, explore these advanced topics:

### Immediate Next Steps
1. **Try different websites** - Test with your favorite documentation sites
2. **Experiment with parameters** - Find optimal settings for your use cases
3. **Set up Ollama** - Enable full text generation capabilities

### Advanced Learning
1. **[Performance Guide](./performance.md)** - Optimize for speed and accuracy
2. **[API Documentation](../api/README.md)** - Deep dive into all available methods
3. **[Architecture Guide](../architecture.md)** - Understand how everything works

### Real-World Applications
1. **Documentation Q&A bot** - Build a chatbot for your documentation
2. **Learning assistant** - Create personalized learning from any website
3. **Research tool** - Extract insights from multiple sources

## 💡 Getting Help

If you encounter issues:

1. **Check similarity scores** - Low scores indicate query or data issues
2. **Review logs** - Enable debug logging for detailed information
3. **Start small** - Test with single pages before full websites
4. **Check examples** - Look at working examples in the `/examples` directory
5. **Read troubleshooting** - See [Troubleshooting Guide](./troubleshooting.md)

## 📝 Quick Reference

### Essential Commands

```python
# Initialize system
rag = RAGSystem()

# Scrape website
success = rag.scrape_and_process_website([url], max_pages=20)

# Query (retrieval only)
result = rag.demo_query("question", top_k=3)

# Generate answer (requires Ollama)
answer = rag.rag_query("question", model="mistral")

# Load existing data
rag.load_data("data/docs.json")
```

### Key Parameters

- `max_pages`: Number of pages to scrape (start with 10-30)
- `top_k`: Number of results to retrieve (3-7 recommended)
- `max_depth`: How deep to crawl (1-3 recommended)
- `temperature`: Generation randomness (0.1-1.0, lower = more focused)

Congratulations! 🎉 You're now ready to use the Universal RAG System effectively. Start experimenting with different websites and queries to discover its full potential!

---

*Next: Try the [Performance Guide](./performance.md) to optimize your setup for maximum speed and accuracy.*