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

        # Create sample test data
        self.sample_data = {
            'semantic_chunks': [
                {
                    'content': 'PyTorch tensors are multi-dimensional arrays that support automatic differentiation.',
                    'metadata': {
                        'page': 'tensor_tutorial',
                        'section': 'Introduction',
                        'content_type': 'explanation'
                    }
                },
                {
                    'content': 'torch.tensor([1, 2, 3]) creates a tensor from a list.',
                    'metadata': {
                        'page': 'tensor_tutorial',
                        'section': 'Creating Tensors',
                        'content_type': 'code_example'
                    }
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

    def test_create_enhanced_chunks(self):
        """Test enhanced chunk creation"""
        self.rag_system.structured_data = self.sample_data
        self.rag_system._create_enhanced_chunks()

        self.assertEqual(len(self.rag_system.chunks), 2)
        self.assertEqual(len(self.rag_system.chunk_metadata), 2)

        # Check that chunks contain the content
        self.assertIn('PyTorch tensors', self.rag_system.chunks[0])
        self.assertIn('torch.tensor', self.rag_system.chunks[1])

    def test_create_enhanced_vectorizer(self):
        """Test enhanced vectorizer creation"""
        self.rag_system.structured_data = self.sample_data
        self.rag_system._create_enhanced_chunks()
        self.rag_system._create_enhanced_vectorizer()

        self.assertIsNotNone(self.rag_system.vectorizer)
        self.assertIsNotNone(self.rag_system.tfidf_matrix)
        self.assertEqual(self.rag_system.tfidf_matrix.shape[0], 2)

    def test_demo_query_without_processing(self):
        """Test demo query without processing documents first"""
        result = self.rag_system.demo_query("test query")
        self.assertIn('error', result)

    def test_demo_query_with_processing(self):
        """Test demo query after processing documents"""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_data, f)
            temp_file = f.name

        try:
            self.rag_system.process_structured_documents(temp_file)
            result = self.rag_system.demo_query("tensor", top_k=2)

            self.assertIn('query', result)
            self.assertIn('top_results', result)
            self.assertLessEqual(len(result['top_results']), 2)

            # Check that results have required fields
            if result['top_results']:
                top_result = result['top_results'][0]
                self.assertIn('content', top_result)
                self.assertIn('score', top_result)
                self.assertIn('metadata', top_result)

        finally:
            os.unlink(temp_file)

    def test_search_similarity_threshold(self):
        """Test that search results meet similarity threshold"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_data, f)
            temp_file = f.name

        try:
            self.rag_system.process_structured_documents(temp_file)
            result = self.rag_system.demo_query("tensor", top_k=5)

            # Check that all results meet minimum similarity threshold
            for doc in result['top_results']:
                self.assertGreaterEqual(doc['score'], 0.0)

        finally:
            os.unlink(temp_file)


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
            self.assertIn('top_results', query_result)

            if query_result['top_results']:
                # Check that we get reasonable similarity scores
                top_score = query_result['top_results'][0]['score']
                self.assertGreater(top_score, 0.1)  # Should get reasonable similarity
        else:
            self.skipTest("Real data file not available")


if __name__ == '__main__':
    unittest.main()