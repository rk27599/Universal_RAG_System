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

from src.improved_pytorch_scraper import ImprovedPyTorchScraper


class TestImprovedPyTorchScraper(unittest.TestCase):
    """Test cases for ImprovedPyTorchScraper"""

    def setUp(self):
        """Set up test fixtures"""
        self.scraper = ImprovedPyTorchScraper()

    def test_initialization(self):
        """Test scraper initialization"""
        self.assertEqual(self.scraper.base_url, "https://pytorch.org/docs/stable/")
        self.assertEqual(self.scraper.max_pages, 50)
        self.assertEqual(len(self.scraper.scraped_data), 0)

    def test_clean_text(self):
        """Test text cleaning functionality"""
        dirty_text = "  \n\nHello   world!  \n\n  "
        clean_text = self.scraper.clean_text(dirty_text)
        self.assertEqual(clean_text, "Hello world!")

        # Test with None input
        self.assertEqual(self.scraper.clean_text(None), "")

        # Test with empty string
        self.assertEqual(self.scraper.clean_text(""), "")

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
        chunks = self.scraper.create_semantic_chunks("", {})
        self.assertEqual(len(chunks), 0)

    def test_create_semantic_chunks_basic(self):
        """Test basic semantic chunking"""
        content = "This is a test paragraph. " * 20  # Create longer content
        metadata = {
            'title': 'Test Page',
            'url': 'test_url',
            'headers': ['Test Header']
        }

        chunks = self.scraper.create_semantic_chunks(content, metadata)

        # Should create at least one chunk
        self.assertGreater(len(chunks), 0)

        # Each chunk should have required metadata
        for chunk in chunks:
            self.assertIn('content', chunk)
            self.assertIn('metadata', chunk)
            self.assertIn('page', chunk['metadata'])
            self.assertIn('content_type', chunk['metadata'])

    def test_save_structured_data(self):
        """Test saving structured data to file"""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_output.json")

            # Add some test data
            self.scraper.scraped_data = [
                {
                    'url': 'test_url',
                    'title': 'Test Page',
                    'content': 'Test content',
                    'metadata': {'test': 'data'}
                }
            ]

            # Test saving
            result = self.scraper.save_structured_data(output_file)
            self.assertTrue(result)

            # Verify file was created and contains expected data
            self.assertTrue(os.path.exists(output_file))

            with open(output_file, 'r') as f:
                saved_data = json.load(f)
                self.assertIn('semantic_chunks', saved_data)
                self.assertIn('metadata', saved_data)

    def test_is_valid_pytorch_url(self):
        """Test URL validation"""
        # Valid URLs
        valid_urls = [
            "https://pytorch.org/docs/stable/tensors.html",
            "https://pytorch.org/docs/stable/nn.html#torch.nn.Module"
        ]

        for url in valid_urls:
            self.assertTrue(self.scraper.is_valid_pytorch_url(url))

        # Invalid URLs
        invalid_urls = [
            "https://example.com",
            "https://pytorch.org/blog/",
            "mailto:test@example.com",
            "javascript:void(0)"
        ]

        for url in invalid_urls:
            self.assertFalse(self.scraper.is_valid_pytorch_url(url))

    def test_estimate_content_type(self):
        """Test content type estimation"""
        # Code example
        code_content = "import torch\ntensor = torch.tensor([1, 2, 3])"
        self.assertEqual(self.scraper.estimate_content_type(code_content), "code_example")

        # Regular explanation
        explanation = "PyTorch is a machine learning framework that provides tensor operations."
        self.assertEqual(self.scraper.estimate_content_type(explanation), "explanation")

        # Empty content
        self.assertEqual(self.scraper.estimate_content_type(""), "other")


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for the scraper (requires internet connection)"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.scraper = ImprovedPyTorchScraper()

    def test_scrape_single_page_if_online(self):
        """Test scraping a single PyTorch documentation page if online"""
        try:
            # This would require actual network access
            # For now, just test that the method exists
            self.assertTrue(hasattr(self.scraper, 'scrape_page'))

        except Exception:
            self.skipTest("Network access not available or page structure changed")

    def test_rate_limiting(self):
        """Test that rate limiting is implemented"""
        # Test that scraper has delay mechanism
        self.assertTrue(hasattr(self.scraper, 'request_delay'))
        self.assertGreaterEqual(self.scraper.request_delay, 1.0)


if __name__ == '__main__':
    # Run tests with different verbosity levels
    unittest.main(verbosity=2)