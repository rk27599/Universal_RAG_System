#!/usr/bin/env python3
"""
Generic Web Scraper for RAG Systems
Scrapes any website and creates semantic chunks for better RAG performance
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
import time
from typing import List, Dict, Set, Optional
import os
from urllib.robotparser import RobotFileParser


class WebScraper:
    """Generic web scraper that can handle any website"""

    def __init__(self, base_url: str = None, respect_robots_txt: bool = True):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.structured_docs: List[Dict] = []
        self.respect_robots_txt = respect_robots_txt
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Generic RAG Scraper; +https://example.com/bot)'
        })

        # Initialize robots.txt parser if needed
        self.robots_parser = None
        if base_url and respect_robots_txt:
            self._init_robots_parser()

    def _init_robots_parser(self):
        """Initialize robots.txt parser for the base domain"""
        try:
            parsed_url = urlparse(self.base_url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()

            print(f"📋 Loaded robots.txt from {robots_url}")
        except Exception as e:
            print(f"⚠️ Could not load robots.txt: {e}")
            self.robots_parser = None

    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.robots_parser:
            return True

        user_agent = self.session.headers.get('User-Agent', '*')
        return self.robots_parser.can_fetch(user_agent, url)

    def discover_urls(self, start_urls: List[str], max_pages: int = 50,
                     same_domain_only: bool = True, max_depth: int = 2) -> List[str]:
        """Discover URLs starting from given URLs"""

        print(f"🔍 Discovering URLs from {len(start_urls)} starting points...")

        discovered_urls = []
        urls_to_process = [(url, 0) for url in start_urls]  # (url, depth)
        processed_urls = set()

        base_domain = None
        if same_domain_only and start_urls:
            base_domain = urlparse(start_urls[0]).netloc

        while urls_to_process and len(discovered_urls) < max_pages:
            current_url, depth = urls_to_process.pop(0)

            if current_url in processed_urls or depth > max_depth:
                continue

            processed_urls.add(current_url)

            # Check robots.txt
            if not self.can_fetch(current_url):
                print(f"🚫 Blocked by robots.txt: {current_url}")
                continue

            try:
                response = self.session.get(current_url, timeout=10)
                if response.status_code == 200:
                    discovered_urls.append(current_url)

                    # Find more links if we haven't reached max depth
                    if depth < max_depth:
                        soup = BeautifulSoup(response.text, 'html.parser')

                        for link in soup.find_all('a', href=True):
                            href = link['href']

                            # Convert relative URLs to absolute
                            if not href.startswith('http'):
                                href = urljoin(current_url, href)

                            # Filter URLs
                            parsed_href = urlparse(href)

                            # Skip non-http protocols
                            if parsed_href.scheme not in ['http', 'https']:
                                continue

                            # Same domain check
                            if same_domain_only and base_domain:
                                if parsed_href.netloc != base_domain:
                                    continue

                            # Avoid common non-content URLs
                            skip_patterns = [
                                r'\.(pdf|jpg|jpeg|png|gif|css|js|ico)$',
                                r'/(login|signup|register|logout)',
                                r'/(search|filter|sort)\?',
                                r'#',  # Skip anchor links
                            ]

                            should_skip = any(re.search(pattern, href.lower())
                                            for pattern in skip_patterns)

                            if not should_skip and href not in processed_urls:
                                if len(discovered_urls) + len(urls_to_process) < max_pages:
                                    urls_to_process.append((href, depth + 1))

                # Be respectful
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Error processing {current_url}: {e}")

        print(f"   Found {len(discovered_urls)} URLs")
        return discovered_urls

    def clean_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove navigation, ads, and non-content elements"""

        # Common selectors for non-content elements
        selectors_to_remove = [
            # Navigation
            'nav', 'header', 'footer', 'aside',
            '.navbar', '.navigation', '.menu', '.sidebar',
            '.breadcrumb', '.breadcrumbs',

            # Ads and tracking
            '.ad', '.ads', '.advertisement', '.banner',
            '.social', '.social-media', '.social-share',
            '.tracking', '.analytics',

            # Comments and interactions
            '.comments', '.comment-section',
            '.related-posts', '.recommended',

            # Forms (usually not content)
            '.search-form', '.login-form', '.newsletter',

            # Common CMS elements
            '.edit-link', '.admin-bar', '.wp-admin',
        ]

        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()

        # Remove script, style, and meta elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()

        # Remove elements with minimal text content
        for element in soup.find_all():
            if element.string and len(element.get_text().strip()) < 10:
                if element.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    element.decompose()

        return soup

    def extract_structured_content(self, url: str) -> Optional[Dict]:
        """Extract structured content from any web page"""

        print(f"   📄 Processing: {url}")

        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"      ❌ Failed: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            soup = self.clean_content(soup)

            # Find main content area (try common patterns)
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
                soup.find('div', id=re.compile(r'content|main|body', re.I)) or
                soup.find('section') or
                soup
            )

            # Extract page title
            page_title = self._extract_title(soup, url)

            # Extract structured sections
            sections = self.extract_sections(main_content, url, page_title)

            doc_structure = {
                "url": url,
                "page_title": page_title,
                "domain": urlparse(url).netloc,
                "sections": sections,
                "total_sections": len(sections)
            }

            print(f"      ✅ Extracted {len(sections)} sections")
            return doc_structure

        except Exception as e:
            print(f"      ❌ Error: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title using multiple strategies"""

        # Try different title sources in order of preference
        title_sources = [
            soup.find('h1'),
            soup.find('title'),
            soup.find('meta', attrs={'property': 'og:title'}),
            soup.find('meta', attrs={'name': 'twitter:title'}),
            soup.find('h2'),
        ]

        for source in title_sources:
            if source:
                if source.name == 'meta':
                    title = source.get('content', '')
                else:
                    title = source.get_text().strip()

                if title and len(title) > 0:
                    return title

        # Fallback to URL-based title
        path = urlparse(url).path
        if path and path != '/':
            title = path.split('/')[-1].replace('-', ' ').replace('_', ' ')
            return title.title()

        return urlparse(url).netloc

    def extract_sections(self, content_soup: BeautifulSoup, url: str, page_title: str) -> List[Dict]:
        """Extract sections with hierarchy and context"""

        sections = []
        current_section = None
        section_content = []

        # Find all elements that could be content
        elements = content_soup.find_all([
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'pre', 'code', 'ul', 'ol', 'dl', 'table', 'blockquote'
        ])

        for element in elements:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save previous section
                if current_section and section_content:
                    current_section["content"] = section_content
                    current_section["content_text"] = "\n\n".join(section_content)
                    current_section["word_count"] = len(current_section["content_text"].split())
                    sections.append(current_section)

                # Start new section
                section_title = element.get_text().strip()
                level = int(element.name[1])

                current_section = {
                    "title": section_title,
                    "level": level,
                    "page_title": page_title,
                    "url": url,
                    "content": [],
                    "section_id": len(sections) + 1
                }
                section_content = []

            elif element.name in ['p', 'pre', 'ul', 'ol', 'dl', 'blockquote']:
                # Content within section
                text = element.get_text().strip()
                if len(text) > 20:  # Filter very short content

                    # Enhance different content types
                    if element.name == 'pre':
                        text = f"Code example:\n{text}"
                    elif element.name in ['ul', 'ol']:
                        text = f"List:\n{text}"
                    elif element.name == 'blockquote':
                        text = f"Quote:\n{text}"

                    section_content.append(text)

            elif element.name == 'table':
                # Handle tables
                table_text = self.extract_table_text(element)
                if table_text:
                    section_content.append(f"Table:\n{table_text}")

        # Add the last section
        if current_section and section_content:
            current_section["content"] = section_content
            current_section["content_text"] = "\n\n".join(section_content)
            current_section["word_count"] = len(current_section["content_text"].split())
            sections.append(current_section)

        return sections

    def extract_table_text(self, table_element) -> str:
        """Extract structured text from tables"""
        rows = []
        for row in table_element.find_all('tr'):
            cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
            if any(cells):  # Only add non-empty rows
                rows.append(" | ".join(cells))
        return "\n".join(rows)

    def create_semantic_chunks(self, structured_docs: List[Dict],
                             max_chunk_size: int = 1200) -> List[Dict]:
        """Create semantically meaningful chunks from structured documents"""

        print(f"🧠 Creating semantic chunks...")

        semantic_chunks = []

        for doc in structured_docs:
            if not doc or "sections" not in doc:
                continue

            page_title = doc.get("page_title", "Unknown Page")
            url = doc.get("url", "")
            domain = doc.get("domain", urlparse(url).netloc)

            for section in doc["sections"]:
                section_title = section.get("title", "Unknown Section")
                content_text = section.get("content_text", "")
                level = section.get("level", 1)

                if len(content_text.strip()) < 30:
                    continue

                # Create contextual title
                contextual_title = f"{page_title} - {section_title}" if section_title != page_title else page_title

                if len(content_text) <= max_chunk_size:
                    # Section fits in one chunk
                    chunk_text = f"# {contextual_title}\n\n{content_text}"

                    semantic_chunks.append({
                        "text": chunk_text,
                        "title": contextual_title,
                        "section_title": section_title,
                        "page_title": page_title,
                        "url": url,
                        "domain": domain,
                        "level": level,
                        "type": "complete_section",
                        "word_count": len(chunk_text.split()),
                        "chunk_id": len(semantic_chunks)
                    })

                else:
                    # Split large section while maintaining context
                    paragraphs = content_text.split("\n\n")
                    current_chunk_paras = []
                    current_length = 0
                    chunk_num = 1

                    for para in paragraphs:
                        para_length = len(para)

                        if current_length + para_length > max_chunk_size and current_chunk_paras:
                            # Create chunk
                            chunk_content = "\n\n".join(current_chunk_paras)
                            chunk_text = f"# {contextual_title} (Part {chunk_num})\n\n{chunk_content}"

                            semantic_chunks.append({
                                "text": chunk_text,
                                "title": f"{contextual_title} (Part {chunk_num})",
                                "section_title": section_title,
                                "page_title": page_title,
                                "url": url,
                                "domain": domain,
                                "level": level,
                                "type": "section_part",
                                "word_count": len(chunk_text.split()),
                                "chunk_id": len(semantic_chunks),
                                "part_number": chunk_num
                            })

                            # Start new chunk
                            current_chunk_paras = [para]
                            current_length = para_length
                            chunk_num += 1
                        else:
                            current_chunk_paras.append(para)
                            current_length += para_length

                    # Add remaining content
                    if current_chunk_paras:
                        chunk_content = "\n\n".join(current_chunk_paras)
                        title_suffix = f" (Part {chunk_num})" if chunk_num > 1 else ""
                        chunk_text = f"# {contextual_title}{title_suffix}\n\n{chunk_content}"

                        semantic_chunks.append({
                            "text": chunk_text,
                            "title": f"{contextual_title}{title_suffix}",
                            "section_title": section_title,
                            "page_title": page_title,
                            "url": url,
                            "domain": domain,
                            "level": level,
                            "type": "section_part",
                            "word_count": len(chunk_text.split()),
                            "chunk_id": len(semantic_chunks),
                            "part_number": chunk_num if chunk_num > 1 else 1
                        })

        print(f"   ✅ Created {len(semantic_chunks)} semantic chunks")
        return semantic_chunks

    def scrape_website(self, start_urls: List[str], max_pages: int = 30,
                      output_file: str = "data/website_docs_structured.json",
                      same_domain_only: bool = True, max_depth: int = 2) -> Dict:
        """Main method to scrape any website and create structured data"""

        print(f"🚀 Starting generic website scraping...")
        print(f"   Starting URLs: {len(start_urls)}")
        print(f"   Max pages: {max_pages}")
        print(f"   Same domain only: {same_domain_only}")
        print(f"   Max depth: {max_depth}")

        # Discover URLs
        urls_to_scrape = self.discover_urls(
            start_urls, max_pages, same_domain_only, max_depth
        )

        # Scrape each URL
        structured_docs = []
        for i, url in enumerate(urls_to_scrape, 1):
            print(f"\n📄 Processing {i}/{len(urls_to_scrape)}: {urlparse(url).path}")

            doc_structure = self.extract_structured_content(url)
            if doc_structure:
                structured_docs.append(doc_structure)

            # Be respectful - delay between requests
            time.sleep(1)

        print(f"\n🧠 Creating semantic chunks from {len(structured_docs)} documents...")
        semantic_chunks = self.create_semantic_chunks(structured_docs)

        # Save structured data
        output_data = {
            "metadata": {
                "scraping_timestamp": time.time(),
                "start_urls": start_urls,
                "total_pages": len(structured_docs),
                "total_chunks": len(semantic_chunks),
                "domains": list(set(doc.get("domain", "") for doc in structured_docs))
            },
            "documents": structured_docs,
            "semantic_chunks": semantic_chunks
        }

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        print(f"\n💾 Saving to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Also create a simple text file for compatibility
        text_file = output_file.replace('.json', '.txt')
        print(f"💾 Creating text file: {text_file}...")

        with open(text_file, 'w', encoding='utf-8') as f:
            for chunk in semantic_chunks:
                f.write(f"{chunk['text']}\n\n{'='*80}\n\n")

        print(f"\n✅ Scraping complete!")
        print(f"   📊 Statistics:")
        print(f"      Pages processed: {len(structured_docs)}")
        print(f"      Semantic chunks: {len(semantic_chunks)}")
        if semantic_chunks:
            avg_chunk_size = sum(c['word_count'] for c in semantic_chunks) / len(semantic_chunks)
            print(f"      Average chunk size: {avg_chunk_size:.0f} words")
        print(f"      Domains covered: {len(output_data['metadata']['domains'])}")
        print(f"   📁 Files created:")
        print(f"      {output_file} (structured JSON)")
        print(f"      {text_file} (plain text)")

        return output_data


def main():
    """Example usage of the generic web scraper"""

    # Example: Scrape a documentation website
    scraper = WebScraper()

    # You can specify any website here
    start_urls = [
        "https://pytorch.org/docs/stable/",  # Example: pytorch docs
        # Add more starting URLs as needed
    ]

    result = scraper.scrape_website(
        start_urls=start_urls,
        max_pages=100,  # Limit for testing
        output_file="data/generic_website_docs.json",
        same_domain_only=True,
        max_depth=2
    )

    return result


if __name__ == "__main__":
    main()