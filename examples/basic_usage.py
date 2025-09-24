#!/usr/bin/env python3
"""
Basic usage example for the Enhanced RAG System
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_rag_system_v2 import EnhancedRAGSystemV2


def main():
    """Demonstrate basic usage of the RAG system"""

    print("🚀 Enhanced RAG System - Basic Usage Example")
    print("=" * 50)

    # Initialize the RAG system
    print("\n📚 Initializing RAG system...")
    rag_system = EnhancedRAGSystemV2()

    # Process the structured documentation
    print("⚙️ Processing structured documents...")
    success = rag_system.process_structured_documents("data/pytorch_docs_structured.json")

    if not success:
        print("❌ Failed to process documents. Make sure pytorch_docs_structured.json exists.")
        print("   Run: python src/improved_pytorch_scraper.py")
        return

    print("✅ Documents processed successfully!")

    # Example queries
    example_queries = [
        "What is tensor parallelism?",
        "How do I create a tensor?",
        "DataLoader batch processing",
        "gradient computation automatic differentiation",
        "neural network layers"
    ]

    print(f"\n🔍 Testing {len(example_queries)} example queries...")
    print("-" * 50)

    for i, query in enumerate(example_queries, 1):
        print(f"\n{i}. Query: '{query}'")

        # Perform retrieval-only search
        result = rag_system.demo_query(query, top_k=3)

        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            continue

        print(f"   ✅ Found {len(result['top_results'])} relevant documents:")

        # Display top results
        for j, doc in enumerate(result['top_results'], 1):
            print(f"      {j}. Score: {doc['score']:.3f} | Page: {doc.get('page', 'Unknown')}")
            print(f"         Section: {doc.get('section', 'N/A')}")
            print(f"         Preview: {doc['content'][:100]}...")

        if result['top_results']:
            best_score = result['top_results'][0]['score']
            if best_score > 0.5:
                print(f"   🎯 Excellent match (score: {best_score:.3f})")
            elif best_score > 0.3:
                print(f"   👍 Good match (score: {best_score:.3f})")
            else:
                print(f"   🤔 Weak match (score: {best_score:.3f})")

    print(f"\n📊 System Performance Summary:")
    print(f"   • Processed chunks: {len(rag_system.chunks)}")
    print(f"   • Average similarity threshold: >0.3 for good results")
    print(f"   • Enhanced TF-IDF with trigrams for better matching")

    print(f"\n💡 Next Steps:")
    print(f"   • Install Ollama for full text generation: ollama serve && ollama pull mistral")
    print(f"   • Use rag_query() instead of demo_query() for complete answers")
    print(f"   • Experiment with different top_k values (3-7 recommended)")
    print(f"   • Try more specific technical queries for best results")


if __name__ == "__main__":
    main()