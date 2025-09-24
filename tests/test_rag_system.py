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

from src.enhanced_rag_system_v2 import EnhancedRAGSystemV2


class TestEnhancedRAGSystem(unittest.TestCase):
    """Test cases for EnhancedRAGSystemV2"""

    def setUp(self):
        """Set up test fixtures"""
        self.rag_system = EnhancedRAGSystemV2()

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
        self.rag_system = EnhancedRAGSystemV2()
        self.data_file = "data/pytorch_docs_structured.json"

    def test_process_real_data_if_exists(self):
        """Test processing real PyTorch documentation data if available"""
        if os.path.exists(self.data_file):
            result = self.rag_system.process_structured_documents(self.data_file)
            self.assertTrue(result)

            # Test a real query
            query_result = self.rag_system.demo_query("DataLoader", top_k=3)

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
            self.skipTest("Real data file not available")


if __name__ == '__main__':
    unittest.main()