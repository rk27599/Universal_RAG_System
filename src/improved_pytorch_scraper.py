#!/usr/bin/env python3
"""
Improved PyTorch Documentation Scraper
Preserves document structure and creates semantic chunks for better RAG performance
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
import time
from typing import List, Dict, Set
import os

class ImprovedPyTorchScraper:
    """Enhanced scraper that preserves document structure and context"""

    def __init__(self, base_url: str = "https://pytorch.org/docs/stable/"):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.structured_docs: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PyTorch Documentation Scraper)'
        })

    def discover_documentation_urls(self, max_pages: int = 50) -> List[str]:
        """Discover all PyTorch documentation URLs"""

        print(f"🔍 Discovering PyTorch documentation URLs...")

        # Key documentation pages to prioritize
        priority_urls = [
            "torch.html",           # Main torch module
            "nn.html",             # Neural networks
            "optim.html",          # Optimizers
            "data.html",           # DataLoader
            "autograd.html",       # Automatic differentiation
            "distributed.html",    # Distributed training
            "tensorboard.html",    # TensorBoard integration
            "jit.html",           # TorchScript
            "cuda.html",          # CUDA utilities
            "amp.html",           # Automatic mixed precision
            "quantization.html",   # Quantization
            "sparse.html",        # Sparse tensors
            "notes/autograd.html", # Autograd notes
            "notes/cuda.html",    # CUDA notes
            "notes/ddp.html",     # DDP notes
            "notes/faq.html",     # FAQ
            # Additional URLs for better tensor parallelism coverage
            "nn.parallel.html",    # Parallel layers
            "distributed/_shard.html", # Tensor sharding
            "distributed.tensor.html", # Distributed tensors
            "notes/multiprocessing.html", # Multiprocessing notes
            "notes/extending.html", # Extending PyTorch
            "notes/serialization.html", # Model serialization
        ]

        discovered_urls = []

        # Add priority URLs
        for url_path in priority_urls:
            full_url = urljoin(self.base_url, url_path)
            discovered_urls.append(full_url)

        # Discover additional URLs from the main index
        try:
            index_response = self.session.get(self.base_url, timeout=10)
            if index_response.status_code == 200:
                soup = BeautifulSoup(index_response.text, 'html.parser')

                # Find documentation links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.endswith('.html') and not href.startswith('http'):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in discovered_urls and len(discovered_urls) < max_pages:
                            discovered_urls.append(full_url)

        except Exception as e:
            print(f"⚠️ Warning: Could not discover additional URLs: {e}")

        print(f"   Found {len(discovered_urls)} documentation pages")
        return discovered_urls[:max_pages]

    def clean_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove navigation and non-content elements"""

        # Remove navigation, headers, footers
        selectors_to_remove = [
            'nav', 'header', 'footer', 'aside',
            '.navbar', '.navigation', '.toctree-wrapper',
            '.related', '.sphinxsidebarwrapper',
            '.breadcrumb', '.edit-page', '.version-switcher'
        ]

        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()

        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()

        return soup

    def extract_structured_content(self, url: str) -> Dict:
        """Extract structured content from a documentation page"""

        print(f"   📄 Processing: {url}")

        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"      ❌ Failed: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            soup = self.clean_content(soup)

            # Find main content area
            main_content = (
                soup.find('div', class_='body') or
                soup.find('div', class_='document') or
                soup.find('main') or
                soup.find('article') or
                soup
            )

            # Extract page title
            page_title = ""
            title_element = (
                soup.find('h1') or
                soup.find('title') or
                soup.find('h2')
            )
            if title_element:
                page_title = title_element.get_text().strip()

            if not page_title:
                # Extract from URL
                page_title = urlparse(url).path.split('/')[-1].replace('.html', '').replace('_', ' ')

            # Extract structured sections
            sections = self.extract_sections(main_content, url, page_title)

            doc_structure = {
                "url": url,
                "page_title": page_title,
                "sections": sections,
                "total_sections": len(sections)
            }

            print(f"      ✅ Extracted {len(sections)} sections")
            return doc_structure

        except Exception as e:
            print(f"      ❌ Error: {e}")
            return None

    def extract_sections(self, content_soup: BeautifulSoup, url: str, page_title: str) -> List[Dict]:
        """Extract sections with hierarchy and context"""

        sections = []
        current_section = None
        section_content = []

        # Find all elements that could be content
        elements = content_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code', 'ul', 'ol', 'dl', 'table'])

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

            elif element.name in ['p', 'pre', 'ul', 'ol', 'dl']:
                # Content within section
                text = element.get_text().strip()
                if len(text) > 10:  # Filter very short content

                    # Enhance code blocks
                    if element.name == 'pre':
                        text = f"Code example:\n{text}"
                    elif element.name in ['ul', 'ol']:
                        text = f"List:\n{text}"

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
                             min_chunk_size: int = 300,
                             max_chunk_size: int = 1200) -> List[Dict]:
        """Create semantically meaningful chunks from structured documents"""

        print(f"🧠 Creating semantic chunks...")

        semantic_chunks = []

        for doc in structured_docs:
            if not doc or "sections" not in doc:
                continue

            page_title = doc.get("page_title", "Unknown Page")
            url = doc.get("url", "")

            for section in doc["sections"]:
                section_title = section.get("title", "Unknown Section")
                content_text = section.get("content_text", "")
                level = section.get("level", 1)

                if len(content_text.strip()) < 20:
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
                            "level": level,
                            "type": "section_part",
                            "word_count": len(chunk_text.split()),
                            "chunk_id": len(semantic_chunks),
                            "part_number": chunk_num if chunk_num > 1 else 1
                        })

        print(f"   ✅ Created {len(semantic_chunks)} semantic chunks")
        return semantic_chunks

    def scrape_pytorch_docs(self, max_pages: int = 30, output_file: str = "data/pytorch_docs_structured.json"):
        """Main method to scrape and structure PyTorch documentation"""

        print(f"🚀 Starting improved PyTorch documentation scraping...")
        print(f"   Target: {max_pages} pages")

        # Discover URLs
        urls_to_scrape = self.discover_documentation_urls(max_pages)

        # Scrape each URL
        structured_docs = []
        for i, url in enumerate(urls_to_scrape, 1):
            print(f"\n📄 Processing {i}/{len(urls_to_scrape)}: {url.split('/')[-1]}")

            doc_structure = self.extract_structured_content(url)
            if doc_structure:
                structured_docs.append(doc_structure)

            # Be respectful - small delay
            time.sleep(0.5)

        print(f"\n🧠 Creating semantic chunks from {len(structured_docs)} documents...")
        semantic_chunks = self.create_semantic_chunks(structured_docs)

        # Save structured data
        output_data = {
            "metadata": {
                "scraping_timestamp": time.time(),
                "total_pages": len(structured_docs),
                "total_chunks": len(semantic_chunks),
                "base_url": self.base_url
            },
            "documents": structured_docs,
            "semantic_chunks": semantic_chunks
        }

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
        print(f"      Average chunk size: {sum(c['word_count'] for c in semantic_chunks) / len(semantic_chunks):.0f} words")
        print(f"   📁 Files created:")
        print(f"      {output_file} (structured JSON)")
        print(f"      {text_file} (plain text)")

        return output_data

def main():
    """Main function to run the improved scraper"""

    scraper = ImprovedPyTorchScraper()

    # Scrape with reasonable limits
    result = scraper.scrape_pytorch_docs(
        max_pages=1000,  # Focus on key pages
        output_file="data/pytorch_docs_structured.json"
    )

    return result

if __name__ == "__main__":
    main()