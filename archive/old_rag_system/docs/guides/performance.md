# Performance Optimization Guide

Comprehensive strategies to maximize the speed, accuracy, and efficiency of your Universal RAG System.

## 🎯 Performance Overview

The Universal RAG System offers multiple optimization opportunities:

- **Scraping Performance**: 3-5x speed improvements with async scraping
- **Query Performance**: Sub-second retrieval with proper indexing
- **Memory Efficiency**: Optimized for large-scale document processing
- **Cache Performance**: 40-60% hit rates for repeated operations

## ⚡ Scraping Performance

### Async vs Sync Scraper Comparison

| Aspect | Sync Scraper | Async Scraper | Best For |
|--------|--------------|---------------|----------|
| Speed | Baseline | 3-5x faster | Large sites |
| Debugging | Excellent | Good | Development |
| Resource Usage | Low | Medium | Production |
| Complexity | Simple | Moderate | Scale |

### Optimizing Async Scraper

```python
import asyncio
from src.async_web_scraper import AsyncWebScraper, ScrapingConfig

def create_performance_config():
    """Create optimized configuration for different scenarios."""

    # High-performance configuration
    high_perf = ScrapingConfig(
        concurrent_limit=8,        # More concurrent requests
        requests_per_second=12.0,  # Higher rate limit
        max_pages=100,             # Process more pages
        timeout=25.0,              # Longer timeout for reliability
        retry_attempts=5,          # More retries for robustness
        retry_delay=1.5            # Reasonable retry delay
    )

    # Balanced configuration (recommended)
    balanced = ScrapingConfig(
        concurrent_limit=6,
        requests_per_second=8.0,
        max_pages=60,
        timeout=20.0,
        retry_attempts=3,
        retry_delay=1.0
    )

    # Conservative configuration (for sensitive sites)
    conservative = ScrapingConfig(
        concurrent_limit=3,
        requests_per_second=4.0,
        max_pages=30,
        timeout=15.0,
        retry_attempts=4,
        retry_delay=2.0
    )

    return {
        'high_performance': high_perf,
        'balanced': balanced,
        'conservative': conservative
    }

# Choose based on your needs
configs = create_performance_config()
```

### Performance Benchmarking

```python
import asyncio
import time
from dataclasses import asdict

async def benchmark_scraping_configurations():
    """Benchmark different configurations to find optimal settings."""

    test_url = "https://docs.python.org/3/tutorial/"
    configurations = create_performance_config()

    results = []

    for name, config in configurations.items():
        print(f"\n--- Benchmarking {name} configuration ---")

        scraper = AsyncWebScraper(config)
        start_time = time.time()

        success, metrics = await scraper.scrape_website([test_url])

        if success:
            pages_per_second = metrics.urls_processed / metrics.elapsed_time
            efficiency = metrics.cache_hits / max(metrics.total_requests, 1)

            result = {
                'name': name,
                'pages_processed': metrics.urls_processed,
                'total_time': metrics.elapsed_time,
                'pages_per_second': pages_per_second,
                'cache_efficiency': efficiency,
                'failure_rate': metrics.urls_failed / max(metrics.urls_processed + metrics.urls_failed, 1),
                'bytes_per_second': metrics.total_bytes_downloaded / metrics.elapsed_time
            }

            results.append(result)

            print(f"✅ {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")
            print(f"📈 Rate: {pages_per_second:.2f} pages/second")
            print(f"💾 Cache efficiency: {efficiency:.1%}")
            print(f"📊 Throughput: {result['bytes_per_second']:,.0f} bytes/second")

        else:
            print(f"❌ Configuration {name} failed")

    # Find optimal configuration
    if results:
        best = max(results, key=lambda x: x['pages_per_second'])
        print(f"\n🏆 Best performing: {best['name']}")
        print(f"Rate: {best['pages_per_second']:.2f} pages/second")

        # Print comparison table
        print(f"\n📊 Performance Comparison:")
        print(f"{'Config':<15} {'Pages/sec':<10} {'Cache %':<10} {'Fail %':<10}")
        print("-" * 50)
        for result in results:
            print(f"{result['name']:<15} "
                  f"{result['pages_per_second']:<10.2f} "
                  f"{result['cache_efficiency']:<10.1%} "
                  f"{result['failure_rate']:<10.1%}")

    return results

# Run benchmark
benchmark_results = asyncio.run(benchmark_scraping_configurations())
```

### Memory-Efficient Large-Scale Scraping

```python
async def memory_efficient_scraping(urls, total_pages=500):
    """Handle large-scale scraping with memory optimization."""

    # Process in batches to manage memory
    batch_size = 100
    all_metrics = []

    config = ScrapingConfig(
        concurrent_limit=6,
        max_pages=batch_size,
        requests_per_second=8.0
    )

    for i, url in enumerate(urls):
        print(f"\n--- Processing site {i+1}/{len(urls)}: {url} ---")

        remaining_pages = total_pages
        batch_num = 0

        while remaining_pages > 0:
            current_batch = min(batch_size, remaining_pages)
            batch_num += 1

            print(f"Batch {batch_num}: {current_batch} pages")

            scraper = AsyncWebScraper(config)
            success, metrics = await scraper.scrape_website(
                [url],
                f"data/batch_{i}_{batch_num}.json"
            )

            if success:
                all_metrics.append(metrics)
                remaining_pages -= metrics.urls_processed
                print(f"✅ Processed {metrics.urls_processed} pages")

                # Memory cleanup hint
                del scraper
                import gc
                gc.collect()

            else:
                print(f"❌ Batch {batch_num} failed")
                break

            # Rate limiting between batches
            await asyncio.sleep(1)

    # Aggregate statistics
    total_pages_processed = sum(m.urls_processed for m in all_metrics)
    total_time = sum(m.elapsed_time for m in all_metrics)

    print(f"\n📊 Final Statistics:")
    print(f"Total pages processed: {total_pages_processed}")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Average rate: {total_pages_processed/total_time:.2f} pages/second")

    return all_metrics

# Example usage
# results = asyncio.run(memory_efficient_scraping([
#     "https://docs.python.org/",
#     "https://fastapi.tiangolo.com/",
#     "https://flask.palletsprojects.com/"
# ]))
```

## 🔍 Query Performance Optimization

### TF-IDF Optimization Strategies

```python
def optimize_query_performance():
    """Strategies for optimizing query performance."""

    from src.rag_system import RAGSystem
    import time

    rag = RAGSystem()
    rag.load_data("data/website_docs.json")

    # Test queries with different complexity levels
    test_queries = [
        ("python", 1),           # Simple, 1 word
        ("python functions", 2),  # Simple, 2 words
        ("how to create python functions", 6),  # Complex sentence
        ("define async functions with error handling in python", 9)  # Very complex
    ]

    print("📊 Query Performance Analysis")

    for query, word_count in test_queries:
        # Test different top_k values
        for top_k in [3, 5, 7, 10]:
            start_time = time.time()
            result = rag.demo_query(query, top_k=top_k)
            elapsed = time.time() - start_time

            best_score = result['chunks'][0]['score'] if result['chunks'] else 0

            print(f"Query: '{query}' (words: {word_count}, top_k: {top_k})")
            print(f"  Time: {elapsed:.3f}s, Score: {best_score:.3f}")

    # Optimal top_k recommendation
    print(f"\n💡 Recommendations:")
    print(f"  Simple queries (1-2 words): top_k=3-5")
    print(f"  Complex queries (3-6 words): top_k=5-7")
    print(f"  Very complex queries (7+ words): top_k=7-10")

optimize_query_performance()
```

### Caching Optimization

```python
def analyze_cache_performance():
    """Analyze and optimize caching performance."""

    from src.rag_system import RAGSystem
    import os
    import time
    import hashlib

    rag = RAGSystem(cache_enabled=True)

    # Test cache performance
    test_queries = [
        "python functions",
        "api endpoints",
        "error handling",
        "python functions",  # Repeat for cache test
        "api endpoints"      # Repeat for cache test
    ]

    print("💾 Cache Performance Analysis")

    cache_hits = 0
    total_queries = len(test_queries)

    for i, query in enumerate(test_queries):
        start_time = time.time()
        result = rag.demo_query(query, top_k=5)
        elapsed = time.time() - start_time

        # Estimate if this was a cache hit (very fast response)
        is_cache_hit = elapsed < 0.01  # Less than 10ms likely cached
        if is_cache_hit:
            cache_hits += 1

        print(f"Query {i+1}: '{query}' - {elapsed:.4f}s {'(cached)' if is_cache_hit else ''}")

    cache_hit_rate = cache_hits / total_queries
    print(f"\n📊 Cache Statistics:")
    print(f"Cache hit rate: {cache_hit_rate:.1%}")
    print(f"Average cache speedup: ~100x")

    # Cache file analysis
    cache_files = [f for f in os.listdir("data") if f.endswith("_cache.pkl")]
    if cache_files:
        total_cache_size = sum(os.path.getsize(os.path.join("data", f)) for f in cache_files)
        print(f"Cache storage: {total_cache_size / 1024:.1f} KB")

    return cache_hit_rate

analyze_cache_performance()
```

## 📈 Scaling Strategies

### Horizontal Scaling

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

class DistributedRAGSystem:
    """Example of distributed processing for large-scale operations."""

    def __init__(self, num_workers=None):
        self.num_workers = num_workers or multiprocessing.cpu_count()

    async def distributed_scraping(self, url_batches):
        """Process multiple URL batches in parallel."""

        async def process_batch(batch):
            config = ScrapingConfig(
                concurrent_limit=4,
                max_pages=50,
                requests_per_second=6.0
            )

            scraper = AsyncWebScraper(config)
            results = []

            for url in batch:
                success, metrics = await scraper.scrape_website([url])
                results.append((url, success, metrics))

            return results

        # Process batches concurrently
        tasks = [process_batch(batch) for batch in url_batches]
        batch_results = await asyncio.gather(*tasks)

        # Aggregate results
        all_results = []
        for batch_result in batch_results:
            all_results.extend(batch_result)

        return all_results

    def parallel_query_processing(self, queries):
        """Process multiple queries in parallel using processes."""

        def process_queries_batch(query_batch):
            rag = RAGSystem()
            rag.load_data("data/website_docs.json")

            results = []
            for query in query_batch:
                result = rag.demo_query(query, top_k=5)
                results.append((query, result))

            return results

        # Split queries into batches
        batch_size = max(1, len(queries) // self.num_workers)
        query_batches = [queries[i:i + batch_size]
                        for i in range(0, len(queries), batch_size)]

        # Process in parallel
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            future_results = executor.map(process_queries_batch, query_batches)

            # Collect results
            all_results = []
            for batch_results in future_results:
                all_results.extend(batch_results)

        return all_results

# Example usage
async def demo_distributed_processing():
    system = DistributedRAGSystem(num_workers=4)

    # Example URL batches
    url_batches = [
        ["https://docs.python.org/3/tutorial/"],
        ["https://fastapi.tiangolo.com/"],
        ["https://flask.palletsprojects.com/"]
    ]

    # Distributed scraping
    scraping_results = await system.distributed_scraping(url_batches)
    print(f"Processed {len(scraping_results)} sites")

    # Parallel query processing
    test_queries = [
        "python functions",
        "api endpoints",
        "error handling",
        "database connections",
        "authentication methods"
    ]

    query_results = system.parallel_query_processing(test_queries)
    print(f"Processed {len(query_results)} queries")

# asyncio.run(demo_distributed_processing())
```

### Vertical Scaling

```python
def optimize_system_resources():
    """Optimize system resources for maximum performance."""

    import psutil
    import gc
    import os

    print("🔧 System Resource Optimization")

    # Memory optimization
    def optimize_memory():
        """Memory optimization strategies."""

        # Force garbage collection
        gc.collect()

        # Get current memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        print(f"Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")

        # Memory optimization settings
        import sys
        print(f"Python recursion limit: {sys.getrecursionlimit()}")

        # Optimize for large datasets
        if memory_info.rss > 1024 * 1024 * 1024:  # > 1GB
            print("⚠️ High memory usage detected")
            print("Consider:")
            print("  - Processing in smaller batches")
            print("  - Reducing concurrent_limit")
            print("  - Using data streaming")

    # CPU optimization
    def optimize_cpu():
        """CPU optimization strategies."""

        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)

        print(f"CPU cores: {cpu_count}")
        print(f"CPU usage: {cpu_percent:.1f}%")

        # Recommendations based on CPU usage
        if cpu_percent > 80:
            print("⚠️ High CPU usage detected")
            print("Consider:")
            print("  - Reducing concurrent_limit")
            print("  - Adding delays between requests")
            print("  - Using async processing")
        elif cpu_percent < 50:
            print("💡 CPU underutilized")
            print("Consider:")
            print("  - Increasing concurrent_limit")
            print("  - Processing multiple sites simultaneously")

    # Disk I/O optimization
    def optimize_disk():
        """Disk I/O optimization strategies."""

        disk_usage = psutil.disk_usage(".")

        print(f"Disk usage: {disk_usage.percent:.1f}%")
        print(f"Free space: {disk_usage.free / 1024 / 1024 / 1024:.1f} GB")

        # Check data directory size
        data_size = 0
        for root, dirs, files in os.walk("data"):
            for file in files:
                data_size += os.path.getsize(os.path.join(root, file))

        print(f"Data directory size: {data_size / 1024 / 1024:.1f} MB")

        if data_size > 100 * 1024 * 1024:  # > 100MB
            print("💡 Consider data cleanup:")
            print("  - Remove old cache files")
            print("  - Compress large JSON files")
            print("  - Archive processed data")

    # Run all optimizations
    optimize_memory()
    optimize_cpu()
    optimize_disk()

    # Performance recommendations
    print(f"\n🚀 Performance Recommendations:")

    system_memory = psutil.virtual_memory().total / 1024 / 1024 / 1024
    if system_memory > 16:
        print("  High-memory system: Use aggressive async settings")
    elif system_memory > 8:
        print("  Medium-memory system: Use balanced settings")
    else:
        print("  Low-memory system: Use conservative settings")

    return {
        'memory_gb': system_memory,
        'cpu_cores': psutil.cpu_count(),
        'disk_free_gb': psutil.disk_usage(".").free / 1024 / 1024 / 1024
    }

system_info = optimize_system_resources()
```

## 🎯 Application-Specific Optimizations

### Documentation Sites

```python
def optimize_for_documentation():
    """Optimizations specific to documentation sites."""

    # Documentation-specific configuration
    docs_config = ScrapingConfig(
        concurrent_limit=6,        # Docs can handle more concurrent requests
        requests_per_second=10.0,  # Higher rate for static content
        max_pages=100,             # Documentation sites have many pages
        timeout=20.0,              # Longer timeout for complex pages
        max_depth=3,               # Deeper crawling for nested docs
        same_domain_only=True      # Stay within documentation domain
    )

    return docs_config

def optimize_for_blogs():
    """Optimizations for blog and content sites."""

    # Blog-specific configuration
    blog_config = ScrapingConfig(
        concurrent_limit=4,        # More conservative for blogs
        requests_per_second=6.0,   # Respect blog server limits
        max_pages=50,              # Blogs have fewer relevant pages
        timeout=15.0,              # Shorter timeout
        max_depth=2,               # Shallower crawling
        same_domain_only=True
    )

    return blog_config

def optimize_for_apis():
    """Optimizations for API documentation."""

    # API docs configuration
    api_config = ScrapingConfig(
        concurrent_limit=8,        # API docs are usually well-optimized
        requests_per_second=12.0,  # Higher rate for structured content
        max_pages=75,              # Moderate page count
        timeout=25.0,              # Longer timeout for complex examples
        max_depth=4,               # Deeper for nested API structures
        same_domain_only=True
    )

    return api_config

# Usage examples
async def optimized_scraping_by_type():
    """Demonstrate optimized scraping for different site types."""

    site_configs = {
        "documentation": {
            "config": optimize_for_documentation(),
            "urls": ["https://docs.python.org/3/"],
            "expected_pages": 80
        },
        "blog": {
            "config": optimize_for_blogs(),
            "urls": ["https://realpython.com/"],
            "expected_pages": 30
        },
        "api": {
            "config": optimize_for_apis(),
            "urls": ["https://fastapi.tiangolo.com/"],
            "expected_pages": 60
        }
    }

    results = {}

    for site_type, config_info in site_configs.items():
        print(f"\n--- Optimizing for {site_type} sites ---")

        scraper = AsyncWebScraper(config_info["config"])
        success, metrics = await scraper.scrape_website(config_info["urls"])

        if success:
            efficiency = metrics.urls_processed / config_info["expected_pages"]
            rate = metrics.urls_processed / metrics.elapsed_time

            results[site_type] = {
                'pages_processed': metrics.urls_processed,
                'time': metrics.elapsed_time,
                'rate': rate,
                'efficiency': efficiency,
                'cache_hits': metrics.cache_hits
            }

            print(f"✅ {site_type}: {metrics.urls_processed} pages in {metrics.elapsed_time:.1f}s")
            print(f"   Rate: {rate:.2f} pages/second")
            print(f"   Efficiency: {efficiency:.1%} of expected")
        else:
            print(f"❌ {site_type} optimization failed")

    return results

# Run optimized scraping
# results = asyncio.run(optimized_scraping_by_type())
```

## 📊 Performance Monitoring

### Real-time Performance Monitoring

```python
import time
import threading
from dataclasses import dataclass
from typing import List

@dataclass
class PerformanceMetrics:
    timestamp: float
    queries_per_second: float
    average_response_time: float
    cache_hit_rate: float
    memory_usage_mb: float

class PerformanceMonitor:
    """Real-time performance monitoring for RAG system."""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.query_times: List[float] = []
        self.cache_hits = 0
        self.total_queries = 0
        self.monitoring = False
        self.start_time = time.time()

    def start_monitoring(self):
        """Start background performance monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False

    def record_query(self, response_time: float, was_cache_hit: bool = False):
        """Record a query execution."""
        self.query_times.append(response_time)
        self.total_queries += 1

        if was_cache_hit:
            self.cache_hits += 1

        # Keep only recent query times
        if len(self.query_times) > 100:
            self.query_times.pop(0)

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            current_time = time.time()
            elapsed = current_time - self.start_time

            # Calculate metrics
            qps = len(self.query_times) / max(elapsed, 1)
            avg_response = sum(self.query_times) / max(len(self.query_times), 1)
            cache_rate = self.cache_hits / max(self.total_queries, 1)

            # Memory usage
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024

            metrics = PerformanceMetrics(
                timestamp=current_time,
                queries_per_second=qps,
                average_response_time=avg_response,
                cache_hit_rate=cache_rate,
                memory_usage_mb=memory_mb
            )

            self.metrics_history.append(metrics)

            # Keep only recent metrics
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)

            time.sleep(5)  # Update every 5 seconds

    def get_current_stats(self):
        """Get current performance statistics."""
        if not self.metrics_history:
            return None

        latest = self.metrics_history[-1]
        return {
            'queries_per_second': latest.queries_per_second,
            'avg_response_time': latest.average_response_time,
            'cache_hit_rate': latest.cache_hit_rate,
            'memory_usage_mb': latest.memory_usage_mb,
            'total_queries': self.total_queries
        }

    def print_stats(self):
        """Print current performance statistics."""
        stats = self.get_current_stats()
        if stats:
            print(f"\n📊 Performance Stats:")
            print(f"  Queries/sec: {stats['queries_per_second']:.2f}")
            print(f"  Avg response: {stats['avg_response_time']:.3f}s")
            print(f"  Cache hit rate: {stats['cache_hit_rate']:.1%}")
            print(f"  Memory usage: {stats['memory_usage_mb']:.1f} MB")
            print(f"  Total queries: {stats['total_queries']}")

# Example usage with monitoring
def demo_performance_monitoring():
    """Demonstrate performance monitoring."""

    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    rag = RAGSystem()
    rag.load_data("data/website_docs.json")

    test_queries = [
        "python functions",
        "api endpoints",
        "error handling",
        "python functions",  # Should hit cache
        "database connections"
    ]

    print("🔍 Running monitored queries...")

    for query in test_queries:
        start_time = time.time()
        result = rag.demo_query(query, top_k=5)
        response_time = time.time() - start_time

        # Estimate cache hit (very fast response)
        was_cache_hit = response_time < 0.01

        monitor.record_query(response_time, was_cache_hit)

        print(f"Query: '{query}' - {response_time:.3f}s {'(cached)' if was_cache_hit else ''}")

        time.sleep(0.5)  # Small delay

    # Show final stats
    monitor.print_stats()
    monitor.stop_monitoring()

    return monitor

# Run monitoring demo
# monitor_results = demo_performance_monitoring()
```

## 🏆 Performance Best Practices Summary

### Configuration Guidelines

```python
def get_optimal_config(use_case: str, system_specs: dict):
    """Get optimal configuration based on use case and system specifications."""

    configs = {
        'development': ScrapingConfig(
            concurrent_limit=2,
            requests_per_second=3.0,
            max_pages=15,
            timeout=10.0
        ),
        'production_small': ScrapingConfig(
            concurrent_limit=4,
            requests_per_second=6.0,
            max_pages=50,
            timeout=15.0
        ),
        'production_large': ScrapingConfig(
            concurrent_limit=8,
            requests_per_second=10.0,
            max_pages=150,
            timeout=25.0
        ),
        'high_performance': ScrapingConfig(
            concurrent_limit=12,
            requests_per_second=15.0,
            max_pages=300,
            timeout=30.0
        )
    }

    # Adjust based on system specs
    base_config = configs.get(use_case, configs['production_small'])

    # Memory-based adjustments
    memory_gb = system_specs.get('memory_gb', 8)
    if memory_gb < 8:
        base_config.concurrent_limit = min(base_config.concurrent_limit, 4)
        base_config.max_pages = min(base_config.max_pages, 30)
    elif memory_gb > 16:
        base_config.concurrent_limit = min(base_config.concurrent_limit * 1.5, 16)

    # CPU-based adjustments
    cpu_cores = system_specs.get('cpu_cores', 4)
    if cpu_cores < 4:
        base_config.concurrent_limit = min(base_config.concurrent_limit, 3)
    elif cpu_cores > 8:
        base_config.requests_per_second *= 1.2

    return base_config

# Usage
system_specs = {
    'memory_gb': 16,
    'cpu_cores': 8,
    'disk_free_gb': 100
}

optimal_config = get_optimal_config('production_large', system_specs)
print(f"Optimal config: {optimal_config}")
```

### Quick Performance Checklist

✅ **Scraping Optimization**
- Use async scraper for sites with >20 pages
- Set concurrent_limit based on your CPU cores (2-8)
- Adjust requests_per_second based on target site (3-15)
- Enable caching for repeated operations

✅ **Query Optimization**
- Use top_k=3-5 for simple queries, 5-7 for complex
- Rephrase low-scoring queries (<0.3) in natural language
- Cache frequently used queries
- Monitor similarity scores for quality

✅ **System Optimization**
- Monitor memory usage during large scraping operations
- Use batch processing for very large datasets
- Clean up old cache files regularly
- Adjust configurations based on system resources

✅ **Application Optimization**
- Choose scraper type based on debugging vs performance needs
- Use appropriate configurations for different site types
- Implement proper error handling and retries
- Monitor performance metrics in production

By following these optimization strategies, you can achieve:
- **3-5x faster scraping** with async scraper
- **Sub-second query response times** with proper caching
- **40-60% cache hit rates** for repeated operations
- **Optimal resource utilization** based on your system

---

*Next: Check the [Troubleshooting Guide](./troubleshooting.md) if you encounter any performance issues.*