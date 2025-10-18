"""
BM25 Retriever - Keyword-based retrieval for hybrid search
Implements BM25 algorithm for sparse retrieval (complements dense vector search)
"""

import logging
from typing import List, Dict, Optional
import pickle
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Check for rank_bm25 availability
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank_bm25 not available. Install with: pip install rank-bm25")


class BM25Retriever:
    """
    BM25 keyword-based retriever for sparse retrieval

    Why BM25?
    - Captures exact keyword matches (e.g., "Forcite module", "MD simulation")
    - Complements semantic vector search
    - Fast and lightweight
    - Works well for technical terminology

    Use Case:
    - User asks: "What is the Forcite module?"
    - BM25: Finds exact mentions of "Forcite" keyword
    - Vector: Finds semantically similar concepts
    - Hybrid: Combines both for best results
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25
    ):
        """
        Initialize BM25 retriever

        Args:
            k1: Term frequency saturation (1.2-2.0 typical)
            b: Document length normalization (0.75 typical)
            epsilon: Floor value for IDF (0.25 typical)
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_texts: List[str] = []
        self.corpus_metadata: List[Dict] = []

        if not BM25_AVAILABLE:
            logger.error("rank_bm25 not available - BM25 retrieval will be disabled")
        else:
            logger.info(f"BM25Retriever initialized (k1={k1}, b={b})")

    def index_documents(self, documents: List[Dict]):
        """
        Index documents for BM25 search

        Args:
            documents: List of dicts with 'text'/'content' and metadata

        Note: This builds the BM25 index from scratch
        Call this when documents are added/updated
        """
        if not BM25_AVAILABLE:
            raise RuntimeError("rank_bm25 not installed. Run: pip install rank-bm25")

        logger.info(f"Indexing {len(documents)} documents for BM25...")

        # Extract texts
        self.corpus_texts = []
        self.corpus_metadata = []

        for doc in documents:
            # Get text content
            text = doc.get('content') or doc.get('text') or doc.get('chunk_content', '')

            if text:
                self.corpus_texts.append(str(text))
                self.corpus_metadata.append(doc)
            else:
                logger.warning(f"Document {doc.get('id', 'unknown')} has no text content")

        if not self.corpus_texts:
            logger.warning("No valid documents to index")
            return

        # Tokenize documents (simple whitespace tokenization)
        tokenized_corpus = [doc.lower().split() for doc in self.corpus_texts]

        # Build BM25 index
        self.bm25 = BM25Okapi(
            tokenized_corpus,
            k1=self.k1,
            b=self.b,
            epsilon=self.epsilon
        )

        logger.info(f"✅ BM25 index built with {len(self.corpus_texts)} documents")

    def search(
        self,
        query: str,
        top_k: int = 20,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Search using BM25 algorithm

        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum BM25 score threshold

        Returns:
            List of documents with BM25 scores
        """
        if self.bm25 is None:
            logger.warning("BM25 index not built. Call index_documents() first.")
            return []

        if not query.strip():
            return []

        try:
            # Tokenize query
            tokenized_query = query.lower().split()

            # Get BM25 scores for all documents
            scores = self.bm25.get_scores(tokenized_query)

            # Combine documents with scores
            scored_docs = []
            for i, score in enumerate(scores):
                if score >= min_score:
                    doc = self.corpus_metadata[i].copy()
                    doc['bm25_score'] = float(score)
                    scored_docs.append((float(score), doc))

            # Sort by score (descending)
            scored_docs.sort(key=lambda x: x[0], reverse=True)

            # Return top_k
            top_docs = [doc for _, doc in scored_docs[:top_k]]

            if top_docs:
                logger.info(
                    f"BM25 search: {len(top_docs)} results "
                    f"(top score: {scored_docs[0][0]:.2f})"
                )

            return top_docs

        except Exception as e:
            logger.error(f"Error during BM25 search: {e}")
            return []

    def get_top_n(
        self,
        query: str,
        n: int = 20
    ) -> List[str]:
        """
        Get top-n document texts (without metadata)

        Args:
            query: Search query
            n: Number of results

        Returns:
            List of document texts
        """
        if self.bm25 is None:
            return []

        tokenized_query = query.lower().split()
        top_n_docs = self.bm25.get_top_n(tokenized_query, self.corpus_texts, n=n)

        return top_n_docs

    def save_index(self, path: str):
        """
        Save BM25 index to disk

        Args:
            path: File path to save index
        """
        if self.bm25 is None:
            logger.warning("No BM25 index to save")
            return

        try:
            index_data = {
                'bm25': self.bm25,
                'corpus_texts': self.corpus_texts,
                'corpus_metadata': self.corpus_metadata,
                'k1': self.k1,
                'b': self.b,
                'epsilon': self.epsilon
            }

            with open(path, 'wb') as f:
                pickle.dump(index_data, f)

            logger.info(f"✅ BM25 index saved to {path}")

        except Exception as e:
            logger.error(f"Error saving BM25 index: {e}")

    def load_index(self, path: str):
        """
        Load BM25 index from disk

        Args:
            path: File path to load index from
        """
        try:
            with open(path, 'rb') as f:
                index_data = pickle.load(f)

            self.bm25 = index_data['bm25']
            self.corpus_texts = index_data['corpus_texts']
            self.corpus_metadata = index_data['corpus_metadata']
            self.k1 = index_data['k1']
            self.b = index_data['b']
            self.epsilon = index_data['epsilon']

            logger.info(
                f"✅ BM25 index loaded from {path} "
                f"({len(self.corpus_texts)} documents)"
            )

        except Exception as e:
            logger.error(f"Error loading BM25 index: {e}")

    def update_document(self, doc_id: str, new_text: str, metadata: Dict):
        """
        Update a single document in the index

        Note: Currently rebuilds entire index (for simplicity)
        For production, consider incremental indexing

        Args:
            doc_id: Document identifier
            new_text: Updated document text
            metadata: Updated metadata
        """
        # Find and update document
        for i, doc in enumerate(self.corpus_metadata):
            if doc.get('id') == doc_id:
                self.corpus_texts[i] = new_text
                self.corpus_metadata[i] = metadata
                break

        # Rebuild index
        docs = [
            {**meta, 'content': text}
            for text, meta in zip(self.corpus_texts, self.corpus_metadata)
        ]
        self.index_documents(docs)

    def get_stats(self) -> Dict:
        """
        Get BM25 index statistics

        Returns:
            Dictionary with index stats
        """
        if self.bm25 is None:
            return {'indexed': False}

        return {
            'indexed': True,
            'num_documents': len(self.corpus_texts),
            'avg_doc_length': self.bm25.avgdl,
            'k1': self.k1,
            'b': self.b,
            'epsilon': self.epsilon
        }


# Example usage
if __name__ == "__main__":
    # Test BM25 retriever
    bm25 = BM25Retriever()

    # Sample documents
    documents = [
        {
            "id": "1",
            "content": "Forcite module provides molecular dynamics simulation tools for optimization.",
            "source": "manual"
        },
        {
            "id": "2",
            "content": "MD simulations can be optimized by adjusting timestep and cutoff parameters.",
            "source": "guide"
        },
        {
            "id": "3",
            "content": "The DMol3 module is used for quantum mechanical calculations.",
            "source": "manual"
        },
        {
            "id": "4",
            "content": "To improve MD performance, use GPU acceleration and efficient force fields.",
            "source": "tutorial"
        },
        {
            "id": "5",
            "content": "Forcite supports various ensembles like NVE, NVT, and NPT for MD simulations.",
            "source": "reference"
        }
    ]

    # Index documents
    bm25.index_documents(documents)

    # Search
    query = "Forcite molecular dynamics optimization"
    results = bm25.search(query, top_k=3)

    print("\n=== BM25 Search Results ===")
    print(f"Query: {query}\n")

    for i, doc in enumerate(results, 1):
        score = doc.get('bm25_score', 0)
        text = doc.get('content', '')
        source = doc.get('source', 'unknown')
        print(f"{i}. Score: {score:.2f} | Source: {source}")
        print(f"   {text}\n")

    # Stats
    stats = bm25.get_stats()
    print("=== Index Stats ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
