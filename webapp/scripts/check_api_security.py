#!/usr/bin/env python3
"""
API Security Checker
Validates FastAPI endpoints for security compliance
"""

import sys
import re
import ast
from pathlib import Path
from typing import List, Dict

class APISecurityChecker:
    def __init__(self):
        self.violations = []
        self.warnings = []

    def check_api_file(self, api_file: str) -> bool:
        """Check API file for security issues"""
        print(f"🔍 Checking API security: {api_file}")

        try:
            with open(api_file, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Could not read API file: {e}")
            return False

        # Parse Python AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"❌ Could not parse Python file: {e}")
            return False

        success = True
        success &= self._check_external_api_calls(content, api_file)
        success &= self._check_authentication(content, api_file)
        success &= self._check_cors_configuration(content, api_file)
        success &= self._check_rate_limiting(content, api_file)
        success &= self._check_input_validation(tree, api_file)
        success &= self._check_error_handling(content, api_file)

        return success

    def _check_external_api_calls(self, content: str, file_path: str) -> bool:
        """Check for external API calls"""
        success = True

        # Check for external HTTP requests
        external_patterns = [
            r'requests\.(?:get|post|put|delete)\s*\(\s*["\']https?://(?!localhost|127\.0\.0\.1)([^"\']+)["\']',
            r'httpx\.(?:get|post|put|delete)\s*\(\s*["\']https?://(?!localhost|127\.0\.0\.1)([^"\']+)["\']',
            r'urllib\.request\.urlopen\s*\(\s*["\']https?://(?!localhost|127\.0\.0\.1)([^"\']+)["\']'
        ]

        for pattern in external_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.violations.append(f"External API call detected: {match}")
                success = False

        # Check for external API imports
        external_imports = [
            'openai', 'anthropic', 'pinecone', 'cohere',
            'boto3', 'azure', 'google.cloud'
        ]

        for imp in external_imports:
            if re.search(f'^(import|from)\s+{imp}', content, re.MULTILINE):
                self.violations.append(f"External API import: {imp}")
                success = False

        return success

    def _check_authentication(self, content: str, file_path: str) -> bool:
        """Check authentication implementation"""
        success = True

        # Check for endpoints without authentication
        endpoint_pattern = r'@app\.(?:get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']'
        endpoints = re.findall(endpoint_pattern, content)

        # Check for Depends(get_current_user) or similar
        auth_patterns = [
            r'Depends\s*\(\s*get_current_user\s*\)',
            r'Depends\s*\(\s*security_manager\.',
            r'@login_required',
            r'@auth_required'
        ]

        for endpoint in endpoints:
            if endpoint.startswith('/auth') or endpoint in ['/health', '/docs', '/openapi.json']:
                continue  # Skip auth and health endpoints

            has_auth = any(re.search(pattern, content) for pattern in auth_patterns)
            if not has_auth:
                self.warnings.append(f"Endpoint may lack authentication: {endpoint}")

        return success

    def _check_cors_configuration(self, content: str, file_path: str) -> bool:
        """Check CORS configuration"""
        success = True

        # Check for wildcard CORS
        if re.search(r'allow_origins\s*=\s*\[\s*["\*"]["\*"]\s*\]', content):
            self.violations.append("CORS configured with wildcard (*) - security risk")
            success = False

        # Check for external origins
        origins_pattern = r'allow_origins\s*=\s*\[(.*?)\]'
        matches = re.findall(origins_pattern, content, re.DOTALL)
        for match in matches:
            origins = re.findall(r'["\']([^"\']+)["\']', match)
            for origin in origins:
                if not ('localhost' in origin or '127.0.0.1' in origin or origin == '*'):
                    self.warnings.append(f"External CORS origin: {origin}")

        return success

    def _check_rate_limiting(self, content: str, file_path: str) -> bool:
        """Check for rate limiting implementation"""
        success = True

        # Check for rate limiting decorators or middleware
        rate_limit_patterns = [
            r'@limiter\.limit',
            r'@rate_limit',
            r'SlowApi',
            r'RateLimiter'
        ]

        has_rate_limiting = any(re.search(pattern, content) for pattern in rate_limit_patterns)

        if not has_rate_limiting and 'main.py' not in file_path:
            self.warnings.append("No rate limiting detected in API endpoints")

        return success

    def _check_input_validation(self, tree: ast.AST, file_path: str) -> bool:
        """Check input validation using Pydantic models"""
        success = True

        # Look for Pydantic BaseModel usage
        has_pydantic = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and 'BaseModel' in base.id:
                        has_pydantic = True
                        break

        # Look for endpoint functions with typed parameters
        endpoint_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has decorators (likely FastAPI endpoint)
                if any(isinstance(decorator, ast.Call) for decorator in node.decorator_list):
                    endpoint_functions.append(node.name)

        if endpoint_functions and not has_pydantic:
            self.warnings.append("API endpoints without Pydantic validation models")

        return success

    def _check_error_handling(self, content: str, file_path: str) -> bool:
        """Check error handling patterns"""
        success = True

        # Check for HTTPException usage
        if 'HTTPException' not in content and 'raise' in content:
            self.warnings.append("Error handling may not use proper HTTP exceptions")

        # Check for information disclosure in error messages
        if re.search(r'raise.*Exception\s*\(\s*f["\'][^"\']*\{[^}]*\}', content):
            self.warnings.append("Potential information disclosure in error messages")

        return success

    def report_results(self) -> bool:
        """Report security check results"""
        if self.violations:
            print("❌ SECURITY VIOLATIONS:")
            for violation in self.violations:
                print(f"  - {violation}")

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.violations and not self.warnings:
            print("✅ API security check passed")

        return len(self.violations) == 0

def main():
    if len(sys.argv) != 2:
        print("Usage: check_api_security.py <api_file>")
        sys.exit(1)

    api_file = sys.argv[1]

    if not Path(api_file).exists():
        print(f"❌ API file not found: {api_file}")
        sys.exit(1)

    checker = APISecurityChecker()
    success = checker.check_api_file(api_file)
    success &= checker.report_results()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()