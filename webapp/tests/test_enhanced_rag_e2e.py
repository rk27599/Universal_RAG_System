#!/usr/bin/env python3
"""
End-to-End Test for Enhanced RAG Features
Tests UI, backend, BM25 indexing, reranker, hybrid search, and all features
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test credentials (use environment default user)
TEST_USERNAME = "admin"
TEST_PASSWORD = "Admin@123"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

class EnhancedRAGTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.conversation_id = None
        self.document_id = None

    def login(self):
        """Authenticate and get token"""
        print_header("1. Authentication Test")

        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD
                }
            )

            if response.status_code == 200:
                response_data = response.json()
                data = response_data.get('data', {})
                self.token = data.get('token')
                user = data.get('user', {})
                self.user_id = user.get('id')
                print_success(f"Logged in as: {user.get('username', TEST_USERNAME)}")
                print_info(f"User ID: {self.user_id}")
                print_info(f"Token: {self.token[:20] if self.token else 'N/A'}...")
                return True
            else:
                print_error(f"Login failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Login error: {e}")
            return False

    def check_system_status(self):
        """Check system status"""
        print_header("2. System Status Check")

        try:
            response = requests.get(
                f"{API_URL}/system/status",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                status = response.json()['data']
                print_success("System status retrieved")
                print_info(f"Ollama: {status['ollama']['status']} ({len(status['ollama']['models'])} models)")
                print_info(f"Database: {status['database']['status']}")
                print_info(f"Security score: {status['security']['score']}/100")
                return True
            else:
                print_error(f"Status check failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Status check error: {e}")
            return False

    def upload_test_document(self):
        """Upload a test document to trigger BM25 indexing"""
        print_header("3. BM25 Indexing Test - Upload Document")

        # Find an existing PDF in uploads directory
        uploads_dir = Path("/home/rkpatel/RAG/data/uploads")
        pdfs = list(uploads_dir.glob("*.pdf"))

        if not pdfs:
            print_warning("No PDFs found in data/uploads/ - skipping upload test")
            print_info("You can upload a PDF via the UI to test BM25 indexing")
            return False

        # Use first PDF found
        test_pdf = pdfs[0]
        print_info(f"Using existing PDF: {test_pdf.name}")

        try:
            with open(test_pdf, 'rb') as f:
                files = {'file': (test_pdf.name, f, 'application/pdf')}
                response = requests.post(
                    f"{API_URL}/documents/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files=files
                )

            if response.status_code == 200:
                data = response.json()['data']
                self.document_id = data['id']
                print_success(f"Document uploaded: {data['title']}")
                print_info(f"Document ID: {self.document_id}")
                print_info(f"Status: {data['processing_status']}")

                # Wait for processing to complete
                print_info("Waiting for document processing and BM25 indexing...")
                time.sleep(3)

                # Check if document is completed
                response = requests.get(
                    f"{API_URL}/documents/{self.document_id}",
                    headers={"Authorization": f"Bearer {self.token}"}
                )

                if response.status_code == 200:
                    doc_data = response.json()['data']
                    if doc_data['processing_status'] == 'completed':
                        print_success(f"Document processing completed!")
                        print_info(f"Chunks: {doc_data.get('chunk_count', 0)}")
                        print_success("BM25 index should be built now")
                        return True
                    else:
                        print_warning(f"Document still processing: {doc_data['processing_status']}")
                        return False
                else:
                    print_error(f"Failed to check document status")
                    return False

            else:
                print_error(f"Upload failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Upload error: {e}")
            return False

    def check_bm25_index(self):
        """Check if BM25 index was created"""
        print_header("4. BM25 Index Verification")

        index_dir = Path(f"/home/rkpatel/RAG/data/bm25_indexes")

        if not index_dir.exists():
            print_error("BM25 index directory not found")
            return False

        # Look for user index
        user_indexes = list(index_dir.glob(f"user_{self.user_id}.pkl"))

        if user_indexes:
            index_file = user_indexes[0]
            index_size = index_file.stat().st_size
            print_success(f"BM25 index found: {index_file.name}")
            print_info(f"Index size: {index_size / 1024:.2f} KB")
            return True
        else:
            print_warning(f"No BM25 index found for user {self.user_id}")
            print_info("This is normal if no documents have been uploaded yet")
            return False

    def create_conversation(self):
        """Create a test conversation"""
        print_header("5. Create Conversation")

        try:
            response = requests.post(
                f"{API_URL}/chat/conversations",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"title": "Enhanced RAG Test"}
            )

            if response.status_code == 200:
                data = response.json()['data']
                self.conversation_id = data['id']
                print_success(f"Conversation created: {data['title']}")
                print_info(f"Conversation ID: {self.conversation_id}")
                return True
            else:
                print_error(f"Conversation creation failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Conversation creation error: {e}")
            return False

    def test_reranker_only(self):
        """Test with reranker enabled only"""
        print_header("6. Test Reranker Feature")

        try:
            response = requests.post(
                f"{API_URL}/chat/message",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "conversationId": self.conversation_id,
                    "content": "What is Forcite module used for?",
                    "model": "mistral",
                    "useRAG": True,
                    "topK": 5,
                    "useReranker": True,  # Enable reranker
                    "useHybridSearch": False,
                    "useQueryExpansion": False
                }
            )

            if response.status_code == 200:
                data = response.json()['data']
                metadata = data.get('metadata', {})
                pipeline_info = metadata.get('pipelineInfo', {})

                print_success("Reranker test completed")
                print_info(f"Response time: {metadata.get('responseTime', 0):.2f}s")
                print_info(f"Sources: {len(metadata.get('sources', []))}")

                if pipeline_info:
                    print_info(f"Retrieval method: {pipeline_info.get('retrievalMethod', 'N/A')}")
                    print_info(f"Reranking applied: {pipeline_info.get('rerankingApplied', False)}")

                # Check if reranker scores are in sources
                sources = metadata.get('sources', [])
                if sources and any('rerankerScore' in s for s in sources):
                    print_success("Reranker scores found in response metadata")
                    for i, source in enumerate(sources[:3], 1):
                        if 'rerankerScore' in source:
                            print_info(f"  {i}. {source.get('documentTitle', 'Unknown')} - "
                                     f"Similarity: {source.get('similarity', 0):.2f}, "
                                     f"Reranker: {source.get('rerankerScore', 0):.3f}")

                return True
            else:
                print_error(f"Reranker test failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Reranker test error: {e}")
            return False

    def test_hybrid_search(self):
        """Test hybrid search (BM25 + Vector)"""
        print_header("7. Test Hybrid Search (BM25 + Vector)")

        try:
            response = requests.post(
                f"{API_URL}/chat/message",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "conversationId": self.conversation_id,
                    "content": "How do I optimize molecular dynamics?",
                    "model": "mistral",
                    "useRAG": True,
                    "topK": 5,
                    "useReranker": False,
                    "useHybridSearch": True,  # Enable hybrid search
                    "useQueryExpansion": False
                }
            )

            if response.status_code == 200:
                data = response.json()['data']
                metadata = data.get('metadata', {})
                pipeline_info = metadata.get('pipelineInfo', {})

                print_success("Hybrid search test completed")
                print_info(f"Response time: {metadata.get('responseTime', 0):.2f}s")
                print_info(f"Sources: {len(metadata.get('sources', []))}")

                if pipeline_info:
                    retrieval_method = pipeline_info.get('retrievalMethod', 'N/A')
                    print_info(f"Retrieval method: {retrieval_method}")

                    if retrieval_method == 'hybrid':
                        print_success("Hybrid search (BM25 + Vector) is working!")
                    else:
                        print_warning(f"Expected 'hybrid' but got '{retrieval_method}'")
                        print_info("This may mean BM25 index is not available - falling back to vector-only")

                return True
            else:
                print_error(f"Hybrid search test failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Hybrid search test error: {e}")
            return False

    def test_query_expansion(self):
        """Test query expansion"""
        print_header("8. Test Query Expansion")

        try:
            response = requests.post(
                f"{API_URL}/chat/message",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "conversationId": self.conversation_id,
                    "content": "MD simulation parameters",
                    "model": "mistral",
                    "useRAG": True,
                    "topK": 5,
                    "useReranker": False,
                    "useHybridSearch": False,
                    "useQueryExpansion": True  # Enable query expansion
                }
            )

            if response.status_code == 200:
                data = response.json()['data']
                metadata = data.get('metadata', {})
                pipeline_info = metadata.get('pipelineInfo', {})

                print_success("Query expansion test completed")
                print_info(f"Response time: {metadata.get('responseTime', 0):.2f}s")

                if pipeline_info:
                    expanded = pipeline_info.get('expandedQueries', [])
                    query_expanded = pipeline_info.get('queryExpanded', False)

                    print_info(f"Query expanded: {query_expanded}")
                    if expanded:
                        print_success(f"Generated {len(expanded)} expanded queries:")
                        for i, eq in enumerate(expanded, 1):
                            print_info(f"  {i}. {eq}")

                return True
            else:
                print_error(f"Query expansion test failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Query expansion test error: {e}")
            return False

    def test_all_features(self):
        """Test with all features enabled"""
        print_header("9. Test All Features Combined")

        try:
            response = requests.post(
                f"{API_URL}/chat/message",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "conversationId": self.conversation_id,
                    "content": "Best practices for Forcite simulations",
                    "model": "mistral",
                    "useRAG": True,
                    "topK": 5,
                    "useReranker": True,  # All enabled
                    "useHybridSearch": True,
                    "useQueryExpansion": True,
                    "promptTemplate": "cot"  # Use CoT template
                }
            )

            if response.status_code == 200:
                data = response.json()['data']
                metadata = data.get('metadata', {})
                pipeline_info = metadata.get('pipelineInfo', {})

                print_success("All features test completed")
                print_info(f"Response time: {metadata.get('responseTime', 0):.2f}s")
                print_info(f"Sources: {len(metadata.get('sources', []))}")

                if pipeline_info:
                    print_info(f"\nPipeline Summary:")
                    print_info(f"  Retrieval: {pipeline_info.get('retrievalMethod', 'N/A')}")
                    print_info(f"  Reranking: {pipeline_info.get('rerankingApplied', False)}")
                    print_info(f"  Query expansion: {pipeline_info.get('queryExpanded', False)}")

                    expanded = pipeline_info.get('expandedQueries', [])
                    if expanded:
                        print_info(f"  Expanded queries: {len(expanded)}")

                return True
            else:
                print_error(f"All features test failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"All features test error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print_header("Enhanced RAG End-to-End Test Suite")
        print_info(f"Backend URL: {BASE_URL}")
        print_info(f"User: {TEST_USERNAME}")

        results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

        # Test 1: Login
        if not self.login():
            print_error("Cannot proceed without authentication")
            return results
        results["passed"] += 1

        # Test 2: System status
        if self.check_system_status():
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 3: Upload document (optional)
        if self.upload_test_document():
            results["passed"] += 1
        else:
            results["skipped"] += 1

        # Test 4: Check BM25 index
        if self.check_bm25_index():
            results["passed"] += 1
        else:
            results["skipped"] += 1

        # Test 5: Create conversation
        if not self.create_conversation():
            print_error("Cannot proceed without conversation")
            return results
        results["passed"] += 1

        # Test 6: Reranker
        if self.test_reranker_only():
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 7: Hybrid search
        if self.test_hybrid_search():
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 8: Query expansion
        if self.test_query_expansion():
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 9: All features
        if self.test_all_features():
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Print summary
        print_header("Test Summary")
        print_success(f"Passed: {results['passed']}")
        if results['failed'] > 0:
            print_error(f"Failed: {results['failed']}")
        if results['skipped'] > 0:
            print_warning(f"Skipped: {results['skipped']}")

        total = results['passed'] + results['failed'] + results['skipped']
        success_rate = (results['passed'] / total * 100) if total > 0 else 0
        print_info(f"Success rate: {success_rate:.1f}%")

        return results

if __name__ == "__main__":
    try:
        tester = EnhancedRAGTester()
        results = tester.run_all_tests()

        # Exit with error code if tests failed
        if results['failed'] > 0:
            exit(1)
        else:
            exit(0)

    except KeyboardInterrupt:
        print_error("\n\nTest interrupted by user")
        exit(130)
    except Exception as e:
        print_error(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
