#!/usr/bin/env python3
"""
Enhanced RAG System v2 - Works with improved structured PyTorch documentation
"""

import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import json
import os
from typing import List, Dict, Tuple, Optional

class EnhancedRAGSystemV2:
    """Enhanced RAG system that works with structured documentation data"""

    def __init__(self, chunk_size: int = 1200, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks = []
        self.chunk_metadata = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.structured_data = None

    def load_structured_data(self, json_file: str = "data/pytorch_docs_structured.json") -> bool:
        """Load structured documentation data"""

        if not os.path.exists(json_file):
            print(f"❌ Structured data file not found: {json_file}")
            print(f"   Please run improved_pytorch_scraper.py first")
            return False

        print(f"📚 Loading structured data from {json_file}...")

        with open(json_file, 'r', encoding='utf-8') as f:
            self.structured_data = json.load(f)

        semantic_chunks = self.structured_data.get('semantic_chunks', [])

        if not semantic_chunks:
            print("❌ No semantic chunks found in structured data")
            return False

        print(f"   ✅ Loaded {len(semantic_chunks)} semantic chunks")
        return True

    def process_structured_documents(self, json_file: str = "data/pytorch_docs_structured.json",
                                   cache_file: str = "data/enhanced_rag_v2_cache.pkl"):
        """Process structured documents and create searchable vectors"""

        # Check if cached data exists
        if os.path.exists(cache_file):
            print("✅ Loading cached processed data...")
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                self.chunks = cache_data['chunks']
                self.chunk_metadata = cache_data['metadata']
                self.vectorizer = cache_data['vectorizer']
                self.tfidf_matrix = cache_data['tfidf_matrix']
                self.structured_data = cache_data.get('structured_data')
            print(f"   Loaded {len(self.chunks)} chunks from cache")
            return True

        # Load structured data
        if not self.load_structured_data(json_file):
            return False

        print("🔄 Processing structured documents...")

        # Extract chunks and metadata from structured data
        semantic_chunks = self.structured_data['semantic_chunks']

        self.chunks = []
        self.chunk_metadata = []

        for chunk_data in semantic_chunks:
            # Use the improved chunk text
            chunk_text = chunk_data.get('text', '')
            if len(chunk_text.strip()) > 100:  # Filter very short chunks - increased for better quality
                self.chunks.append(chunk_text)

                # Enhanced metadata
                metadata = {
                    'title': chunk_data.get('title', 'Unknown'),
                    'section_title': chunk_data.get('section_title', ''),
                    'page_title': chunk_data.get('page_title', ''),
                    'url': chunk_data.get('url', ''),
                    'level': chunk_data.get('level', 1),
                    'type': chunk_data.get('type', 'unknown'),
                    'word_count': chunk_data.get('word_count', len(chunk_text.split())),
                    'chunk_id': len(self.chunk_metadata),
                    'part_number': chunk_data.get('part_number', 1)
                }
                self.chunk_metadata.append(metadata)

        print(f"   Created {len(self.chunks)} chunks from structured data")

        # Create enhanced TF-IDF vectors
        print("🔄 Vectorizing chunks with enhanced TF-IDF...")
        self.vectorizer = TfidfVectorizer(
            max_features=15000,  # More features for better precision
            stop_words='english',
            ngram_range=(1, 3),  # Include trigrams for better technical term matching
            min_df=2,
            max_df=0.7,
            sublinear_tf=True   # Use sublinear term frequency scaling
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)

        # Cache everything
        print("💾 Caching processed data...")
        cache_data = {
            'chunks': self.chunks,
            'metadata': self.chunk_metadata,
            'vectorizer': self.vectorizer,
            'tfidf_matrix': self.tfidf_matrix,
            'structured_data': self.structured_data
        }

        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)

        print("✅ Processing complete!")
        return True

    def retrieve_context(self, query: str, top_k: int = 5, min_similarity: float = 0.05) -> Tuple[List[str], List[Dict]]:
        """Retrieve most relevant chunks with enhanced similarity scoring"""

        if self.vectorizer is None:
            print("❌ System not initialized. Please run process_structured_documents() first.")
            return [], []

        # Enhanced query preprocessing
        processed_query = self.preprocess_query(query)

        # Vectorize the query
        query_vector = self.vectorizer.transform([processed_query])

        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Get top-k most similar chunks
        top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get more candidates

        retrieved_chunks = []
        retrieved_metadata = []

        # Apply filters and scoring
        for idx in top_indices:
            if similarities[idx] > min_similarity:
                chunk_metadata = self.chunk_metadata[idx].copy()
                chunk_metadata['similarity_score'] = similarities[idx]

                # Boost score for exact matches and technical terms
                boosted_score = self.calculate_boosted_score(query, self.chunks[idx], similarities[idx])
                chunk_metadata['boosted_score'] = boosted_score

                retrieved_chunks.append(self.chunks[idx])
                retrieved_metadata.append(chunk_metadata)

                if len(retrieved_chunks) >= top_k:
                    break

        # Sort by boosted score
        if retrieved_metadata:
            sorted_pairs = sorted(zip(retrieved_chunks, retrieved_metadata),
                                key=lambda x: x[1]['boosted_score'], reverse=True)
            retrieved_chunks, retrieved_metadata = zip(*sorted_pairs)
            retrieved_chunks, retrieved_metadata = list(retrieved_chunks), list(retrieved_metadata)

        return retrieved_chunks, retrieved_metadata

    def preprocess_query(self, query: str) -> str:
        """Enhanced query preprocessing for better matching"""

        # Add common PyTorch context terms to improve matching
        pytorch_context_terms = []
        query_lower = query.lower()

        if any(term in query_lower for term in ['optimizer', 'adam', 'sgd']):
            pytorch_context_terms.append("torch.optim")

        if any(term in query_lower for term in ['dataloader', 'dataset', 'batch']):
            pytorch_context_terms.append("torch.utils.data")

        if any(term in query_lower for term in ['neural network', 'layer', 'module']):
            pytorch_context_terms.append("torch.nn")

        if any(term in query_lower for term in ['tensor', 'cuda', 'gpu']):
            pytorch_context_terms.append("torch")

        # Enhanced support for parallelism queries
        if any(term in query_lower for term in ['tensor parallelism', 'model parallelism', 'pipeline parallelism']):
            pytorch_context_terms.extend(["torch.distributed", "nn.parallel", "sharding", "pipeline", "model partition"])

        if any(term in query_lower for term in ['data parallelism', 'distributed training', 'ddp']):
            pytorch_context_terms.extend(["torch.distributed", "DataParallel", "DistributedDataParallel"])

        if any(term in query_lower for term in ['parallelism', 'parallel', 'distributed']):
            pytorch_context_terms.extend(["torch.distributed", "torch.multiprocessing", "parallel"])

        if any(term in query_lower for term in ['shard', 'sharding', 'partition']):
            pytorch_context_terms.extend(["distributed tensor", "sharding", "partition"])

        enhanced_query = query
        if pytorch_context_terms:
            enhanced_query = f"{query} {' '.join(pytorch_context_terms)}"

        return enhanced_query

    def calculate_boosted_score(self, query: str, chunk_text: str, base_score: float) -> float:
        """Calculate boosted similarity score based on content quality"""

        boost_factor = 1.0
        query_lower = query.lower()
        chunk_lower = chunk_text.lower()

        # Boost for exact phrase matches
        if query_lower in chunk_lower:
            boost_factor += 0.3

        # Major boost for specific parallelism terms
        parallelism_terms = [
            "tensor parallelism", "model parallelism", "pipeline parallelism",
            "data parallelism", "distributed training", "sharding", "partition"
        ]
        for term in parallelism_terms:
            if term in chunk_lower:
                boost_factor += 0.4  # Higher boost for parallelism content
                break

        # Boost for distributed PyTorch modules
        distributed_modules = [
            "torch.distributed", "nn.parallel", "distributeddataparallel",
            "dataparallel", "torch.multiprocessing", "distributed tensor"
        ]
        if any(term in chunk_lower for term in distributed_modules):
            boost_factor += 0.25

        # Boost for technical implementation details
        technical_terms = ["shard", "rank", "world_size", "backend", "process group", "communication"]
        if any(term in chunk_lower for term in technical_terms):
            boost_factor += 0.2

        # Boost for code examples
        if "code example:" in chunk_lower or "```" in chunk_text or ">>>" in chunk_text:
            boost_factor += 0.2

        # Boost for function definitions and API references
        if any(term in chunk_lower for term in ["def ", "class ", "torch.", "nn."]):
            boost_factor += 0.15

        # Boost for complete sections vs parts
        if "(Part " not in chunk_text:
            boost_factor += 0.1

        # Boost for longer, more detailed chunks
        word_count = len(chunk_text.split())
        if word_count > 200:
            boost_factor += 0.1
        elif word_count < 50:
            boost_factor -= 0.2  # Penalize very short chunks more

        # Penalize generic chunks
        generic_indicators = ["example::", "note:", "warning:", "see also"]
        if any(indicator in chunk_lower for indicator in generic_indicators):
            boost_factor -= 0.05

        return base_score * boost_factor

    def ollama_generate(self, prompt: str, model: str = "mistral"):
        """Generate response using Ollama"""
        try:
            url = "http://localhost:11434/api/generate"
            headers = {"Content-Type": "application/json"}
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.ok:
                return response.json().get("response", "").strip()
            else:
                return f"Ollama Error: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Ollama not available: {e}"

    def rag_query(self, query: str, top_k: int = 4, model: str = "mistral") -> str:
        """Enhanced RAG query with better context and generation"""

        contexts, metadata = self.retrieve_context(query, top_k)

        if not contexts:
            return "❌ No relevant documents found."

        # Create rich context with source information
        context_parts = []
        for i, (context, meta) in enumerate(zip(contexts, metadata)):
            source_info = f"[Source: {meta['page_title']} - {meta['section_title']}]"
            score_info = f"[Relevance: {meta['boosted_score']:.3f}]"

            context_parts.append(f"{source_info} {score_info}\n{context}")

        combined_context = "\n\n" + "="*50 + "\n\n".join(context_parts)

        # Enhanced prompt for better answers
        prompt = f"""You are a PyTorch expert assistant. Based on the official PyTorch documentation provided below, answer the question accurately and comprehensively.

PYTORCH DOCUMENTATION CONTEXT:
{combined_context}

QUESTION: {query}

INSTRUCTIONS:
- Answer based ONLY on the provided documentation context
- Include specific code examples if available in the context
- Mention relevant PyTorch modules and functions
- If the context doesn't fully answer the question, say so clearly
- Be precise and technical where appropriate

ANSWER:"""

        answer = self.ollama_generate(prompt, model)

        # Format response with enhanced source information
        sources_info = []
        for meta in metadata:
            source = f"• {meta['page_title']}"
            if meta['section_title'] and meta['section_title'] != meta['page_title']:
                source += f" - {meta['section_title']}"
            source += f" (Score: {meta['boosted_score']:.3f})"
            if meta.get('type') == 'section_part':
                source += f" [Part {meta.get('part_number', 1)}]"
            sources_info.append(source)

        return f"{answer}\n\n📚 Sources:\n" + "\n".join(sources_info)

    def demo_query(self, query: str, top_k: int = 4) -> str:
        """Demo query that works without Ollama - shows enhanced retrieval"""

        print(f"\n🔍 Enhanced Query: {query}")
        print("=" * 80)

        contexts, metadata = self.retrieve_context(query, top_k)

        if not contexts:
            return "❌ No relevant documents found."

        print(f"✅ Found {len(contexts)} relevant chunks:")

        for i, (context, meta) in enumerate(zip(contexts, metadata)):
            print(f"\n📄 Result {i+1}: {meta['title']}")
            print(f"   Page: {meta['page_title']}")
            print(f"   Section: {meta['section_title']}")
            print(f"   Type: {meta['type']}")
            print(f"   Relevance: {meta['boosted_score']:.3f} (base: {meta['similarity_score']:.3f})")
            print(f"   Words: {meta['word_count']}")
            print(f"   Preview: {context[:200]}...")

        sources_info = "\n".join([
            f"• {meta['page_title']} - {meta['section_title']} (Score: {meta['boosted_score']:.3f})"
            for meta in metadata
        ])

        return f"\n✅ Retrieved {len(contexts)} enhanced chunks\n\n📚 Sources:\n{sources_info}"

def main():
    """Test the enhanced RAG system"""

    print("🚀 Enhanced RAG System v2 - Testing")
    print("=" * 80)

    # Initialize system
    rag_system = EnhancedRAGSystemV2()

    # Process structured documents
    if not rag_system.process_structured_documents():
        print("❌ Failed to process documents. Please run the scraper first.")
        return

    # Test queries
    test_questions = [
        "What is tensor parallelism in PyTorch?",
        "How do I use DataLoader for batching?",
        "What are the different types of PyTorch optimizers?",
        "How to implement custom loss functions?",
        "What is the difference between .cuda() and .to(device)?"
    ]

    print(f"\n🧪 Testing with {len(test_questions)} questions:")

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"🔍 Question {i}: {question}")
        result = rag_system.demo_query(question, top_k=3)
        print(result)

if __name__ == "__main__":
    main()