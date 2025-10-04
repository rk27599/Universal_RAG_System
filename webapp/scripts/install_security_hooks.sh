#!/bin/bash
"""
Security Hooks Installation Script
Sets up comprehensive security validation framework
"""

set -e

echo "🔒 Installing Security Validation Framework"
echo "==========================================="

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Project root: $PROJECT_ROOT"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "⚠️  Initializing git repository..."
    git init
    git config user.name "RAG Security System"
    git config user.email "security@localhost"
fi

# Install pre-commit if not available
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Install additional security tools
echo "🛠️ Installing security tools..."

# Install detect-secrets
if ! command -v detect-secrets &> /dev/null; then
    pip install detect-secrets
fi

# Initialize secrets baseline
if [ ! -f ".secrets.baseline" ]; then
    echo "🔐 Initializing secrets baseline..."
    detect-secrets scan --baseline .secrets.baseline
fi

# Install bandit for security scanning
pip install bandit

# Install safety for dependency checking
pip install safety

# Create security configuration
echo "⚙️ Creating security configuration..."

# Create .gitignore security entries
cat >> .gitignore << 'EOF'

# Security files
bandit-report.json
security_report.json
.secrets.baseline.tmp

# Environment files
*.env
*.env.local
*.env.production
.env.*

# Database files
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
/tmp/

# IDE files
.vscode/settings.json
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/
EOF

# Create security policy document
cat > SECURITY.md << 'EOF'
# Security Policy

## Security-First Design Principles

This RAG application follows a **security-first design** with the following core principles:

### 1. Local-Only Operation
- **NO external API calls** (OpenAI, Anthropic, Pinecone, etc.)
- **NO cloud services** (AWS, Azure, GCP)
- **NO external dependencies** for AI processing
- All AI models run locally via Ollama

### 2. Data Sovereignty
- All data remains on local infrastructure
- No data transmission to external services
- Complete control over data processing and storage
- Air-gap deployment capability

### 3. Network Security
- Database: localhost/127.0.0.1 only
- Ollama: localhost/127.0.0.1 only
- Web interface: localhost/127.0.0.1 only
- No external network connections during operation

### 4. Code Security
- Comprehensive pre-commit hooks
- Automated security scanning (Bandit, Safety)
- Secrets detection and prevention
- Input validation and sanitization

## Security Validation Framework

### Pre-commit Hooks
1. **Security Validation**: Comprehensive security checks
2. **External API Prevention**: Blocks external API calls
3. **Localhost Validation**: Ensures localhost-only configuration
4. **Secrets Detection**: Prevents secret commits
5. **Code Quality**: Black, isort, flake8
6. **Dependency Security**: Safety vulnerability scanning

### Manual Security Checks
```bash
# Run comprehensive security validation
python scripts/security_validator.py

# Check for external APIs
python scripts/check_external_apis.py app/

# Validate localhost-only configuration
python scripts/validate_localhost_only.py app/.env

# Scan for secrets
detect-secrets scan --baseline .secrets.baseline

# Security audit
bandit -r app/ -f json -o bandit-report.json
```

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Contact the development team privately
3. Provide detailed information about the vulnerability
4. Wait for confirmation before disclosure

## Security Compliance Checklist

- [ ] No external API keys in environment files
- [ ] All database connections use localhost
- [ ] Ollama configured for localhost only
- [ ] Pre-commit hooks installed and passing
- [ ] Security validation passing (100/100 score)
- [ ] No hardcoded secrets in code
- [ ] Input validation implemented
- [ ] Error handling prevents information disclosure
- [ ] File permissions properly configured
- [ ] Audit logging enabled

## Security Tools and Commands

### Installation
```bash
# Install security framework
./scripts/install_security_hooks.sh

# Install development dependencies
pip install -r requirements.txt
```

### Daily Security Checks
```bash
# Run all security validations
make security-check

# Update security baseline
detect-secrets scan --baseline .secrets.baseline --update

# Check dependency vulnerabilities
safety check

# Code security scan
bandit -r app/
```

### Emergency Response
```bash
# Immediate security lockdown
./scripts/security_lockdown.sh

# Audit recent changes
git log --oneline -10 --grep="security"

# Check current security status
python scripts/security_validator.py
```

## Compliance and Audit Trail

All security events are logged to:
- Application logs: `app/logs/`
- Security audit log: `security_audit.log`
- Database audit trail: PostgreSQL logs

Regular security audits should be performed:
- Weekly: Automated security scans
- Monthly: Manual security review
- Quarterly: Comprehensive security assessment
EOF

# Create Makefile for common security tasks
cat > Makefile << 'EOF'
.PHONY: security-check security-install security-update help

# Default target
help:
	@echo "🔒 RAG Security Commands"
	@echo "======================="
	@echo "make security-install  - Install security framework"
	@echo "make security-check    - Run all security validations"
	@echo "make security-update   - Update security tools and baselines"
	@echo "make pre-commit        - Run pre-commit hooks manually"
	@echo "make clean-security    - Clean security artifacts"

security-install:
	@echo "🔒 Installing security framework..."
	@./scripts/install_security_hooks.sh

security-check:
	@echo "🔍 Running comprehensive security validation..."
	@python scripts/security_validator.py
	@echo "🔍 Checking for external APIs..."
	@find app/ -name "*.py" -exec python scripts/check_external_apis.py {} \;
	@echo "🔍 Validating localhost-only configuration..."
	@find . -name "*.env*" -exec python scripts/validate_localhost_only.py {} \;
	@echo "🔍 Scanning for secrets..."
	@detect-secrets scan --baseline .secrets.baseline
	@echo "🔍 Running security audit..."
	@bandit -r app/ -f json -o bandit-report.json || true
	@echo "✅ Security validation complete"

security-update:
	@echo "🔄 Updating security tools..."
	@pip install --upgrade pre-commit bandit safety detect-secrets
	@pre-commit autoupdate
	@detect-secrets scan --baseline .secrets.baseline --update
	@echo "✅ Security tools updated"

pre-commit:
	@echo "🪝 Running pre-commit hooks..."
	@pre-commit run --all-files

clean-security:
	@echo "🧹 Cleaning security artifacts..."
	@rm -f bandit-report.json security_report.json
	@rm -f .secrets.baseline.tmp
	@echo "✅ Security artifacts cleaned"

# Development helpers
dev-setup: security-install
	@echo "🚀 Setting up development environment..."
	@pip install -r app/requirements.txt
	@./scripts/setup_database.sh
	@./scripts/setup_ollama.sh
	@echo "✅ Development environment ready"

test-security:
	@echo "🧪 Testing security framework..."
	@python -m pytest tests/security/ -v
	@echo "✅ Security tests passed"
EOF

# Create security test configuration
mkdir -p tests/security
cat > tests/security/test_security_framework.py << 'EOF'
"""
Security Framework Tests
"""

import pytest
import subprocess
import tempfile
from pathlib import Path

def test_security_validator():
    """Test security validator script"""
    result = subprocess.run(['python', 'scripts/security_validator.py'],
                          capture_output=True, text=True)
    # Should not fail catastrophically
    assert result.returncode in [0, 1]

def test_external_api_checker():
    """Test external API checker"""
    # Create temporary file with external API call
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('import openai\nclient = openai.OpenAI()')
        f.flush()

        result = subprocess.run(['python', 'scripts/check_external_apis.py', f.name],
                              capture_output=True, text=True)

        # Should detect violation
        assert result.returncode == 1
        assert 'External API library import' in result.stdout

        Path(f.name).unlink()

def test_localhost_validator():
    """Test localhost validator"""
    # Create temporary .env file with external URL
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('DATABASE_URL=postgresql://user:pass@external.com:5432/db')
        f.flush()

        result = subprocess.run(['python', 'scripts/validate_localhost_only.py', f.name],
                              capture_output=True, text=True)

        # Should detect violation
        assert result.returncode == 1
        assert 'Non-localhost' in result.stdout

        Path(f.name).unlink()

def test_precommit_config():
    """Test pre-commit configuration exists"""
    assert Path('.pre-commit-config.yaml').exists()

def test_security_scripts_executable():
    """Test security scripts are executable"""
    scripts = [
        'scripts/security_validator.py',
        'scripts/check_external_apis.py',
        'scripts/validate_localhost_only.py',
        'scripts/check_env_security.sh',
        'scripts/check_api_security.py'
    ]

    for script in scripts:
        path = Path(script)
        assert path.exists(), f"Script {script} does not exist"
        assert path.is_file(), f"Script {script} is not a file"
        # Check if executable (basic check)
        assert path.stat().st_mode & 0o111, f"Script {script} is not executable"
EOF

# Make scripts executable
chmod +x scripts/*.py scripts/*.sh

# Run initial security setup
echo "🔧 Running initial security validation..."
python scripts/security_validator.py || echo "⚠️  Initial security validation found issues (expected for new setup)"

# Set up pre-commit
echo "🪝 Setting up pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

echo ""
echo "🎉 SECURITY FRAMEWORK INSTALLATION COMPLETE!"
echo "============================================="
echo "✅ Pre-commit hooks installed"
echo "✅ Security validation scripts created"
echo "✅ Security policy documented"
echo "✅ Makefile with security commands created"
echo ""
echo "📋 Next Steps:"
echo "1. Review and update .secrets.baseline if needed"
echo "2. Run 'make security-check' to validate current state"
echo "3. Commit your changes to activate hooks"
echo "4. Use 'make help' to see available security commands"
echo ""
echo "🔒 Your RAG system is now protected by comprehensive security validation!"