#!/usr/bin/env python3
"""
Example demonstrating async local file processing capabilities
Shows how to use the new async extract_from_local_file() functionality for high-performance local HTML processing
"""

import os
import sys
import asyncio
import tempfile
import time
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.async_web_scraper import AsyncWebScraper, ScrapingConfig, process_local_files_fast
from src.rag_system import RAGSystem


def create_sample_documentation_files():
    """Create sample HTML documentation files for demonstration"""

    # Sample documentation content
    html_docs = {
        "getting_started.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Getting Started - MyFramework Documentation</title>
</head>
<body>
    <main>
        <h1>Getting Started with MyFramework</h1>
        <p>Welcome to MyFramework, a powerful web development framework that simplifies building modern applications.</p>

        <h2>Installation</h2>
        <p>You can install MyFramework using your preferred package manager.</p>

        <h3>Using npm</h3>
        <pre>npm install myframework</pre>

        <h3>Using yarn</h3>
        <pre>yarn add myframework</pre>

        <h2>Quick Start</h2>
        <p>Create your first application in just a few steps:</p>

        <ol>
            <li>Initialize a new project</li>
            <li>Configure your application settings</li>
            <li>Create your first route</li>
            <li>Start the development server</li>
        </ol>

        <h3>Example Code</h3>
        <pre>
import { MyFramework } from 'myframework';

const app = new MyFramework();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000);
        </pre>
    </main>
</body>
</html>
""",

        "api_reference.html": """
<!DOCTYPE html>
<html>
<head>
    <title>API Reference - MyFramework Documentation</title>
</head>
<body>
    <main>
        <h1>API Reference</h1>
        <p>Complete reference for all MyFramework APIs and methods.</p>

        <h2>Core Classes</h2>

        <h3>MyFramework</h3>
        <p>The main framework class that handles application setup and routing.</p>

        <h4>Constructor</h4>
        <pre>new MyFramework(options?: FrameworkOptions)</pre>

        <h4>Methods</h4>

        <h5>get(path, handler)</h5>
        <p>Defines a GET route for the specified path.</p>
        <ul>
            <li><strong>path</strong>: String - The URL path to match</li>
            <li><strong>handler</strong>: Function - The request handler function</li>
        </ul>

        <h5>post(path, handler)</h5>
        <p>Defines a POST route for the specified path.</p>

        <h5>listen(port)</h5>
        <p>Starts the application server on the specified port.</p>

        <h2>Request Object</h2>
        <p>The request object contains information about the HTTP request.</p>

        <h3>Properties</h3>
        <ul>
            <li><strong>params</strong>: Object - Route parameters</li>
            <li><strong>query</strong>: Object - Query string parameters</li>
            <li><strong>body</strong>: Object - Request body data</li>
            <li><strong>headers</strong>: Object - Request headers</li>
        </ul>

        <h2>Response Object</h2>
        <p>The response object is used to send data back to the client.</p>

        <h3>Methods</h3>
        <ul>
            <li><strong>send(data)</strong>: Send a response with data</li>
            <li><strong>json(object)</strong>: Send a JSON response</li>
            <li><strong>status(code)</strong>: Set the response status code</li>
        </ul>
    </main>
</body>
</html>
""",

        "advanced_usage.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Usage - MyFramework Documentation</title>
</head>
<body>
    <main>
        <h1>Advanced Usage</h1>
        <p>Advanced patterns and techniques for building sophisticated applications with MyFramework.</p>

        <h2>Middleware</h2>
        <p>Middleware functions are functions that have access to the request and response objects.</p>

        <h3>Creating Custom Middleware</h3>
        <p>You can create custom middleware to handle cross-cutting concerns like authentication, logging, and error handling.</p>

        <pre>
function authMiddleware(req, res, next) {
    if (!req.headers.authorization) {
        return res.status(401).send('Unauthorized');
    }
    next();
}

app.use(authMiddleware);
        </pre>

        <h2>Database Integration</h2>
        <p>MyFramework integrates seamlessly with various database systems.</p>

        <h3>SQL Databases</h3>
        <p>Connect to SQL databases using the built-in ORM:</p>

        <pre>
const db = new Database({
    host: 'localhost',
    database: 'myapp',
    username: 'user',
    password: 'password'
});
        </pre>

        <h3>NoSQL Databases</h3>
        <p>NoSQL database support is provided through plugins:</p>

        <pre>
const mongodb = require('@myframework/mongodb');
app.use(mongodb.connect('mongodb://localhost:27017/myapp'));
        </pre>

        <h2>Testing</h2>
        <p>MyFramework provides comprehensive testing utilities.</p>

        <h3>Unit Testing</h3>
        <p>Test individual components in isolation:</p>

        <pre>
import { test } from '@myframework/testing';

test('should handle GET requests', async () => {
    const response = await app.request().get('/api/users');
    expect(response.status).toBe(200);
});
        </pre>

        <h2>Performance Optimization</h2>
        <p>Tips for optimizing your MyFramework applications:</p>

        <ul>
            <li>Use caching middleware for frequently accessed data</li>
            <li>Implement request/response compression</li>
            <li>Optimize database queries with proper indexing</li>
            <li>Use clustering to take advantage of multi-core systems</li>
        </ul>
    </main>
</body>
</html>
""",

        "troubleshooting.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Troubleshooting - MyFramework Documentation</title>
</head>
<body>
    <main>
        <h1>Troubleshooting Guide</h1>
        <p>Common issues and their solutions when working with MyFramework.</p>

        <h2>Installation Issues</h2>

        <h3>Package Not Found</h3>
        <p>If you're getting "package not found" errors during installation:</p>
        <ol>
            <li>Check that you're using the correct package name</li>
            <li>Ensure your npm registry is properly configured</li>
            <li>Try clearing npm cache: <code>npm cache clean --force</code></li>
        </ol>

        <h3>Version Conflicts</h3>
        <p>When dealing with version conflicts:</p>
        <ul>
            <li>Check your package.json for conflicting dependencies</li>
            <li>Use npm ls to view the dependency tree</li>
            <li>Consider using npm-check-updates to update dependencies</li>
        </ul>

        <h2>Runtime Issues</h2>

        <h3>Port Already in Use</h3>
        <p>If you get "EADDRINUSE" errors:</p>
        <pre>
// Solution: Use environment variable for port
const port = process.env.PORT || 3000;
app.listen(port);
        </pre>

        <h3>Memory Leaks</h3>
        <p>To identify and fix memory leaks:</p>
        <ol>
            <li>Use Node.js built-in profiler</li>
            <li>Monitor heap usage with process.memoryUsage()</li>
            <li>Clean up event listeners and timers properly</li>
        </ol>

        <h2>Performance Issues</h2>

        <h3>Slow Response Times</h3>
        <p>If your application is responding slowly:</p>
        <ul>
            <li>Profile your code to identify bottlenecks</li>
            <li>Check database query performance</li>
            <li>Implement appropriate caching strategies</li>
            <li>Use async/await properly to avoid blocking operations</li>
        </ul>

        <h2>Common Errors</h2>

        <h3>TypeError: Cannot read property 'X' of undefined</h3>
        <p>This usually indicates a missing or incorrectly structured object:</p>
        <ul>
            <li>Check that objects are properly initialized</li>
            <li>Use optional chaining: <code>object?.property</code></li>
            <li>Validate input data before processing</li>
        </ul>

        <h2>Getting Help</h2>
        <p>If you're still experiencing issues:</p>
        <ul>
            <li>Check the GitHub issues page</li>
            <li>Join our community Discord server</li>
            <li>Post questions on Stack Overflow with the 'myframework' tag</li>
            <li>Contact support at support@myframework.com</li>
        </ul>
    </main>
</body>
</html>
"""
    }

    # Create temporary files
    temp_files = []
    temp_dir = tempfile.mkdtemp(prefix="myframework_docs_")

    print(f"📁 Creating sample documentation in {temp_dir}")

    for filename, content in html_docs.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        temp_files.append(file_path)
        print(f"   📄 Created: {filename}")

    return temp_files, temp_dir


async def demo_single_file_async():
    """Demonstrate async processing of a single local HTML file"""

    print("\n" + "="*60)
    print("📂 Demo 1: Single File Async Processing")
    print("="*60)

    # Create sample files
    temp_files, temp_dir = create_sample_documentation_files()

    try:
        # Use the first file for single file demo
        test_file = temp_files[0]

        print(f"🔍 Processing single file: {Path(test_file).name}")

        # Configure async scraper
        config = ScrapingConfig(concurrent_limit=4)

        async with AsyncWebScraper(config) as scraper:
            start_time = time.time()

            # Extract content from single file
            doc_structure = await scraper.extract_from_local_file_async(test_file)

            duration = time.time() - start_time

            if doc_structure:
                print(f"✅ Extraction completed in {duration:.3f} seconds")
                print(f"📊 Results:")
                print(f"   - Page title: {doc_structure['page_title']}")
                print(f"   - Total sections: {doc_structure['total_sections']}")
                print(f"   - Domain: {doc_structure['domain']}")

                # Show section breakdown
                print(f"📋 Content structure:")
                for i, section in enumerate(doc_structure['sections'][:5], 1):
                    word_count = section.get('word_count', 0)
                    print(f"   {i}. {section['title']} (Level {section['level']}, {word_count} words)")
                    if i == 5 and len(doc_structure['sections']) > 5:
                        print(f"   ... and {len(doc_structure['sections']) - 5} more sections")

                return True
            else:
                print("❌ Failed to extract content")
                return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_batch_processing():
    """Demonstrate high-performance batch processing of multiple HTML files"""

    print("\n" + "="*60)
    print("⚡ Demo 2: High-Performance Batch Processing")
    print("="*60)

    # Create sample files
    temp_files, temp_dir = create_sample_documentation_files()

    try:
        print(f"🚀 Processing {len(temp_files)} documentation files concurrently...")

        start_time = time.time()

        # Use convenience function for batch processing
        results = await process_local_files_fast(
            file_paths=temp_files,
            output_file="data/myframework_docs_async.json",
            concurrent_limit=6
        )

        duration = time.time() - start_time
        metadata = results.get("metadata", {})

        print(f"✅ Batch processing completed in {duration:.2f} seconds")
        print(f"📊 Performance metrics:")
        print(f"   - Files processed: {metadata.get('total_files', 0)}")
        print(f"   - Processing rate: {metadata.get('files_per_second', 0):.1f} files/second")
        print(f"   - Total chunks: {metadata.get('total_chunks', 0)}")
        print(f"   - Failed files: {metadata.get('failed_files', 0)}")

        # Analyze content
        documents = results.get("documents", [])
        chunks = results.get("semantic_chunks", [])

        if documents and chunks:
            # Content statistics
            total_sections = sum(doc['total_sections'] for doc in documents)
            avg_sections = total_sections / len(documents)
            avg_chunk_words = sum(c.get('word_count', 0) for c in chunks) / len(chunks)

            print(f"📋 Content analysis:")
            print(f"   - Total sections extracted: {total_sections}")
            print(f"   - Average sections per file: {avg_sections:.1f}")
            print(f"   - Average chunk size: {avg_chunk_words:.0f} words")

            # Show sample chunks
            print(f"📖 Sample content chunks:")
            for i, chunk in enumerate(chunks[:3], 1):
                title = chunk.get('title', 'Unknown')[:50]
                content_preview = chunk.get('text', '')[:100].replace('\n', ' ')
                print(f"   {i}. {title}...")
                print(f"      Preview: {content_preview}...")

        return True

    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
        return False
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_rag_integration():
    """Demonstrate full RAG integration with async local file processing"""

    print("\n" + "="*60)
    print("🧠 Demo 3: Full RAG Integration")
    print("="*60)

    # Create sample files
    temp_files, temp_dir = create_sample_documentation_files()

    try:
        print(f"🤖 Processing {len(temp_files)} files for RAG system...")

        # Initialize RAG system
        rag = RAGSystem()

        start_time = time.time()

        # Process files asynchronously for RAG
        success = await rag.process_local_files_async(
            file_paths=temp_files,
            output_file="data/myframework_rag_async.json",
            concurrent_limit=4
        )

        duration = time.time() - start_time

        if success:
            print(f"✅ RAG processing completed in {duration:.2f} seconds")

            # Test various queries
            print(f"\n🔍 Testing intelligent queries:")

            test_queries = [
                ("How to install MyFramework?", "Installation and setup"),
                ("What are the main API methods?", "API reference"),
                ("How to create custom middleware?", "Advanced usage patterns"),
                ("How to fix port already in use error?", "Troubleshooting"),
                ("Database integration options", "Database connectivity"),
                ("Performance optimization tips", "Performance tuning")
            ]

            successful_queries = 0

            for query, description in test_queries:
                print(f"\n💭 Query: '{query}' ({description})")

                # Test retrieval
                result = rag.demo_query(query, top_k=3)

                if result and "No relevant documents" not in result:
                    print(f"✅ Found relevant information")
                    successful_queries += 1

                    # Extract score from result if possible
                    if "Score" in result:
                        lines = result.split('\n')
                        score_line = next((line for line in lines if 'Score' in line), None)
                        if score_line:
                            print(f"   Best relevance score: {score_line.split('Score ')[1].split(' ')[0] if 'Score ' in score_line else 'N/A'}")
                else:
                    print(f"⚠️  No relevant results found")

            success_rate = successful_queries / len(test_queries)
            print(f"\n📊 Query Results:")
            print(f"   - Successful queries: {successful_queries}/{len(test_queries)}")
            print(f"   - Success rate: {success_rate:.1%}")

            if success_rate >= 0.8:
                print("🎉 Excellent RAG performance!")
            elif success_rate >= 0.6:
                print("✅ Good RAG performance!")
            else:
                print("⚠️  RAG performance needs improvement")

            return success_rate >= 0.5

        else:
            print("❌ RAG processing failed")
            return False

    except Exception as e:
        print(f"❌ Error during RAG integration: {e}")
        return False
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_mixed_sources():
    """Demonstrate mixed processing of web content and local files"""

    print("\n" + "="*60)
    print("🌐 Demo 4: Mixed Source Processing (Web + Local)")
    print("="*60)

    # Create sample local files
    temp_files, temp_dir = create_sample_documentation_files()

    try:
        print(f"🔄 Processing mixed sources:")
        print(f"   - Local files: {len(temp_files)}")
        print(f"   - Web URLs: 1 (example.com)")

        # Initialize RAG system
        rag = RAGSystem()

        start_time = time.time()

        # Process both web and local sources
        success = await rag.process_mixed_sources_async(
            web_urls=["https://example.com"],  # Simple test page
            local_files=temp_files,
            output_file="data/mixed_sources_demo.json",
            max_pages=2,  # Small limit for demo
            concurrent_limit=4
        )

        duration = time.time() - start_time

        if success:
            print(f"✅ Mixed processing completed in {duration:.2f} seconds")

            # Test query that might find content from both sources
            print(f"\n🔍 Testing cross-source query:")
            result = rag.demo_query("documentation examples information", top_k=5)

            if result and "No relevant documents" not in result:
                print(f"✅ Successfully retrieved information from mixed sources")
                # Count domains if possible
                if "Domain:" in result:
                    domains = set()
                    for line in result.split('\n'):
                        if "Domain:" in line:
                            domain = line.split("Domain:")[1].strip()
                            if domain:
                                domains.add(domain)
                    print(f"📊 Retrieved from {len(domains)} different domains")

                return True
            else:
                print(f"⚠️  Mixed processing completed but queries returned no results")
                return False

        else:
            print("❌ Mixed processing failed")
            return False

    except Exception as e:
        print(f"❌ Error during mixed processing: {e}")
        return False
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """Run all async local file processing demonstrations"""

    print("🚀 Async Local File Processing - Complete Demonstration")
    print("="*70)
    print("This example showcases the new async extract_from_local_file() functionality")
    print("for high-performance local HTML file processing with RAG integration.")
    print("="*70)

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Run all demonstrations
    demos = [
        ("Single File Processing", demo_single_file_async),
        ("Batch Processing", demo_batch_processing),
        ("RAG Integration", demo_rag_integration),
        ("Mixed Sources", demo_mixed_sources),
    ]

    results = []

    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*20} {demo_name} {'='*20}")
            success = await demo_func()
            results.append((demo_name, success))
            if success:
                print(f"✅ {demo_name} completed successfully")
            else:
                print(f"⚠️ {demo_name} completed with issues")
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results.append((demo_name, False))

    # Summary
    print("\n" + "="*70)
    print("📊 Demonstration Summary")
    print("="*70)

    successful = sum(1 for _, success in results if success)

    for demo_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status:<12} {demo_name}")

    print(f"\n🎯 Overall Results: {successful}/{len(results)} demonstrations successful")

    if successful == len(results):
        print("🎉 All demonstrations completed successfully!")
        print("\n💡 Key Benefits of Async Local File Processing:")
        print("   • Concurrent processing of multiple HTML files")
        print("   • Seamless integration with existing RAG system")
        print("   • Same output format as synchronous version")
        print("   • High-performance file I/O with aiofiles")
        print("   • Intelligent error handling and progress tracking")
    elif successful >= len(results) * 0.75:
        print("✅ Most demonstrations passed - async functionality working well!")
    else:
        print("⚠️  Some demonstrations had issues - check implementation")

    print(f"\n📁 Generated files:")
    print(f"   • data/myframework_docs_async.json - Batch processed documentation")
    print(f"   • data/myframework_rag_async.json - RAG-ready processed files")
    print(f"   • data/mixed_sources_demo.json - Mixed source processing result")

    return successful == len(results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n{'✅ Demo completed successfully!' if success else '⚠️  Demo completed with issues'}")
    except KeyboardInterrupt:
        print("\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")