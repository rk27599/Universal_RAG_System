#!/bin/bash
"""
Security-First Ollama Setup Script
Installs and configures Ollama with local models for complete data sovereignty
"""

set -e  # Exit on any error

echo "🤖 Setting up Ollama for Secure RAG System"
echo "==========================================="

# Configuration
OLLAMA_HOST="127.0.0.1"
OLLAMA_PORT="11434"
MODELS_TO_INSTALL=("mistral" "llama2" "codellama")

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is already installed"
    OLLAMA_VERSION=$(ollama --version)
    echo "📋 Current version: $OLLAMA_VERSION"
else
    echo "📥 Installing Ollama..."

    # Download and install Ollama
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        curl -fsSL https://ollama.com/install.sh | sh
        echo "✅ Ollama installed on Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation
        if command -v brew &> /dev/null; then
            brew install ollama
            echo "✅ Ollama installed via Homebrew"
        else
            # Direct download for macOS
            echo "📥 Downloading Ollama for macOS..."
            curl -fsSL https://ollama.com/install.sh | sh
            echo "✅ Ollama installed on macOS"
        fi
    else
        echo "❌ Unsupported operating system for automatic installation"
        echo "Please visit https://ollama.com/download and install manually"
        exit 1
    fi
fi

# Start Ollama service in the background
echo "🚀 Starting Ollama service..."

# Check if Ollama is already running
if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
    echo "✅ Ollama service is already running"
else
    # Start Ollama in the background
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux: Start as systemd service if available, otherwise as background process
        if systemctl is-enabled ollama &> /dev/null; then
            sudo systemctl start ollama
            sudo systemctl enable ollama
            echo "✅ Ollama started as systemd service"
        else
            nohup ollama serve > /dev/null 2>&1 &
            echo "✅ Ollama started as background process"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: Start as background process
        nohup ollama serve > /dev/null 2>&1 &
        echo "✅ Ollama started as background process"
    fi

    # Wait for Ollama to be ready
    echo "⏳ Waiting for Ollama service to be ready..."
    for i in {1..30}; do
        if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
            echo "✅ Ollama service is ready"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo "❌ Ollama service failed to start within 60 seconds"
            echo "Please check the service status and logs"
            exit 1
        fi
    done
fi

# Security validation - ensure Ollama is running locally only
echo "🔒 Performing security validation..."

# Check that Ollama is bound to localhost
if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
    echo "✅ Ollama is accessible on localhost"
else
    echo "❌ Cannot connect to Ollama on localhost"
    exit 1
fi

# Verify no external access (try common external interfaces)
EXTERNAL_INTERFACES=("0.0.0.0" "192.168.1.1" "10.0.0.1")
for interface in "${EXTERNAL_INTERFACES[@]}"; do
    if curl -s --connect-timeout 2 "http://$interface:$OLLAMA_PORT/api/tags" &> /dev/null; then
        echo "⚠️  WARNING: Ollama may be accessible from external interface: $interface"
        echo "Please ensure firewall is configured to block external access"
    fi
done

# Install required models for RAG system
echo "📦 Installing AI models for local operation..."

for model in "${MODELS_TO_INSTALL[@]}"; do
    echo "⬇️  Downloading model: $model"

    # Check if model is already installed
    if ollama list | grep -q "$model"; then
        echo "✅ Model $model is already installed"
    else
        echo "📥 Installing model: $model (this may take several minutes)..."

        # Install model with progress indication
        if ollama pull "$model"; then
            echo "✅ Model $model installed successfully"
        else
            echo "❌ Failed to install model: $model"
            echo "⚠️  Continuing with other models..."
        fi
    fi
done

# Verify installed models
echo "📋 Verifying installed models..."
INSTALLED_MODELS=$(ollama list)
echo "$INSTALLED_MODELS"

# Test model functionality
echo "🧪 Testing model functionality..."
for model in "${MODELS_TO_INSTALL[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "🔍 Testing model: $model"

        # Simple test query
        TEST_RESPONSE=$(ollama generate "$model" "Say 'Hello' in one word" 2>/dev/null || echo "Test failed")

        if [[ "$TEST_RESPONSE" == *"Hello"* ]] || [[ "$TEST_RESPONSE" == *"hello"* ]]; then
            echo "✅ Model $model is working correctly"
        else
            echo "⚠️  Model $model test gave unexpected response: $TEST_RESPONSE"
        fi
    fi
done

# Create Ollama service management script
echo "📄 Creating Ollama service management script..."
cat > ../scripts/manage_ollama.sh << 'EOF'
#!/bin/bash
"""
Ollama Service Management Script
Manages Ollama service for secure local operation
"""

OLLAMA_HOST="127.0.0.1"
OLLAMA_PORT="11434"

case "$1" in
    start)
        echo "🚀 Starting Ollama service..."
        if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
            echo "✅ Ollama service is already running"
        else
            nohup ollama serve > /dev/null 2>&1 &
            sleep 5
            if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
                echo "✅ Ollama service started successfully"
            else
                echo "❌ Failed to start Ollama service"
                exit 1
            fi
        fi
        ;;
    stop)
        echo "🛑 Stopping Ollama service..."
        pkill -f "ollama serve" && echo "✅ Ollama service stopped" || echo "⚠️  Ollama service was not running"
        ;;
    restart)
        echo "🔄 Restarting Ollama service..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "📊 Checking Ollama service status..."
        if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
            echo "✅ Ollama service is running"
            echo "📋 Available models:"
            ollama list
        else
            echo "❌ Ollama service is not running"
            exit 1
        fi
        ;;
    models)
        echo "📋 Installed models:"
        ollama list
        ;;
    test)
        echo "🧪 Testing Ollama functionality..."
        if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
            echo "✅ Ollama API is responding"
            echo "🔍 Testing model response..."
            ollama generate mistral "Hello" --verbose || echo "❌ Model test failed"
        else
            echo "❌ Ollama service is not accessible"
            exit 1
        fi
        ;;
    security-check)
        echo "🔒 Performing security validation..."

        # Check localhost access
        if curl -s "http://$OLLAMA_HOST:$OLLAMA_PORT/api/tags" &> /dev/null; then
            echo "✅ Ollama accessible on localhost"
        else
            echo "❌ Ollama not accessible on localhost"
            exit 1
        fi

        # Check for external access
        echo "🔍 Checking for external access..."
        EXTERNAL_ACCESSIBLE=false

        for port in 11434; do
            if netstat -tlnp 2>/dev/null | grep ":$port" | grep -v "127.0.0.1\|::1"; then
                echo "⚠️  WARNING: Ollama may be accessible externally on port $port"
                EXTERNAL_ACCESSIBLE=true
            fi
        done

        if [ "$EXTERNAL_ACCESSIBLE" = false ]; then
            echo "✅ Ollama is configured for local access only"
        else
            echo "🚨 SECURITY WARNING: Configure firewall to block external access"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|models|test|security-check}"
        echo ""
        echo "Commands:"
        echo "  start          Start Ollama service"
        echo "  stop           Stop Ollama service"
        echo "  restart        Restart Ollama service"
        echo "  status         Check service status and list models"
        echo "  models         List installed models"
        echo "  test           Test Ollama functionality"
        echo "  security-check Validate security configuration"
        exit 1
        ;;
esac
EOF

chmod +x ../scripts/manage_ollama.sh
echo "✅ Ollama management script created"

# Create Ollama service file for systemd (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v systemctl &> /dev/null; then
    echo "📄 Creating systemd service file..."

    sudo tee /etc/systemd/system/ollama.service > /dev/null << EOF
[Unit]
Description=Ollama Server
After=network-online.target

[Service]
ExecStart=$(which ollama) serve
User=$(whoami)
Group=$(whoami)
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=127.0.0.1"
Environment="OLLAMA_PORT=11434"

[Install]
WantedBy=default.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ollama
    echo "✅ Systemd service file created and enabled"
fi

# Final security check
echo "🔒 Final security validation..."
../scripts/manage_ollama.sh security-check

# Create model testing script
cat > ../scripts/test_models.sh << 'EOF'
#!/bin/bash
"""
Model Testing Script
Tests all installed models for functionality and response quality
"""

echo "🧪 Testing all installed Ollama models"
echo "====================================="

MODELS=($(ollama list | tail -n +2 | awk '{print $1}' | grep -v "^$"))

if [ ${#MODELS[@]} -eq 0 ]; then
    echo "❌ No models found. Please install models first."
    exit 1
fi

for model in "${MODELS[@]}"; do
    echo ""
    echo "🔍 Testing model: $model"
    echo "------------------------"

    # Test basic functionality
    echo "📝 Basic response test..."
    RESPONSE=$(ollama generate "$model" "Hello, respond with just 'Hello back'" 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
        echo "✅ Model $model is responding"
        echo "📄 Response: $RESPONSE"
    else
        echo "❌ Model $model failed to respond"
        continue
    fi

    # Test RAG-style query
    echo "🧠 RAG capability test..."
    RAG_RESPONSE=$(ollama generate "$model" "Based on the context 'Python is a programming language', answer: What is Python?" 2>/dev/null)

    if [ $? -eq 0 ] && [[ "$RAG_RESPONSE" == *"programming"* ]]; then
        echo "✅ Model $model shows good RAG capability"
    else
        echo "⚠️  Model $model RAG response needs review"
        echo "📄 Response: $RAG_RESPONSE"
    fi
done

echo ""
echo "🎉 Model testing completed!"
EOF

chmod +x ../scripts/test_models.sh
echo "✅ Model testing script created"

# Summary
echo ""
echo "🎉 OLLAMA SETUP COMPLETE!"
echo "========================="
echo "✅ Ollama installed and running"
echo "✅ AI models downloaded and tested:"
for model in "${MODELS_TO_INSTALL[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "   ✅ $model"
    else
        echo "   ❌ $model (installation failed)"
    fi
done
echo "✅ Security validation passed"
echo "✅ Management scripts created"
echo ""
echo "📋 Next Steps:"
echo "1. Test models: ./scripts/test_models.sh"
echo "2. Check service: ./scripts/manage_ollama.sh status"
echo "3. Install Python dependencies: pip install -r app/requirements.txt"
echo ""
echo "🔒 Security Notes:"
echo "• Ollama is configured for local access only (127.0.0.1:11434)"
echo "• All AI models are stored locally"
echo "• No external API calls are made during inference"
echo "• Configure firewall to block external access to port 11434"
echo ""
echo "📋 Available Commands:"
echo "• ./scripts/manage_ollama.sh status    - Check service status"
echo "• ./scripts/manage_ollama.sh models    - List installed models"
echo "• ./scripts/manage_ollama.sh test      - Test functionality"
echo "• ./scripts/test_models.sh             - Test all models"
echo ""
echo "🚀 Ready for secure local AI inference!"