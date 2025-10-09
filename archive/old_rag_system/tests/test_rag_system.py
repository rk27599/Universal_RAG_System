#!/usr/bin/env python3
"""
Test cases for the Enhanced RAG System
"""

import unittest
import os
import sys
import tempfile
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system import RAGSystem


class TestRAGSystem(unittest.TestCase):
    """Test cases for RAGSystem"""

    def setUp(self):
        """Set up test fixtures"""
        self.rag_system = RAGSystem()

        # Create sample test data with more substantial content (using 'text' field as expected by RAG system)
        self.sample_data = {
            'semantic_chunks': [
                {
                    'text': 'PyTorch tensors are multi-dimensional arrays that support automatic differentiation. Tensors are fundamental data structures in PyTorch machine learning framework. They can be created using various methods including torch.tensor(), torch.zeros(), and torch.ones(). Tensors support mathematical operations like addition, multiplication, and matrix operations.',
                    'title': 'Introduction to Tensors',
                    'page_title': 'Tensor Tutorial',
                    'section_title': 'Introduction to Tensors',
                    'type': 'explanation',
                    'word_count': 45
                },
                {
                    'text': 'torch.tensor([1, 2, 3]) creates a tensor from a list. You can also create tensors with torch.zeros(3, 4) for zero-filled tensors or torch.randn(2, 3) for random tensors. DataLoader is used for batch processing of datasets in PyTorch machine learning workflows.',
                    'title': 'Creating Tensors',
                    'page_title': 'Tensor Tutorial',
                    'section_title': 'Creating Tensors',
                    'type': 'code_example',
                    'word_count': 38
                }
            ]
        }

    def test_initialization(self):
        """Test RAG system initialization"""
        self.assertEqual(self.rag_system.chunk_size, 1200)
        self.assertEqual(self.rag_system.overlap, 100)
        self.assertEqual(len(self.rag_system.chunks), 0)
        self.assertEqual(len(self.rag_system.chunk_metadata), 0)

    def test_load_structured_data_file_not_found(self):
        """Test loading non-existent structured data file"""
        result = self.rag_system.load_structured_data("non_existent_file.json")
        self.assertFalse(result)

    def test_load_structured_data_success(self):
        """Test successful loading of structured data"""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_data, f)
            temp_file = f.name

        try:
            result = self.rag_system.load_structured_data(temp_file)
            self.assertTrue(result)
            self.assertIsNotNone(self.rag_system.structured_data)
            self.assertEqual(len(self.rag_system.structured_data['semantic_chunks']), 2)
        finally:
            os.unlink(temp_file)

    def test_load_and_basic_processing(self):
        """Test loading structured data and basic processing without full TF-IDF"""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_data, f)
            temp_file = f.name

        try:
            # Test loading structured data
            result = self.rag_system.load_structured_data(temp_file)
            self.assertTrue(result)
            self.assertEqual(len(self.rag_system.structured_data['semantic_chunks']), 2)

            # Test that structured data was loaded correctly
            chunks = self.rag_system.structured_data['semantic_chunks']
            self.assertIn('tensors', chunks[0]['text'].lower())
            self.assertIn('dataloader', chunks[1]['text'].lower())

        finally:
            os.unlink(temp_file)

    def test_demo_query_without_processing(self):
        """Test demo query without processing documents first"""
        result = self.rag_system.demo_query("test query")
        # Should return a string indicating system not initialized or no results
        self.assertIsInstance(result, str)
        self.assertTrue(
            'not initialized' in result.lower() or
            'no relevant documents' in result.lower()
        )

    def test_scrape_and_process_method_exists(self):
        """Test that scrape_and_process_website method exists"""
        self.assertTrue(hasattr(self.rag_system, 'scrape_and_process_website'))
        self.assertTrue(hasattr(self.rag_system, 'scraper'))
        self.assertIsNotNone(self.rag_system.scraper)

    def test_query_preprocessing(self):
        """Test query preprocessing functionality"""
        # Test with a basic query
        query = "tensor operations"
        processed = self.rag_system.preprocess_query(query)

        # Should return a string
        self.assertIsInstance(processed, str)
        self.assertTrue(len(processed) > 0)

    def test_system_attributes(self):
        """Test basic system attributes and methods exist"""
        # Test that basic attributes exist
        self.assertTrue(hasattr(self.rag_system, 'chunks'))
        self.assertTrue(hasattr(self.rag_system, 'chunk_metadata'))
        self.assertTrue(hasattr(self.rag_system, 'vectorizer'))
        self.assertTrue(hasattr(self.rag_system, 'tfidf_matrix'))

        # Test that key methods exist
        self.assertTrue(hasattr(self.rag_system, 'demo_query'))
        self.assertTrue(hasattr(self.rag_system, 'retrieve_context'))
        self.assertTrue(hasattr(self.rag_system, 'preprocess_query'))
        self.assertTrue(hasattr(self.rag_system, 'process_structured_documents'))


class TestRAGSystemIntegration(unittest.TestCase):
    """Integration tests for RAG system with real data"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.rag_system = RAGSystem()

    def test_process_existing_data_if_available(self):
        """Test processing any existing structured data"""
        # Look for any existing data files
        data_files = []
        if os.path.exists("data"):
            for filename in os.listdir("data"):
                if filename.endswith("_docs.json"):
                    data_files.append(os.path.join("data", filename))

        if data_files:
            # Test with the first available data file
            test_file = data_files[0]
            result = self.rag_system.process_structured_documents(test_file)

            if result:  # Only test queries if processing succeeded
                # Test a generic query
                query_result = self.rag_system.demo_query("documentation", top_k=3)

                # Should return a string result
                self.assertIsInstance(query_result, str)
                self.assertTrue(len(query_result) > 0)

                # Should indicate either found results or no results
                self.assertTrue(
                    'found' in query_result.lower() or
                    'retrieved' in query_result.lower() or
                    'no relevant' in query_result.lower()
                )
        else:
            self.skipTest("No data files available for testing")


if __name__ == '__main__':
    unittest.main()