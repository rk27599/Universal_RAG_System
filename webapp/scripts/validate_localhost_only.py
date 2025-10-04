#!/usr/bin/env python3
"""
Localhost-Only Configuration Validator
Ensures all configurations use localhost/127.0.0.1 only
"""

import sys
import re
import json
import yaml
from pathlib import Path
from urllib.parse import urlparse

class LocalhostValidator:
    def __init__(self):
        self.violations = []
        self.warnings = []

    def validate_file(self, file_path: str) -> bool:
        """Validate configuration file for localhost-only access"""
        print(f"🔒 Validating localhost-only configuration: {file_path}")

        file_type = self._detect_file_type(file_path)

        if file_type == 'env':
            return self._validate_env_file(file_path)
        elif file_type == 'json':
            return self._validate_json_file(file_path)
        elif file_type == 'yaml':
            return self._validate_yaml_file(file_path)
        elif file_type == 'python':
            return self._validate_python_file(file_path)
        else:
            print(f"⚠️  Unknown file type, skipping: {file_path}")
            return True

    def _detect_file_type(self, file_path: str) -> str:
        """Detect configuration file type"""
        path = Path(file_path)

        if '.env' in path.name:
            return 'env'
        elif path.suffix == '.json':
            return 'json'
        elif path.suffix in ['.yml', '.yaml']:
            return 'yaml'
        elif path.suffix == '.py':
            return 'python'
        else:
            return 'unknown'

    def _validate_env_file(self, file_path: str) -> bool:
        """Validate .env file"""
        success = True

        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Could not read file: {e}")
            return False

        # Check database URLs
        db_patterns = [
            r'DATABASE_URL\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'DB_HOST\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'POSTGRES_HOST\s*=\s*[\'"]([^\'"]+)[\'"]'
        ]

        for pattern in db_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not self._is_localhost(match):
                    self.violations.append(f"Non-localhost database connection: {match}")
                    success = False

        # Check Ollama URLs
        ollama_patterns = [
            r'OLLAMA_[^=]*\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'LLM_HOST\s*=\s*[\'"]([^\'"]+)[\'"]'
        ]

        for pattern in ollama_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not self._is_localhost(match):
                    self.violations.append(f"Non-localhost Ollama connection: {match}")
                    success = False

        # Check Redis/Cache URLs
        cache_patterns = [
            r'REDIS_URL\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'CACHE_HOST\s*=\s*[\'"]([^\'"]+)[\'"]'
        ]

        for pattern in cache_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not self._is_localhost(match):
                    self.violations.append(f"Non-localhost cache connection: {match}")
                    success = False

        return success

    def _validate_json_file(self, file_path: str) -> bool:
        """Validate JSON configuration file"""
        success = True

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Could not parse JSON file: {e}")
            return False

        success &= self._check_nested_config(data, file_path)
        return success

    def _validate_yaml_file(self, file_path: str) -> bool:
        """Validate YAML configuration file"""
        success = True

        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Could not parse YAML file: {e}")
            return False

        if data:
            success &= self._check_nested_config(data, file_path)
        return success

    def _validate_python_file(self, file_path: str) -> bool:
        """Validate Python configuration file"""
        success = True

        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Could not read Python file: {e}")
            return False

        # Check for hardcoded non-localhost configurations
        url_patterns = [
            r'[\'"]https?://([^/\'\"]+)',
            r'[\'"]postgresql://[^@]*@([^:/\'\"]+)',
            r'[\'"]mysql://[^@]*@([^:/\'\"]+)',
            r'host\s*=\s*[\'"]([^\'\"]+)[\'"]',
            r'HOST\s*=\s*[\'"]([^\'\"]+)[\'"]'
        ]

        for pattern in url_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not self._is_localhost(match) and not self._is_variable_reference(match):
                    self.violations.append(f"Non-localhost connection in Python config: {match}")
                    success = False

        return success

    def _check_nested_config(self, data, file_path: str, path="") -> bool:
        """Recursively check nested configuration data"""
        success = True

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                if isinstance(value, str):
                    if self._looks_like_connection_string(value):
                        if not self._is_localhost(value):
                            self.violations.append(f"Non-localhost connection at {current_path}: {value}")
                            success = False
                elif isinstance(value, (dict, list)):
                    success &= self._check_nested_config(value, file_path, current_path)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                success &= self._check_nested_config(item, file_path, current_path)

        return success

    def _is_localhost(self, value: str) -> bool:
        """Check if value refers to localhost"""
        if not value:
            return True

        value = value.lower()

        # Direct localhost references
        localhost_patterns = [
            'localhost', '127.0.0.1', '::1',
            'local', '0.0.0.0'  # 0.0.0.0 is acceptable for binding
        ]

        for pattern in localhost_patterns:
            if pattern in value:
                return True

        # Parse URLs
        if value.startswith(('http://', 'https://', 'postgresql://', 'mysql://')):
            try:
                parsed = urlparse(value)
                hostname = parsed.hostname
                if hostname in ['localhost', '127.0.0.1', None]:
                    return True
            except Exception:
                pass

        return False

    def _looks_like_connection_string(self, value: str) -> bool:
        """Check if string looks like a connection string"""
        connection_indicators = [
            '://', 'host=', 'server=', '.com', '.net', '.org',
            'postgresql:', 'mysql:', 'redis:', 'mongodb:'
        ]

        return any(indicator in value.lower() for indicator in connection_indicators)

    def _is_variable_reference(self, value: str) -> bool:
        """Check if value is a variable reference"""
        variable_patterns = [
            r'^\$\{[^}]+\}$',  # ${VAR}
            r'^\$[A-Z_]+$',    # $VAR
            r'^%[A-Z_]+%$',    # %VAR%
        ]

        return any(re.match(pattern, value) for pattern in variable_patterns)

    def report_results(self) -> bool:
        """Report validation results"""
        if self.violations:
            print("❌ LOCALHOST-ONLY VIOLATIONS:")
            for violation in self.violations:
                print(f"  - {violation}")
            print("\n🚨 SECURITY POLICY: All connections must be localhost-only!")
            return False

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("✅ Localhost-only validation passed")
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: validate_localhost_only.py <config_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    validator = LocalhostValidator()
    success = validator.validate_file(file_path)
    success &= validator.report_results()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()