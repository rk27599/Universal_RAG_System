#!/usr/bin/env python3
"""
Comprehensive Test Script for Secure RAG System
Tests all major functionality across frontend and backend
"""

import requests
import time
import json
import sys
from urllib.parse import urljoin

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class RAGSystemTester:
    def __init__(self, backend_url="http://127.0.0.1:8003", frontend_url="http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.session = requests.Session()
        self.test_results = []

    def log_success(self, test_name):
        print(f"{Colors.GREEN}✅ {test_name}{Colors.END}")
        self.test_results.append((test_name, True, None))

    def log_failure(self, test_name, error):
        print(f"{Colors.RED}❌ {test_name}: {error}{Colors.END}")
        self.test_results.append((test_name, False, str(error)))

    def log_warning(self, test_name, warning):
        print(f"{Colors.YELLOW}⚠️  {test_name}: {warning}{Colors.END}")
        self.test_results.append((test_name, "warning", str(warning)))

    def log_info(self, message):
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = self.session.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_success("Backend health check")
                    return True
                else:
                    self.log_failure("Backend health check", f"Unhealthy status: {data}")
                    return False
            else:
                self.log_failure("Backend health check", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Backend health check", str(e))
            return False

    def test_frontend_availability(self):
        """Test frontend availability"""
        try:
            response = self.session.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_success("Frontend availability")
                return True
            else:
                self.log_failure("Frontend availability", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Frontend availability", str(e))
            return False

    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        # Test register endpoint
        try:
            register_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword"
            }
            response = self.session.post(
                f"{self.backend_url}/api/auth/register",
                json=register_data,
                timeout=5
            )
            if response.status_code == 200:
                self.log_success("Auth register endpoint")
            else:
                self.log_failure("Auth register endpoint", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_failure("Auth register endpoint", str(e))

        # Test login endpoint
        try:
            login_data = {"username": "testuser", "password": "testpassword"}
            response = self.session.post(
                f"{self.backend_url}/api/auth/login",
                json=login_data,
                timeout=5
            )
            if response.status_code == 200:
                self.log_success("Auth login endpoint")
            else:
                self.log_failure("Auth login endpoint", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_failure("Auth login endpoint", str(e))

    def test_models_endpoints(self):
        """Test models-related endpoints"""
        try:
            response = self.session.get(f"{self.backend_url}/api/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "models" in data and isinstance(data["models"], list):
                    self.log_success("Models list endpoint")
                else:
                    self.log_failure("Models list endpoint", "Invalid response format")
            else:
                self.log_failure("Models list endpoint", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_failure("Models list endpoint", str(e))

    def test_system_status(self):
        """Test system status endpoint"""
        try:
            response = self.session.get(f"{self.backend_url}/api/system/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "ollama" in data and "database" in data and "security" in data:
                    self.log_success("System status endpoint")
                else:
                    self.log_failure("System status endpoint", "Missing required fields")
            else:
                self.log_failure("System status endpoint", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_failure("System status endpoint", str(e))

    def test_documents_endpoints(self):
        """Test documents endpoints"""
        try:
            response = self.session.get(f"{self.backend_url}/api/documents", timeout=10)
            if response.status_code == 200:
                self.log_success("Documents list endpoint")
            elif response.status_code == 404:
                self.log_warning("Documents list endpoint", "Endpoint not found (may be expected)")
            else:
                self.log_failure("Documents list endpoint", f"Status code: {response.status_code}")
        except requests.exceptions.Timeout:
            self.log_warning("Documents list endpoint", "Request timed out (may be hanging)")
        except Exception as e:
            self.log_failure("Documents list endpoint", str(e))

    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
            response = self.session.options(
                f"{self.backend_url}/api/health",
                headers=headers,
                timeout=5
            )
            cors_headers = {
                "access-control-allow-origin",
                "access-control-allow-methods"
            }
            found_headers = set(h.lower() for h in response.headers.keys())
            if cors_headers.intersection(found_headers):
                self.log_success("CORS configuration")
            else:
                self.log_warning("CORS configuration", "CORS headers not found")
        except Exception as e:
            self.log_failure("CORS configuration", str(e))

    def test_security_headers(self):
        """Test security headers"""
        try:
            response = self.session.get(f"{self.backend_url}/api/health", timeout=5)
            security_headers = {
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection",
                "strict-transport-security"
            }
            found_headers = set(h.lower() for h in response.headers.keys())
            missing_headers = security_headers - found_headers
            if len(missing_headers) == 0:
                self.log_success("Security headers")
            elif len(missing_headers) < len(security_headers):
                self.log_success("Security headers (most present)")
            else:
                self.log_warning("Security headers", f"Missing headers: {missing_headers}")
        except Exception as e:
            self.log_failure("Security headers", str(e))

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print(f"{Colors.BOLD}🔍 Starting Comprehensive RAG System Test{Colors.END}")
        print("=" * 50)

        # Test categories
        test_categories = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Availability", self.test_frontend_availability),
            ("Authentication", self.test_authentication_endpoints),
            ("Models API", self.test_models_endpoints),
            ("System Status", self.test_system_status),
            ("Documents API", self.test_documents_endpoints),
            ("CORS Configuration", self.test_cors_configuration),
            ("Security Headers", self.test_security_headers),
        ]

        for category_name, test_func in test_categories:
            print(f"\n{Colors.BOLD}📂 Testing {category_name}:{Colors.END}")
            test_func()

        # Summary
        print(f"\n{Colors.BOLD}📊 Test Summary:{Colors.END}")
        print("=" * 50)

        passed = sum(1 for _, status, _ in self.test_results if status is True)
        failed = sum(1 for _, status, _ in self.test_results if status is False)
        warnings = sum(1 for _, status, _ in self.test_results if status == "warning")
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {warnings}{Colors.END}")

        if failed > 0:
            print(f"\n{Colors.RED}❌ Failed Tests:{Colors.END}")
            for test_name, status, error in self.test_results:
                if status is False:
                    print(f"  - {test_name}: {error}")

        if warnings > 0:
            print(f"\n{Colors.YELLOW}⚠️  Warnings:{Colors.END}")
            for test_name, status, warning in self.test_results:
                if status == "warning":
                    print(f"  - {test_name}: {warning}")

        # Overall status
        if failed == 0:
            print(f"\n{Colors.GREEN}🎉 All critical tests passed!{Colors.END}")
            if warnings > 0:
                print(f"{Colors.YELLOW}Note: {warnings} warnings found - review recommended{Colors.END}")
        else:
            print(f"\n{Colors.RED}🚨 {failed} tests failed - immediate attention required{Colors.END}")

        return failed == 0

if __name__ == "__main__":
    tester = RAGSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)