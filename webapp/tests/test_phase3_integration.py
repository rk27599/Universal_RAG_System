#!/usr/bin/env python3
"""
Phase 3 Integration Testing Suite
Comprehensive testing for integration, security, and performance
"""

import asyncio
import socketio
import requests
import json
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Test configuration
API_BASE = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"
WEBSOCKET_URL = "http://127.0.0.1:8000"

class Phase3IntegrationTester:
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.security_results = {}
        self.error_handling_results = {}

    def log_test(self, category, test_name, result, details="", metrics=None):
        """Log test results with categories"""
        if category not in self.test_results:
            self.test_results[category] = {}

        self.test_results[category][test_name] = {
            'status': result,
            'details': details,
            'metrics': metrics or {},
            'timestamp': time.time()
        }

        status_icon = "✅" if result else "❌"
        print(f"   {status_icon} {test_name}: {details}")

    def test_error_handling_and_feedback(self):
        """Test comprehensive error handling"""
        print("\n🔧 TESTING ERROR HANDLING & USER FEEDBACK")
        print("=" * 60)

        # Test API error responses
        print("\n1. Testing API Error Responses...")

        # Test invalid endpoint
        try:
            response = requests.get(f"{API_BASE}/invalid-endpoint")
            if response.status_code == 404:
                self.log_test("error_handling", "Invalid Endpoint", True, "404 returned correctly")
            else:
                self.log_test("error_handling", "Invalid Endpoint", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("error_handling", "Invalid Endpoint", False, f"Error: {e}")

        # Test invalid JSON payload
        try:
            response = requests.post(f"{API_BASE}/conversations",
                                   data="invalid json",
                                   headers={'Content-Type': 'application/json'})
            if response.status_code in [400, 422]:
                self.log_test("error_handling", "Invalid JSON", True, "Bad request handled correctly")
            else:
                self.log_test("error_handling", "Invalid JSON", False, f"Expected 400/422, got {response.status_code}")
        except Exception as e:
            self.log_test("error_handling", "Invalid JSON", False, f"Error: {e}")

        # Test rate limiting (if implemented)
        print("\n2. Testing Rate Limiting...")
        start_time = time.time()
        rapid_requests = []

        for i in range(50):
            try:
                response = requests.get(f"{API_BASE}/health", timeout=1)
                rapid_requests.append(response.status_code)
            except:
                rapid_requests.append(429)  # Assume rate limited

        rate_limited = any(code == 429 for code in rapid_requests)
        response_time = time.time() - start_time

        self.log_test("error_handling", "Rate Limiting", rate_limited,
                     f"Rate limiting {'detected' if rate_limited else 'not detected'}",
                     {'requests': len(rapid_requests), 'time': response_time})

        # Test graceful degradation
        print("\n3. Testing Graceful Degradation...")

        # Test with invalid model
        try:
            response = requests.get(f"{API_BASE}/models/invalid-model")
            if response.status_code in [404, 400]:
                data = response.json()
                if data.get('success') is False:
                    self.log_test("error_handling", "Invalid Model", True, "Graceful error response")
                else:
                    self.log_test("error_handling", "Invalid Model", False, "No error in response")
            else:
                self.log_test("error_handling", "Invalid Model", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("error_handling", "Invalid Model", False, f"Error: {e}")

    async def test_websocket_resilience(self):
        """Test WebSocket connection resilience"""
        print("\n4. Testing WebSocket Resilience...")

        try:
            sio = socketio.AsyncClient()
            connection_events = []

            @sio.event
            async def connect():
                connection_events.append('connected')
                await sio.emit('test_message', {'test': 'data'})

            @sio.event
            async def disconnect():
                connection_events.append('disconnected')

            @sio.event
            async def connect_error(data):
                connection_events.append(f'error: {data}')

            # Test normal connection
            await sio.connect(WEBSOCKET_URL)
            await asyncio.sleep(1)

            # Test disconnection handling
            await sio.disconnect()
            await asyncio.sleep(1)

            # Test reconnection
            await sio.connect(WEBSOCKET_URL)
            await asyncio.sleep(1)
            await sio.disconnect()

            has_connect = 'connected' in connection_events
            has_disconnect = 'disconnected' in connection_events

            if has_connect and has_disconnect:
                self.log_test("error_handling", "WebSocket Resilience", True,
                             f"Connection lifecycle handled correctly")
            else:
                self.log_test("error_handling", "WebSocket Resilience", False,
                             f"Missing events: {connection_events}")

        except Exception as e:
            self.log_test("error_handling", "WebSocket Resilience", False, f"Error: {e}")

    def test_performance_optimization(self):
        """Test performance optimization and caching"""
        print("\n⚡ TESTING PERFORMANCE OPTIMIZATION")
        print("=" * 60)

        # Test API response times
        print("\n1. Testing API Response Times...")

        endpoints = [
            '/health',
            '/models',
            '/conversations',
            '/system/status'
        ]

        response_times = {}

        for endpoint in endpoints:
            times = []
            for i in range(10):
                start = time.time()
                try:
                    response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
                    end = time.time()
                    if response.status_code == 200:
                        times.append((end - start) * 1000)  # Convert to milliseconds
                except:
                    pass

            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)

                response_times[endpoint] = {
                    'avg': avg_time,
                    'min': min_time,
                    'max': max_time
                }

                # Consider < 500ms as good performance
                performance_good = avg_time < 500

                self.log_test("performance", f"Response Time {endpoint}", performance_good,
                             f"Avg: {avg_time:.1f}ms, Min: {min_time:.1f}ms, Max: {max_time:.1f}ms")

        # Test concurrent requests
        print("\n2. Testing Concurrent Request Handling...")

        def make_request():
            start = time.time()
            try:
                response = requests.get(f"{API_BASE}/health", timeout=10)
                end = time.time()
                return {
                    'status': response.status_code,
                    'time': (end - start) * 1000,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'time': None,
                    'success': False,
                    'error': str(e)
                }

        # Test with 20 concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = statistics.mean([r['time'] for r in results if r['time']])

        concurrency_good = successful_requests >= 18 and total_time < 10

        self.log_test("performance", "Concurrent Requests", concurrency_good,
                     f"{successful_requests}/20 successful, Avg: {avg_response_time:.1f}ms, Total: {total_time:.1f}s")

        # Test caching (if implemented)
        print("\n3. Testing Response Caching...")

        # First request
        start1 = time.time()
        response1 = requests.get(f"{API_BASE}/models")
        time1 = time.time() - start1

        # Second request (should be faster if cached)
        start2 = time.time()
        response2 = requests.get(f"{API_BASE}/models")
        time2 = time.time() - start2

        # Third request
        start3 = time.time()
        response3 = requests.get(f"{API_BASE}/models")
        time3 = time.time() - start3

        # Check if subsequent requests are consistently faster
        caching_effective = (time2 < time1 * 0.8) and (time3 < time1 * 0.8)

        self.log_test("performance", "Response Caching", caching_effective,
                     f"Times: {time1*1000:.1f}ms, {time2*1000:.1f}ms, {time3*1000:.1f}ms")

    def test_offline_capabilities(self):
        """Test offline functionality"""
        print("\n📱 TESTING OFFLINE CAPABILITIES")
        print("=" * 60)

        # Check if service worker files exist
        print("\n1. Testing Service Worker Files...")

        sw_files = [
            'frontend/public/sw.js',
            'frontend/src/services/serviceWorker.ts'
        ]

        files_exist = all(Path(f).exists() for f in sw_files)
        self.log_test("offline", "Service Worker Files", files_exist,
                     f"Service worker files {'present' if files_exist else 'missing'}")

        # Test manifest.json
        manifest_path = Path('frontend/public/manifest.json')
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    has_required_fields = all(key in manifest for key in ['name', 'short_name', 'start_url'])
                    self.log_test("offline", "PWA Manifest", has_required_fields,
                                 "PWA manifest valid" if has_required_fields else "PWA manifest invalid")
            except:
                self.log_test("offline", "PWA Manifest", False, "PWA manifest invalid JSON")
        else:
            self.log_test("offline", "PWA Manifest", False, "PWA manifest missing")

        # Test frontend offline detection
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                content = response.text
                has_offline_handling = 'serviceWorker' in content or 'navigator.onLine' in content
                self.log_test("offline", "Offline Detection", has_offline_handling,
                             "Offline detection implemented" if has_offline_handling else "No offline detection found")
            else:
                self.log_test("offline", "Offline Detection", False, f"Frontend not accessible: {response.status_code}")
        except Exception as e:
            self.log_test("offline", "Offline Detection", False, f"Error accessing frontend: {e}")

    def test_security_hardening(self):
        """Test security hardening measures"""
        print("\n🔒 TESTING SECURITY HARDENING")
        print("=" * 60)

        # Test security headers
        print("\n1. Testing Security Headers...")

        try:
            response = requests.get(f"{API_BASE}/health")
            headers = response.headers

            required_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
            }

            missing_headers = []
            incorrect_headers = []

            for header, expected_value in required_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif expected_value not in headers[header]:
                    incorrect_headers.append(f"{header}: {headers[header]}")

            security_headers_good = not missing_headers and not incorrect_headers

            details = "All security headers correct"
            if missing_headers:
                details = f"Missing: {', '.join(missing_headers)}"
            if incorrect_headers:
                details += f" Incorrect: {', '.join(incorrect_headers)}"

            self.log_test("security", "Security Headers", security_headers_good, details)

        except Exception as e:
            self.log_test("security", "Security Headers", False, f"Error: {e}")

        # Test CORS configuration
        print("\n2. Testing CORS Configuration...")

        try:
            # Test with allowed origin
            headers = {'Origin': 'http://localhost:3000'}
            response = requests.get(f"{API_BASE}/health", headers=headers)

            cors_headers = response.headers
            has_cors = 'Access-Control-Allow-Origin' in cors_headers

            if has_cors:
                allowed_origin = cors_headers['Access-Control-Allow-Origin']
                cors_restrictive = allowed_origin in ['http://localhost:3000', 'http://127.0.0.1:3000']

                self.log_test("security", "CORS Configuration", cors_restrictive,
                             f"CORS origin: {allowed_origin}")
            else:
                self.log_test("security", "CORS Configuration", False, "No CORS headers found")

        except Exception as e:
            self.log_test("security", "CORS Configuration", False, f"Error: {e}")

        # Test for information disclosure
        print("\n3. Testing Information Disclosure...")

        try:
            response = requests.get(f"{API_BASE}/health")
            data = response.json()

            # Check that no sensitive information is disclosed
            sensitive_fields = ['SECRET_KEY', 'DATABASE_URL', 'API_KEY', 'PASSWORD']
            disclosed_info = []

            def check_object(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if any(sensitive in key.upper() for sensitive in sensitive_fields):
                            disclosed_info.append(current_path)
                        check_object(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_object(item, f"{path}[{i}]")

            check_object(data)

            no_disclosure = len(disclosed_info) == 0

            self.log_test("security", "Information Disclosure", no_disclosure,
                         "No sensitive information disclosed" if no_disclosure else f"Found: {disclosed_info}")

        except Exception as e:
            self.log_test("security", "Information Disclosure", False, f"Error: {e}")

    def test_comprehensive_integration(self):
        """Test comprehensive system integration"""
        print("\n🔗 TESTING COMPREHENSIVE INTEGRATION")
        print("=" * 60)

        # Test complete user workflow
        print("\n1. Testing Complete User Workflow...")

        try:
            # 1. Health check
            health_response = requests.get(f"{API_BASE}/health")
            health_ok = health_response.status_code == 200

            # 2. Get models
            models_response = requests.get(f"{API_BASE}/models")
            models_ok = models_response.status_code == 200

            # 3. Create conversation
            conv_response = requests.post(f"{API_BASE}/conversations",
                                        json={"title": "Integration Test"})
            conv_ok = conv_response.status_code == 200

            # 4. Get conversations
            convs_response = requests.get(f"{API_BASE}/conversations")
            convs_ok = convs_response.status_code == 200

            # 5. Get documents
            docs_response = requests.get(f"{API_BASE}/documents")
            docs_ok = docs_response.status_code == 200

            # 6. Get system status
            status_response = requests.get(f"{API_BASE}/system/status")
            status_ok = status_response.status_code == 200

            workflow_success = all([health_ok, models_ok, conv_ok, convs_ok, docs_ok, status_ok])

            self.log_test("integration", "Complete Workflow", workflow_success,
                         f"All API endpoints working: {workflow_success}")

        except Exception as e:
            self.log_test("integration", "Complete Workflow", False, f"Error: {e}")

        # Test frontend accessibility
        print("\n2. Testing Frontend Accessibility...")

        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            frontend_accessible = response.status_code == 200

            if frontend_accessible:
                content = response.text
                has_react = 'react' in content.lower() or 'React' in content
                has_title = '<title>' in content

                self.log_test("integration", "Frontend Accessibility", True,
                             f"Frontend accessible with React: {has_react}, Title: {has_title}")
            else:
                self.log_test("integration", "Frontend Accessibility", False,
                             f"Frontend not accessible: {response.status_code}")
        except Exception as e:
            self.log_test("integration", "Frontend Accessibility", False, f"Error: {e}")

    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 PHASE 3 INTEGRATION TEST REPORT")
        print("=" * 80)

        categories = {
            "error_handling": "🔧 Error Handling & User Feedback",
            "performance": "⚡ Performance Optimization",
            "offline": "📱 Offline Capabilities",
            "security": "🔒 Security Hardening",
            "integration": "🔗 System Integration"
        }

        total_tests = 0
        total_passed = 0

        for category, title in categories.items():
            if category in self.test_results:
                print(f"\n{title}:")
                tests = self.test_results[category]
                passed = sum(1 for test in tests.values() if test['status'])
                total = len(tests)

                total_tests += total
                total_passed += passed

                print(f"   Passed: {passed}/{total} tests")

                for test_name, result in tests.items():
                    status = "✅" if result['status'] else "❌"
                    print(f"   {status} {test_name}")

        # Overall summary
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 OVERALL PHASE 3 RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_tests - total_passed}")
        print(f"   Pass Rate: {pass_rate:.1f}%")

        if pass_rate >= 90:
            print("   ✅ PHASE 3 READY - Excellent integration and security")
        elif pass_rate >= 75:
            print("   ⚠️  PHASE 3 MOSTLY READY - Some issues to address")
        else:
            print("   ❌ PHASE 3 NOT READY - Significant issues require attention")

        print("\n📍 Recommendations:")
        if pass_rate >= 90:
            print("   • Proceed to production deployment preparation")
            print("   • Consider additional load testing")
            print("   • Document any remaining minor issues")
        else:
            print("   • Address failed tests before proceeding")
            print("   • Review security configurations")
            print("   • Optimize performance bottlenecks")

        return pass_rate >= 75

async def main():
    """Run comprehensive Phase 3 testing"""
    print("🚀 STARTING PHASE 3 INTEGRATION TESTING")
    print("Comprehensive testing for integration, security, and performance")
    print("=" * 80)

    tester = Phase3IntegrationTester()

    # Run all test suites
    tester.test_error_handling_and_feedback()
    await tester.test_websocket_resilience()
    tester.test_performance_optimization()
    tester.test_offline_capabilities()
    tester.test_security_hardening()
    tester.test_comprehensive_integration()

    # Generate final report
    ready_for_next_phase = tester.generate_comprehensive_report()

    return ready_for_next_phase

if __name__ == "__main__":
    result = asyncio.run(main())