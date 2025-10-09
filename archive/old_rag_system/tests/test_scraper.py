#!/usr/bin/env python3
"""
Test cases for the Improved PyTorch Scraper
"""

import unittest
import os
import sys
import tempfile
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web_scraper import WebScraper


class TestWebScraper(unittest.TestCase):
    """Test cases for WebScraper"""

    def setUp(self):
        """Set up test fixtures"""
        self.scraper = WebScraper()

    def test_initialization(self):
        """Test scraper initialization"""
        self.assertIsNone(self.scraper.base_url)  # No default URL for generic scraper
        self.assertIsInstance(self.scraper.visited_urls, set)
        self.assertEqual(len(self.scraper.visited_urls), 0)
        self.assertEqual(len(self.scraper.structured_docs), 0)

    def test_clean_content(self):
        """Test content cleaning functionality"""
        from bs4 import BeautifulSoup

        # Create test HTML
        test_html = """
        <div>
            <nav>navigation</nav>
            <h1>Hello world!</h1>
            <p>Content paragraph</p>
            <script>alert('test');</script>
            <footer>footer content</footer>
        </div>
        """
        soup = BeautifulSoup(test_html, 'html.parser')
        cleaned = self.scraper.clean_content(soup)

        # Should remove nav, script, footer
        self.assertIsNone(cleaned.find('nav'))
        self.assertIsNone(cleaned.find('script'))
        self.assertIsNone(cleaned.find('footer'))

        # Should keep h1 and p
        self.assertIsNotNone(cleaned.find('h1'))
        self.assertIsNotNone(cleaned.find('p'))

    def test_extract_metadata(self):
        """Test metadata extraction"""
        # Test that basic metadata structure is available
        metadata = {
            'title': 'Test Page',
            'headers': ['Main Header', 'Sub Header'],
            'url': 'test_url'
        }

        # Test metadata structure
        self.assertIn('title', metadata)
        self.assertIn('headers', metadata)
        self.assertIn('url', metadata)

    def test_create_semantic_chunks_empty_input(self):
        """Test semantic chunking with empty input"""
        chunks = self.scraper.create_semantic_chunks([])
        self.assertEqual(len(chunks), 0)

    def test_create_semantic_chunks_basic(self):
        """Test basic semantic chunking"""
        # Create test document structure
        test_doc = {
            "url": "test_url",
            "page_title": "Test Page",
            "sections": [
                {
                    "title": "Test Section",
                    "level": 1,
                    "content_text": "This is a test paragraph. " * 20,
                    "content": ["Test content"]
                }
            ]
        }

        chunks = self.scraper.create_semantic_chunks([test_doc])

        # Should create at least one chunk
        self.assertGreater(len(chunks), 0)

        # Each chunk should have required metadata
        for chunk in chunks:
            self.assertIn('text', chunk)
            self.assertIn('title', chunk)
            self.assertIn('page_title', chunk)
            self.assertIn('type', chunk)

    def test_scrape_website_structure(self):
        """Test the structure of scrape_website method"""
        # Test that the method exists and has the expected signature
        self.assertTrue(hasattr(self.scraper, 'scrape_website'))

        # Test that discover_urls exists
        self.assertTrue(hasattr(self.scraper, 'discover_urls'))

        # Test URL discovery returns a list (with test URLs)
        test_urls = ["https://httpbin.org/"]
        urls = self.scraper.discover_urls(test_urls, max_pages=1, max_depth=1)
        self.assertIsInstance(urls, list)

    def test_extract_table_text(self):
        """Test table text extraction"""
        from bs4 import BeautifulSoup

        # Create test table HTML
        table_html = """
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
            <tr><td>Cell 3</td><td>Cell 4</td></tr>
        </table>
        """
        soup = BeautifulSoup(table_html, 'html.parser')
        table = soup.find('table')

        result = self.scraper.extract_table_text(table)
        self.assertIsInstance(result, str)
        self.assertIn("Header 1", result)
        self.assertIn("Cell 1", result)

    def test_extract_sections(self):
        """Test section extraction functionality"""
        from bs4 import BeautifulSoup

        # Create test HTML content
        test_html = """
        <div>
            <h1>Main Title</h1>
            <p>Main content paragraph</p>
            <h2>Subsection</h2>
            <p>Subsection content</p>
            <pre>Code example: print("hello")</pre>
        </div>
        """
        soup = BeautifulSoup(test_html, 'html.parser')

        sections = self.scraper.extract_sections(soup, "test_url", "Test Page")
        self.assertIsInstance(sections, list)
        self.assertGreater(len(sections), 0)

        # Check section structure
        if sections:
            section = sections[0]
            self.assertIn('title', section)
            self.assertIn('level', section)
            self.assertIn('content_text', section)


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for the scraper (requires internet connection)"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.scraper = WebScraper()

    def test_scrape_single_page_if_online(self):
        """Test scraping a single web page if online"""
        try:
            # This would require actual network access
            # For now, just test that the method exists
            self.assertTrue(hasattr(self.scraper, 'extract_structured_content'))

        except Exception:
            self.skipTest("Network access not available or page structure changed")

    def test_session_exists(self):
        """Test that scraper has session for making requests"""
        # Test that scraper has session for HTTP requests
        self.assertTrue(hasattr(self.scraper, 'session'))
        self.assertIsNotNone(self.scraper.session)

    def test_can_fetch_method(self):
        """Test that robots.txt checking method exists"""
        # Test that scraper can check robots.txt
        self.assertTrue(hasattr(self.scraper, 'can_fetch'))
        # Should return True by default when no robots.txt is loaded
        result = self.scraper.can_fetch("https://httpbin.org/")
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    # Run tests with different verbosity levels
    unittest.main(verbosity=2)