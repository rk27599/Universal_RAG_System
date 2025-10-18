"""
Enhanced Search Service - Integrates all RAG enhancements
Provides modular, composable search pipeline with reranking, hybrid search, query expansion, etc.
"""

import logging
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)


class EnhancedSearchService:
    """
    Enhanced search service integrating all RAG improvements

    Features:
    1. Reranker: Cross-encoder reranking (BGE-reranker-v2-m3)
    2. Hybrid Search: BM25 + Vector ensemble
    3. Query Expansion: LLM-based multi-query retrieval
    4. Corrective RAG: Self-correcting with relevance checks
    5. Prompt Templates: CoT, Extractive, Citation

    Privacy: All local processing except optional DuckDuckGo fallback
    """

    def __init__(
        self,
        document_service,
        enable_reranker: bool = True,
        enable_hybrid_search: bool = True,
        enable_query_expansion: bool = True,
        enable_corrective_rag: bool = False,
        enable_web_search: bool = False
    ):
        """
        Initialize enhanced search service

        Args:
            document_service: DocumentProcessingService instance
            enable_reranker: Use cross-encoder reranking
            enable_hybrid_search: Use BM25 + Vector hybrid
            enable_query_expansion: Use LLM query expansion
            enable_corrective_rag: Use corrective RAG workflow
            enable_web_search: Allow web search fallback (privacy setting)
        """
        self.document_service = document_service
        self.enable_reranker = enable_reranker
        self.enable_hybrid_search = enable_hybrid_search
        self.enable_query_expansion = enable_query_expansion
        self.enable_corrective_rag = enable_corrective_rag
        self.enable_web_search = enable_web_search

        # Initialize services (lazy loading)
        self.reranker = None
        self.bm25 = None
        self.ensemble = None
        self.query_expander = None
        self.corrective_rag = None

        logger.info(
            f"EnhancedSearchService initialized "
            f"(reranker={enable_reranker}, hybrid={enable_hybrid_search}, "
            f"expansion={enable_query_expansion}, corrective={enable_corrective_rag})"
        )

    def _init_reranker(self):
        """Lazy load reranker service"""
        if self.reranker is None and self.enable_reranker:
            try:
                from services.reranker_service import get_reranker_service
                self.reranker = get_reranker_service()
                self.reranker.load_model()
                logger.info("✅ Reranker loaded")
            except Exception as e:
                logger.warning(f"Failed to load reranker: {e}")
                self.enable_reranker = False

    def _init_bm25(self):
        """Lazy load BM25 retriever and user's index"""
        if self.bm25 is None and self.enable_hybrid_search:
            try:
                from services.bm25_retriever import BM25Retriever
                from pathlib import Path

                self.bm25 = BM25Retriever()

                # Load user's BM25 index if it exists
                user_id = self.document_service.user_id
                index_path = Path("data/bm25_indexes") / f"user_{user_id}.pkl"

                if index_path.exists():
                    self.bm25.load_index(str(index_path))
                    logger.info(f"✅ BM25 retriever loaded with {len(self.bm25.documents)} documents for user {user_id}")
                else:
                    logger.warning(f"⚠️ BM25 index not found for user {user_id} at {index_path}")
                    logger.warning("Hybrid search will be disabled. Upload documents to build BM25 index.")
                    self.enable_hybrid_search = False
            except Exception as e:
                logger.warning(f"Failed to load BM25: {e}")
                self.enable_hybrid_search = False

    def _init_ensemble(self):
        """Lazy load ensemble retriever"""
        if self.ensemble is None and self.enable_hybrid_search:
            try:
                from services.ensemble_retriever import EnsembleRetriever
                self.ensemble = EnsembleRetriever(bm25_weight=0.3, vector_weight=0.7)
                logger.info("✅ Ensemble retriever initialized")
            except Exception as e:
                logger.warning(f"Failed to load ensemble retriever: {e}")
                self.enable_hybrid_search = False

    def _init_query_expander(self):
        """Lazy load query expander"""
        if self.query_expander is None and self.enable_query_expansion:
            try:
                from services.query_expander import QueryExpander
                self.query_expander = QueryExpander(model="mistral", num_expansions=3)
                logger.info("✅ Query expander initialized")
            except Exception as e:
                logger.warning(f"Failed to load query expander: {e}")
                self.enable_query_expansion = False

    def _init_corrective_rag(self):
        """Lazy load corrective RAG"""
        if self.corrective_rag is None and self.enable_corrective_rag:
            try:
                from services.corrective_rag import CorrectiveRAG
                self.corrective_rag = CorrectiveRAG(
                    model="mistral",
                    relevance_threshold=7.0,
                    min_relevant_docs=3,
                    enable_web_search=self.enable_web_search
                )
                logger.info(f"✅ Corrective RAG initialized (web_search={self.enable_web_search})")
            except Exception as e:
                logger.warning(f"Failed to load corrective RAG: {e}")
                self.enable_corrective_rag = False

    async def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
        min_similarity: float = 0.70,
        use_reranker: Optional[bool] = None,
        use_hybrid: Optional[bool] = None,
        use_expansion: Optional[bool] = None,
        use_corrective: Optional[bool] = None
    ) -> Dict:
        """
        Enhanced search with all improvements

        Args:
            query: Search query
            top_k: Number of final results
            document_ids: Optional document filter
            min_similarity: Minimum similarity threshold
            use_reranker: Override reranker setting
            use_hybrid: Override hybrid search setting
            use_expansion: Override query expansion setting
            use_corrective: Override corrective RAG setting

        Returns:
            Dict with results, metadata, and pipeline info
        """
        # Determine which features to use
        use_reranker = use_reranker if use_reranker is not None else self.enable_reranker
        use_hybrid = use_hybrid if use_hybrid is not None else self.enable_hybrid_search
        use_expansion = use_expansion if use_expansion is not None else self.enable_query_expansion
        use_corrective = use_corrective if use_corrective is not None else self.enable_corrective_rag

        logger.info(
            f"🔍 Enhanced search: query='{query[:50]}...' | "
            f"reranker={use_reranker}, hybrid={use_hybrid}, "
            f"expansion={use_expansion}, corrective={use_corrective}"
        )

        # Track pipeline stages
        pipeline_info = {
            'original_query': query,
            'expanded_queries': [],
            'retrieval_method': 'vector',
            'reranking_applied': False,
            'corrective_applied': False,
            'web_search_used': False
        }

        try:
            # Stage 1: Query Expansion (optional)
            queries = [query]
            if use_expansion:
                self._init_query_expander()
                if self.query_expander:
                    expanded = await self.query_expander.expand_query(query)
                    queries = expanded
                    pipeline_info['expanded_queries'] = expanded[1:]  # Exclude original
                    logger.info(f"📝 Query expanded: 1 → {len(queries)} queries")

            # Stage 2: Retrieval (Vector or Hybrid)
            all_results = []

            if use_hybrid:
                # Hybrid: BM25 + Vector
                self._init_bm25()
                self._init_ensemble()

                if self.bm25 and self.ensemble:
                    pipeline_info['retrieval_method'] = 'hybrid'
                    all_results = await self._hybrid_retrieval(
                        queries,
                        top_k=100,  # Get more candidates for reranking
                        document_ids=document_ids,
                        min_similarity=min_similarity
                    )
                else:
                    # Fallback to vector-only
                    all_results = await self._vector_retrieval(
                        queries,
                        top_k=100,
                        document_ids=document_ids,
                        min_similarity=min_similarity
                    )
            else:
                # Vector-only retrieval
                all_results = await self._vector_retrieval(
                    queries,
                    top_k=100,
                    document_ids=document_ids,
                    min_similarity=min_similarity
                )

            logger.info(f"📦 Retrieved {len(all_results)} candidates")

            # Stage 3: Deduplication
            unique_results = self._deduplicate_results(all_results)
            logger.info(f"🔄 Deduplicated: {len(all_results)} → {len(unique_results)}")

            # Stage 4: Reranking (optional)
            if use_reranker and len(unique_results) > top_k:
                self._init_reranker()
                if self.reranker:
                    unique_results = self.reranker.rerank(
                        query,  # Use original query for reranking
                        unique_results,
                        top_k=top_k
                    )
                    pipeline_info['reranking_applied'] = True
                    logger.info(f"✨ Reranked to top {len(unique_results)}")

            # Take top_k
            final_results = unique_results[:top_k]

            # Stage 5: Corrective RAG (optional)
            if use_corrective and len(final_results) > 0:
                self._init_corrective_rag()
                if self.corrective_rag:
                    # Run corrective workflow
                    corrective_result = await self.corrective_rag.query(
                        query,
                        final_results
                    )

                    pipeline_info['corrective_applied'] = True
                    pipeline_info['web_search_used'] = corrective_result.get('used_web_search', False)

                    # Update results with relevance scores
                    final_results = corrective_result.get('relevant_documents', final_results)
                    logger.info(
                        f"✅ Corrective RAG applied "
                        f"(web_search={corrective_result.get('used_web_search')})"
                    )

            return {
                'results': final_results,
                'total_results': len(final_results),
                'pipeline_info': pipeline_info
            }

        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            # Fallback to basic vector search
            results = await self.document_service.search_documents(
                query,
                top_k=top_k,
                document_ids=document_ids,
                min_similarity=min_similarity
            )

            return {
                'results': results,
                'total_results': len(results),
                'pipeline_info': {
                    **pipeline_info,
                    'fallback': True,
                    'error': str(e)
                }
            }

    async def _vector_retrieval(
        self,
        queries: List[str],
        top_k: int,
        document_ids: Optional[List[int]],
        min_similarity: float
    ) -> List[Dict]:
        """Vector-only retrieval for multiple queries"""
        all_results = []

        for q in queries:
            results = await self.document_service.search_documents(
                q,
                top_k=top_k,
                document_ids=document_ids,
                min_similarity=min_similarity
            )
            all_results.extend(results)

        return all_results

    async def _hybrid_retrieval(
        self,
        queries: List[str],
        top_k: int,
        document_ids: Optional[List[int]],
        min_similarity: float
    ) -> List[Dict]:
        """Hybrid BM25 + Vector retrieval"""
        all_results = []

        # Check if BM25 is available
        if not self.bm25 or not self.bm25.bm25:
            logger.warning("BM25 index not available - falling back to vector-only retrieval")
            return await self._vector_retrieval(queries, top_k, document_ids, min_similarity)

        for q in queries:
            # 1. Vector search
            vector_results = await self.document_service.search_documents(
                q,
                top_k=top_k,
                document_ids=document_ids,
                min_similarity=min_similarity
            )

            # 2. BM25 search
            try:
                bm25_results = self.bm25.search(q, top_k=top_k, document_ids=document_ids)
                logger.info(f"📊 BM25 search returned {len(bm25_results)} results")
            except Exception as e:
                logger.warning(f"BM25 search failed: {e}")
                bm25_results = []

            # 3. Ensemble merge (Reciprocal Rank Fusion)
            if bm25_results and self.ensemble:
                try:
                    merged = self.ensemble.merge_results(bm25_results, vector_results, top_k=top_k)
                    all_results.extend(merged)
                    logger.info(f"🔀 Ensemble merged {len(bm25_results)} BM25 + {len(vector_results)} vector → {len(merged)} results")
                except Exception as e:
                    logger.warning(f"Ensemble merge failed: {e}")
                    # Fallback: combine both
                    all_results.extend(bm25_results)
                    all_results.extend(vector_results)
            else:
                # No BM25 results or no ensemble - just use vector
                all_results.extend(vector_results)

        return all_results

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Deduplicate results by chunk_id"""
        seen_ids = set()
        unique_results = []

        for result in results:
            chunk_id = result.get('chunk_id')
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)

        return unique_results

    async def search_with_template(
        self,
        query: str,
        template: str = "cot",
        top_k: int = 5,
        **search_kwargs
    ) -> Dict:
        """
        Search and return results with selected prompt template

        Args:
            query: Search query
            template: Prompt template ("cot", "extractive", "citation")
            top_k: Number of results
            **search_kwargs: Additional search parameters

        Returns:
            Dict with results and formatted prompt
        """
        # Perform search
        search_result = await self.search(query, top_k=top_k, **search_kwargs)

        # Build context from results
        results = search_result['results']
        context_parts = []

        for i, result in enumerate(results, 1):
            content = result.get('content', '')[:500]
            title = result.get('document_title', 'Document')
            section = result.get('section_path', 'N/A')

            context_parts.append(
                f"[{i}] {title} - {section}:\n{content}\n"
            )

        context = "\n".join(context_parts)

        # Build prompt with selected template
        from prompts import build_cot_prompt, build_extractive_prompt, build_citation_prompt

        if template == "cot":
            prompt = build_cot_prompt(query, context)
        elif template == "extractive":
            prompt = build_extractive_prompt(query, context)
        elif template == "citation":
            prompt = build_citation_prompt(query, context)
        else:
            # Default to CoT
            prompt = build_cot_prompt(query, context)

        return {
            **search_result,
            'prompt': prompt,
            'template': template,
            'context': context
        }


# Example usage
async def main():
    """Test enhanced search service"""
    from sqlalchemy.orm import Session
    from core.database import get_db

    # Get database session
    db = next(get_db())
    user_id = 1  # Example user

    # Initialize document service
    from services.document_service import DocumentProcessingService
    doc_service = DocumentProcessingService(db, user_id)

    # Initialize enhanced search
    enhanced_search = EnhancedSearchService(
        document_service=doc_service,
        enable_reranker=True,
        enable_hybrid_search=True,
        enable_query_expansion=True,
        enable_corrective_rag=False,  # Privacy mode
        enable_web_search=False
    )

    # Test search
    query = "How do I optimize Forcite MD simulations?"

    result = await enhanced_search.search(query, top_k=5)

    print("\n=== Enhanced Search Results ===")
    print(f"Query: {query}")
    print(f"\nPipeline:")
    for key, value in result['pipeline_info'].items():
        print(f"  {key}: {value}")

    print(f"\nResults: {len(result['results'])}")
    for i, res in enumerate(result['results'], 1):
        print(f"\n{i}. Similarity: {res.get('similarity', 0):.3f}")
        if 'reranker_score' in res:
            print(f"   Reranker: {res['reranker_score']:.3f}")
        print(f"   {res.get('document_title', 'Unknown')}")
        print(f"   {res.get('content', '')[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
