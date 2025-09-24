#!/usr/bin/env python3
"""
Advanced usage example for the Enhanced RAG System with Ollama integration
"""

import sys
import os
import requests

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_rag_system_v2 import EnhancedRAGSystemV2


def check_ollama_status():
    """Check if Ollama is running and what models are available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            return True, model_names
        else:
            return False, []
    except requests.exceptions.RequestException:
        return False, []


def main():
    """Demonstrate advanced usage with Ollama integration"""

    print("🚀 Enhanced RAG System - Advanced Usage Example")
    print("=" * 55)

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

    # Check Ollama status
    print("\n🤖 Checking Ollama status...")
    ollama_running, available_models = check_ollama_status()

    if ollama_running:
        print("✅ Ollama is running!")
        print(f"   Available models: {', '.join(available_models) if available_models else 'None'}")

        if not available_models:
            print("⚠️ No models installed. Install one with: ollama pull mistral")

    else:
        print("❌ Ollama is not running.")
        print("   Start with: ollama serve")
        print("   Install models with: ollama pull mistral")

    # Advanced query examples
    advanced_queries = [
        {
            "query": "How do I implement custom loss functions in PyTorch?",
            "context": "neural network training"
        },
        {
            "query": "What are the best practices for memory management with large tensors?",
            "context": "performance optimization"
        },
        {
            "query": "How to use torch.utils.data.DataLoader for efficient batch processing?",
            "context": "data loading and preprocessing"
        }
    ]

    print(f"\n🔍 Testing {len(advanced_queries)} advanced queries...")
    print("-" * 55)

    for i, query_info in enumerate(advanced_queries, 1):
        query = query_info["query"]
        context = query_info["context"]

        print(f"\n{i}. Query: '{query}'")
        print(f"   Context: {context}")

        # First, show retrieval results
        print("   \n🔍 Retrieval Results:")
        result = rag_system.demo_query(query, top_k=5)

        if 'error' in result:
            print(f"      ❌ Error: {result['error']}")
            continue

        for j, doc in enumerate(result['top_results'][:3], 1):  # Show top 3
            print(f"      {j}. Score: {doc['score']:.3f}")
            print(f"         Page: {doc.get('page', 'Unknown')}")
            print(f"         Type: {doc.get('content_type', 'N/A')}")
            print(f"         Content: {doc['content'][:150]}...")
            print()

        # If Ollama is available, generate complete answer
        if ollama_running and available_models:
            print("   🤖 Generating complete answer with Ollama...")

            # Use the first available model
            model = available_models[0]
            if 'mistral' in available_models:
                model = 'mistral'

            try:
                answer = rag_system.rag_query(query, top_k=3, model=model)
                print(f"   \n💬 Complete Answer (using {model}):")
                print("   " + "─" * 50)
                print(f"   {answer}")
                print("   " + "─" * 50)

            except Exception as e:
                print(f"   ❌ Failed to generate answer: {e}")

        else:
            print("   ⚠️ Skipping answer generation (Ollama not available)")

    # Performance analysis
    print(f"\n📊 Advanced Performance Analysis:")
    print("-" * 40)

    if rag_system.chunks:
        chunk_lengths = [len(chunk) for chunk in rag_system.chunks]
        avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths)

        print(f"   • Total chunks: {len(rag_system.chunks)}")
        print(f"   • Average chunk length: {avg_chunk_length:.0f} characters")
        print(f"   • Vectorizer features: {rag_system.tfidf_matrix.shape[1] if rag_system.tfidf_matrix is not None else 'N/A'}")

        # Count content types
        content_types = {}
        for metadata in rag_system.chunk_metadata:
            ctype = metadata.get('content_type', 'unknown')
            content_types[ctype] = content_types.get(ctype, 0) + 1

        print(f"   • Content type distribution:")
        for ctype, count in sorted(content_types.items()):
            print(f"     - {ctype}: {count} chunks")

    print(f"\n🎯 Advanced Tips:")
    print("   • Use higher top_k (5-7) for complex queries")
    print("   • Try different Ollama models: mistral, llama2, codellama")
    print("   • Combine specific technical terms for better matching")
    print("   • Use the notebook interface for interactive exploration")


if __name__ == "__main__":
    main()