#!/usr/bin/env python3
"""
Test script to demonstrate RAG improvements for tensor parallelism queries
"""

import os
from src.enhanced_rag_system_v2 import EnhancedRAGSystemV2

def test_tensor_parallelism_improvements():
    """Test the improved tensor parallelism handling"""

    print("🧪 TESTING IMPROVED TENSOR PARALLELISM HANDLING")
    print("=" * 80)

    # Initialize enhanced system
    rag_system = EnhancedRAGSystemV2()

    # Check if we need to refresh the data with new URLs
    structured_file = "data/pytorch_docs_structured.json"

    if os.path.exists(structured_file):
        print("📄 Using existing structured data...")
        if rag_system.process_structured_documents(structured_file):
            print("✅ System initialized successfully!")
        else:
            print("❌ Failed to initialize system")
            return
    else:
        print("❌ No structured data found. Please run:")
        print("   python improved_pytorch_scraper.py")
        return

    # Test queries with different parallelism types
    test_queries = [
        "What is tensor parallelism in PyTorch?",
        "How do I implement model parallelism?",
        "What is data parallelism vs model parallelism?",
        "How to use torch.distributed for sharding?",
        "Pipeline parallelism implementation",
    ]

    print(f"\n🔍 Testing {len(test_queries)} parallelism queries:")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 60)

        # Show enhanced query processing
        enhanced_query = rag_system.preprocess_query(query)
        if enhanced_query != query:
            print(f"🔧 Enhanced query: {enhanced_query}")

        # Get results
        contexts, metadata = rag_system.retrieve_context(query, top_k=3)

        if contexts and metadata:
            max_score = max(meta['boosted_score'] for meta in metadata)
            avg_score = sum(meta['boosted_score'] for meta in metadata) / len(metadata)

            print(f"📊 Scores: Max={max_score:.3f}, Avg={avg_score:.3f}")

            # Show top result with detailed info
            top_meta = metadata[0]
            print(f"🏆 Top Result:")
            print(f"   Title: {top_meta['page_title']} - {top_meta['section_title']}")
            print(f"   Type: {top_meta['type']}")
            print(f"   Boosted Score: {top_meta['boosted_score']:.3f} (base: {top_meta['similarity_score']:.3f})")
            print(f"   Preview: {contexts[0][:200]}...")

            # Quality indicators
            quality = "🟢 Excellent" if max_score > 0.7 else "🟡 Good" if max_score > 0.5 else "🔴 Needs Improvement"
            print(f"   Quality: {quality}")

        else:
            print("❌ No relevant chunks found")

    print(f"\n💡 IMPROVEMENT SUGGESTIONS:")
    print("=" * 80)
    print("1. 🔄 Re-scrape with expanded URLs: `rm data/pytorch_docs_structured.json && python src/improved_pytorch_scraper.py`")
    print("2. 🎯 Try more specific queries: 'torch.distributed sharding tutorial'")
    print("3. 📊 Look for scores >0.6 for high-quality matches")
    print("4. 🤖 Use rag_query() with Ollama for complete answers")

if __name__ == "__main__":
    test_tensor_parallelism_improvements()