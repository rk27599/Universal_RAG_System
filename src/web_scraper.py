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
from pathlib import Path
import glob


class WebScraper:
    """Generic web scraper that can handle any website"""

    def __init__(self, base_url: str = None, respect_robots_txt: bool = True, local_mode: bool = False):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.structured_docs: List[Dict] = []
        self.respect_robots_txt = respect_robots_txt
        self.local_mode = local_mode

        # Only initialize web session if not in local mode
        if not local_mode:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (compatible; Generic RAG Scraper; +https://example.com/bot)'
            })

            # Initialize robots.txt parser if needed
            self.robots_parser = None
            if base_url and respect_robots_txt:
                self._init_robots_parser()
        else:
            self.session = None
            self.robots_parser = None

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

    def extract_structured_content(self, url: str, html_content: str = None) -> Optional[Dict]:
        """Extract structured content from web page or local HTML content"""

        print(f"   📄 Processing: {url}")

        try:
            if html_content:
                # Use provided HTML content (for local files)
                soup = BeautifulSoup(html_content, 'html.parser')
            else:
                # Fetch from web (original behavior)
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

            # Determine domain - use file scheme for local files
            if url.startswith('file://'):
                domain = 'local'
            else:
                domain = urlparse(url).netloc

            doc_structure = {
                "url": url,
                "page_title": page_title,
                "domain": domain,
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

    def extract_from_local_file(self, file_path: str) -> Optional[Dict]:
        """Extract structured content from a local HTML file"""

        try:
            file_path = Path(file_path).resolve()

            if not file_path.exists():
                print(f"   ❌ File not found: {file_path}")
                return None

            if not file_path.suffix.lower() in ['.html', '.htm']:
                print(f"   ⚠️ Not an HTML file: {file_path}")
                return None

            print(f"   📂 Reading local file: {file_path.name}")

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            # Create file:// URL for consistency
            file_url = f"file://{file_path}"

            return self.extract_structured_content(file_url, html_content)

        except Exception as e:
            print(f"   ❌ Error reading {file_path}: {e}")
            return None

    def process_local_files(self, file_paths: List[str], output_file: str = "data/local_docs_structured.json") -> Dict:
        """Process multiple local HTML files"""

        print(f"🚀 Processing {len(file_paths)} local HTML files...")

        structured_docs = []

        for i, file_path in enumerate(file_paths, 1):
            print(f"\n📂 Processing {i}/{len(file_paths)}: {Path(file_path).name}")

            doc_structure = self.extract_from_local_file(file_path)
            if doc_structure:
                structured_docs.append(doc_structure)

        print(f"\n🧠 Creating semantic chunks from {len(structured_docs)} documents...")
        semantic_chunks = self.create_semantic_chunks(structured_docs)

        # Save structured data
        output_data = {
            "metadata": {
                "processing_timestamp": time.time(),
                "source_type": "local_files",
                "file_paths": file_paths,
                "total_files": len(structured_docs),
                "total_chunks": len(semantic_chunks)
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

        print(f"\n✅ Local file processing complete!")
        print(f"   📊 Statistics:")
        print(f"      Files processed: {len(structured_docs)}")
        print(f"      Semantic chunks: {len(semantic_chunks)}")
        if semantic_chunks:
            avg_chunk_size = sum(c['word_count'] for c in semantic_chunks) / len(semantic_chunks)
            print(f"      Average chunk size: {avg_chunk_size:.0f} words")
        print(f"   📁 Files created:")
        print(f"      {output_file} (structured JSON)")
        print(f"      {text_file} (plain text)")

        return output_data

    def find_html_files(self, directory: str, pattern: str = "*.html") -> List[str]:
        """Find HTML files in a directory (supports glob patterns)"""

        directory_path = Path(directory)
        if not directory_path.exists():
            print(f"❌ Directory not found: {directory}")
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
        print(f"🔍 Found {len(html_files)} HTML files in {directory}")

        return html_files

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

    def process_mixed_sources(self, web_urls: List[str] = None, local_files: List[str] = None,
                             output_file: str = "data/mixed_docs_structured.json",
                             max_pages: int = 30, same_domain_only: bool = True, max_depth: int = 2) -> Dict:
        """Process both web URLs and local HTML files in a single operation"""

        print(f"🚀 Processing mixed sources...")
        print(f"   Web URLs: {len(web_urls) if web_urls else 0}")
        print(f"   Local files: {len(local_files) if local_files else 0}")

        all_structured_docs = []

        # Process web URLs if provided
        if web_urls:
            web_data = self.scrape_website(
                web_urls, max_pages, f"{output_file}_web_temp.json",
                same_domain_only, max_depth
            )
            all_structured_docs.extend(web_data.get('documents', []))

        # Process local files if provided
        if local_files:
            local_data = self.process_local_files(local_files, f"{output_file}_local_temp.json")
            all_structured_docs.extend(local_data.get('documents', []))

        # Create combined semantic chunks
        print(f"\n🧠 Creating semantic chunks from {len(all_structured_docs)} total documents...")
        semantic_chunks = self.create_semantic_chunks(all_structured_docs)

        # Combine metadata
        combined_output = {
            "metadata": {
                "processing_timestamp": time.time(),
                "source_type": "mixed",
                "web_urls": web_urls or [],
                "local_files": local_files or [],
                "total_documents": len(all_structured_docs),
                "total_chunks": len(semantic_chunks),
                "domains": list(set(doc.get("domain", "") for doc in all_structured_docs))
            },
            "documents": all_structured_docs,
            "semantic_chunks": semantic_chunks
        }

        # Save combined data
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        print(f"\n💾 Saving combined data to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_output, f, indent=2, ensure_ascii=False)

        # Create text file
        text_file = output_file.replace('.json', '.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            for chunk in semantic_chunks:
                f.write(f"{chunk['text']}\n\n{'='*80}\n\n")

        # Clean up temporary files
        for temp_file in [f"{output_file}_web_temp.json", f"{output_file}_local_temp.json"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print(f"\n✅ Mixed processing complete!")
        print(f"   📊 Statistics:")
        print(f"      Documents processed: {len(all_structured_docs)}")
        print(f"      Semantic chunks: {len(semantic_chunks)}")
        print(f"      Domains: {len(combined_output['metadata']['domains'])}")

        return combined_output


def main():
    """Example usage of the generic web scraper with local and web sources"""

    print("🔍 WebScraper Usage Examples\n")

    # Example 1: Process local HTML files
    print("=" * 50)
    print("Example 1: Processing Local HTML Files")
    print("=" * 50)

    scraper_local = WebScraper(local_mode=True)

    # Find HTML files in current directory (example)
    # html_files = scraper_local.find_html_files(".", "**/*.html")

    # For demonstration, using example paths
    html_files = [
        # Add your local HTML file paths here
        # Example: "/path/to/your/file.html"
    ]

    if html_files:
        local_result = scraper_local.process_local_files(
            html_files,
            output_file="data/local_html_docs.json"
        )
        print(f"✅ Processed {len(local_result.get('documents', []))} local HTML files")
    else:
        print("⚠️ No HTML files found. Add file paths to html_files list.")

    # Example 2: Web scraping (original functionality)
    print("\n" + "=" * 50)
    print("Example 2: Web Scraping")
    print("=" * 50)

    scraper_web = WebScraper()

    start_urls = [
        "https://fastapi.tiangolo.com/",  # Example: FastAPI docs
    ]

    web_result = scraper_web.scrape_website(
        start_urls=start_urls,
        max_pages=10,  # Small limit for testing
        output_file="data/web_docs.json",
        same_domain_only=True,
        max_depth=1
    )

    # Example 3: Mixed processing
    print("\n" + "=" * 50)
    print("Example 3: Mixed Sources Processing")
    print("=" * 50)

    scraper_mixed = WebScraper()

    if html_files:
        mixed_result = scraper_mixed.process_mixed_sources(
            web_urls=["https://fastapi.tiangolo.com/"],
            local_files=html_files[:2],  # Limit local files for demo
            output_file="data/mixed_sources.json",
            max_pages=5
        )
        print(f"✅ Mixed processing complete with {len(mixed_result.get('documents', []))} total documents")
    else:
        print("⚠️ Skipping mixed processing - no local HTML files provided")

    print(f"\n🎉 All examples completed! Check the data/ directory for output files.")

    return {
        "local_files_processed": len(html_files) if html_files else 0,
        "web_scraping_completed": True,
        "mixed_processing": bool(html_files)
    }


if __name__ == "__main__":
    main()