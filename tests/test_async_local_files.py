#!/usr/bin/env python3
"""
Test script for async local file processing functionality
Tests the new async extract_from_local_file() implementation
"""

import os
import sys
import tempfile
import asyncio
import time
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.async_web_scraper import AsyncWebScraper, ScrapingConfig, process_local_files_fast
from src.rag_system import RAGSystem


def create_test_html_files():
    """Create sample HTML files for testing async processing"""

    sample_files = []

    # Sample HTML content variations
    html_templates = [
        {
            "name": "documentation.html",
            "content": """
<!DOCTYPE html>
<html>
<head>
    <title>Documentation Page</title>
</head>
<body>
    <nav>Navigation - should be removed</nav>

    <main>
        <h1>API Documentation</h1>
        <p>This is comprehensive API documentation covering all endpoints and methods available in our system.</p>

        <h2>Authentication</h2>
        <p>All API requests must include proper authentication headers using JWT tokens.</p>

        <pre>
# Example authentication
curl -H "Authorization: Bearer your-token" https://api.example.com/data
        </pre>

        <h2>Endpoints</h2>
        <p>The following endpoints are available for data retrieval and manipulation.</p>

        <h3>GET /users</h3>
        <p>Retrieve a list of all users in the system with pagination support.</p>

        <ul>
            <li>Parameter: page (optional) - Page number for pagination</li>
            <li>Parameter: limit (optional) - Number of items per page</li>
            <li>Returns: JSON array of user objects</li>
        </ul>

        <h3>POST /users</h3>
        <p>Create a new user account in the system.</p>

        <table>
            <tr><th>Field</th><th>Type</th><th>Required</th></tr>
            <tr><td>name</td><td>string</td><td>Yes</td></tr>
            <tr><td>email</td><td>string</td><td>Yes</td></tr>
            <tr><td>role</td><td>string</td><td>No</td></tr>
        </table>
    </main>

    <footer>Footer - should be removed</footer>
</body>
</html>
"""
        },
        {
            "name": "tutorial.html",
            "content": """
<!DOCTYPE html>
<html>
<head>
    <title>Getting Started Tutorial</title>
</head>
<body>
    <header>Header content</header>

    <article>
        <h1>Getting Started Guide</h1>
        <p>Welcome to our comprehensive getting started guide. This tutorial will walk you through the entire setup process.</p>

        <h2>Installation</h2>
        <p>Follow these steps to install the software on your system:</p>

        <ol>
            <li>Download the installer from our website</li>
            <li>Run the installer with administrator privileges</li>
            <li>Follow the on-screen instructions</li>
            <li>Restart your system when prompted</li>
        </ol>

        <h2>Configuration</h2>
        <p>After installation, you need to configure the system for your specific needs.</p>

        <blockquote>
        Important: Make sure to backup your configuration files before making changes.
        </blockquote>

        <h3>Basic Configuration</h3>
        <p>Edit the main configuration file located in the config directory.</p>

        <pre>
// Example configuration
{
    "host": "localhost",
    "port": 8080,
    "debug": false,
    "features": ["auth", "logging", "metrics"]
}
        </pre>

        <h3>Advanced Settings</h3>
        <p>For advanced users, additional configuration options are available in the advanced settings panel.</p>
    </article>
</body>
</html>
"""
        },
        {
            "name": "reference.html",
            "content": """
<!DOCTYPE html>
<html>
<head>
    <title>Technical Reference</title>
</head>
<body>
    <div class="sidebar">Sidebar navigation</div>

    <section>
        <h1>Technical Reference Manual</h1>
        <p>This reference manual provides detailed technical information about system components and architecture.</p>

        <h2>System Architecture</h2>
        <p>The system follows a microservices architecture with the following key components:</p>

        <ul>
            <li><strong>API Gateway</strong> - Routes requests to appropriate services</li>
            <li><strong>Authentication Service</strong> - Handles user authentication and authorization</li>
            <li><strong>Data Service</strong> - Manages data persistence and retrieval</li>
            <li><strong>Notification Service</strong> - Handles all system notifications</li>
        </ul>

        <h2>Database Schema</h2>
        <p>The database uses a relational schema with the following main tables:</p>

        <h3>Users Table</h3>
        <p>Stores user account information and preferences.</p>

        <table>
            <tr><th>Column</th><th>Type</th><th>Constraints</th></tr>
            <tr><td>id</td><td>INTEGER</td><td>PRIMARY KEY</td></tr>
            <tr><td>username</td><td>VARCHAR(50)</td><td>UNIQUE, NOT NULL</td></tr>
            <tr><td>email</td><td>VARCHAR(100)</td><td>UNIQUE, NOT NULL</td></tr>
            <tr><td>created_at</td><td>TIMESTAMP</td><td>NOT NULL</td></tr>
        </table>

        <h2>API Specifications</h2>
        <p>All API endpoints follow REST conventions and return JSON responses.</p>

        <h3>Error Handling</h3>
        <p>The API uses standard HTTP status codes and provides detailed error messages.</p>

        <pre>
// Error response format
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": ["Email format is invalid"]
    }
}
        </pre>
    </section>
</body>
</html>
"""
        }
    ]

    # Create temporary HTML files
    for template in html_templates:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(template["content"])
            sample_files.append(f.name)
            print(f"📄 Created test file: {f.name} ({template['name']})")

    return sample_files


async def test_single_file_extraction():
    """Test async extraction of a single local HTML file"""

    print("\n" + "="*60)
    print("🧪 Test 1: Single File Async Extraction")
    print("="*60)

    # Create a test file
    test_files = create_test_html_files()
    test_file = test_files[0]

    try:
        config = ScrapingConfig(concurrent_limit=4)
        scraper = AsyncWebScraper(config)

        print(f"📂 Testing single file extraction: {Path(test_file).name}")

        start_time = time.time()
        doc_structure = await scraper.extract_from_local_file_async(test_file)
        duration = time.time() - start_time

        if doc_structure:
            print(f"✅ Successfully extracted content in {duration:.3f}s:")
            print(f"   - Page title: {doc_structure['page_title']}")
            print(f"   - Domain: {doc_structure['domain']}")
            print(f"   - Total sections: {doc_structure['total_sections']}")
            print(f"   - URL: {doc_structure['url']}")

            # Show section details
            for i, section in enumerate(doc_structure['sections'][:3], 1):
                print(f"   Section {i}: {section['title']} (Level {section['level']}, {section.get('word_count', 0)} words)")

            return True
        else:
            print("❌ Failed to extract content from file")
            return False

    except Exception as e:
        print(f"❌ Error during single file test: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)


async def test_batch_file_processing():
    """Test async batch processing of multiple HTML files"""

    print("\n" + "="*60)
    print("🧪 Test 2: Batch File Async Processing")
    print("="*60)

    # Create multiple test files
    test_files = create_test_html_files()

    try:
        print(f"📂 Testing batch processing of {len(test_files)} files...")

        start_time = time.time()

        # Test using convenience function
        results = await process_local_files_fast(
            file_paths=test_files,
            output_file="data/test_async_local.json",
            concurrent_limit=4
        )

        duration = time.time() - start_time
        metadata = results.get("metadata", {})

        print(f"✅ Batch processing completed in {duration:.2f}s")
        print(f"📊 Performance metrics:")
        print(f"   - Files processed: {metadata.get('total_files', 0)}")
        print(f"   - Files failed: {metadata.get('failed_files', 0)}")
        print(f"   - Processing rate: {metadata.get('files_per_second', 0):.1f} files/sec")
        print(f"   - Total chunks created: {metadata.get('total_chunks', 0)}")

        documents = results.get("documents", [])
        chunks = results.get("semantic_chunks", [])

        if documents and chunks:
            avg_sections = sum(len(doc.get('sections', [])) for doc in documents) / len(documents)
            avg_chunk_words = sum(c.get('word_count', 0) for c in chunks) / len(chunks)

            print(f"📊 Content analysis:")
            print(f"   - Average sections per document: {avg_sections:.1f}")
            print(f"   - Average chunk size: {avg_chunk_words:.0f} words")

            # Test chunk quality
            high_quality_chunks = sum(1 for c in chunks if c.get('word_count', 0) > 50)
            print(f"   - High-quality chunks (>50 words): {high_quality_chunks}/{len(chunks)} ({high_quality_chunks/len(chunks)*100:.1f}%)")

            return True
        else:
            print("❌ No documents or chunks were created")
            return False

    except Exception as e:
        print(f"❌ Error during batch processing test: {e}")
        return False
    finally:
        # Clean up test files
        for test_file in test_files:
            if os.path.exists(test_file):
                os.remove(test_file)


async def test_rag_integration():
    """Test integration with RAG system for local file processing"""

    print("\n" + "="*60)
    print("🧪 Test 3: RAG System Integration")
    print("="*60)

    # Create test files
    test_files = create_test_html_files()

    try:
        print(f"🧠 Testing RAG system integration with {len(test_files)} local files...")

        # Initialize RAG system
        rag_system = RAGSystem()

        start_time = time.time()

        # Test async local file processing
        success = await rag_system.process_local_files_async(
            file_paths=test_files,
            output_file="data/test_rag_local_async.json",
            concurrent_limit=3
        )

        duration = time.time() - start_time

        if success:
            print(f"✅ RAG integration successful in {duration:.2f}s")

            # Test querying
            print("\n🔍 Testing queries on processed local files...")

            test_queries = [
                "API authentication methods",
                "How to install the software?",
                "Database schema information",
                "System architecture components"
            ]

            query_results = []

            for query in test_queries:
                print(f"\nQuery: '{query}'")
                result = rag_system.demo_query(query, top_k=3)

                # Parse demo_query result (it returns formatted string)
                if result and "No relevant documents" not in result:
                    print(f"✅ Query successful - got relevant results")
                    query_results.append(True)
                else:
                    print(f"⚠️  Query returned no relevant results")
                    query_results.append(False)

            success_rate = sum(query_results) / len(query_results)
            print(f"\n📊 Query success rate: {success_rate:.1%} ({sum(query_results)}/{len(query_results)})")

            if success_rate >= 0.5:
                print("✅ RAG integration test passed!")
                return True
            else:
                print("⚠️  RAG integration had low query success rate")
                return False

        else:
            print("❌ RAG integration failed during processing")
            return False

    except Exception as e:
        print(f"❌ Error during RAG integration test: {e}")
        return False
    finally:
        # Clean up test files
        for test_file in test_files:
            if os.path.exists(test_file):
                os.remove(test_file)


async def test_performance_comparison():
    """Compare async vs sync local file processing performance"""

    print("\n" + "="*60)
    print("🧪 Test 4: Performance Comparison (Async vs Sync)")
    print("="*60)

    # Create multiple test files for better performance measurement
    test_files = create_test_html_files()
    # Add duplicates to have more files for testing
    test_files.extend(test_files[:2])  # Now we have 5 files total

    try:
        print(f"⚡ Comparing async vs sync performance with {len(test_files)} files...")

        # Test sync processing
        print("\n--- Sync Processing ---")
        from src.web_scraper import WebScraper

        sync_scraper = WebScraper(local_mode=True)

        sync_start = time.time()
        sync_result = sync_scraper.process_local_files(
            test_files,
            output_file="data/test_sync_comparison.json"
        )
        sync_duration = time.time() - sync_start

        sync_docs = len(sync_result.get('documents', []))
        sync_chunks = len(sync_result.get('semantic_chunks', []))

        print(f"✅ Sync processing: {sync_duration:.2f}s")
        print(f"   Documents: {sync_docs}, Chunks: {sync_chunks}")
        print(f"   Rate: {sync_docs/sync_duration:.2f} files/sec")

        # Test async processing
        print("\n--- Async Processing ---")

        async_start = time.time()
        async_result =  process_local_files_fast(
            file_paths=test_files,
            output_file="data/test_async_comparison.json",
            concurrent_limit=4
        )
        async_duration = time.time() - async_start

        async_docs = len(async_result.get('documents', []))
        async_chunks = len(async_result.get('semantic_chunks', []))
        async_rate = async_result.get('metadata', {}).get('files_per_second', 0)

        print(f"✅ Async processing: {async_duration:.2f}s")
        print(f"   Documents: {async_docs}, Chunks: {async_chunks}")
        print(f"   Rate: {async_rate:.2f} files/sec")

        # Calculate performance improvement
        if sync_duration > 0 and async_duration > 0:
            speedup = sync_duration / async_duration
            throughput_improvement = (async_docs/async_duration) / (sync_docs/sync_duration)

            print(f"\n📈 Performance Analysis:")
            print(f"   Time speedup: {speedup:.1f}x {'faster' if speedup > 1 else 'slower'}")
            print(f"   Throughput improvement: {throughput_improvement:.1f}x")

            # Check content consistency
            if sync_docs == async_docs and sync_chunks == async_chunks:
                print(f"   ✅ Content consistency: Identical results")
            else:
                print(f"   ⚠️  Content difference: Sync({sync_docs}/{sync_chunks}) vs Async({async_docs}/{async_chunks})")

            # Performance expectations
            if speedup > 0.8:  # Allow for some variation in small file processing
                print(f"✅ Performance test passed!")
                return True
            else:
                print(f"⚠️  Async processing was significantly slower than expected")
                return False
        else:
            print("❌ Could not measure performance properly")
            return False

    except Exception as e:
        print(f"❌ Error during performance comparison: {e}")
        return False
    finally:
        # Clean up test files
        for test_file in test_files:
            if os.path.exists(test_file):
                os.remove(test_file)


async def run_all_tests():
    """Run all async local file processing tests"""

    print("🚀 Testing Async Local File Processing Implementation")
    print("=" * 70)

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    tests = [
        ("Single File Extraction", test_single_file_extraction),
        ("Batch File Processing", test_batch_file_processing),
        ("RAG System Integration", test_rag_integration),
        ("Performance Comparison", test_performance_comparison)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("🎯 Test Results Summary")
    print("="*70)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<12} {test_name}")
        if result:
            passed += 1

    print(f"\n📊 Overall Results: {passed}/{len(results)} tests passed ({passed/len(results)*100:.1f}%)")

    if passed == len(results):
        print("🎉 All tests passed! Async local file processing is working correctly.")
    elif passed >= len(results) * 0.75:
        print("⚠️  Most tests passed, but some issues were found.")
    else:
        print("❌ Multiple test failures - implementation needs review.")

    # Clean up any remaining test files
    test_files = [f for f in os.listdir("data") if f.startswith("test_")]
    if test_files:
        print(f"\n🧹 Cleaning up {len(test_files)} test files...")
        for test_file in test_files:
            try:
                os.remove(os.path.join("data", test_file))
            except:
                pass

    return passed == len(results)


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        sys.exit(1)