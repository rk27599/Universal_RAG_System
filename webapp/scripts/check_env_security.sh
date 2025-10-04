#!/bin/bash
"""
Environment File Security Checker
Validates .env files for security compliance
"""

set -e

echo "🔒 Checking environment file security..."

# Get the file being checked
ENV_FILE="$1"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file not found: $ENV_FILE"
    exit 1
fi

# Check for prohibited external API keys
PROHIBITED_VARS=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "PINECONE_API_KEY"
    "AWS_ACCESS_KEY"
    "AWS_SECRET_ACCESS_KEY"
    "GCP_PROJECT_ID"
    "AZURE_SUBSCRIPTION_ID"
    "COHERE_API_KEY"
    "HF_TOKEN"
)

violations=0

for var in "${PROHIBITED_VARS[@]}"; do
    if grep -q "^$var=" "$ENV_FILE"; then
        echo "❌ SECURITY VIOLATION: External API variable found: $var"
        violations=$((violations + 1))
    fi
done

# Check for non-localhost database URLs
if grep -q "DATABASE_URL" "$ENV_FILE"; then
    db_url=$(grep "DATABASE_URL" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"'"'"'"')
    if [[ ! "$db_url" =~ (localhost|127\.0\.0\.1) ]]; then
        echo "❌ SECURITY VIOLATION: Database URL is not localhost: $db_url"
        violations=$((violations + 1))
    fi
fi

# Check for non-localhost Ollama URLs
if grep -q "OLLAMA_" "$ENV_FILE"; then
    while IFS= read -r line; do
        if [[ "$line" =~ ^OLLAMA_.*= ]]; then
            url=$(echo "$line" | cut -d'=' -f2- | tr -d '"'"'"'"')
            if [[ ! "$url" =~ (localhost|127\.0\.0\.1) ]]; then
                echo "❌ SECURITY VIOLATION: Ollama URL is not localhost: $url"
                violations=$((violations + 1))
            fi
        fi
    done < "$ENV_FILE"
fi

# Check file permissions
permissions=$(stat -c "%a" "$ENV_FILE")
if [ "$permissions" != "600" ] && [ "$permissions" != "640" ]; then
    echo "⚠️  WARNING: Environment file permissions should be 600 or 640, current: $permissions"
fi

# Check for secrets in plain text (basic patterns)
if grep -E "(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]" "$ENV_FILE" > /dev/null; then
    echo "⚠️  WARNING: Potential plain text secrets detected"
fi

if [ $violations -gt 0 ]; then
    echo "❌ SECURITY CHECK FAILED: $violations violations found"
    exit 1
fi

echo "✅ Environment file security check passed"
exit 0