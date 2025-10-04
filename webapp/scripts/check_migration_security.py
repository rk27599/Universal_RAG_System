#!/usr/bin/env python3
"""
Database Migration Security Checker
Validates Alembic migrations for security compliance
"""

import sys
import re
import ast
from pathlib import Path

def check_migration_security(migration_file):
    """Check database migration for security issues"""
    print(f"🔍 Checking migration security: {migration_file}")

    violations = []
    warnings = []

    try:
        with open(migration_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read migration file: {e}")
        return False

    # Check for dangerous SQL operations
    dangerous_patterns = [
        (r'DROP\s+DATABASE', 'DROP DATABASE operation detected'),
        (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE operation detected'),
        (r'DELETE\s+FROM.*WHERE\s+1=1', 'DELETE without proper WHERE clause'),
        (r'UPDATE.*SET.*WHERE\s+1=1', 'UPDATE without proper WHERE clause'),
        (r'GRANT\s+ALL', 'GRANT ALL privileges detected'),
        (r'CREATE\s+USER.*SUPERUSER', 'Creating superuser detected'),
    ]

    for pattern, message in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(message)

    # Check for external connections in migrations
    external_patterns = [
        (r'postgresql://[^@]*@(?!localhost|127\.0\.0\.1)', 'External database connection'),
        (r'mysql://[^@]*@(?!localhost|127\.0\.0\.1)', 'External database connection'),
    ]

    for pattern, message in external_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(message)

    # Check for hardcoded credentials
    credential_patterns = [
        (r'password\s*=\s*[\'"][^\'"]{6,}[\'"]', 'Hardcoded password detected'),
        (r'secret\s*=\s*[\'"][^\'"]{10,}[\'"]', 'Hardcoded secret detected'),
    ]

    for pattern, message in credential_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(message)

    # Report results
    if violations:
        print("❌ SECURITY VIOLATIONS:")
        for violation in violations:
            print(f"  - {violation}")
        return False

    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    print("✅ Migration security check passed")
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: check_migration_security.py <migration_file>")
        sys.exit(1)

    migration_file = sys.argv[1]

    if not Path(migration_file).exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    success = check_migration_security(migration_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()