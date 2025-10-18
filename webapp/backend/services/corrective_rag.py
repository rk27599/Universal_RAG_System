"""
Corrective RAG (CRAG) Workflow - Self-correcting retrieval with LangGraph
Implements a StateGraph workflow that evaluates retrieval quality and triggers web search fallback if needed
"""

import logging
from typing import List, Dict, Optional, TypedDict, Annotated
import asyncio
import operator

logger = logging.getLogger(__name__)

# Check for LangGraph availability
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available. Install with: pip install langgraph langchain-core")


class RAGState(TypedDict):
    """State for Corrective RAG workflow"""
    query: str
    documents: Annotated[List[Dict], operator.add]  # Retrieved documents
    relevant_documents: List[Dict]  # Filtered relevant documents
    web_search_results: List[Dict]  # Optional web search results
    relevance_scores: List[float]  # Relevance scores from LLM
    final_answer: str  # Generated answer
    used_web_search: bool  # Whether web search was triggered
    error: Optional[str]  # Error message if any


class CorrectiveRAG:
    """
    Corrective RAG (CRAG) implementation with self-correction

    Workflow:
    1. Initial Retrieval: Get top-k documents from vector store
    2. Evaluate Relevance: LLM scores each document (0-10 scale)
    3. Decision: If <3 relevant docs (score ≥7) → trigger web search
    4. Web Search (optional): DuckDuckGo fallback for external knowledge
    5. Synthesize Answer: Generate final response with all relevant context

    Why Corrective RAG?
    - Handles cases where vector search returns poor results
    - Uses LLM to judge relevance before generation
    - Falls back to web search only when needed
    - Improves answer quality through self-correction

    Privacy:
    - Local LLM (Ollama) for all reasoning
    - Web search is OPTIONAL and user-controlled
    - Can disable web search for fully air-gapped operation
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "mistral",
        relevance_threshold: float = 7.0,
        min_relevant_docs: int = 3,
        enable_web_search: bool = False
    ):
        """
        Initialize Corrective RAG workflow

        Args:
            ollama_base_url: Local Ollama API URL
            model: LLM model for relevance scoring and generation
            relevance_threshold: Minimum score for relevant document (0-10 scale)
            min_relevant_docs: Minimum relevant docs before triggering web search
            enable_web_search: Allow web search fallback (default: False for privacy)
        """
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.relevance_threshold = relevance_threshold
        self.min_relevant_docs = min_relevant_docs
        self.enable_web_search = enable_web_search

        # Initialize workflow graph
        self.graph = None

        if not LANGGRAPH_AVAILABLE:
            logger.error("LangGraph not available - Corrective RAG will be disabled")
        else:
            self._build_workflow()
            logger.info(
                f"CorrectiveRAG initialized "
                f"(model={model}, threshold={relevance_threshold}, "
                f"web_search={enable_web_search})"
            )

    def _build_workflow(self):
        """Build the LangGraph StateGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            return

        # Create workflow graph
        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("evaluate_relevance", self._evaluate_relevance_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("synthesize_answer", self._synthesize_answer_node)

        # Define edges
        workflow.set_entry_point("evaluate_relevance")

        # Conditional edge: web search or direct synthesis
        workflow.add_conditional_edges(
            "evaluate_relevance",
            self._should_search_web,
            {
                "web_search": "web_search",
                "synthesize": "synthesize_answer"
            }
        )

        workflow.add_edge("web_search", "synthesize_answer")
        workflow.add_edge("synthesize_answer", END)

        # Compile graph
        self.graph = workflow.compile()

        logger.info("✅ Corrective RAG workflow compiled")

    async def query(
        self,
        query: str,
        initial_documents: List[Dict]
    ) -> Dict:
        """
        Run Corrective RAG workflow

        Args:
            query: User question
            initial_documents: Documents from initial retrieval

        Returns:
            Dict with final_answer and metadata
        """
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph not installed")

        if self.graph is None:
            raise RuntimeError("Workflow not initialized")

        try:
            # Initialize state
            initial_state = RAGState(
                query=query,
                documents=initial_documents,
                relevant_documents=[],
                web_search_results=[],
                relevance_scores=[],
                final_answer="",
                used_web_search=False,
                error=None
            )

            # Run workflow
            logger.info(f"🔄 Starting Corrective RAG workflow for query: {query[:50]}...")

            final_state = await self.graph.ainvoke(initial_state)

            logger.info(
                f"✅ Corrective RAG complete "
                f"(relevant_docs={len(final_state['relevant_documents'])}, "
                f"web_search={final_state['used_web_search']})"
            )

            return {
                'answer': final_state['final_answer'],
                'relevant_documents': final_state['relevant_documents'],
                'used_web_search': final_state['used_web_search'],
                'relevance_scores': final_state['relevance_scores'],
                'error': final_state['error']
            }

        except Exception as e:
            logger.error(f"Error in Corrective RAG workflow: {e}")
            return {
                'answer': "I encountered an error processing your question.",
                'relevant_documents': [],
                'used_web_search': False,
                'relevance_scores': [],
                'error': str(e)
            }

    async def _evaluate_relevance_node(self, state: RAGState) -> RAGState:
        """
        Node 1: Evaluate relevance of retrieved documents

        Uses local LLM to score each document on 0-10 scale
        Filters documents above threshold
        """
        logger.info("📊 Evaluating document relevance...")

        query = state['query']
        documents = state['documents']

        relevance_scores = []
        relevant_docs = []

        try:
            # Import OllamaService
            from services.ollama_service import OllamaService
            ollama = OllamaService(base_url=self.ollama_base_url)

            # Score each document
            for doc in documents:
                content = doc.get('content') or doc.get('text') or doc.get('chunk_content', '')

                # Build relevance scoring prompt
                prompt = f"""Rate the relevance of this document to the query on a scale of 0-10.

Query: {query}

Document:
{content[:500]}

Provide ONLY a number from 0-10, where:
- 0-3: Not relevant
- 4-6: Somewhat relevant
- 7-8: Relevant
- 9-10: Highly relevant

Relevance Score:"""

                # Get score from LLM
                response = await ollama.generate_async(
                    prompt=prompt,
                    model=self.model,
                    temperature=0.1,  # Low temp for consistent scoring
                    max_tokens=10
                )

                # Parse score
                try:
                    score = float(response.strip().split()[0])
                    score = max(0.0, min(10.0, score))  # Clamp to [0, 10]
                except:
                    logger.warning(f"Failed to parse relevance score: {response}")
                    score = 5.0  # Default to neutral

                relevance_scores.append(score)

                # Filter by threshold
                if score >= self.relevance_threshold:
                    relevant_docs.append({**doc, 'relevance_score': score})

            logger.info(
                f"📊 Relevance evaluation: {len(relevant_docs)}/{len(documents)} "
                f"documents above threshold ({self.relevance_threshold})"
            )

        except Exception as e:
            logger.error(f"Error evaluating relevance: {e}")
            # Fallback: keep all documents
            relevant_docs = documents
            relevance_scores = [self.relevance_threshold] * len(documents)

        # Update state
        state['relevant_documents'] = relevant_docs
        state['relevance_scores'] = relevance_scores

        return state

    def _should_search_web(self, state: RAGState) -> str:
        """
        Decision: Should we trigger web search?

        Triggers web search if:
        1. Web search is enabled
        2. Fewer than min_relevant_docs were found
        """
        num_relevant = len(state['relevant_documents'])

        if not self.enable_web_search:
            logger.info("🔒 Web search disabled (privacy mode)")
            return "synthesize"

        if num_relevant < self.min_relevant_docs:
            logger.info(
                f"🌐 Triggering web search "
                f"({num_relevant} < {self.min_relevant_docs} relevant docs)"
            )
            return "web_search"

        logger.info(f"✅ Sufficient relevant docs ({num_relevant}), skipping web search")
        return "synthesize"

    async def _web_search_node(self, state: RAGState) -> RAGState:
        """
        Node 2: Web search fallback using DuckDuckGo

        Only called if local knowledge is insufficient
        """
        logger.info("🌐 Performing web search fallback...")

        query = state['query']

        try:
            # Import web search service
            from services.web_search_fallback import WebSearchFallback

            search = WebSearchFallback()
            results = await search.search(query, max_results=3)

            if results:
                logger.info(f"✅ Web search found {len(results)} results")
                state['web_search_results'] = results
                state['used_web_search'] = True

                # Add web results to relevant documents
                for result in results:
                    state['relevant_documents'].append({
                        'content': result['snippet'],
                        'title': result['title'],
                        'source': result['link'],
                        'source_type': 'web_search',
                        'relevance_score': 8.0  # Assume web results are relevant
                    })
            else:
                logger.warning("⚠️ Web search returned no results")

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            state['error'] = f"Web search error: {str(e)}"

        return state

    async def _synthesize_answer_node(self, state: RAGState) -> RAGState:
        """
        Node 3: Generate final answer using all relevant context

        Combines local documents + web search results
        """
        logger.info("💭 Synthesizing final answer...")

        query = state['query']
        relevant_docs = state['relevant_documents']

        if not relevant_docs:
            state['final_answer'] = (
                "I couldn't find sufficient relevant information to answer your question. "
                "Please try rephrasing or providing more context."
            )
            return state

        try:
            # Build context from relevant documents
            context_parts = []
            for i, doc in enumerate(relevant_docs[:5], 1):  # Top 5
                content = doc.get('content', '')[:300]
                source = doc.get('source_type', 'document')
                title = doc.get('title', 'Document')
                context_parts.append(f"[{i}] {title} ({source}):\n{content}")

            context = "\n\n".join(context_parts)

            # Build generation prompt
            prompt = f"""Answer the following question using the provided context. If using web sources, cite them.

Context:
{context}

Question: {query}

Answer:"""

            # Generate answer with local LLM
            from services.ollama_service import OllamaService
            ollama = OllamaService(base_url=self.ollama_base_url)

            answer = await ollama.generate_async(
                prompt=prompt,
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )

            state['final_answer'] = answer.strip()

            logger.info("✅ Answer synthesized successfully")

        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            state['final_answer'] = "I encountered an error generating the answer."
            state['error'] = str(e)

        return state


# Example usage
async def main():
    """Test Corrective RAG workflow"""

    # Initialize CRAG (with web search disabled for privacy)
    crag = CorrectiveRAG(
        model="mistral",
        relevance_threshold=7.0,
        min_relevant_docs=3,
        enable_web_search=False  # Privacy mode
    )

    # Sample query and documents
    query = "How do I optimize Forcite MD simulations?"

    initial_documents = [
        {
            "id": "1",
            "content": "Forcite module provides molecular dynamics simulation capabilities.",
            "source_type": "manual"
        },
        {
            "id": "2",
            "content": "The weather is nice today.",
            "source_type": "unrelated"
        },
        {
            "id": "3",
            "content": "To optimize MD simulations, adjust timestep and cutoff parameters.",
            "source_type": "guide"
        }
    ]

    # Run workflow
    result = await crag.query(query, initial_documents)

    print("\n=== Corrective RAG Results ===")
    print(f"Query: {query}\n")
    print(f"Answer: {result['answer']}\n")
    print(f"Relevant Docs: {len(result['relevant_documents'])}")
    print(f"Used Web Search: {result['used_web_search']}")
    print(f"Relevance Scores: {result['relevance_scores']}")


if __name__ == "__main__":
    if LANGGRAPH_AVAILABLE:
        asyncio.run(main())
    else:
        print("LangGraph not available. Install with: pip install langgraph langchain-core")
