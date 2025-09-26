#!/usr/bin/env python3
"""
Generic RAG System for Any Website
Complete RAG system with web scraping and enhanced retrieval capabilities
"""

import json
import pickle
import os
import requests
import time
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

try:
    from .web_scraper import WebScraper
    from .async_web_scraper import AsyncWebScraper, scrape_website_fast, ScrapingConfig
except ImportError:
    from web_scraper import WebScraper
    from async_web_scraper import AsyncWebScraper, scrape_website_fast, ScrapingConfig

import asyncio


class RAGSystem:
    """Complete RAG system that can work with any website"""

    def __init__(self, chunk_size: int = 1200, overlap: int = 100, use_async: bool = False):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks = []
        self.chunk_metadata = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.structured_data = None
        self.scraper = WebScraper()
        self.use_async = use_async

    def scrape_and_process_website(self, start_urls: List[str],
                                 max_pages: int = 30,
                                 output_file: str = "data/website_docs.json",
                                 same_domain_only: bool = True,
                                 max_depth: int = 2,
                                 use_cache: bool = True) -> bool:
        """Scrape a website and process it for RAG"""

        print(f"🚀 RAG: Scraping and processing website...")

        # Check if we already have cached data and processing cache
        cache_file = output_file.replace('.json', '_cache.pkl')

        if use_cache and os.path.exists(output_file) and os.path.exists(cache_file):
            print(f"💾 Found cached data and processed index!")
            print(f"📄 Data file: {output_file}")
            print(f"🧠 Processed cache: {cache_file}")

            # Load the processed data directly
            success = self.process_structured_documents(output_file)

            if success:
                print("✅ Using cached data - ready to query!")
                return True
            else:
                print("⚠️ Cache corrupted, will re-scrape...")

        elif use_cache and os.path.exists(output_file):
            print(f"📄 Found scraped data file: {output_file}")
            print("🧠 Processing existing data...")

            # Process existing scraped data
            success = self.process_structured_documents(output_file)

            if success:
                print("✅ Existing data processed successfully!")
                return True
            else:
                print("⚠️ Failed to process existing data, will re-scrape...")

        # If we get here, we need to scrape
        print(f"🌐 Scraping website from: {', '.join(start_urls)}")

        # Scrape the website
        scraping_result = self.scraper.scrape_website(
            start_urls=start_urls,
            max_pages=max_pages,
            output_file=output_file,
            same_domain_only=same_domain_only,
            max_depth=max_depth
        )

        if not scraping_result:
            print("❌ Failed to scrape website")
            return False

        # Process the newly scraped data
        success = self.process_structured_documents(output_file)

        if success:
            print("✅ Website scraped and processed successfully!")
        else:
            print("❌ Failed to process scraped data")

        return success

    async def process_local_files_async(self, file_paths: List[str],
                                      output_file: str = "data/local_docs_async.json",
                                      concurrent_limit: int = 6,
                                      use_cache: bool = True) -> bool:
        """Process local HTML files asynchronously for RAG"""

        print(f"🚀 RAG: High-Performance Async Local File Processing...")

        # Check cache first
        cache_file = output_file.replace('.json', '_cache.pkl')

        if use_cache and os.path.exists(output_file) and os.path.exists(cache_file):
            print(f"💾 Found cached local file data!")
            success = self.process_structured_documents(output_file)
            if success:
                print("✅ Using cached data - ready to query!")
                return True

        # Perform async local file processing
        start_time = time.time()

        try:
            from .async_web_scraper import process_local_files_fast

            results = await process_local_files_fast(
                file_paths=file_paths,
                output_file=output_file,
                concurrent_limit=concurrent_limit
            )

            duration = time.time() - start_time
            metadata = results.get("metadata", {})

            print(f"⚡ Async local file processing completed in {duration:.2f}s")
            print(f"📊 Performance: {metadata.get('files_per_second', 0):.1f} files/sec")
            print(f"✅ Success rate: {metadata.get('total_files', 0) - metadata.get('failed_files', 0)}/{metadata.get('total_files', 0)} files")

            # Process the data for RAG
            success = self.process_structured_documents(output_file)

            if success:
                print("✅ Async local files processed and ready for RAG!")
            else:
                print("❌ Failed to process local file data for RAG")

            return success

        except Exception as e:
            print(f"❌ Async local file processing failed: {e}")
            return False

    async def scrape_and_process_website_async(self, start_urls: List[str],
                                             max_pages: int = 30,
                                             output_file: str = "data/website_docs_async.json",
                                             concurrent_limit: int = 8,
                                             requests_per_second: float = 10.0,
                                             use_cache: bool = True) -> bool:
        """Async version for high-performance scraping"""

        print(f"🚀 RAG: High-Performance Async Scraping...")

        # Check cache first
        cache_file = output_file.replace('.json', '_cache.pkl')

        if use_cache and os.path.exists(output_file) and os.path.exists(cache_file):
            print(f"💾 Found cached async data!")
            success = self.process_structured_documents(output_file)
            if success:
                print("✅ Using cached data - ready to query!")
                return True

        # Perform async scraping
        start_time = time.time()

        try:
            results = await scrape_website_fast(
                start_urls=start_urls,
                max_pages=max_pages,
                concurrent_limit=concurrent_limit,
                requests_per_second=requests_per_second,
                output_file=output_file
            )

            duration = time.time() - start_time
            metadata = results.get("metadata", {})

            print(f"⚡ Async scraping completed in {duration:.2f}s")
            print(f"📊 Performance: {metadata.get('requests_per_second', 0):.1f} RPS average")
            print(f"✅ Success rate: {metadata.get('success_rate', 0):.1f}%")

            # Process the scraped data
            success = self.process_structured_documents(output_file)

            if success:
                print("✅ Async website scraped and processed successfully!")
            else:
                print("❌ Failed to process async scraped data")

            return success

        except Exception as e:
            print(f"❌ Async scraping failed: {e}")
            return False

    async def process_mixed_sources_async(self, web_urls: List[str] = None,
                                        local_files: List[str] = None,
                                        output_file: str = "data/mixed_docs_async.json",
                                        max_pages: int = 30,
                                        concurrent_limit: int = 6,
                                        use_cache: bool = True) -> bool:
        """Process both web URLs and local HTML files asynchronously in a single operation"""

        print(f"🚀 RAG: High-Performance Mixed Async Processing...")
        print(f"   Web URLs: {len(web_urls) if web_urls else 0}")
        print(f"   Local files: {len(local_files) if local_files else 0}")

        # Check cache first
        cache_file = output_file.replace('.json', '_cache.pkl')

        if use_cache and os.path.exists(output_file) and os.path.exists(cache_file):
            print(f"💾 Found cached mixed data!")
            success = self.process_structured_documents(output_file)
            if success:
                print("✅ Using cached data - ready to query!")
                return True

        start_time = time.time()
        all_structured_docs = []

        try:
            # Process web URLs if provided
            if web_urls:
                print(f"🌐 Processing {len(web_urls)} web URLs asynchronously...")
                web_success = await self.scrape_and_process_website_async(
                    start_urls=web_urls,
                    max_pages=max_pages,
                    output_file=f"{output_file}_web_temp.json",
                    concurrent_limit=concurrent_limit,
                    use_cache=False  # Don't cache temp files
                )

                if web_success:
                    # Load web data and extract documents
                    with open(f"{output_file}_web_temp.json", 'r') as f:
                        web_data = json.load(f)
                    all_structured_docs.extend(web_data.get('documents', []))
                    print(f"✅ Web processing complete: {len(web_data.get('documents', []))} documents")
                else:
                    print("⚠️  Web processing failed, continuing with local files only")

            # Process local files if provided
            if local_files:
                print(f"📂 Processing {len(local_files)} local files asynchronously...")
                local_success = await self.process_local_files_async(
                    file_paths=local_files,
                    output_file=f"{output_file}_local_temp.json",
                    concurrent_limit=concurrent_limit,
                    use_cache=False  # Don't cache temp files
                )

                if local_success:
                    # Load local data and extract documents
                    with open(f"{output_file}_local_temp.json", 'r') as f:
                        local_data = json.load(f)
                    all_structured_docs.extend(local_data.get('documents', []))
                    print(f"✅ Local processing complete: {len(local_data.get('documents', []))} documents")
                else:
                    print("⚠️  Local file processing failed")

            if not all_structured_docs:
                print("❌ No documents were successfully processed")
                return False

            # Create combined semantic chunks using sync scraper method
            print(f"🧠 Creating semantic chunks from {len(all_structured_docs)} total documents...")
            from .web_scraper import WebScraper
            scraper = WebScraper()
            semantic_chunks = scraper.create_semantic_chunks(all_structured_docs)

            # Create combined output
            combined_output = {
                "metadata": {
                    "processing_timestamp": time.time(),
                    "source_type": "mixed_async",
                    "web_urls": web_urls or [],
                    "local_files": local_files or [],
                    "total_documents": len(all_structured_docs),
                    "total_chunks": len(semantic_chunks),
                    "processing_time": time.time() - start_time,
                    "domains": list(set(doc.get("domain", "") for doc in all_structured_docs))
                },
                "documents": all_structured_docs,
                "semantic_chunks": semantic_chunks
            }

            # Save combined data
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            print(f"💾 Saving combined data to {output_file}...")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_output, f, indent=2, ensure_ascii=False)

            # Create text file for compatibility
            text_file = output_file.replace('.json', '.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                for chunk in semantic_chunks:
                    f.write(f"{chunk['text']}\n\n{'='*80}\n\n")

            # Clean up temporary files
            for temp_file in [f"{output_file}_web_temp.json", f"{output_file}_local_temp.json"]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            # Process the combined data for RAG
            success = self.process_structured_documents(output_file)

            duration = time.time() - start_time

            if success:
                print(f"✅ Mixed async processing complete in {duration:.1f}s!")
                print(f"   📊 Statistics:")
                print(f"      Documents processed: {len(all_structured_docs)}")
                print(f"      Semantic chunks: {len(semantic_chunks)}")
                print(f"      Domains: {len(combined_output['metadata']['domains'])}")
                print(f"      Processing rate: {len(all_structured_docs)/duration:.1f} docs/sec")
            else:
                print("❌ Failed to process mixed data for RAG")

            return success

        except Exception as e:
            print(f"❌ Mixed async processing failed: {e}")
            return False

    def clear_cache(self, output_file: str = "data/website_docs.json") -> bool:
        """Clear cached data files to force re-scraping"""

        cache_file = output_file.replace('.json', '_cache.pkl')
        text_file = output_file.replace('.json', '.txt')

        files_removed = []

        for file_path in [output_file, cache_file, text_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_removed.append(file_path)
                except Exception as e:
                    print(f"⚠️ Could not remove {file_path}: {e}")

        if files_removed:
            print(f"🗑️ Cleared cache files: {', '.join(files_removed)}")
            return True
        else:
            print("📄 No cache files found to remove")
            return False

    def load_structured_data(self, file_path: str) -> bool:
        """Load structured data from JSON file"""

        if not os.path.exists(file_path):
            print(f"❌ Structured data file not found: {file_path}")
            return False

        try:
            print(f"📚 Loading structured data from {file_path}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                self.structured_data = json.load(f)

            semantic_chunks = self.structured_data.get('semantic_chunks', [])
            print(f"   ✅ Loaded {len(semantic_chunks)} semantic chunks")
            return True

        except Exception as e:
            print(f"❌ Error loading structured data: {e}")
            return False

    def process_structured_documents(self, file_path: str = None) -> bool:
        """Process structured documents and build TF-IDF index"""

        # Load data if file path provided
        if file_path:
            if not self.load_structured_data(file_path):
                return False

        if not self.structured_data:
            return False

        semantic_chunks = self.structured_data.get('semantic_chunks', [])

        if not semantic_chunks:
            print("❌ No semantic chunks found in data")
            return False

        # Check for cached processed data
        cache_file = file_path.replace('.json', '_cache.pkl') if file_path else 'rag_cache.pkl'

        if os.path.exists(cache_file):
            try:
                print("✅ Loading cached processed data...")
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)

                self.chunks = cache_data['chunks']
                self.chunk_metadata = cache_data['chunk_metadata']
                self.vectorizer = cache_data['vectorizer']
                self.tfidf_matrix = cache_data['tfidf_matrix']

                print(f"   Loaded {len(self.chunks)} chunks from cache")
                return True

            except Exception as e:
                print(f"⚠️ Cache loading failed: {e}, rebuilding...")

        # Process chunks
        print("🧠 Processing semantic chunks for RAG...")

        self.chunks = []
        self.chunk_metadata = []

        for chunk_data in semantic_chunks:
            chunk_text = chunk_data.get('text', '')
            if len(chunk_text.strip()) < 10:
                continue

            self.chunks.append(chunk_text)

            # Extract metadata
            metadata = {
                'title': chunk_data.get('title', 'Unknown'),
                'section_title': chunk_data.get('section_title', 'Unknown'),
                'page_title': chunk_data.get('page_title', 'Unknown'),
                'url': chunk_data.get('url', ''),
                'domain': chunk_data.get('domain', ''),
                'type': chunk_data.get('type', 'unknown'),
                'level': chunk_data.get('level', 3),
                'word_count': chunk_data.get('word_count', 0),
                'chunk_id': chunk_data.get('chunk_id', len(self.chunks) - 1)
            }

            self.chunk_metadata.append(metadata)

        if not self.chunks:
            print("❌ No valid chunks found")
            return False

        # Build TF-IDF vectorizer and matrix
        print("🔧 Building TF-IDF index...")

        # Enhanced TF-IDF configuration
        # Adjust parameters based on corpus size
        num_docs = len(self.chunks)

        if num_docs < 5:
            # For very small corpora, use minimal constraints
            min_df = 1
            max_df = 1.0
            ngram_range = (1, 2)  # Limit to bigrams for small corpora
        else:
            min_df = max(1, min(2, num_docs // 4))
            max_df = min(0.95, max(0.6, (num_docs - 1) / num_docs))
            ngram_range = (1, 3)

        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=ngram_range,
            sublinear_tf=True,   # Use sublinear term frequency scaling
            min_df=min_df,       # Adjust based on corpus size
            max_df=max_df        # Adjust based on corpus size
        )

        # Fit and transform
        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)

        print(f"   ✅ Processed {len(self.chunks)} chunks")
        print(f"   📊 TF-IDF matrix shape: {self.tfidf_matrix.shape}")

        # Cache the processed data
        try:
            cache_data = {
                'chunks': self.chunks,
                'chunk_metadata': self.chunk_metadata,
                'vectorizer': self.vectorizer,
                'tfidf_matrix': self.tfidf_matrix
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)

            print(f"💾 Cached processed data to {cache_file}")

        except Exception as e:
            print(f"⚠️ Failed to cache data: {e}")

        return True

    def preprocess_query(self, query: str) -> str:
        """Generic query preprocessing"""

        enhanced_query = query.lower().strip()

        # Generic technical terms expansion
        technical_expansions = {
            # Programming terms
            'function': 'function method procedure',
            'class': 'class object type',
            'api': 'api interface endpoint',
            'database': 'database db data storage',
            'server': 'server backend service',
            'client': 'client frontend application',

            # Common concepts
            'install': 'install setup configure deployment',
            'config': 'config configuration settings',
            'tutorial': 'tutorial guide example walkthrough',
            'error': 'error exception bug issue',
            'performance': 'performance optimization speed',
            'security': 'security authentication authorization',

            # Documentation terms
            'documentation': 'documentation docs guide reference',
            'example': 'example sample code snippet',
            'how to': 'how to tutorial guide steps',
        }

        # Apply expansions
        for term, expansion in technical_expansions.items():
            if term in enhanced_query:
                enhanced_query += f" {expansion}"

        # Add domain-specific terms if we can detect the domain
        if hasattr(self, 'structured_data') and self.structured_data:
            domains = self.structured_data.get('metadata', {}).get('domains', [])
            if domains:
                # Simple domain detection for common sites
                for domain in domains:
                    if 'github' in domain:
                        enhanced_query += " code repository github"
                    elif any(doc_term in domain for doc_term in ['docs', 'documentation']):
                        enhanced_query += " documentation reference guide"
                    elif 'api' in domain:
                        enhanced_query += " api endpoint method"
                    elif any(blog_term in domain for blog_term in ['blog', 'medium', 'dev']):
                        enhanced_query += " article tutorial blog post"

        return enhanced_query

    def retrieve_context(self, query: str, top_k: int = 5) -> Tuple[List[str], List[Dict]]:
        """Retrieve relevant context with enhanced scoring"""

        if not self.chunks or not hasattr(self, 'tfidf_matrix'):
            return [], []

        # Preprocess query
        enhanced_query = self.preprocess_query(query)

        # Transform query using the fitted vectorizer
        query_vector = self.vectorizer.transform([enhanced_query])

        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Apply boosting based on content type and structure
        boosted_scores = []
        for i, sim_score in enumerate(similarities):
            metadata = self.chunk_metadata[i]

            boost_factor = 1.0

            # Boost based on content type
            content_type = metadata.get('type', 'unknown')
            if content_type == 'code_example':
                boost_factor *= 1.3
            elif content_type == 'complete_section':
                boost_factor *= 1.2

            # Boost based on section level (higher level = more important)
            level = metadata.get('level', 3)
            if level <= 2:  # h1, h2
                boost_factor *= 1.2
            elif level == 3:  # h3
                boost_factor *= 1.1

            # Boost if query terms appear in title
            title = metadata.get('title', '').lower()
            query_words = query.lower().split()
            title_matches = sum(1 for word in query_words if word in title)
            if title_matches > 0:
                boost_factor *= 1 + (0.1 * title_matches)

            # Boost based on word count (prefer substantial content)
            word_count = metadata.get('word_count', 0)
            if word_count > 100:
                boost_factor *= 1.1
            elif word_count > 200:
                boost_factor *= 1.15

            boosted_score = sim_score * boost_factor
            boosted_scores.append(boosted_score)

        # Get top results
        top_indices = np.argsort(boosted_scores)[-top_k:][::-1]

        contexts = []
        metadata_list = []

        for idx in top_indices:
            if boosted_scores[idx] > 0.1:  # Minimum threshold
                contexts.append(self.chunks[idx])

                # Enhanced metadata
                meta = self.chunk_metadata[idx].copy()
                meta['similarity_score'] = similarities[idx]
                meta['boosted_score'] = boosted_scores[idx]
                metadata_list.append(meta)

        return contexts, metadata_list

    def demo_query(self, query: str, top_k: int = 5) -> str:
        """Perform a demonstration query with detailed output"""

        if not self.chunks:
            return "❌ System not initialized. Please run scrape_and_process_website() or process_structured_documents() first."

        print(f"\n🔍 Enhanced Query: {self.preprocess_query(query)}")
        print("=" * 80)

        contexts, metadata = self.retrieve_context(query, top_k)

        if not contexts:
            return "❌ No relevant documents found for this query."

        print(f"✅ Found {len(contexts)} relevant chunks:\n")

        result_text = f"✅ Found {len(contexts)} relevant chunks:\n\n"

        for i, (context, meta) in enumerate(zip(contexts, metadata), 1):
            domain = meta.get('domain', 'Unknown')
            page_title = meta.get('page_title', 'Unknown Page')
            section_title = meta.get('section_title', 'No Section')
            content_type = meta.get('type', 'unknown')
            score = meta.get('boosted_score', 0)
            base_score = meta.get('similarity_score', 0)
            word_count = meta.get('word_count', 0)

            print(f"📄 Result {i}: {page_title} - {section_title}")
            print(f"   Domain: {domain}")
            print(f"   Type: {content_type}")
            print(f"   Relevance: {score:.3f} (base: {base_score:.3f})")
            print(f"   Words: {word_count}")
            print(f"   Preview: {context[:200]}...\n")

            result_text += f"📄 Result {i}: {page_title} - {section_title}\n"
            result_text += f"   Domain: {domain}\n"
            result_text += f"   Type: {content_type}\n"
            result_text += f"   Relevance: {score:.3f} (base: {base_score:.3f})\n"
            result_text += f"   Words: {word_count}\n"
            result_text += f"   Preview: {context[:200]}...\n\n"

        return result_text

    def rag_query(self, query: str, top_k: int = 5, model: str = "llama2",
                  ollama_url: str = "http://localhost:11434") -> str:
        """Perform RAG query with Ollama integration"""

        contexts, _ = self.retrieve_context(query, top_k)

        if not contexts:
            return "No relevant information found for your query."

        # Build context
        context_text = "\n\n".join(contexts)

        # Create prompt
        prompt = f"""Based on the following information, please answer the question accurately and comprehensively.

Context information:
{context_text}

Question: {query}

Please provide a detailed answer based on the context provided. If the context doesn't contain enough information to answer the question completely, please indicate what information is missing."""

        try:
            # Query Ollama
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error querying Ollama: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return f"Error connecting to Ollama: {e}. Make sure Ollama is running with 'ollama serve'."


def main():
    """Example usage of the RAG system"""

    print("🚀 RAG System - Example Usage")
    print("=" * 40)

    # Initialize the system
    rag_system = RAGSystem()

    # Scrape a website and process it
    start_urls = [
        "https://pytorch.org/docs/stable/",  # Example: FastAPI documentation
    ]

    # Scrape and process
    success = rag_system.scrape_and_process_website(
        start_urls=start_urls,
        max_pages=100,  # Small number for testing
        output_file="data/website_docs.json",
        same_domain_only=True,
        max_depth=2
    )

    if success:
        # Test some queries
        test_queries = [
            "How to create a tensor?",
            "What is automatic differentiation?",
            "How to build neural networks?",
            "Training a model with optimizers",
            "DataLoader and datasets usage",
            "GPU acceleration with CUDA",
            "Model parallelism and distributed training"
        ]

        print(f"\n🔍 Testing {len(test_queries)} queries...")
        for query in test_queries:
            print(f"\n" + "="*60)
            print(f"Query: {query}")
            result = rag_system.demo_query(query, top_k=3)
            print(result[:500] + "..." if len(result) > 500 else result)

    else:
        print("❌ Failed to scrape and process website")

    print("\n💡 Usage Tips:")
    print("• Use scrape_and_process_website() for new websites")
    print("• Use process_structured_documents() for existing scraped data")
    print("• Use demo_query() for retrieval testing")
    print("• Use rag_query() with Ollama for full answers")


if __name__ == "__main__":
    main()