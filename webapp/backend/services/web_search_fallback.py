"""
Web Search Fallback - DuckDuckGo search for corrective RAG
Only used when local knowledge is insufficient (privacy-preserving fallback)
"""

import logging
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)

# Check for duckduckgo_search availability
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("duckduckgo_search not available. Install with: pip install duckduckgo-search")


class WebSearchFallback:
    """
    Web search fallback using DuckDuckGo

    Privacy Considerations:
    - Only used when local knowledge is insufficient
    - User-controlled (can be disabled completely)
    - Uses DuckDuckGo (privacy-focused search engine)
    - No API keys or tracking required
    - Rate-limited to prevent abuse

    Use Cases:
    - Query about recent events (post-training cutoff)
    - Query outside domain of uploaded documents
    - Query where vector search returns no good matches

    Disable for Air-Gapped Operation:
    - Set enable_web_search=False in CorrectiveRAG
    - System will work entirely offline
    """

    def __init__(
        self,
        max_results: int = 3,
        timeout: int = 10,
        region: str = "wt-wt",  # Worldwide
        safesearch: str = "moderate"
    ):
        """
        Initialize web search fallback

        Args:
            max_results: Maximum search results to return
            timeout: Search timeout in seconds
            region: Search region (wt-wt = worldwide)
            safesearch: Safe search level (off, moderate, strict)
        """
        self.max_results = max_results
        self.timeout = timeout
        self.region = region
        self.safesearch = safesearch

        if not DDGS_AVAILABLE:
            logger.error("duckduckgo_search not available - web search will be disabled")
        else:
            logger.info(
                f"WebSearchFallback initialized "
                f"(max_results={max_results}, region={region})"
            )

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search the web using DuckDuckGo

        Args:
            query: Search query
            max_results: Override default max_results

        Returns:
            List of search results with title, snippet, link
        """
        if not DDGS_AVAILABLE:
            logger.error("DuckDuckGo search not available")
            return []

        if not query.strip():
            return []

        max_res = max_results or self.max_results

        try:
            logger.info(f"🔍 Searching DuckDuckGo: {query[:50]}...")

            # Run search in thread pool (DDGS is synchronous)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._search_sync,
                query,
                max_res
            )

            logger.info(f"✅ Web search returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    def _search_sync(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """
        Synchronous search (called via executor)

        Args:
            query: Search query
            max_results: Max results

        Returns:
            List of search results
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    max_results=max_results
                ))

                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'title': result.get('title', 'No Title'),
                        'snippet': result.get('body', ''),
                        'link': result.get('href', ''),
                        'source_type': 'web_search'
                    })

                return formatted_results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    async def search_with_fallback(
        self,
        query: str,
        max_results: Optional[int] = None,
        fallback_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Search with fallback query if first search fails

        Args:
            query: Primary search query
            max_results: Max results
            fallback_query: Alternative query if primary fails

        Returns:
            Search results
        """
        # Try primary query
        results = await self.search(query, max_results)

        # If no results and fallback provided, try fallback
        if not results and fallback_query:
            logger.info(f"🔄 Trying fallback query: {fallback_query[:50]}...")
            results = await self.search(fallback_query, max_results)

        return results

    async def search_news(
        self,
        query: str,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for recent news articles

        Args:
            query: Search query
            max_results: Max results

        Returns:
            List of news results
        """
        if not DDGS_AVAILABLE:
            logger.error("DuckDuckGo search not available")
            return []

        max_res = max_results or self.max_results

        try:
            logger.info(f"📰 Searching DuckDuckGo News: {query[:50]}...")

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._search_news_sync,
                query,
                max_res
            )

            logger.info(f"✅ News search returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"News search error: {e}")
            return []

    def _search_news_sync(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Synchronous news search"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    max_results=max_results
                ))

                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'title': result.get('title', 'No Title'),
                        'snippet': result.get('body', ''),
                        'link': result.get('url', ''),
                        'date': result.get('date', ''),
                        'source': result.get('source', ''),
                        'source_type': 'web_news'
                    })

                return formatted_results

        except Exception as e:
            logger.error(f"DuckDuckGo news search failed: {e}")
            return []

    async def verify_url_exists(self, url: str) -> bool:
        """
        Verify that a URL is accessible

        Args:
            url: URL to check

        Returns:
            True if URL is accessible
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=self.timeout) as response:
                    return response.status == 200

        except Exception as e:
            logger.warning(f"URL verification failed for {url}: {e}")
            return False


# Example usage
async def main():
    """Test web search fallback"""

    search = WebSearchFallback(max_results=3)

    # Test query
    query = "Material Studio Forcite module molecular dynamics"

    print(f"Searching: {query}\n")

    # Regular search
    results = await search.search(query)

    print("=== Web Search Results ===")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet'][:100]}...")
        print(f"   {result['link']}\n")

    # News search
    news_results = await search.search_news("Materials Studio software")

    print("=== News Results ===")
    for i, result in enumerate(news_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Source: {result.get('source', 'Unknown')}")
        print(f"   Date: {result.get('date', 'Unknown')}\n")


if __name__ == "__main__":
    if DDGS_AVAILABLE:
        asyncio.run(main())
    else:
        print("DuckDuckGo search not available. Install with: pip install duckduckgo-search")
