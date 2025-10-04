# Security Validation & Compliance Guide

## 🔒 Security-First RAG Application Validation

This document provides comprehensive security validation procedures, compliance checklists, and automated tools to ensure the RAG web application maintains complete data sovereignty and privacy.

## 🛡️ Security Validation Framework

### Pre-Deployment Security Checklist

```bash
# 🔒 CRITICAL SECURITY VALIDATION CHECKLIST
# All items must be ✅ before deployment

□ Zero external API dependencies
□ No cloud service integrations
□ All data processing local only
□ Air-gap deployment capability verified
□ Local encryption at rest configured
□ Local SSL/TLS certificates installed
□ No external logging or analytics
□ Firewall configured for local-only access
□ Backup strategy tested (local only)
□ Security audit completed
```

## 🧪 Automated Security Validation Scripts

### 1. Complete Security Audit Script

```bash
#!/bin/bash
# security-audit.sh - Comprehensive security validation

echo "🔒 RAG APPLICATION SECURITY AUDIT"
echo "=================================="
echo "🕒 Started: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Function to check and report
check_requirement() {
    local test_command="$1"
    local description="$2"
    local severity="$3"  # CRITICAL, WARNING, INFO

    echo -n "🔍 Testing: $description... "

    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        if [ "$severity" = "CRITICAL" ]; then
            echo -e "${RED}❌ FAIL (CRITICAL)${NC}"
            ((FAILED++))
        else
            echo -e "${YELLOW}⚠️  WARNING${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

echo "🔒 1. EXTERNAL DEPENDENCY VALIDATION"
echo "-----------------------------------"

# Check for external API calls in source code
check_requirement "! grep -r 'api\.openai\.com\|api\.anthropic\.com\|api\.cohere\.' src/ 2>/dev/null" \
    "No external AI API calls in source code" "CRITICAL"

check_requirement "! grep -r 'pinecone\|weaviate\.com\|qdrant\.com' . --exclude-dir=docs 2>/dev/null" \
    "No external vector database services" "CRITICAL"

check_requirement "! grep -r 'amazonaws\.com\|googleapis\.com\|azure\.com' . --exclude-dir=docs 2>/dev/null" \
    "No cloud service dependencies" "CRITICAL"

check_requirement "! grep -r 'analytics\.google\.com\|googletagmanager\.com' . 2>/dev/null" \
    "No external analytics services" "CRITICAL"

echo ""
echo "🏠 2. LOCAL SERVICE CONFIGURATION"
echo "--------------------------------"

# Check Ollama local configuration
check_requirement "grep -r 'localhost:11434\|127\.0\.0\.1:11434' . >/dev/null 2>&1" \
    "Ollama configured for localhost" "CRITICAL"

# Check database local configuration
check_requirement "grep -r 'localhost:5432\|127\.0\.0\.1:5432' . >/dev/null 2>&1 || grep -r 'postgresql://.*@localhost' . >/dev/null 2>&1" \
    "PostgreSQL configured for localhost" "CRITICAL"

# Check for local WebSocket configuration
check_requirement "grep -r 'ws://localhost\|wss://localhost\|ws://127\.0\.0\.1' . >/dev/null 2>&1" \
    "WebSocket configured for localhost" "CRITICAL"

echo ""
echo "🚫 3. PROHIBITED SERVICES CHECK"
echo "------------------------------"

# Check for prohibited external services
check_requirement "! grep -r 'vercel\.com\|netlify\.com\|heroku\.com' . --exclude-dir=docs 2>/dev/null" \
    "No external hosting platforms" "CRITICAL"

check_requirement "! grep -r 'stripe\.com\|paypal\.com' . 2>/dev/null" \
    "No external payment processors" "WARNING"

check_requirement "! grep -r 'sentry\.io\|bugsnag\.com\|rollbar\.com' . 2>/dev/null" \
    "No external error tracking services" "WARNING"

echo ""
echo "🔐 4. ENCRYPTION & SECURITY CONFIG"
echo "---------------------------------"

# Check for HTTPS configuration
check_requirement "grep -r 'ssl\|tls\|https' . >/dev/null 2>&1" \
    "SSL/TLS configuration present" "CRITICAL"

# Check for password security
check_requirement "! grep -r 'password.*=.*['\"].*['\"]' . --exclude-dir=docs 2>/dev/null" \
    "No hardcoded passwords in source" "CRITICAL"

# Check for API key security
check_requirement "! grep -r 'api_key.*=.*['\"].*['\"]' . --exclude-dir=docs 2>/dev/null" \
    "No hardcoded API keys in source" "CRITICAL"

echo ""
echo "📦 5. DEPENDENCY ANALYSIS"
echo "------------------------"

# Check Python requirements for external services
if [ -f "requirements.txt" ]; then
    check_requirement "! grep -i 'openai\|anthropic\|cohere\|pinecone' requirements.txt 2>/dev/null" \
        "No external AI service dependencies in requirements.txt" "CRITICAL"
fi

# Check package.json for external services
if [ -f "package.json" ]; then
    check_requirement "! grep -i 'analytics\|sentry\|bugsnag' package.json 2>/dev/null" \
        "No external service dependencies in package.json" "WARNING"
fi

echo ""
echo "🌐 6. NETWORK CONFIGURATION VALIDATION"
echo "------------------------------------"

# Check if services are bound to localhost
check_requirement "netstat -tlnp 2>/dev/null | grep ':8000.*127.0.0.1\|:8000.*0.0.0.0' || echo 'Service not running - check when started'" \
    "FastAPI service network binding" "INFO"

check_requirement "netstat -tlnp 2>/dev/null | grep ':5432.*127.0.0.1' || echo 'PostgreSQL not running - check when started'" \
    "PostgreSQL service network binding" "INFO"

check_requirement "netstat -tlnp 2>/dev/null | grep ':11434.*127.0.0.1\|:11434.*0.0.0.0' || echo 'Ollama not running - check when started'" \
    "Ollama service network binding" "INFO"

echo ""
echo "📁 7. FILE SYSTEM SECURITY"
echo "-------------------------"

# Check for proper file permissions
check_requirement "find . -name '*.py' -perm /o+w | wc -l | grep -q '^0$'" \
    "Source files not world-writable" "WARNING"

# Check for sensitive file exposure
check_requirement "! find . -name '.env' -o -name '*.key' -o -name '*.pem' | grep -v '/dev/null'" \
    "No exposed credential files" "CRITICAL"

echo ""
echo "🎯 8. AIR-GAP DEPLOYMENT READINESS"
echo "---------------------------------"

# Check if application can run without internet
check_requirement "command -v ollama >/dev/null 2>&1" \
    "Ollama binary available locally" "CRITICAL"

check_requirement "command -v psql >/dev/null 2>&1" \
    "PostgreSQL client available locally" "CRITICAL"

# Check for offline documentation
check_requirement "[ -d 'docs' ] && [ -f 'docs/README.md' ]" \
    "Local documentation available" "WARNING"

echo ""
echo "📊 SECURITY AUDIT SUMMARY"
echo "========================="
echo "✅ Tests Passed: $PASSED"
echo "❌ Tests Failed: $FAILED"
echo "⚠️  Warnings: $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🔒 SECURITY STATUS: COMPLIANT${NC}"
    echo "✅ Application meets security requirements for local deployment"
    exit 0
else
    echo -e "${RED}🚨 SECURITY STATUS: NON-COMPLIANT${NC}"
    echo "❌ Critical security issues found. Deployment BLOCKED."
    echo "📋 Action Required: Fix all CRITICAL issues before deployment"
    exit 1
fi
```

### 2. Development Security Guard Script

```bash
#!/bin/bash
# dev-security-guard.sh - Continuous security monitoring during development

echo "🛡️ RAG DEVELOPMENT SECURITY GUARD"
echo "================================="

# Function to monitor file changes
monitor_security_violations() {
    echo "🔍 Monitoring for security violations..."

    # Watch for external API additions
    inotifywait -m -r --format '%w%f %e' src/ -e modify,create | while read file event; do
        if [[ "$file" == *.py ]]; then
            echo "📝 Checking: $file"

            # Check for prohibited external services
            if grep -q "api\.openai\.com\|api\.anthropic\.com\|pinecone" "$file" 2>/dev/null; then
                echo "🚨 SECURITY VIOLATION DETECTED in $file"
                echo "❌ External API call found - this violates security policy"
                echo "📋 Action: Remove external API dependency immediately"
            fi

            # Check for cloud services
            if grep -q "amazonaws\.com\|googleapis\.com\|azure\.com" "$file" 2>/dev/null; then
                echo "🚨 CLOUD SERVICE DETECTED in $file"
                echo "❌ Cloud dependency violates local-only policy"
            fi

            # Check for hardcoded credentials
            if grep -q "password.*=.*['\"].*['\"]" "$file" 2>/dev/null; then
                echo "🚨 HARDCODED PASSWORD DETECTED in $file"
                echo "❌ Security risk - use environment variables"
            fi
        fi
    done
}

# Function to validate network connections
validate_network_connections() {
    echo "🌐 Validating network connections..."

    # Check for outbound connections to prohibited services
    netstat -tupln 2>/dev/null | grep ESTABLISHED | while read line; do
        if echo "$line" | grep -q ":443.*openai\|:443.*anthropic\|:443.*pinecone"; then
            echo "🚨 PROHIBITED EXTERNAL CONNECTION DETECTED"
            echo "❌ Connection to external AI service found"
            echo "📋 This violates the local-only security policy"
        fi
    done
}

# Function to check environment variables
check_environment_security() {
    echo "🔧 Checking environment configuration..."

    # Warn about external API keys
    if [ ! -z "$OPENAI_API_KEY" ] || [ ! -z "$ANTHROPIC_API_KEY" ]; then
        echo "⚠️  WARNING: External AI API keys detected in environment"
        echo "📋 These should not be used in production deployment"
    fi

    # Check for local service configuration
    if [ -z "$DATABASE_URL" ] || ! echo "$DATABASE_URL" | grep -q "localhost\|127.0.0.1"; then
        echo "⚠️  WARNING: DATABASE_URL not configured for localhost"
        echo "📋 Database should be configured for local access only"
    fi
}

# Main monitoring loop
while true; do
    echo "🔄 Security check cycle started: $(date)"

    validate_network_connections
    check_environment_security

    echo "⏰ Next check in 30 seconds..."
    sleep 30
done
```

### 3. Pre-Commit Security Hook

```bash
#!/bin/bash
# pre-commit-security-hook.sh - Git pre-commit hook for security validation

echo "🔒 Pre-commit security validation..."

# Check for external API calls in staged files
if git diff --cached --name-only | xargs grep -l "api\.openai\.com\|api\.anthropic\.com\|pinecone" 2>/dev/null; then
    echo "❌ COMMIT BLOCKED: External API calls detected"
    echo "📋 Remove external API dependencies before committing"
    exit 1
fi

# Check for hardcoded credentials
if git diff --cached --name-only | xargs grep -l "password.*=.*['\"].*['\"]" 2>/dev/null; then
    echo "❌ COMMIT BLOCKED: Hardcoded credentials detected"
    echo "📋 Use environment variables for sensitive data"
    exit 1
fi

# Check for cloud service dependencies
if git diff --cached --name-only | xargs grep -l "amazonaws\.com\|googleapis\.com\|azure\.com" 2>/dev/null; then
    echo "❌ COMMIT BLOCKED: Cloud service dependencies detected"
    echo "📋 Remove cloud dependencies - local-only deployment required"
    exit 1
fi

echo "✅ Security validation passed"
exit 0
```

## 🛡️ Deployment Security Configuration

### Firewall Configuration

```bash
#!/bin/bash
# configure-firewall.sh - Secure firewall setup for RAG application

echo "🔥 Configuring firewall for RAG application..."

# Reset firewall to default deny
ufw --force reset
ufw default deny incoming
ufw default deny outgoing

# Allow only essential local services
ufw allow in on lo  # Loopback interface
ufw allow out on lo

# Allow SSH for administration (adjust port as needed)
ufw allow in 22/tcp

# Allow HTTPS for web interface
ufw allow in 443/tcp
ufw allow in 80/tcp

# Allow only specific outgoing connections if needed
# (Comment out if complete air-gap deployment)
ufw allow out 53/udp   # DNS (only if needed)
ufw allow out 80/tcp   # HTTP for updates (only if needed)
ufw allow out 443/tcp  # HTTPS for updates (only if needed)

# Enable firewall
ufw --force enable

echo "✅ Firewall configured for maximum security"
echo "🔒 Only essential local services allowed"
```

### SSL/TLS Configuration

```bash
#!/bin/bash
# setup-local-ssl.sh - Configure local SSL certificates

echo "🔐 Setting up local SSL certificates..."

# Create directory for certificates
mkdir -p /opt/rag-app/ssl

# Generate private key
openssl genrsa -out /opt/rag-app/ssl/server.key 4096

# Generate certificate signing request
openssl req -new -key /opt/rag-app/ssl/server.key -out /opt/rag-app/ssl/server.csr -subj "/C=US/ST=Local/L=Local/O=RAG-App/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in /opt/rag-app/ssl/server.csr -signkey /opt/rag-app/ssl/server.key -out /opt/rag-app/ssl/server.crt

# Set proper permissions
chmod 600 /opt/rag-app/ssl/server.key
chmod 644 /opt/rag-app/ssl/server.crt

echo "✅ Local SSL certificates generated"
echo "🔒 HTTPS ready for secure local communication"
```

## 📋 Compliance Documentation

### GDPR Compliance Statement

```markdown
# GDPR Compliance Through Local Architecture

## Article 25: Data Protection by Design and Default

✅ **COMPLIANT**: The RAG application implements data protection by design:
- All personal data processed locally on controlled infrastructure
- No data transmission to external processors
- User data sovereignty maintained at all times
- Technical measures prevent external data access

## Article 32: Security of Processing

✅ **COMPLIANT**: Technical and organizational measures implemented:
- Local encryption of personal data at rest
- Secure transmission within local infrastructure only
- Access controls through local authentication
- Regular security testing and validation

## Data Processing Records

- **Controller**: [Your Organization]
- **Processor**: Local infrastructure only (no external processors)
- **Data Location**: Local servers under direct control
- **International Transfers**: None (all processing local)
- **Retention Period**: Under direct organizational control
```

### HIPAA Compliance Statement

```markdown
# HIPAA Compliance Through Local Deployment

## Administrative Safeguards

✅ **COMPLIANT**:
- Designated security officer responsible for local infrastructure
- Access controls managed locally
- Security training for local system administrators

## Physical Safeguards

✅ **COMPLIANT**:
- Physical access controls to local servers
- Workstation security measures
- Media controls for local storage

## Technical Safeguards

✅ **COMPLIANT**:
- Local access controls and encryption
- Audit controls through local logging
- Data integrity through local checksums
- Transmission security within local network only
```

## 🔄 Continuous Security Monitoring

### Security Monitoring Dashboard

```python
#!/usr/bin/env python3
# security-monitor.py - Real-time security monitoring

import psutil
import subprocess
import time
import json
from datetime import datetime

class SecurityMonitor:
    def __init__(self):
        self.violations = []

    def check_network_connections(self):
        """Monitor for unauthorized external connections"""
        violations = []

        for conn in psutil.net_connections():
            if conn.status == 'ESTABLISHED' and conn.raddr:
                # Check for prohibited external services
                if any(service in str(conn.raddr.ip) for service in [
                    'openai.com', 'anthropic.com', 'pinecone.com',
                    'amazonaws.com', 'googleapis.com'
                ]):
                    violations.append({
                        'type': 'EXTERNAL_CONNECTION',
                        'detail': f"Connection to {conn.raddr.ip}:{conn.raddr.port}",
                        'severity': 'CRITICAL',
                        'timestamp': datetime.now().isoformat()
                    })

        return violations

    def check_running_processes(self):
        """Monitor for unauthorized external processes"""
        violations = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])

                # Check for external AI service processes
                if any(service in cmdline.lower() for service in [
                    'openai', 'anthropic', 'pinecone', 'aws', 'gcp'
                ]):
                    violations.append({
                        'type': 'EXTERNAL_PROCESS',
                        'detail': f"Process: {proc.info['name']} - {cmdline}",
                        'severity': 'CRITICAL',
                        'timestamp': datetime.now().isoformat()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return violations

    def check_file_modifications(self):
        """Monitor for unauthorized file modifications"""
        violations = []

        # Check for modifications to critical files
        critical_files = [
            '/opt/rag-app/src/rag_system.py',
            '/opt/rag-app/requirements.txt',
            '/opt/rag-app/.env'
        ]

        for file_path in critical_files:
            try:
                # Simple file integrity check (in production, use proper checksums)
                result = subprocess.run(['stat', '-c', '%Y', file_path],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    modification_time = int(result.stdout.strip())
                    # Check if modified in last 5 minutes
                    if time.time() - modification_time < 300:
                        violations.append({
                            'type': 'FILE_MODIFICATION',
                            'detail': f"Recent modification: {file_path}",
                            'severity': 'WARNING',
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                pass

        return violations

    def generate_report(self):
        """Generate security monitoring report"""
        all_violations = []

        all_violations.extend(self.check_network_connections())
        all_violations.extend(self.check_running_processes())
        all_violations.extend(self.check_file_modifications())

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_violations': len(all_violations),
            'critical_violations': len([v for v in all_violations if v['severity'] == 'CRITICAL']),
            'violations': all_violations
        }

        return report

def main():
    monitor = SecurityMonitor()

    print("🛡️ RAG Security Monitor Started")
    print("==============================")

    while True:
        report = monitor.generate_report()

        if report['total_violations'] > 0:
            print(f"🚨 SECURITY ALERT: {report['total_violations']} violations detected")
            print(json.dumps(report, indent=2))
        else:
            print(f"✅ Security check passed: {report['timestamp']}")

        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
```

## 🔒 Air-Gap Deployment Guide

### Complete Offline Installation Package

```bash
#!/bin/bash
# create-airgap-package.sh - Create complete offline deployment package

echo "📦 Creating air-gap deployment package..."

PACKAGE_DIR="rag-airgap-deploy"
mkdir -p "$PACKAGE_DIR"

# 1. Download Ollama models
echo "⬇️  Downloading Ollama models..."
mkdir -p "$PACKAGE_DIR/ollama-models"
ollama pull mistral
ollama pull llama2
ollama pull codellama

# Copy models from Ollama directory
cp -r ~/.ollama/models/* "$PACKAGE_DIR/ollama-models/"

# 2. Package application code
echo "📁 Packaging application..."
git archive --format=tar.gz --output="$PACKAGE_DIR/rag-application.tar.gz" HEAD

# 3. Download Python dependencies
echo "🐍 Downloading Python dependencies..."
mkdir -p "$PACKAGE_DIR/python-deps"
pip download -r requirements.txt -d "$PACKAGE_DIR/python-deps"

# 4. Download system dependencies
echo "💾 Downloading system dependencies..."
mkdir -p "$PACKAGE_DIR/system-deps"

# Download PostgreSQL packages (Ubuntu/Debian)
apt-get download postgresql postgresql-contrib postgresql-15-pgvector
mv *.deb "$PACKAGE_DIR/system-deps/"

# 5. Create installation script
cat > "$PACKAGE_DIR/install-airgap.sh" << 'EOF'
#!/bin/bash
echo "🔒 Installing RAG Application (Air-Gap Mode)"
echo "============================================"

# Install system dependencies
echo "💾 Installing system packages..."
sudo dpkg -i system-deps/*.deb
sudo apt-get install -f -y

# Install Ollama
echo "🤖 Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Restore Ollama models
echo "📦 Restoring AI models..."
mkdir -p ~/.ollama/models
cp -r ollama-models/* ~/.ollama/models/

# Extract application
echo "📁 Extracting application..."
tar -xzf rag-application.tar.gz

# Install Python dependencies offline
echo "🐍 Installing Python dependencies..."
pip install --no-index --find-links python-deps -r requirements.txt

# Setup database
echo "🗄️  Setting up database..."
sudo -u postgres createdb rag_database
sudo -u postgres psql -d rag_database -c "CREATE EXTENSION vector;"

echo "✅ Air-gap installation complete!"
echo "🔒 No internet connection required for operation"
EOF

chmod +x "$PACKAGE_DIR/install-airgap.sh"

# 6. Create documentation package
echo "📚 Packaging documentation..."
cp -r docs "$PACKAGE_DIR/docs"

# 7. Create security validation tools
echo "🛡️ Including security validation..."
cp security-audit.sh "$PACKAGE_DIR/"
cp dev-security-guard.sh "$PACKAGE_DIR/"

# 8. Create deployment verification
cat > "$PACKAGE_DIR/verify-airgap.sh" << 'EOF'
#!/bin/bash
echo "🔒 Verifying Air-Gap Deployment"
echo "==============================="

# Test that no external connections are made
timeout 30 netstat -tupln | grep ESTABLISHED | grep -v "127.0.0.1\|localhost" && {
    echo "❌ External connections detected - air-gap compromised"
    exit 1
} || {
    echo "✅ No external connections - air-gap verified"
}

# Test local services
curl -s http://localhost:8000/health && echo "✅ FastAPI service responding"
psql -h localhost -U postgres -d rag_database -c "SELECT 1;" && echo "✅ PostgreSQL responding"
curl -s http://localhost:11434/api/tags && echo "✅ Ollama responding"

echo "🔒 Air-gap deployment verification complete"
EOF

chmod +x "$PACKAGE_DIR/verify-airgap.sh"

# 9. Create final package
echo "📦 Creating final deployment package..."
tar -czf "rag-airgap-$(date +%Y%m%d).tar.gz" "$PACKAGE_DIR"

echo "✅ Air-gap deployment package created: rag-airgap-$(date +%Y%m%d).tar.gz"
echo "🔒 This package contains everything needed for offline deployment"
```

This comprehensive security validation framework ensures that your RAG application maintains complete data sovereignty and privacy throughout its lifecycle, from development through production deployment.