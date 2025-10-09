#!/usr/bin/env python3
"""
Advanced usage example for the RAG System with Ollama integration
"""

import sys
import os
import requests

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system import RAGSystem


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

    print("🚀 RAG System - Advanced Usage with Ollama Integration")
    print("=" * 60)

    # Initialize the RAG system
    print("\n📚 Initializing RAG system...")
    rag_system = RAGSystem()

    # Scrape and process a website (will use cache if available)
    print("⚙️ Scraping and processing documentation...")

    start_urls = ["https://docs.python.org/3/"]  # Using Python docs as example

    success = rag_system.scrape_and_process_website(
        start_urls=start_urls,
        max_pages=15,
        output_file="data/python_docs_advanced.json",
        same_domain_only=True,
        max_depth=2
    )

    if not success:
        print("❌ Failed to scrape and process website.")
        return

    print("✅ Website processed successfully!")

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
            "query": "How do I create and use Python classes with inheritance?",
            "context": "object-oriented programming"
        },
        {
            "query": "What are the best practices for exception handling in Python?",
            "context": "error management"
        },
        {
            "query": "How to use Python decorators and context managers effectively?",
            "context": "advanced Python features"
        },
        {
            "query": "What are Python generators and how do they work?",
            "context": "memory-efficient iteration"
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
        contexts, metadata = rag_system.retrieve_context(query, top_k=5)

        if not contexts:
            print("      ❌ No relevant documents found")
            continue

        for j, (context, meta) in enumerate(zip(contexts[:3], metadata[:3]), 1):  # Show top 3
            score = meta.get('boosted_score', 0)
            page = meta.get('page_title', 'Unknown')
            content_type = meta.get('type', 'N/A')

            print(f"      {j}. Score: {score:.3f}")
            print(f"         Page: {page}")
            print(f"         Type: {content_type}")
            print(f"         Content: {context[:150]}...")
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