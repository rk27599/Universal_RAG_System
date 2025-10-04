# Deployment & Scalability Options

## 🔒 Security-First Deployment Strategy for RAG Web Application

### CRITICAL SECURITY REQUIREMENTS
- **🔒 Data Sovereignty**: ZERO external data transmission
- **🏠 Local-Only Processing**: All AI inference on controlled infrastructure
- **🚫 No Cloud Dependencies**: Complete independence from external services
- **🛡️ Air-Gap Capability**: Can operate without internet connection
- **📋 Compliance**: GDPR, HIPAA, SOC2 ready through local control
- **🔐 Encryption**: All data encrypted at rest and in transit locally

### Secondary Requirements
- **Performance**: Low latency for chat interactions (<500ms)
- **Availability**: 99.5%+ uptime for production use
- **Scalability**: Support 1K-100K users growth path while maintaining local control
- **Cost Optimization**: Minimize infrastructure costs during early stages
- **Maintenance**: Simple operations and monitoring

## 📊 Security-Focused Deployment Options Comparison

| Option | Self-Hosted VPS | Managed Cloud | Containerized | Serverless | Scoring Weight |
|--------|----------------|---------------|---------------|------------|----------------|
| **🔒 Data Security** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐ | **35%** |
| **🏠 Local Control** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ | **25%** |
| **🚫 No External Dependencies** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐ | **20%** |
| **💰 Cost Efficiency** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **10%** |
| **⚡ Ollama Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **10%** |
| **🔧 Setup Complexity** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **0%** |
| **🔒 SECURITY SCORE** | **🥇 100%** | **❌ 35%** | **⚠️ 70%** | **❌ 30%** | **100%** |

### ⚠️ Security Risk Assessment

| Deployment Option | Security Risk Level | Data Exposure Risk | Compliance Risk |
|------------------|-------------------|-------------------|-----------------|
| **Self-Hosted VPS** | 🟢 **MINIMAL** | 🟢 **ZERO** | 🟢 **COMPLIANT** |
| **Managed Cloud** | 🔴 **HIGH** | 🔴 **EXTERNAL** | 🔴 **COMPLEX** |
| **Containerized** | 🟡 **MEDIUM** | 🟡 **DEPENDS** | 🟡 **VARIABLE** |
| **Serverless** | 🔴 **MAXIMUM** | 🔴 **EXTERNAL** | 🔴 **NON-COMPLIANT** |

## 🖥️ Self-Hosted VPS - Detailed Analysis

### Recommended Self-Hosted Architecture

#### Phase 1: Single Server Setup (1-1K users)
```yaml
# Digital Ocean Droplet Configuration
CPU: 4 vCPUs
RAM: 8GB
Storage: 160GB SSD
Bandwidth: 5TB
Cost: $48/month

# Server Components
Services:
  - FastAPI application (port 8000)
  - PostgreSQL + pgvector (port 5432)
  - Ollama service (port 11434)
  - Nginx reverse proxy (port 80/443)
  - React build (served by Nginx)

# Directory Structure
/opt/rag-app/
├── app/                    # FastAPI application
├── frontend/build/         # React production build
├── models/                 # Ollama models
├── data/                   # Document storage
├── logs/                   # Application logs
├── backups/                # Database backups
└── ssl/                    # TLS certificates
```

#### Complete Single Server Setup Script
```bash
#!/bin/bash
# RAG Application Deployment Script

# System updates and dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx postgresql postgresql-contrib python3.10 python3-pip nodejs npm

# Install pgvector extension
sudo apt install -y postgresql-15-pgvector

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Setup application directory
sudo mkdir -p /opt/rag-app
sudo chown $USER:$USER /opt/rag-app
cd /opt/rag-app

# Clone and setup application
git clone https://github.com/your-repo/rag-web-app.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..

# PostgreSQL setup
sudo -u postgres createdb rag_database
sudo -u postgres psql -c "CREATE USER rag_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rag_database TO rag_user;"
sudo -u postgres psql -d rag_database -c "CREATE EXTENSION vector;"

# Initialize database schema
python manage.py migrate

# Ollama model setup
ollama pull mistral
ollama pull llama2

# Nginx configuration
sudo tee /etc/nginx/sites-available/rag-app << EOF
server {
    listen 80;
    server_name your-domain.com;

    # Static files
    location / {
        root /opt/rag-app/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/rag-app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Systemd services
sudo tee /etc/systemd/system/rag-app.service << EOF
[Unit]
Description=RAG Web Application
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/rag-app
Environment=PATH=/opt/rag-app/venv/bin
ExecStart=/opt/rag-app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable rag-app
sudo systemctl start rag-app

# Backup script
sudo tee /opt/rag-app/backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U rag_user rag_database > /opt/rag-app/backups/backup_\${DATE}.sql
gzip /opt/rag-app/backups/backup_\${DATE}.sql
find /opt/rag-app/backups -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /opt/rag-app/backup.sh
echo "0 2 * * * /opt/rag-app/backup.sh" | sudo crontab -
```

### Cost Analysis - Self-Hosted
```
Monthly Costs:
- DigitalOcean Droplet (8GB): $48/month
- Domain name: $12/year (~$1/month)
- SSL certificate: Free (Let's Encrypt)
- Backup storage: $5/month (optional)
Total: $54/month

Annual Cost: $648

vs Cloud Alternative:
- AWS ECS + RDS + ALB: ~$150-250/month
- Annual savings: $1,152-2,352 (64-78% savings)
```

### Performance Benchmarks
```
Single Server Performance (8GB RAM, 4 vCPU):
- Concurrent Users: 500-1000
- Document Processing: 2-5 docs/minute
- Chat Response Time: <500ms
- Vector Search: <100ms
- Database Queries: <50ms

Bottlenecks:
1. Ollama model inference (CPU bound)
2. Vector similarity search (memory bound)
3. File upload processing (I/O bound)
```

## ☁️ Managed Cloud Services - Analysis

### AWS ECS Fargate Setup
```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/rag_db
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - db
      - ollama

  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:80"

volumes:
  postgres_data:
  ollama_models:
```

### AWS Infrastructure as Code (Terraform)
```hcl
# AWS ECS deployment
resource "aws_ecs_cluster" "rag_cluster" {
  name = "rag-web-app"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_service" "rag_api" {
  name            = "rag-api"
  cluster         = aws_ecs_cluster.rag_cluster.id
  task_definition = aws_ecs_task_definition.rag_api.arn
  desired_count   = 2

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.rag_api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.rag_api.arn
    container_name   = "rag-api"
    container_port   = 8000
  }
}

resource "aws_rds_instance" "rag_database" {
  identifier = "rag-database"
  engine     = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.medium"
  allocated_storage = 100
  storage_encrypted = true

  db_name  = "rag_database"
  username = "rag_user"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.rag.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "rag-database-final-snapshot"
}

# Application Load Balancer
resource "aws_lb" "rag_alb" {
  name               = "rag-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = var.public_subnet_ids
}
```

### Cloud Cost Analysis
```
AWS Monthly Costs (US East):
- ECS Fargate (2 tasks, 0.5 vCPU, 1GB): $35/month
- RDS PostgreSQL (db.t3.medium): $65/month
- Application Load Balancer: $18/month
- CloudFront CDN: $10/month
- Route 53 DNS: $1/month
- S3 storage (documents): $5/month
- CloudWatch logs: $5/month
Total: $139/month

GCP Monthly Costs:
- Cloud Run (similar config): $40/month
- Cloud SQL PostgreSQL: $70/month
- Load Balancer: $18/month
- CDN: $8/month
- Storage: $5/month
Total: $141/month

Azure Monthly Costs:
- Container Instances: $45/month
- PostgreSQL Database: $75/month
- Load Balancer: $20/month
- CDN: $10/month
- Storage: $5/month
Total: $155/month
```

### ❌ Why Managed Cloud is REJECTED for Security Reasons

**CRITICAL SECURITY FAILURES:**
- **Data Exposure**: All user documents and conversations transmitted to cloud providers
- **Vendor Surveillance**: Cloud providers can access, log, and analyze all data
- **Compliance Violations**: GDPR Article 25 violations through third-party processing
- **External Dependencies**: System becomes dependent on external services for core functionality
- **API Logging**: All AI model interactions logged by cloud providers
- **Jurisdictional Risk**: Data processed in multiple unknown jurisdictions

**ADDITIONAL CONCERNS:**
- **Cost**: 2.5x more expensive than self-hosted ($150-300/month vs $50/month)
- **Complexity**: More infrastructure components to manage and secure
- **Vendor Lock-in**: Platform-specific configurations
- **Ollama Integration**: Impossible - requires external AI APIs instead of local models

**🚫 CLOUD DEPLOYMENT EXPLICITLY FORBIDDEN FOR SECURITY REASONS**

## 🐳 Containerized Deployment - Analysis

### Docker Compose Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: rag-app:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://rag_user:${DB_PASSWORD}@db:5432/rag_database
      - OLLAMA_URL=http://ollama:11434
      - ENVIRONMENT=production
    volumes:
      - app_data:/app/data
      - app_logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - rag_network

  db:
    image: pgvector/pgvector:pg15
    restart: unless-stopped
    environment:
      POSTGRES_DB: rag_database
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - rag_network
    ports:
      - "5432:5432"

  ollama:
    image: ollama/ollama
    restart: unless-stopped
    volumes:
      - ollama_models:/root/.ollama
    networks:
      - rag_network
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - rag_network
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - frontend_build:/usr/share/nginx/html
    depends_on:
      - app
    networks:
      - rag_network

volumes:
  postgres_data:
  ollama_models:
  redis_data:
  app_data:
  app_logs:
  frontend_build:

networks:
  rag_network:
    driver: bridge
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-app
  template:
    metadata:
      labels:
        app: rag-app
    spec:
      containers:
      - name: rag-app
        image: rag-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: rag-app-service
spec:
  selector:
    app: rag-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - rag-app.example.com
    secretName: rag-app-tls
  rules:
  - host: rag-app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rag-app-service
            port:
              number: 80
```

### Container Orchestration Benefits
```bash
# Easy scaling
docker-compose up --scale app=3

# Zero-downtime deployments
kubectl rollout restart deployment/rag-app

# Resource monitoring
kubectl top pods
kubectl describe pod rag-app-xxx

# Log aggregation
kubectl logs -f deployment/rag-app

# Health checks and auto-recovery
# Automatically handled by orchestrator
```

### Container Strategy Limitations
- **Complexity**: Requires container orchestration knowledge
- **Resource Overhead**: Container runtime overhead
- **Ollama Integration**: GPU access more complex in containers
- **Local Development**: Additional complexity for developers

## ⚡ Serverless Options - Analysis

### AWS Lambda + API Gateway Approach
```python
# lambda_handler.py - Serverless function
import json
import boto3
from rag_system import RAGSystem

# Initialize outside handler for container reuse
rag_system = RAGSystem()

def lambda_handler(event, context):
    """AWS Lambda handler for RAG queries"""

    try:
        # Parse request
        body = json.loads(event['body'])
        query = body.get('query')
        user_id = event['requestContext']['authorizer']['userId']

        # Perform RAG query
        result = rag_system.demo_query(query, top_k=5)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# serverless.yml configuration
service: rag-web-app

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  environment:
    DATABASE_URL: ${env:DATABASE_URL}

functions:
  api:
    handler: lambda_handler.lambda_handler
    timeout: 30
    memory: 3008  # Max memory for better performance
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true

  websocket:
    handler: websocket_handler.handler
    events:
      - websocketApi:
          route: $connect
      - websocketApi:
          route: $disconnect
      - websocketApi:
          route: sendMessage

plugins:
  - serverless-python-requirements
  - serverless-wsgi

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
```

### Serverless Limitations for RAG
```python
# Problem 1: Cold start times
"""
Lambda cold start: 2-5 seconds
With ML models: 10-15 seconds
User experience: Poor for real-time chat
"""

# Problem 2: Memory/timeout constraints
"""
Max memory: 10GB (expensive)
Max timeout: 15 minutes
Large model loading: Problematic
"""

# Problem 3: Ollama integration
"""
Cannot run Ollama in Lambda
Must use external API (OpenAI, etc.)
Defeats purpose of local model hosting
"""

# Problem 4: WebSocket complexity
"""
API Gateway WebSocket:
- Complex state management
- Connection management overhead
- No persistent connections to Ollama
"""
```

### ❌ Why Serverless is COMPLETELY INCOMPATIBLE with Security Requirements

**FUNDAMENTAL SECURITY INCOMPATIBILITIES:**
- **No Local Models**: Serverless CANNOT run Ollama - forces external AI APIs
- **External Data Processing**: All function executions on vendor infrastructure
- **No Data Control**: Zero control over where code runs or data is processed
- **Vendor Logging**: All function calls, inputs, and outputs logged by provider
- **Cold Start Surveillance**: Provider can analyze all function invocations
- **No Air-Gap Capability**: Requires constant internet connectivity to vendor

**TECHNICAL LIMITATIONS:**
- **Cold Starts**: Poor user experience for real-time chat (2-15 second delays)
- **WebSocket Complexity**: Difficult to implement real-time features
- **Memory Constraints**: Cannot load local AI models
- **Timeout Limits**: Insufficient for document processing tasks
- **Cost at Scale**: Expensive for high-frequency chat operations

**🚫 SERVERLESS DEPLOYMENT CATEGORICALLY REJECTED FOR SECURITY REASONS**

## 🎯 Deployment Decision Matrix

### Scoring Breakdown

#### Setup Complexity (15% weight)
- **Self-Hosted**: Single server setup, manageable complexity
- **Managed Cloud**: Multiple services, complex infrastructure
- **Containerized**: Docker knowledge required, orchestration setup
- **Serverless**: Simple deployment, complex application constraints

#### Cost Efficiency (25% weight)
- **Self-Hosted**: $54/month, excellent value
- **Managed Cloud**: $139-155/month, 2.5x more expensive
- **Containerized**: $60-80/month (including orchestration)
- **Serverless**: Variable, expensive at scale

#### Scalability (20% weight)
- **Self-Hosted**: Limited to single server initially
- **Managed Cloud**: Excellent auto-scaling capabilities
- **Containerized**: Good horizontal scaling with orchestration
- **Serverless**: Excellent auto-scaling, limited by constraints

#### Control & Privacy (20% weight)
- **Self-Hosted**: Complete control, data privacy
- **Managed Cloud**: Limited control, vendor dependency
- **Containerized**: Good control, portable between providers
- **Serverless**: Limited control, vendor lock-in

## 🚀 Recommended Deployment Strategy

### Phase 1: Self-Hosted VPS (0-6 months)
```bash
# Immediate deployment
- DigitalOcean 8GB droplet: $48/month
- Single server with all components
- Manual deployment and monitoring
- 500-1000 concurrent users capacity

# Benefits:
✅ Low cost ($648/year)
✅ Complete control
✅ Simple architecture
✅ Fast time to market
✅ Full Ollama integration
```

### Phase 2: Enhanced Self-Hosted (6-12 months)
```bash
# Performance improvements
- Upgrade to 16GB droplet: $96/month
- Add Redis caching layer
- Implement monitoring (Prometheus + Grafana)
- Set up automated backups
- 1000-2000 concurrent users capacity

# Optimizations:
✅ Better performance monitoring
✅ Redis for query caching
✅ Automated operations
✅ Improved reliability
```

### Phase 3: Hybrid Cloud (12+ months)
```bash
# Scale components separately
- Application: Multiple VPS instances behind load balancer
- Database: Managed PostgreSQL (RDS/Cloud SQL)
- Models: Dedicated GPU instances for Ollama
- CDN: CloudFront/CloudFlare for static assets
- 5000+ concurrent users capacity

# Benefits:
✅ Horizontal scaling
✅ Managed database reliability
✅ Better performance
✅ Global CDN distribution
```

### Migration Path Example
```yaml
# Phase 1: All-in-one server
Server 1:
  - FastAPI app
  - PostgreSQL + pgvector
  - Ollama
  - Nginx
  - React static files

# Phase 2: Separated concerns
Load Balancer:
  - Nginx/HAProxy
App Servers (2-3):
  - FastAPI app
  - Redis cache
Database Server:
  - PostgreSQL + pgvector
AI Server:
  - Ollama + GPU
CDN:
  - Static assets

# Phase 3: Cloud hybrid
Load Balancer: Cloud LB
App Servers: Container orchestration
Database: Managed PostgreSQL
AI Services: GPU cloud instances
Storage: Object storage (S3/GCS)
CDN: Global edge locations
```

## 📊 Monitoring & Operations

### Essential Monitoring Setup
```python
# Health check endpoints
from fastapi import FastAPI
import psutil
import requests

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/ready")
async def readiness_check():
    """Readiness check for load balancers"""
    checks = {
        "database": await check_database(),
        "ollama": await check_ollama(),
        "disk_space": check_disk_space(),
        "memory": check_memory()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        content={"status": "ready" if all_healthy else "not ready", "checks": checks},
        status_code=status_code
    )

async def check_database():
    try:
        await database.fetch_one("SELECT 1")
        return True
    except:
        return False

async def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_disk_space():
    usage = psutil.disk_usage('/')
    free_percent = (usage.free / usage.total) * 100
    return free_percent > 10  # Alert if less than 10% free

def check_memory():
    memory = psutil.virtual_memory()
    return memory.percent < 90  # Alert if memory usage > 90%
```

### Backup Strategy
```bash
#!/bin/bash
# Comprehensive backup script

# Database backup
pg_dump -h localhost -U rag_user rag_database | gzip > "db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"

# Application data backup
tar -czf "app_data_$(date +%Y%m%d_%H%M%S).tar.gz" /opt/rag-app/data/

# Ollama models backup
tar -czf "models_$(date +%Y%m%d_%H%M%S).tar.gz" ~/.ollama/

# Upload to cloud storage (optional)
aws s3 sync /opt/rag-app/backups/ s3://rag-app-backups/

# Retention policy (keep 7 days local, 30 days cloud)
find /opt/rag-app/backups/ -name "*.gz" -mtime +7 -delete
```

This deployment strategy provides a clear path from simple self-hosted beginnings to scalable cloud infrastructure, optimizing for cost and simplicity initially while maintaining growth options.