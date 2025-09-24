#!/usr/bin/env python3
"""
Basic usage example for the RAG System
Shows how to use the RAG system with any website
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system import RAGSystem


def demo_with_website():
    """Demo RAG system with a website"""

    print("🚀 RAG System - Basic Usage Example")
    print("=" * 50)

    # Initialize the RAG system
    print("\n📚 Initializing RAG system...")
    rag_system = RAGSystem()

    # Demo with a simple website
    start_urls = ["https://fastapi.tiangolo.com/"]

    print("⚙️ Scraping and processing website (will use cache if available)...")
    success = rag_system.scrape_and_process_website(
        start_urls=start_urls,
        max_pages=8,
        output_file="data/demo_website_docs.json",
        same_domain_only=True,
        max_depth=2,
        use_cache=True  # This is the default - will use cached data if available
    )

    if not success:
        print("❌ No data available.")
        return

    print("✅ Website processed successfully!")

    # Example queries
    example_queries = [
        "How to create an application?",
        "What is dependency injection?",
        "API documentation and examples",
        "Request handling and routing",
        "Database integration"
    ]

    print(f"\n🔍 Testing {len(example_queries)} example queries...")
    print("-" * 50)

    for i, query in enumerate(example_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        result = rag_system.demo_query(query, top_k=3)

        # Parse result for display
        if isinstance(result, str):
            lines = result.split('\n')
            # Show just the first few lines for brevity
            for line in lines[:10]:
                if line.strip():
                    print(f"   {line}")
            if len(lines) > 10:
                print("   ...")

    print(f"\n📊 System Features:")
    print(f"   • Works with any website")
    print(f"   • Automatic content extraction")
    print(f"   • Respects robots.txt")
    print(f"   • Domain-aware processing")
    print(f"   • Enhanced query matching")

    print(f"\n💡 Next Steps:")
    print(f"   • Install Ollama for full text generation: ollama serve && ollama pull mistral")
    print(f"   • Use rag_query() instead of demo_query() for complete answers")
    print(f"   • Experiment with different top_k values (3-7 recommended)")
    print(f"   • Try different websites and adjust max_pages/max_depth")


if __name__ == "__main__":
    demo_with_website()