#!/usr/bin/env python3
"""
Security-First Validation Framework
Comprehensive security checks for RAG application
"""

import os
import sys
import json
import re
import subprocess
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import ast

class SecurityValidator:
    """Comprehensive security validation for RAG application"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.violations = []
        self.warnings = []

        # Security patterns and rules
        self.external_apis = [
            "openai.com", "api.openai.com", "anthropic.com",
            "pinecone.io", "amazonaws.com", "azure.com", "googleapis.com",
            "cohere.ai", "huggingface.co"
        ]

        self.prohibited_env_vars = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PINECONE_API_KEY",
            "AWS_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY", "GCP_PROJECT_ID",
            "AZURE_SUBSCRIPTION_ID", "COHERE_API_KEY", "HF_TOKEN"
        ]

        self.sensitive_patterns = [
            r"(?i)(password|secret|key|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
            r"(?i)api[_-]?key\s*[=:]\s*['\"][^'\"]{20,}['\"]",
            r"(?i)(sk-[a-zA-Z0-9]{48})",  # OpenAI API key pattern
            r"(?i)(xoxb-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24})",  # Slack token
        ]

    def log_violation(self, severity: str, message: str, file_path: str = None):
        """Log security violation"""
        violation = {
            "severity": severity,
            "message": message,
            "file": file_path,
            "timestamp": str(subprocess.check_output(["date"], text=True).strip())
        }

        if severity == "ERROR":
            self.violations.append(violation)
        else:
            self.warnings.append(violation)

        print(f"🚨 {severity}: {message}")
        if file_path:
            print(f"   File: {file_path}")

    def validate_network_configuration(self) -> bool:
        """Validate all network configurations are localhost-only"""
        print("🔒 Validating network configuration...")
        success = True

        # Check environment files
        env_files = [
            self.project_root / "app" / ".env",
            self.project_root / ".env"
        ]

        for env_file in env_files:
            if env_file.exists():
                success &= self._check_env_file(env_file)

        # Check configuration files
        config_files = list(self.project_root.rglob("config.py")) + list(self.project_root.rglob("settings.py"))
        for config_file in config_files:
            success &= self._check_config_file(config_file)

        return success

    def _check_env_file(self, env_file: Path) -> bool:
        """Check environment file for security violations"""
        success = True

        try:
            with open(env_file, 'r') as f:
                content = f.read()

            # Check for prohibited environment variables
            for var in self.prohibited_env_vars:
                if re.search(f"^{var}=", content, re.MULTILINE):
                    self.log_violation("ERROR", f"Prohibited external API variable: {var}", str(env_file))
                    success = False

            # Check database URLs
            db_urls = re.findall(r'DATABASE_URL\s*=\s*["\']([^"\']+)["\']', content)
            for url in db_urls:
                parsed = urlparse(url)
                if parsed.hostname not in ["localhost", "127.0.0.1", None]:
                    self.log_violation("ERROR", f"Database URL not localhost: {url}", str(env_file))
                    success = False

            # Check Ollama URLs
            ollama_urls = re.findall(r'OLLAMA_[^=]*=\s*["\']([^"\']+)["\']', content)
            for url in ollama_urls:
                if "localhost" not in url and "127.0.0.1" not in url:
                    self.log_violation("ERROR", f"Ollama URL not localhost: {url}", str(env_file))
                    success = False

        except Exception as e:
            self.log_violation("WARNING", f"Could not read env file: {e}", str(env_file))

        return success

    def _check_config_file(self, config_file: Path) -> bool:
        """Check Python configuration file for security issues"""
        success = True

        try:
            with open(config_file, 'r') as f:
                content = f.read()

            # Parse Python AST to check for hardcoded external URLs
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        value = node.s
                        if isinstance(value, str):
                            for api in self.external_apis:
                                if api in value.lower():
                                    self.log_violation("ERROR", f"External API reference: {value}", str(config_file))
                                    success = False
            except SyntaxError:
                self.log_violation("WARNING", "Could not parse Python file", str(config_file))

        except Exception as e:
            self.log_violation("WARNING", f"Could not read config file: {e}", str(config_file))

        return success

    def validate_code_security(self) -> bool:
        """Validate all Python code for security issues"""
        print("🔍 Validating code security...")
        success = True

        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            success &= self._check_python_file(py_file)

        return success

    def _check_python_file(self, py_file: Path) -> bool:
        """Check individual Python file for security issues"""
        success = True

        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check for hardcoded secrets
            for pattern in self.sensitive_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    self.log_violation("ERROR", f"Potential hardcoded secret: {match[:20]}...", str(py_file))
                    success = False

            # Check for external API imports
            external_imports = [
                "openai", "anthropic", "pinecone", "cohere",
                "boto3", "azure", "google.cloud"
            ]

            for imp in external_imports:
                if re.search(f"^(import|from)\s+{imp}", content, re.MULTILINE):
                    self.log_violation("ERROR", f"External API import: {imp}", str(py_file))
                    success = False

            # Check for external URLs in requests
            url_patterns = [
                r'requests\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
                r'httpx\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
                r'urllib\.request\.urlopen\s*\(\s*["\']([^"\']+)["\']'
            ]

            for pattern in url_patterns:
                matches = re.findall(pattern, content)
                for url in matches:
                    parsed = urlparse(url)
                    if parsed.hostname and parsed.hostname not in ["localhost", "127.0.0.1"]:
                        self.log_violation("ERROR", f"External HTTP request: {url}", str(py_file))
                        success = False

        except Exception as e:
            self.log_violation("WARNING", f"Could not read Python file: {e}", str(py_file))

        return success

    def validate_database_connections(self) -> bool:
        """Validate database connections are local only"""
        print("🗄️ Validating database connections...")
        success = True

        # Check if PostgreSQL is running locally
        try:
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                self.log_violation("WARNING", "PostgreSQL not accessible on localhost:5432")
        except Exception:
            self.log_violation("WARNING", "Could not check PostgreSQL status")

        # Check for remote database configurations
        netstat_cmd = ["netstat", "-tlnp"]
        try:
            result = subprocess.run(netstat_cmd, capture_output=True, text=True, timeout=10)
            lines = result.stdout.split('\n')

            for line in lines:
                if ":5432" in line and "0.0.0.0" in line:
                    self.log_violation("ERROR", "PostgreSQL listening on all interfaces (0.0.0.0)")
                    success = False
        except Exception:
            self.log_violation("WARNING", "Could not check network connections")

        return success

    def validate_ollama_security(self) -> bool:
        """Validate Ollama is configured securely"""
        print("🤖 Validating Ollama security...")
        success = True

        # Check if Ollama is running locally
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama accessible on localhost")
            else:
                self.log_violation("WARNING", "Ollama not responding on localhost:11434")
        except Exception:
            self.log_violation("WARNING", "Could not check Ollama status")

        # Check for external Ollama access by checking actual network binding
        try:
            result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=10)
            lines = result.stdout.split('\n')

            for line in lines:
                if ":11434" in line:
                    # Check if bound to 0.0.0.0 or external interface
                    if "0.0.0.0:11434" in line and "127.0.0.1:11434" not in line:
                        self.log_violation("ERROR", "Ollama listening on all interfaces (0.0.0.0)")
                        success = False
                    elif not ("127.0.0.1:11434" in line or "localhost:11434" in line):
                        # Check for other external interfaces
                        for external_ip in ["192.168.", "10.0.", "172."]:
                            if external_ip in line and ":11434" in line:
                                self.log_violation("ERROR", f"Ollama accessible from external interface: {line.strip()}")
                                success = False
                                break
        except Exception:
            self.log_violation("WARNING", "Could not check Ollama network binding")

        return success

    def validate_file_permissions(self) -> bool:
        """Validate file permissions are secure"""
        print("📁 Validating file permissions...")
        success = True

        sensitive_files = [
            self.project_root / "app" / ".env",
            self.project_root / ".env",
            self.project_root / "scripts" / "setup_database.sh",
            self.project_root / "scripts" / "setup_ollama.sh"
        ]

        for file_path in sensitive_files:
            if file_path.exists():
                stat = file_path.stat()
                permissions = oct(stat.st_mode)[-3:]

                # Check if file is world-readable
                if int(permissions[2]) >= 4:
                    self.log_violation("WARNING", f"File world-readable: {file_path}")

                # Check if file is group-writable
                if int(permissions[1]) >= 6:
                    self.log_violation("WARNING", f"File group-writable: {file_path}")

        return success

    def generate_security_report(self) -> Dict:
        """Generate comprehensive security report"""
        report = {
            "timestamp": str(subprocess.check_output(["date"], text=True).strip()),
            "project_root": str(self.project_root),
            "violations": self.violations,
            "warnings": self.warnings,
            "summary": {
                "total_violations": len(self.violations),
                "total_warnings": len(self.warnings),
                "security_score": max(0, 100 - (len(self.violations) * 10) - (len(self.warnings) * 2))
            }
        }

        return report

    def run_full_validation(self) -> bool:
        """Run all security validations"""
        print("🔒 Starting comprehensive security validation...")
        print("=" * 50)

        success = True
        success &= self.validate_network_configuration()
        success &= self.validate_code_security()
        success &= self.validate_database_connections()
        success &= self.validate_ollama_security()
        success &= self.validate_file_permissions()

        # Generate report
        report = self.generate_security_report()

        print("\n" + "=" * 50)
        print("🏁 Security Validation Complete")
        print(f"Security Score: {report['summary']['security_score']}/100")
        print(f"Violations: {report['summary']['total_violations']}")
        print(f"Warnings: {report['summary']['total_warnings']}")

        # Save report
        report_file = self.project_root / "security_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Detailed report saved: {report_file}")

        if not success:
            print("\n❌ SECURITY VALIDATION FAILED")
            print("Please fix all violations before proceeding")
            return False

        print("\n✅ SECURITY VALIDATION PASSED")
        print("System is configured for secure local operation")
        return True


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = None

    validator = SecurityValidator(project_root)
    success = validator.run_full_validation()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()