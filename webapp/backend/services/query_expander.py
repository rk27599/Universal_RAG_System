"""
Query Expansion Service - LLM-based query expansion for improved retrieval
Uses local Ollama to generate semantically similar queries
"""

import logging
from typing import List, Optional, Dict
import asyncio
import re
import json

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Query expansion using local LLM (Ollama)

    Purpose:
    - Single query → Multiple semantically similar queries
    - Retrieve with each query → More comprehensive results
    - Aggregate and deduplicate → Better coverage

    Example:
        Original: "How to optimize MD simulations?"

        Expanded:
        1. "molecular dynamics optimization techniques"
        2. "improving MD simulation performance"
        3. "best practices for MD calculations"
        4. "speeding up molecular dynamics runs"

        Benefits:
        - Captures different phrasings
        - Covers related concepts
        - Improves recall

    Privacy:
    - Uses LOCAL Ollama (no external API calls)
    - All processing stays on your machine
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "mistral",
        num_expansions: int = 3,
        temperature: float = 0.3
    ):
        """
        Initialize query expander

        Args:
            ollama_base_url: Ollama API base URL
            model: Model to use for expansion (mistral, llama2, etc.)
            num_expansions: Number of expanded queries to generate
            temperature: LLM temperature (lower = more focused)
        """
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.num_expansions = num_expansions
        self.temperature = temperature

        logger.info(
            f"QueryExpander initialized "
            f"(model={model}, expansions={num_expansions})"
        )

    async def expand_query(
        self,
        query: str,
        num_expansions: Optional[int] = None,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Expand query into multiple semantically similar queries

        Args:
            query: Original user query
            num_expansions: Number of expansions (overrides default)
            context: Optional context about the domain (e.g., "Material Studio")

        Returns:
            List of expanded queries (including original)
        """
        if not query.strip():
            return [query]

        num_exp = num_expansions or self.num_expansions

        try:
            # Build expansion prompt
            prompt = self._build_expansion_prompt(query, num_exp, context)

            # Generate expanded queries with local Ollama
            expanded_queries = await self._generate_with_ollama(prompt)

            # Parse and clean expanded queries
            queries = self._parse_expanded_queries(expanded_queries, num_exp)

            # Always include original query
            if query not in queries:
                queries.insert(0, query)

            logger.info(
                f"Query expansion: 1 → {len(queries)} queries "
                f"(original + {len(queries) - 1} expanded)"
            )

            return queries

        except Exception as e:
            logger.error(f"Error during query expansion: {e}")
            # Fallback: return original query
            return [query]

    def _build_expansion_prompt(
        self,
        query: str,
        num_expansions: int,
        context: Optional[str] = None
    ) -> str:
        """Build prompt for query expansion"""

        if context:
            context_instruction = f"\nContext: This is for {context} software."
        else:
            context_instruction = ""

        prompt = f"""You are a query expansion expert. Your task is to generate {num_expansions} alternative phrasings of the given query that capture the same intent using different words and perspectives.{context_instruction}

Original Query: "{query}"

Requirements:
1. Generate {num_expansions} semantically similar queries
2. Use different terminology and phrasings
3. Keep queries focused and relevant
4. Each query should be on a new line
5. Do NOT number the queries
6. Do NOT include explanations

Example:
Original: "How to optimize MD simulations?"

Alternative Queries:
molecular dynamics optimization techniques
improving MD simulation performance
best practices for speeding up molecular dynamics

Now generate {num_expansions} alternative queries for: "{query}"

Alternative Queries:
"""

        return prompt

    async def _generate_with_ollama(self, prompt: str) -> str:
        """
        Generate text with local Ollama

        Args:
            prompt: Expansion prompt

        Returns:
            Generated text with expanded queries
        """
        try:
            # Import OllamaService
            from services.ollama_service import OllamaService

            ollama = OllamaService()  # Uses settings.OLLAMA_BASE_URL

            # Generate with lower temperature for focused expansions
            response = await ollama.generate(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=200  # Short responses
            )

            return response

        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise

    def _parse_expanded_queries(
        self,
        response: str,
        num_expansions: int
    ) -> List[str]:
        """
        Parse LLM response to extract expanded queries

        Args:
            response: LLM generated text
            num_expansions: Expected number of expansions

        Returns:
            List of cleaned queries
        """
        queries = []

        # Split by newlines
        lines = response.strip().split('\n')

        for line in lines:
            # Clean line
            cleaned = line.strip()

            # Skip empty lines
            if not cleaned:
                continue

            # Skip lines that look like headers or explanations
            if any(skip in cleaned.lower() for skip in [
                'alternative', 'query:', 'queries:', 'example:',
                'original:', 'here are', 'generated'
            ]):
                continue

            # Remove leading numbers/bullets
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            cleaned = re.sub(r'^[-•*]\s*', '', cleaned)

            # Remove quotes
            cleaned = cleaned.strip('"\'')

            # Add if non-empty and reasonable length
            if cleaned and 5 <= len(cleaned) <= 200:
                queries.append(cleaned)

            # Stop if we have enough
            if len(queries) >= num_expansions:
                break

        # Fallback: if parsing failed, try to extract anything useful
        if not queries and response:
            # Just split by common delimiters
            for delimiter in ['\n', '.', ';']:
                parts = response.split(delimiter)
                for part in parts:
                    cleaned = part.strip().strip('"\'')
                    if 5 <= len(cleaned) <= 200:
                        queries.append(cleaned)
                        if len(queries) >= num_expansions:
                            break
                if queries:
                    break

        logger.info(f"Parsed {len(queries)} expanded queries from LLM response")

        return queries[:num_expansions]

    async def expand_and_deduplicate(
        self,
        query: str,
        num_expansions: Optional[int] = None
    ) -> List[str]:
        """
        Expand query and remove near-duplicates

        Args:
            query: Original query
            num_expansions: Number of expansions

        Returns:
            Deduplicated list of queries
        """
        expanded = await self.expand_query(query, num_expansions)

        # Simple deduplication by lowercased text
        seen = set()
        unique_queries = []

        for q in expanded:
            q_lower = q.lower().strip()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)

        logger.info(f"Deduplication: {len(expanded)} → {len(unique_queries)} unique queries")

        return unique_queries

    async def expand_with_variants(
        self,
        query: str,
        include_synonyms: bool = True,
        include_broader: bool = True,
        include_narrower: bool = True
    ) -> Dict[str, List[str]]:
        """
        Advanced expansion with different variant types

        Args:
            query: Original query
            include_synonyms: Generate synonym-based variants
            include_broader: Generate broader queries
            include_narrower: Generate more specific queries

        Returns:
            Dict with variant types and their queries
        """
        variants = {'original': [query]}

        try:
            if include_synonyms:
                prompt = self._build_synonym_prompt(query)
                response = await self._generate_with_ollama(prompt)
                variants['synonyms'] = self._parse_expanded_queries(response, 2)

            if include_broader:
                prompt = self._build_broader_prompt(query)
                response = await self._generate_with_ollama(prompt)
                variants['broader'] = self._parse_expanded_queries(response, 2)

            if include_narrower:
                prompt = self._build_narrower_prompt(query)
                response = await self._generate_with_ollama(prompt)
                variants['narrower'] = self._parse_expanded_queries(response, 2)

        except Exception as e:
            logger.error(f"Error generating variants: {e}")

        return variants

    def _build_synonym_prompt(self, query: str) -> str:
        """Build prompt for synonym-based expansion"""
        return f"""Rephrase this query using synonyms and alternative terms, keeping the same specificity:

Original: "{query}"

Generate 2 synonym-based variants (one per line, no numbering):
"""

    def _build_broader_prompt(self, query: str) -> str:
        """Build prompt for broader query expansion"""
        return f"""Generate 2 broader, more general versions of this query:

Original: "{query}"

Broader variants (one per line, no numbering):
"""

    def _build_narrower_prompt(self, query: str) -> str:
        """Build prompt for narrower query expansion"""
        return f"""Generate 2 more specific, detailed versions of this query:

Original: "{query}"

More specific variants (one per line, no numbering):
"""


# Example usage
async def main():
    """Test query expansion"""
    expander = QueryExpander(model="mistral", num_expansions=3)

    query = "How do I optimize molecular dynamics simulations?"

    print(f"Original Query: {query}\n")

    # Basic expansion
    expanded = await expander.expand_query(query)

    print("=== Expanded Queries ===")
    for i, q in enumerate(expanded, 1):
        marker = "(original)" if i == 1 else "(expanded)"
        print(f"{i}. {q} {marker}")

    # Advanced expansion with variants
    print("\n=== Query Variants ===")
    variants = await expander.expand_with_variants(
        query,
        include_synonyms=True,
        include_broader=True,
        include_narrower=True
    )

    for variant_type, queries in variants.items():
        print(f"\n{variant_type.upper()}:")
        for q in queries:
            print(f"  - {q}")


if __name__ == "__main__":
    asyncio.run(main())
