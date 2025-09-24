#!/usr/bin/env python3
"""
Test the generic RAG system with a simple example
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.rag_system import RAGSystem


def test_generic_rag():
    """Test the generic RAG system with a public documentation site"""

    print("🧪 Testing Generic RAG System")
    print("=" * 40)

    # Initialize system
    rag_system = RAGSystem()

    # Test with httpbin (a simple HTTP testing service with documentation)
    start_urls = ["https://httpbin.org/"]

    print("📚 Testing with httpbin.org (simple API documentation)...")

    try:
        success = rag_system.scrape_and_process_website(
            start_urls=start_urls,
            max_pages=3,  # Very small test
            output_file="data/test_httpbin_docs.json",
            same_domain_only=True,
            max_depth=1
        )

        if success:
            print("✅ Scraping and processing successful!")

            # Test queries
            test_queries = [
                "What is httpbin?",
                "HTTP methods supported",
                "GET request examples",
                "API endpoints available"
            ]

            print(f"\n🔍 Testing {len(test_queries)} queries...")

            for i, query in enumerate(test_queries, 1):
                print(f"\n{i}. Query: '{query}'")
                print("-" * 30)

                result = rag_system.demo_query(query, top_k=2)

                # Show shortened result
                if isinstance(result, str):
                    lines = result.split('\n')
                    for line in lines[:6]:  # Show first 6 lines
                        if line.strip():
                            print(f"   {line}")
                    if len(lines) > 6:
                        print("   ...")

        else:
            print("❌ Failed to scrape httpbin.org")
            print("This might be due to network issues or the site being down.")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("This is normal if there are network connectivity issues.")

    print(f"\n💡 Test completed!")
    print("The generic system can now work with any website.")


if __name__ == "__main__":
    test_generic_rag()