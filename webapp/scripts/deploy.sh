#!/bin/bash

# Production Deployment Script for Secure RAG System
# This script deploys the complete RAG system with security configurations

set -e

echo "🚀 Starting Secure RAG System Deployment"
echo "========================================"

# Configuration
PROJECT_NAME="secure-rag-system"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
ENV_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed. Please install Docker first."
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is required but not installed. Please install Docker Compose first."
    fi

    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        warn ".env file not found. Creating from template..."
        create_env_file
    fi

    log "Prerequisites check completed ✅"
}

# Create environment file
create_env_file() {
    cat > "$ENV_FILE" << 'EOF'
# Database Configuration
POSTGRES_DB=rag_system
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=secure_random_password_here

# Redis Configuration
REDIS_PASSWORD=redis_secure_password_here

# Application Security
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
GRAFANA_PASSWORD=admin_secure_password

# SSL Configuration (set to true for HTTPS)
ENABLE_SSL=false
SSL_EMAIL=admin@localhost

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=./backups

# Monitoring
ENABLE_MONITORING=true
EOF

    log "Created .env file template. Please update passwords and configuration."
    warn "IMPORTANT: Update all passwords in .env file before deploying!"
}

# Backup existing data
backup_data() {
    if [ -d "./data" ]; then
        log "Creating backup of existing data..."
        mkdir -p "$BACKUP_DIR"
        cp -r ./data "$BACKUP_DIR/"
        log "Backup created: $BACKUP_DIR ✅"
    fi
}

# Pre-deployment validation
validate_configuration() {
    log "Validating configuration..."

    # Check if environment variables are set
    source "$ENV_FILE"

    if [ "$POSTGRES_PASSWORD" = "secure_random_password_here" ]; then
        error "Please update POSTGRES_PASSWORD in .env file"
    fi

    if [ "$REDIS_PASSWORD" = "redis_secure_password_here" ]; then
        error "Please update REDIS_PASSWORD in .env file"
    fi

    if [ "$SECRET_KEY" = "your-super-secret-key-minimum-32-characters-long" ]; then
        error "Please update SECRET_KEY in .env file"
    fi

    log "Configuration validation completed ✅"
}

# Initialize directories
init_directories() {
    log "Initializing directories..."

    # Create necessary directories
    mkdir -p data/uploads
    mkdir -p data/logs/nginx
    mkdir -p nginx/ssl
    mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources}}
    mkdir -p backups

    # Set proper permissions
    chmod 755 data/uploads
    chmod 755 data/logs

    log "Directories initialized ✅"
}

# Setup Ollama models
setup_ollama() {
    log "Setting up Ollama models..."

    cat > scripts/setup_ollama.sh << 'EOF'
#!/bin/bash
echo "Setting up Ollama models..."

# Wait for Ollama to be ready
sleep 30

# Pull required models
ollama pull mistral
ollama pull llama2
ollama pull codellama

echo "Ollama models setup completed"
EOF

    chmod +x scripts/setup_ollama.sh
    log "Ollama setup script created ✅"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring configuration..."

    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rag-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'rag-frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/health'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'ollama'
    static_configs:
      - targets: ['ollama:11434']
EOF

    # Grafana datasource
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    log "Monitoring configuration created ✅"
}

# Deploy services
deploy_services() {
    log "Deploying services..."

    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull

    # Build custom images
    docker-compose -f docker-compose.prod.yml build

    # Start services
    docker-compose -f docker-compose.prod.yml up -d

    log "Services deployed ✅"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."

    # Wait for database
    echo -n "Waiting for database..."
    while ! docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U ${POSTGRES_USER:-rag_user} > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"

    # Wait for backend
    echo -n "Waiting for backend..."
    while ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"

    # Wait for frontend
    echo -n "Waiting for frontend..."
    while ! curl -s http://localhost:3000 > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"

    log "All services are ready ✅"
}

# Post-deployment validation
validate_deployment() {
    log "Validating deployment..."

    # Check service health
    if ! curl -s http://localhost:8000/api/health | grep -q "healthy"; then
        error "Backend health check failed"
    fi

    if ! curl -s http://localhost:3000 > /dev/null; then
        error "Frontend is not accessible"
    fi

    # Check database connection
    if ! docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U ${POSTGRES_USER:-rag_user} > /dev/null; then
        error "Database connection failed"
    fi

    log "Deployment validation completed ✅"
}

# Setup SSL certificates (if enabled)
setup_ssl() {
    source "$ENV_FILE"

    if [ "$ENABLE_SSL" = "true" ]; then
        log "Setting up SSL certificates..."

        # Create self-signed certificates for development
        if [ ! -f "nginx/ssl/cert.pem" ]; then
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout nginx/ssl/key.pem \
                -out nginx/ssl/cert.pem \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

            log "Self-signed SSL certificates created ✅"
        fi
    fi
}

# Main deployment function
main() {
    log "Starting deployment of Secure RAG System..."

    check_prerequisites
    backup_data
    validate_configuration
    init_directories
    setup_ollama
    setup_monitoring
    setup_ssl
    deploy_services
    wait_for_services
    validate_deployment

    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "========================================"
    echo ""
    echo -e "${BLUE}Access your Secure RAG System:${NC}"
    echo "• Frontend: http://localhost:3000"
    echo "• Backend API: http://localhost:8000"
    echo "• API Documentation: http://localhost:8000/docs"
    echo "• Monitoring: http://localhost:3001 (admin/admin)"
    echo ""
    echo -e "${YELLOW}Important notes:${NC}"
    echo "• All services are running in Docker containers"
    echo "• Data is persisted in Docker volumes"
    echo "• Logs are available in ./data/logs/"
    echo "• Backups are stored in ./backups/"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Change default passwords in Grafana"
    echo "2. Configure SSL certificates for production"
    echo "3. Set up regular backups"
    echo "4. Review security configurations"
    echo ""
}

# Run main function
main "$@"