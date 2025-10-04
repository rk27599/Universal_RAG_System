#!/usr/bin/env python3
"""
Phase 1 & Phase 2 Validation Test
Comprehensive testing to ensure all requirements are met before Phase 3
"""

import asyncio
import socketio
import requests
import json
import os
import subprocess
import time
from pathlib import Path

# Test configuration
API_BASE = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"
WEBSOCKET_URL = "http://127.0.0.1:8000"

class PhaseValidator:
    def __init__(self):
        self.phase1_results = {}
        self.phase2_results = {}
        self.overall_status = True

    def log_result(self, phase, test, result, details=""):
        """Log test results"""
        if phase == 1:
            self.phase1_results[test] = {'status': result, 'details': details}
        else:
            self.phase2_results[test] = {'status': result, 'details': details}

        if not result:
            self.overall_status = False

        status_icon = "✅" if result else "❌"
        print(f"   {status_icon} {test}: {details}")

    def test_phase1_backend_foundation(self):
        """Test Phase 1: Backend Foundation Requirements"""
        print("🔍 PHASE 1 VALIDATION: Backend Foundation")
        print("=" * 60)

        # 1. Security Framework
        print("\n1. Testing Security Framework...")
        try:
            # Test localhost-only configuration
            response = requests.get(f"{API_BASE}/health")
            if response.status_code == 200:
                data = response.json()
                security_mode = data.get('security_mode', '')
                if security_mode == 'local_only':
                    self.log_result(1, "Local-only Security", True, "Security mode verified")
                else:
                    self.log_result(1, "Local-only Security", False, f"Wrong security mode: {security_mode}")
            else:
                self.log_result(1, "Local-only Security", False, f"Health check failed: {response.status_code}")
        except Exception as e:
            self.log_result(1, "Local-only Security", False, f"Error: {e}")

        # Test security headers
        try:
            response = requests.get(f"{API_BASE}/health")
            headers = response.headers
            required_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            missing_headers = [h for h in required_headers if h not in headers]
            if not missing_headers:
                self.log_result(1, "Security Headers", True, "All security headers present")
            else:
                self.log_result(1, "Security Headers", False, f"Missing headers: {missing_headers}")
        except Exception as e:
            self.log_result(1, "Security Headers", False, f"Error: {e}")

        # 2. Database Models & API Development
        print("\n2. Testing Core API Development...")

        # Test authentication endpoints
        try:
            # Test login
            login_response = requests.post(f"{API_BASE}/auth/login", json={})
            if login_response.status_code == 200:
                login_data = login_response.json()
                if login_data.get('success'):
                    self.log_result(1, "Authentication API", True, "Login endpoint working")
                else:
                    self.log_result(1, "Authentication API", False, "Login failed")
            else:
                self.log_result(1, "Authentication API", False, f"Login status: {login_response.status_code}")
        except Exception as e:
            self.log_result(1, "Authentication API", False, f"Error: {e}")

        # Test document endpoints
        try:
            docs_response = requests.get(f"{API_BASE}/documents")
            if docs_response.status_code == 200:
                docs_data = docs_response.json()
                if docs_data.get('success'):
                    self.log_result(1, "Document API", True, "Document endpoints working")
                else:
                    self.log_result(1, "Document API", False, "Document API response invalid")
            else:
                self.log_result(1, "Document API", False, f"Documents status: {docs_response.status_code}")
        except Exception as e:
            self.log_result(1, "Document API", False, f"Error: {e}")

        # Test models API
        try:
            models_response = requests.get(f"{API_BASE}/models")
            if models_response.status_code == 200:
                models_data = models_response.json()
                if models_data.get('success'):
                    models = models_data.get('data', [])
                    if isinstance(models, list) and len(models) > 0:
                        self.log_result(1, "Models API", True, f"Models available: {', '.join(models)}")
                    else:
                        self.log_result(1, "Models API", False, "No models available")
                else:
                    self.log_result(1, "Models API", False, "Models API response invalid")
            else:
                self.log_result(1, "Models API", False, f"Models status: {models_response.status_code}")
        except Exception as e:
            self.log_result(1, "Models API", False, f"Error: {e}")

        # 3. WebSocket & Real-time Features
        print("\n3. Testing WebSocket & Real-time Features...")

        # Test conversation management
        try:
            conv_response = requests.post(f"{API_BASE}/conversations", json={"title": "Phase 1 Test"})
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                if conv_data.get('success'):
                    self.log_result(1, "Conversation Management", True, "Conversation creation working")
                else:
                    self.log_result(1, "Conversation Management", False, "Conversation creation failed")
            else:
                self.log_result(1, "Conversation Management", False, f"Status: {conv_response.status_code}")
        except Exception as e:
            self.log_result(1, "Conversation Management", False, f"Error: {e}")

    async def test_websocket_functionality(self):
        """Test WebSocket connectivity"""
        try:
            sio = socketio.AsyncClient()
            connected = False

            @sio.event
            async def connect():
                nonlocal connected
                connected = True
                await sio.emit('send_message', {
                    'conversationId': 'test-conv',
                    'content': 'Phase 1 WebSocket test',
                    'model': 'mistral'
                })

            @sio.event
            async def message(data):
                await sio.disconnect()

            await sio.connect(WEBSOCKET_URL)
            await asyncio.sleep(2)

            if connected:
                self.log_result(1, "WebSocket Support", True, "WebSocket connection successful")
            else:
                self.log_result(1, "WebSocket Support", False, "WebSocket connection failed")

        except Exception as e:
            self.log_result(1, "WebSocket Support", False, f"Error: {e}")

    def test_phase2_frontend_development(self):
        """Test Phase 2: Frontend Development Requirements"""
        print("\n🔍 PHASE 2 VALIDATION: Frontend Development")
        print("=" * 60)

        # 1. React Application Setup
        print("\n1. Testing React Application Setup...")

        # Check if frontend is running
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                self.log_result(2, "React App Running", True, "Frontend accessible")
            else:
                self.log_result(2, "React App Running", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result(2, "React App Running", False, f"Error: {e}")

        # Check frontend file structure
        frontend_path = Path("frontend/src")
        required_dirs = ['components', 'contexts', 'services', 'config']
        missing_dirs = []

        for dir_name in required_dirs:
            if not (frontend_path / dir_name).exists():
                missing_dirs.append(dir_name)

        if not missing_dirs:
            self.log_result(2, "Frontend Structure", True, "All required directories present")
        else:
            self.log_result(2, "Frontend Structure", False, f"Missing directories: {missing_dirs}")

        # 2. Authentication Flow
        print("\n2. Testing Authentication Flow...")

        # Check auth components exist
        auth_files = [
            "frontend/src/contexts/AuthContext.tsx",
            "frontend/src/services/api.ts"
        ]

        auth_files_exist = all(Path(f).exists() for f in auth_files)
        if auth_files_exist:
            self.log_result(2, "Authentication Components", True, "Auth components present")
        else:
            missing = [f for f in auth_files if not Path(f).exists()]
            self.log_result(2, "Authentication Components", False, f"Missing: {missing}")

        # 3. Chat Interface Implementation
        print("\n3. Testing Chat Interface Implementation...")

        # Check chat components
        chat_files = [
            "frontend/src/contexts/ChatContext.tsx",
            "frontend/src/components/Chat"
        ]

        chat_components_exist = True
        for file_path in chat_files:
            if not Path(file_path).exists():
                chat_components_exist = False
                break

        if chat_components_exist:
            self.log_result(2, "Chat Components", True, "Chat interface components present")
        else:
            self.log_result(2, "Chat Components", False, "Missing chat components")

        # Test chat context configuration
        try:
            with open("frontend/src/contexts/ChatContext.tsx", 'r') as f:
                content = f.read()
                if 'WebSocket' in content or 'socket.io' in content:
                    self.log_result(2, "WebSocket Integration", True, "WebSocket integration in chat context")
                else:
                    self.log_result(2, "WebSocket Integration", False, "No WebSocket integration found")
        except Exception as e:
            self.log_result(2, "WebSocket Integration", False, f"Error reading chat context: {e}")

        # 4. Document Management
        print("\n4. Testing Document Management...")

        # Check if document components exist
        doc_components = [
            "frontend/src/components/Documents",
            "frontend/src/contexts/DocumentContext.tsx"
        ]

        doc_exists = any(Path(p).exists() for p in doc_components)
        if doc_exists:
            self.log_result(2, "Document Management UI", True, "Document management components present")
        else:
            self.log_result(2, "Document Management UI", False, "Document management components missing")

        # Test configuration security
        try:
            with open("frontend/src/config/config.ts", 'r') as f:
                config_content = f.read()
                if 'localhost' in config_content or '127.0.0.1' in config_content:
                    self.log_result(2, "Frontend Security Config", True, "Localhost-only configuration")
                else:
                    self.log_result(2, "Frontend Security Config", False, "Non-localhost configuration detected")
        except Exception as e:
            self.log_result(2, "Frontend Security Config", False, f"Error reading config: {e}")

    def check_system_status(self):
        """Check overall system status"""
        print("\n📊 SYSTEM STATUS CHECK")
        print("=" * 60)

        try:
            status_response = requests.get(f"{API_BASE}/system/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                system_info = status_data.get('data', {})

                print(f"   🔧 Ollama Status: {system_info.get('ollama', {}).get('status', 'unknown')}")
                print(f"   💾 Database Status: {system_info.get('database', {}).get('status', 'unknown')}")
                print(f"   🔒 Security Score: {system_info.get('security', {}).get('score', 'unknown')}")

                ollama_status = system_info.get('ollama', {}).get('status', '') == 'running'
                db_status = system_info.get('database', {}).get('status', '') == 'connected'
                security_score = system_info.get('security', {}).get('score', 0) > 90

                if ollama_status and db_status and security_score:
                    print("   ✅ All systems operational")
                else:
                    print("   ⚠️  Some systems need attention")

        except Exception as e:
            print(f"   ❌ System status check failed: {e}")

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("📋 PHASE VALIDATION SUMMARY")
        print("=" * 60)

        # Phase 1 Summary
        print("\n🔧 PHASE 1 - Backend Foundation:")
        phase1_passed = sum(1 for result in self.phase1_results.values() if result['status'])
        phase1_total = len(self.phase1_results)
        print(f"   Passed: {phase1_passed}/{phase1_total} tests")

        for test, result in self.phase1_results.items():
            status = "✅" if result['status'] else "❌"
            print(f"   {status} {test}")

        # Phase 2 Summary
        print("\n💻 PHASE 2 - Frontend Development:")
        phase2_passed = sum(1 for result in self.phase2_results.values() if result['status'])
        phase2_total = len(self.phase2_results)
        print(f"   Passed: {phase2_passed}/{phase2_total} tests")

        for test, result in self.phase2_results.items():
            status = "✅" if result['status'] else "❌"
            print(f"   {status} {test}")

        # Overall Status
        print(f"\n🎯 OVERALL STATUS:")
        if self.overall_status:
            print("   ✅ READY FOR PHASE 3: Integration & Security")
            print("   🚀 All Phase 1 & 2 requirements validated successfully")
        else:
            print("   ❌ NOT READY - Issues found that need resolution")
            print("   🔧 Please address failed tests before proceeding")

        print("\n📍 Next Steps:")
        if self.overall_status:
            print("   1. Proceed with Phase 3: Integration & Security")
            print("   2. Implement error handling and user feedback")
            print("   3. Add offline capability and service worker")
            print("   4. Create comprehensive testing suite")
            print("   5. Performance optimization and caching")
        else:
            print("   1. Fix failed validation tests")
            print("   2. Re-run validation")
            print("   3. Ensure all Phase 1 & 2 requirements are met")

async def main():
    """Run comprehensive phase validation"""
    print("🚀 STARTING PHASE 1 & 2 VALIDATION")
    print("Comprehensive testing before Phase 3: Integration & Security")
    print("=" * 60)

    validator = PhaseValidator()

    # Test Phase 1
    validator.test_phase1_backend_foundation()
    await validator.test_websocket_functionality()

    # Test Phase 2
    validator.test_phase2_frontend_development()

    # System status
    validator.check_system_status()

    # Summary
    validator.print_summary()

if __name__ == "__main__":
    asyncio.run(main())