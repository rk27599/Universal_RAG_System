#!/usr/bin/env python3
"""
External API Prevention Checker
Prevents any external API calls from being committed
"""

import sys
import re
import ast
from pathlib import Path

class ExternalAPIChecker:
    def __init__(self):
        self.violations = []

        # Known external API domains
        self.external_domains = [
            'api.openai.com', 'openai.com',
            'anthropic.com', 'api.anthropic.com',
            'pinecone.io', 'api.pinecone.io',
            'cohere.ai', 'api.cohere.ai',
            'huggingface.co', 'api.huggingface.co',
            'amazonaws.com', 'aws.amazon.com',
            'azure.com', 'api.azure.com',
            'googleapis.com', 'google.com'
        ]

        # External API libraries
        self.external_libraries = [
            'openai', 'anthropic', 'pinecone-client', 'cohere',
            'boto3', 'azure-identity', 'google-cloud',
            'transformers', 'huggingface_hub'
        ]

    def check_file(self, file_path: str) -> bool:
        """Check Python file for external API usage"""
        print(f"🔍 Checking for external APIs: {file_path}")

        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Could not read file: {e}")
            return False

        success = True
        success &= self._check_imports(content, file_path)
        success &= self._check_http_requests(content, file_path)
        success &= self._check_environment_variables(content, file_path)
        success &= self._check_hardcoded_urls(content, file_path)

        return success

    def _check_imports(self, content: str, file_path: str) -> bool:
        """Check for external API library imports"""
        success = True

        for library in self.external_libraries:
            patterns = [
                f'^import {library}',
                f'^from {library}',
                f'^import {library}\\.',
                f'^from {library}\\.'
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE):
                    self.violations.append(f"External API library import: {library} in {file_path}")
                    success = False

        return success

    def _check_http_requests(self, content: str, file_path: str) -> bool:
        """Check for HTTP requests to external APIs"""
        success = True

        # HTTP request patterns
        request_patterns = [
            r'requests\.(?:get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'httpx\.(?:get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'urllib\.request\.urlopen\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'aiohttp\.(?:get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
        ]

        for pattern in request_patterns:
            matches = re.findall(pattern, content)
            for url in matches:
                # Skip localhost and relative URLs
                if url.startswith('http') and not ('localhost' in url or '127.0.0.1' in url):
                    for domain in self.external_domains:
                        if domain in url:
                            self.violations.append(f"External API request to {domain}: {url} in {file_path}")
                            success = False

        return success

    def _check_environment_variables(self, content: str, file_path: str) -> bool:
        """Check for external API environment variables"""
        success = True

        external_env_vars = [
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'PINECONE_API_KEY',
            'COHERE_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
            'AZURE_SUBSCRIPTION_ID', 'GOOGLE_APPLICATION_CREDENTIALS',
            'HF_TOKEN', 'HUGGINGFACE_API_KEY'
        ]

        for var in external_env_vars:
            patterns = [
                f'os\\.environ\\.get\\s*\\(\\s*[\'\"]{var}[\'\"',
                f'os\\.getenv\\s*\\(\\s*[\'\"]{var}[\'\"',
                f'settings\\.[a-z_]*{var.lower()}[a-z_]*',
                f'{var}\\s*=\\s*os\\.'
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.violations.append(f"External API environment variable: {var} in {file_path}")
                    success = False

        return success

    def _check_hardcoded_urls(self, content: str, file_path: str) -> bool:
        """Check for hardcoded external API URLs"""
        success = True

        for domain in self.external_domains:
            if domain in content:
                # Get context around the domain
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if domain in line and not line.strip().startswith('#'):
                        self.violations.append(f"Hardcoded external domain {domain} in {file_path}:{i+1}")
                        success = False

        return success

    def report_results(self) -> bool:
        """Report check results"""
        if self.violations:
            print("❌ EXTERNAL API VIOLATIONS DETECTED:")
            for violation in self.violations:
                print(f"  - {violation}")
            print("\n🚨 SECURITY POLICY: No external API calls allowed!")
            print("   All AI processing must use local Ollama models only.")
            return False

        print("✅ No external API calls detected")
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: check_external_apis.py <python_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    checker = ExternalAPIChecker()
    success = checker.check_file(file_path)
    success &= checker.report_results()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()