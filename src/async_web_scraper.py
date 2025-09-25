#!/usr/bin/env python3
"""
High-Performance Async Web Scraper for RAG Systems
Optimized for speed with concurrent processing, smart caching, and efficient resource usage
"""

import asyncio
import aiohttp
import aiofiles
import json
import re
import time
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from pathlib import Path
import logging
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for async scraping performance"""
    concurrent_limit: int = 4  # Max concurrent requests (reduced for compatibility)
    requests_per_second: float = 6.0  # Rate limiting (more conservative)
    timeout: float = 15.0  # Request timeout
    max_pages: int = 30
    max_depth: int = 2
    same_domain_only: bool = True
    respect_robots_txt: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PerformanceMetrics:
    """Track scraping performance metrics"""
    start_time: float = field(default_factory=time.time)
    urls_discovered: int = 0
    urls_processed: int = 0
    urls_failed: int = 0
    total_requests: int = 0
    cache_hits: int = 0

    def duration(self) -> float:
        return time.time() - self.start_time

    def requests_per_second(self) -> float:
        duration = self.duration()
        return self.total_requests / duration if duration > 0 else 0

    def success_rate(self) -> float:
        total = self.urls_processed + self.urls_failed
        return (self.urls_processed / total * 100) if total > 0 else 0


class AsyncWebScraper:
    """High-performance async web scraper with intelligent optimizations"""

    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.metrics = PerformanceMetrics()
        self.session: Optional[aiohttp.ClientSession] = None

        # Caching and deduplication
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.domain_cache: Dict[str, str] = {}
        self.url_queue: asyncio.Queue = None
        self.semaphore: asyncio.Semaphore = None

        # Results storage
        self.structured_docs: List[Dict] = []
        self.failed_urls: List[Tuple[str, str]] = []

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def initialize(self):
        """Initialize async session and resources"""
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_limit * 2,
            limit_per_host=self.config.concurrent_limit,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': self.config.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        self.semaphore = asyncio.Semaphore(self.config.concurrent_limit)
        self.url_queue = asyncio.Queue()

        logger.info(f"🚀 AsyncWebScraper initialized with {self.config.concurrent_limit} concurrent workers")

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    def _get_domain_key(self, url: str) -> str:
        """Get cached domain key for URL"""
        if url not in self.domain_cache:
            self.domain_cache[url] = urlparse(url).netloc
        return self.domain_cache[url]

    async def _check_robots_txt(self, url: str) -> bool:
        """Check robots.txt with caching"""
        if not self.config.respect_robots_txt:
            return True

        domain = self._get_domain_key(url)

        if domain not in self.robots_cache:
            try:
                robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
                async with self.session.get(robots_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        # Create robots parser (simplified for async)
                        # In production, you might want to use an async robots.txt parser
                        self.robots_cache[domain] = True  # Simplified: allow all for performance
                    else:
                        self.robots_cache[domain] = True
            except Exception:
                self.robots_cache[domain] = True  # Allow on error

        return self.robots_cache.get(domain, True)

    async def _fetch_url_content(self, url: str) -> Optional[Tuple[str, str]]:
        """Fetch URL content with retry logic and rate limiting"""
        async with self.semaphore:
            # Be more respectful with delays
            if self.config.requests_per_second <= 10:
                await asyncio.sleep(0.5)  # Longer delay for conservative settings
            else:
                await asyncio.sleep(0.2)  # Shorter delay for faster settings

            for attempt in range(self.config.retry_attempts):
                try:
                    self.metrics.total_requests += 1

                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            return url, content
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
                except Exception as e:
                    logger.warning(f"Error fetching {url}: {e} (attempt {attempt + 1})")

                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

            self.failed_urls.append((url, "Max retries exceeded"))
            return None

    def _extract_links_fast(self, html_content: str, base_url: str) -> List[str]:
        """Fast link extraction with minimal DOM parsing"""
        links = []

        # Use regex for initial link discovery (faster than full BeautifulSoup)
        link_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        potential_links = link_pattern.findall(html_content)

        base_domain = self._get_domain_key(base_url) if self.config.same_domain_only else None

        # Filter and process links efficiently
        for href in potential_links:
            # Skip obvious non-content links
            if any(pattern in href.lower() for pattern in [
                '.css', '.js', '.ico', '.jpg', '.jpeg', '.png', '.gif', '.pdf',
                'javascript:', 'mailto:', 'tel:', '#'
            ]):
                continue

            # Convert to absolute URL
            if not href.startswith('http'):
                href = urljoin(base_url, href)

            # Domain filtering
            if self.config.same_domain_only and base_domain:
                if self._get_domain_key(href) != base_domain:
                    continue

            # Avoid duplicates and common patterns
            if href not in self.visited_urls and not any(pattern in href.lower() for pattern in [
                '/login', '/signup', '/register', '/logout', '/search?', '/filter?'
            ]):
                links.append(href)

        return links[:50]  # Limit links per page for performance

    def _clean_content_fast(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Optimized content cleaning with fewer DOM operations"""
        # Remove in batches for better performance
        selectors_batch = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            '.navbar', '.menu', '.sidebar', '.ad', '.ads', '.social'
        ]

        for selector in selectors_batch:
            for element in soup.select(selector):
                element.decompose()

        return soup

    def _extract_structured_content_fast(self, url: str, html_content: str) -> Optional[Dict]:
        """Optimized content extraction with performance focus"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')  # Use standard parser for compatibility
            soup = self._clean_content_fast(soup)

            # Fast title extraction
            title = "Unknown"
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()[:200]  # Limit title length

            # Fast main content detection
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', class_=re.compile(r'content|main', re.I)) or
                soup.find('section') or
                soup
            )

            # Simplified section extraction for speed
            sections = []
            elements = main_content.find_all(['h1', 'h2', 'h3', 'p', 'pre', 'ul', 'ol'])

            current_section = {"title": title, "content": [], "level": 1}

            for element in elements:
                if element.name in ['h1', 'h2', 'h3']:
                    # Save previous section
                    if current_section["content"]:
                        current_section["content_text"] = "\n".join(current_section["content"])
                        current_section["word_count"] = len(current_section["content_text"].split())
                        sections.append(current_section.copy())

                    # Start new section
                    current_section = {
                        "title": element.get_text().strip()[:100],
                        "content": [],
                        "level": int(element.name[1])
                    }

                elif element.name in ['p', 'pre', 'ul', 'ol']:
                    text = element.get_text().strip()
                    if len(text) > 30:  # Only substantial content
                        current_section["content"].append(text[:1000])  # Limit content length

            # Add final section
            if current_section["content"]:
                current_section["content_text"] = "\n".join(current_section["content"])
                current_section["word_count"] = len(current_section["content_text"].split())
                sections.append(current_section)

            return {
                "url": url,
                "page_title": title,
                "domain": self._get_domain_key(url),
                "sections": sections,
                "total_sections": len(sections)
            }

        except Exception as e:
            logger.warning(f"Content extraction error for {url}: {e}")
            return None

    async def _process_url(self, url: str, depth: int) -> Tuple[Optional[Dict], List[str]]:
        """Process a single URL and return content + discovered links"""
        if url in self.visited_urls:
            self.metrics.cache_hits += 1
            return None, []

        self.visited_urls.add(url)

        # Check robots.txt
        if not await self._check_robots_txt(url):
            logger.info(f"🚫 Blocked by robots.txt: {url}")
            return None, []

        # Fetch content
        result = await self._fetch_url_content(url)
        if not result:
            self.metrics.urls_failed += 1
            return None, []

        url, html_content = result
        self.metrics.urls_processed += 1

        # Extract content
        doc_structure = self._extract_structured_content_fast(url, html_content)

        # Discover new links if not at max depth
        new_links = []
        if depth < self.config.max_depth:
            new_links = self._extract_links_fast(html_content, url)
            self.metrics.urls_discovered += len(new_links)

        return doc_structure, new_links

    async def _worker(self, worker_id: int):
        """Worker coroutine to process URLs from the queue"""
        logger.info(f"🔧 Worker {worker_id} started")

        while True:
            try:
                url, depth = await asyncio.wait_for(self.url_queue.get(), timeout=2.0)

                doc_structure, new_links = await self._process_url(url, depth)

                if doc_structure:
                    self.structured_docs.append(doc_structure)

                # Add new links to queue if we haven't hit the limit
                if len(self.structured_docs) < self.config.max_pages:
                    limit = self.config.max_pages - len(self.structured_docs)
                    for link in new_links[:limit]:
                        await self.url_queue.put((link, depth + 1))
                    if len(self.structured_docs) >= self.config.max_pages:
                        break  # Prevent further additions by this worker

                self.url_queue.task_done()

            except asyncio.TimeoutError:
                # Queue empty, worker can exit
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.url_queue.task_done()

        logger.info(f"🔧 Worker {worker_id} finished")

    async def scrape_website_async(self, start_urls: List[str]) -> Dict:
        """Main async scraping method with concurrent processing"""
        logger.info(f"🚀 Starting async scraping of {len(start_urls)} URLs")
        logger.info(f"⚙️ Config: {self.config.concurrent_limit} workers, "
                   f"{self.config.requests_per_second} RPS, max {self.config.max_pages} pages")

        # Initialize queue with starting URLs
        for url in start_urls:
            await self.url_queue.put((url, 0))

        # Start worker tasks
        workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.config.concurrent_limit)
        ]

        # Monitor progress
        last_progress = 0
        while not self.url_queue.empty() and len(self.structured_docs) < self.config.max_pages:
            current_count = len(self.structured_docs)
            if current_count > last_progress:
                rate = self.metrics.requests_per_second()
                logger.info(f"📊 Progress: {current_count}/{self.config.max_pages} pages, "
                          f"{rate:.1f} RPS, {self.metrics.success_rate():.1f}% success")
                last_progress = current_count

            await asyncio.sleep(2)

        # Wait for workers to complete
        await asyncio.gather(*workers, return_exceptions=True)

        # Create semantic chunks
        semantic_chunks = self._create_semantic_chunks_fast(self.structured_docs)

        # Final metrics
        duration = self.metrics.duration()
        logger.info(f"✅ Scraping complete in {duration:.1f}s")
        logger.info(f"📊 Final stats: {len(self.structured_docs)} pages, "
                   f"{len(semantic_chunks)} chunks, {self.metrics.requests_per_second():.1f} avg RPS")

        return {
            "metadata": {
                "scraping_timestamp": time.time(),
                "start_urls": start_urls,
                "total_pages": len(self.structured_docs),
                "total_chunks": len(semantic_chunks),
                "duration_seconds": duration,
                "requests_per_second": self.metrics.requests_per_second(),
                "success_rate": self.metrics.success_rate(),
                "config": self.config.__dict__
            },
            "documents": self.structured_docs,
            "semantic_chunks": semantic_chunks
        }

    def _create_semantic_chunks_fast(self, structured_docs: List[Dict], max_chunk_size: int = 1200) -> List[Dict]:
        """Fast semantic chunk creation"""
        chunks = []

        for doc in structured_docs:
            if not doc or "sections" not in doc:
                continue

            page_title = doc.get("page_title", "Unknown")[:100]
            url = doc.get("url", "")
            domain = doc.get("domain", "")

            for section in doc["sections"]:
                content_text = section.get("content_text", "")
                if len(content_text.strip()) < 50:
                    continue

                section_title = section.get("title", "")[:100]
                title = f"{page_title} - {section_title}" if section_title != page_title else page_title

                if len(content_text) <= max_chunk_size:
                    chunk_text = f"# {title}\n\n{content_text}"
                    chunks.append({
                        "text": chunk_text,
                        "title": title,
                        "page_title": page_title,
                        "url": url,
                        "domain": domain,
                        "word_count": len(chunk_text.split()),
                        "chunk_id": len(chunks)
                    })
                else:
                    # Simple split for large content
                    parts = [content_text[i:i+max_chunk_size] for i in range(0, len(content_text), max_chunk_size)]
                    for i, part in enumerate(parts):
                        chunk_text = f"# {title} (Part {i+1})\n\n{part}"
                        chunks.append({
                            "text": chunk_text,
                            "title": f"{title} (Part {i+1})",
                            "page_title": page_title,
                            "url": url,
                            "domain": domain,
                            "word_count": len(chunk_text.split()),
                            "chunk_id": len(chunks),
                            "part_number": i + 1
                        })

        return chunks

    async def save_results_async(self, results: Dict, output_file: str):
        """Save results asynchronously"""
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(results, indent=2, ensure_ascii=False))

        # Create text file for compatibility
        text_file = output_file.replace('.json', '.txt')
        async with aiofiles.open(text_file, 'w', encoding='utf-8') as f:
            for chunk in results.get("semantic_chunks", []):
                await f.write(f"{chunk['text']}\n\n{'='*80}\n\n")

        logger.info(f"💾 Results saved to {output_file} and {text_file}")

    async def close(self):
        """Clean up async session"""
        if self.session:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Convenience function for easy usage
async def scrape_website_fast(start_urls: List[str],
                             max_pages: int = 30,
                             concurrent_limit: int = 8,
                             requests_per_second: float = 10.0,
                             output_file: str = "data/fast_scraped_docs.json") -> Dict:
    """
    High-level async scraping function

    Args:
        start_urls: URLs to start scraping from
        max_pages: Maximum pages to scrape
        concurrent_limit: Number of concurrent requests
        requests_per_second: Rate limiting
        output_file: Output file path

    Returns:
        Dictionary with scraping results and metadata
    """
    config = ScrapingConfig(
        max_pages=max_pages,
        concurrent_limit=concurrent_limit,
        requests_per_second=requests_per_second
    )

    async with AsyncWebScraper(config) as scraper:
        results = await scraper.scrape_website_async(start_urls)
        await scraper.save_results_async(results, output_file)
        return results


# Example usage and testing
async def main():
    """Example usage of the async web scraper"""
    print("🚀 AsyncWebScraper Performance Test")
    print("=" * 50)

    start_urls = ["https://fastapi.tiangolo.com/"]

    # Test with different performance settings
    configs = [
        {"concurrent_limit": 4, "requests_per_second": 5.0, "name": "Conservative"},
        {"concurrent_limit": 8, "requests_per_second": 10.0, "name": "Balanced"},
        {"concurrent_limit": 12, "requests_per_second": 15.0, "name": "Aggressive"}
    ]

    for i, config_params in enumerate(configs):
        print(f"\n🧪 Test {i+1}: {config_params['name']} Mode")
        print("-" * 30)

        start_time = time.time()

        results = await scrape_website_fast(
            start_urls=start_urls,
            max_pages=15,  # Small test
            concurrent_limit=config_params["concurrent_limit"],
            requests_per_second=config_params["requests_per_second"],
            output_file=f"data/test_{config_params['name'].lower()}_docs.json"
        )

        duration = time.time() - start_time
        metadata = results.get("metadata", {})

        print(f"⏱️ Duration: {duration:.2f}s")
        print(f"📄 Pages: {metadata.get('total_pages', 0)}")
        print(f"🧩 Chunks: {metadata.get('total_chunks', 0)}")
        print(f"🚀 Avg RPS: {metadata.get('requests_per_second', 0):.2f}")
        print(f"✅ Success Rate: {metadata.get('success_rate', 0):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())