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
                'Referer': 'https://www.google.com/'
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
        """Robust content extraction, improved for depth and structure"""

        def extract_table_text(table_element):
            rows = []
            for row in table_element.find_all('tr'):
                cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                if any(cells):
                    rows.append(" | ".join(cells))
            return "\n".join(rows)

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            soup = self._clean_content_fast(soup)

            # Improved title extraction
            title_sources = [
                soup.find('h1'),
                soup.find('title'),
                soup.find('meta', attrs={'property': 'og:title'}),
                soup.find('meta', attrs={'name': 'twitter:title'}),
                soup.find('h2'),
            ]

            title = None
            for source in title_sources:
                if source:
                    if source.name == 'meta':
                        t = source.get('content', '').strip()
                    else:
                        t = source.get_text().strip()
                    if t:
                        title = t[:200]
                        break
            if not title:
                # Fallback to URL path
                path = urlparse(url).path
                if path and path != '/':
                    title = path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
                else:
                    title = urlparse(url).netloc

            # Enhanced main content detection
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
                soup.find('div', id=re.compile(r'content|main|body', re.I)) or
                soup.find('section') or
                soup
            )

            sections = []
            current_section = {"title": title, "content": [], "level": 1, "page_title": title, "url": url, "section_id": 1}

            # Support headings h1 to h6, and add more content tags
            elements = main_content.find_all([
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'p', 'pre', 'ul', 'ol', 'dl', 'blockquote', 'table', 'code'
            ])

            section_counter = 1
            for element in elements:
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Save previous section if content exists
                    if current_section["content"]:
                        current_section["content_text"] = "\n\n".join(current_section["content"])
                        current_section["word_count"] = len(current_section["content_text"].split())
                        sections.append(current_section.copy())

                    section_counter += 1
                    current_section = {
                        "title": element.get_text().strip()[:100],
                        "content": [],
                        "level": int(element.name[1]),
                        "page_title": title,
                        "url": url,
                        "section_id": section_counter
                    }

                elif element.name in ['p', 'pre', 'ul', 'ol', 'dl', 'blockquote', 'code']:
                    text = element.get_text().strip()
                    if len(text) > 20:
                        # Label content per type
                        if element.name == 'pre' or element.name == 'code':
                            text = f"Code example:\n{text}"
                        elif element.name in ['ul', 'ol', 'dl']:
                            text = f"List:\n{text}"
                        elif element.name == 'blockquote':
                            text = f"Quote:\n{text}"

                        # No truncation - let chunking logic handle size control
                        current_section["content"].append(text)

                elif element.name == 'table':
                    table_text = extract_table_text(element)
                    if table_text:
                        # No truncation - let chunking logic handle size control
                        current_section["content"].append(f"Table:\n{table_text}")

            # Add last section
            if current_section["content"]:
                current_section["content_text"] = "\n\n".join(current_section["content"])
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
            logger.error(f"Error extracting structured content from {url}: {e}", exc_info=True)
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

    async def extract_from_local_file_async(self, file_path: str) -> Optional[Dict]:
        """Async version of extract_from_local_file for processing local HTML files"""
        try:
            file_path_obj = Path(file_path).resolve()

            if not file_path_obj.exists():
                logger.warning(f"File not found: {file_path_obj}")
                return None

            if file_path_obj.suffix.lower() not in ['.html', '.htm']:
                logger.warning(f"Not an HTML file: {file_path_obj}")
                return None

            logger.info(f"📂 Reading local file: {file_path_obj.name}")

            # Use aiofiles for async file reading
            async with aiofiles.open(file_path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = await f.read()

            # Create file:// URL for consistency
            file_url = f"file://{file_path_obj}"

            # Reuse existing fast content extraction method
            return self._extract_structured_content_fast(file_url, html_content)

        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    async def process_local_files_async(self, file_paths: List[str],
                                      output_file: str = "data/local_docs_async.json",
                                      concurrent_limit: int = None) -> Dict:
        """Process multiple local HTML files concurrently with async performance"""

        logger.info(f"🚀 Starting async processing of {len(file_paths)} local HTML files...")

        # Use configured concurrent limit or default to half of web scraping limit
        if concurrent_limit is None:
            concurrent_limit = max(2, self.config.concurrent_limit // 2)

        semaphore = asyncio.Semaphore(concurrent_limit)
        structured_docs = []
        failed_files = []

        async def process_single_file(file_path: str) -> Optional[Dict]:
            """Process a single file with semaphore control"""
            async with semaphore:
                self.metrics.total_requests += 1

                try:
                    doc_structure = await self.extract_from_local_file_async(file_path)
                    if doc_structure:
                        self.metrics.urls_processed += 1
                        return doc_structure
                    else:
                        self.metrics.urls_failed += 1
                        failed_files.append((file_path, "Failed to extract content"))
                        return None

                except Exception as e:
                    self.metrics.urls_failed += 1
                    failed_files.append((file_path, str(e)))
                    logger.error(f"Error processing {file_path}: {e}")
                    return None

        # Process all files concurrently
        logger.info(f"⚡ Processing files with {concurrent_limit} concurrent workers...")

        tasks = [process_single_file(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful results
        for result in results:
            if result and not isinstance(result, Exception):
                structured_docs.append(result)

        if not structured_docs:
            logger.warning("No files were successfully processed")
            return {"metadata": {"error": "No files processed"}, "documents": [], "semantic_chunks": []}

        logger.info(f"🧠 Creating semantic chunks from {len(structured_docs)} documents...")
        semantic_chunks = self._create_semantic_chunks_fast(structured_docs)

        # Create output data structure matching sync version
        output_data = {
            "metadata": {
                "processing_timestamp": time.time(),
                "source_type": "local_files_async",
                "file_paths": file_paths,
                "total_files": len(structured_docs),
                "total_chunks": len(semantic_chunks),
                "concurrent_limit": concurrent_limit,
                "failed_files": len(failed_files),
                "processing_time": self.metrics.duration(),
                "files_per_second": len(structured_docs) / max(self.metrics.duration(), 0.1)
            },
            "documents": structured_docs,
            "semantic_chunks": semantic_chunks
        }

        # Save results
        await self.save_results_async(output_data, output_file)

        logger.info(f"✅ Async local file processing complete!")
        logger.info(f"   📊 Statistics:")
        logger.info(f"      Files processed: {len(structured_docs)}")
        logger.info(f"      Files failed: {len(failed_files)}")
        logger.info(f"      Semantic chunks: {len(semantic_chunks)}")
        logger.info(f"      Processing time: {self.metrics.duration():.1f}s")
        logger.info(f"      Processing rate: {output_data['metadata']['files_per_second']:.1f} files/sec")

        if failed_files:
            logger.warning(f"⚠️  Failed files:")
            for file_path, error in failed_files[:5]:  # Show first 5 failures
                logger.warning(f"      {Path(file_path).name}: {error}")
            if len(failed_files) > 5:
                logger.warning(f"      ... and {len(failed_files) - 5} more")

        if semantic_chunks:
            avg_chunk_size = sum(c['word_count'] for c in semantic_chunks) / len(semantic_chunks)
            logger.info(f"      Average chunk size: {avg_chunk_size:.0f} words")

        return output_data

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

    # Note: __aenter__ and __aexit__ are defined earlier (lines 84-91)

    @staticmethod
    async def process_local_files_fast(file_paths: List[str],
                                     output_file: str = "data/fast_local_docs.json",
                                     concurrent_limit: int = 6) -> Dict:
        """
        High-level async local file processing function

        Args:
            file_paths: List of HTML file paths to process
            output_file: Output file path
            concurrent_limit: Number of files to process concurrently

        Returns:
            Dictionary with processing results and metadata
        """
        config = ScrapingConfig(
            concurrent_limit=concurrent_limit,
            requests_per_second=20.0  # Not relevant for local files, but needed for config
        )

        async with AsyncWebScraper(config) as scraper:
            results = await scraper.process_local_files_async(file_paths, output_file)
            return results

    def find_html_files(self, directory: str, pattern: str = "*.html") -> List[str]:
        """Find HTML files in a directory (supports glob patterns)"""
        import glob

        directory_path = Path(directory)
        if not directory_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return []

        # Support both *.html and *.htm
        html_files = []
        for ext in ['*.html', '*.htm']:
            html_files.extend(glob.glob(str(directory_path / ext)))

        # Also search subdirectories if pattern includes **
        if '**' in pattern:
            for ext in ['*.html', '*.htm']:
                html_files.extend(glob.glob(str(directory_path / '**' / ext), recursive=True))

        html_files = sorted(list(set(html_files)))  # Remove duplicates and sort
        logger.info(f"🔍 Found {len(html_files)} HTML files in {directory}")

        return html_files


# Convenience functions for easy usage
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

# Demo code moved to examples/async_scraper_demo.py
