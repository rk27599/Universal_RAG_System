# Secure RAG System - Administrator Guide

## Overview

This guide provides comprehensive instructions for system administrators managing the Secure RAG System. It covers installation, configuration, monitoring, maintenance, and troubleshooting procedures for production environments.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation & Setup](#installation--setup)
3. [Configuration Management](#configuration-management)
4. [Service Management](#service-management)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Security Management](#security-management)
7. [Backup & Recovery](#backup--recovery)
8. [Performance Tuning](#performance-tuning)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance Procedures](#maintenance-procedures)

## System Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Frontend    │    │      Nginx      │    │    Backend      │
│   (React App)   │◄──►│  (Reverse Proxy)│◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │    │     Ollama      │
│   (Database)    │    │    (Cache)      │    │  (LLM Service)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      Monitoring         │
                    │  (Prometheus/Grafana)   │
                    └─────────────────────────┘
```

### Service Dependencies

- **Frontend**: Depends on Nginx and Backend
- **Backend**: Depends on PostgreSQL, Redis, and Ollama
- **Nginx**: Acts as reverse proxy for all services
- **PostgreSQL**: Primary data store
- **Redis**: Session and cache storage
- **Ollama**: Local LLM inference
- **Monitoring**: Observes all services

## Installation & Setup

### Prerequisites

#### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ SSD
- **Network**: Stable internet connection

#### Software Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y git curl wget htop iotop jq
```

### Initial Deployment

1. **Clone Repository**
```bash
git clone <repository-url>
cd secure-rag-system
```

2. **Configure Environment**
```bash
cp .env.example .env
nano .env  # Update all passwords and configurations
```

3. **Deploy System**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

4. **Verify Installation**
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Test health endpoints
curl http://localhost:8000/api/health
curl http://localhost:3000/health
```

## Configuration Management

### Environment Variables

#### Critical Security Settings
```bash
# Database Configuration
POSTGRES_DB=rag_system
POSTGRES_USER=rag_admin
POSTGRES_PASSWORD=<STRONG_PASSWORD>

# Redis Configuration
REDIS_PASSWORD=<STRONG_PASSWORD>

# Application Security
SECRET_KEY=<MINIMUM_32_CHARACTER_KEY>
JWT_SECRET_KEY=<MINIMUM_32_CHARACTER_KEY>

# SSL Configuration
ENABLE_SSL=true
SSL_EMAIL=admin@yourdomain.com
```

#### Performance Settings
```bash
# Resource Limits
MAX_UPLOAD_SIZE=50MB
MAX_CONCURRENT_UPLOADS=5
WORKER_PROCESSES=4

# Cache Configuration
REDIS_MAX_MEMORY=2GB
CACHE_TTL=3600

# Database Settings
POSTGRES_MAX_CONNECTIONS=100
POSTGRES_SHARED_BUFFERS=256MB
```

### Docker Configuration

#### Production Compose Override
Create `docker-compose.override.yml` for environment-specific settings:

```yaml
version: '3.8'
services:
  backend:
    environment:
      - LOG_LEVEL=INFO
      - WORKERS=4
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  postgres:
    environment:
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_MAX_CONNECTIONS=100
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

### Nginx Configuration

#### SSL Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Your existing location blocks here
}
```

## Service Management

### Docker Commands

#### Service Control
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# View service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

#### Container Management
```bash
# Execute commands in containers
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U rag_admin -d rag_system

# View container resource usage
docker stats

# Clean up unused resources
docker system prune -f
```

### Health Checks

#### Automated Health Monitoring
```bash
#!/bin/bash
# health_check.sh

SERVICES=("backend:8000/api/health" "frontend:3000/health")
ALERT_EMAIL="admin@yourdomain.com"

for service in "${SERVICES[@]}"; do
    if ! curl -sf "http://$service" > /dev/null; then
        echo "ALERT: $service is down" | mail -s "Service Alert" $ALERT_EMAIL
    fi
done
```

#### Manual Health Checks
```bash
# Backend health
curl -f http://localhost:8000/api/health || echo "Backend down"

# Database connection
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U rag_admin

# Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Ollama service
curl -f http://localhost:11434/api/version || echo "Ollama down"
```

## Monitoring & Alerting

### Prometheus Configuration

#### Key Metrics to Monitor
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'rag-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

#### Alert Rules
```yaml
# alert_rules.yml
groups:
  - name: rag_system_alerts
    rules:
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"

      - alert: DatabaseConnectionsFull
        expr: pg_stat_database_numbackends > 80
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly full"
```

### Grafana Dashboards

#### System Overview Dashboard
Import dashboard ID: 1860 (Node Exporter Full)

#### Custom RAG System Dashboard
```json
{
  "dashboard": {
    "title": "RAG System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### Log Management

#### Centralized Logging
```bash
# Configure log rotation
sudo tee /etc/logrotate.d/rag-system << EOF
/var/log/rag-system/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 root root
}
EOF
```

#### Log Analysis Commands
```bash
# Backend errors
docker-compose -f docker-compose.prod.yml logs backend | grep ERROR

# Nginx access patterns
tail -f data/logs/nginx/access.log | grep -E "(POST|PUT|DELETE)"

# Database slow queries
docker-compose -f docker-compose.prod.yml exec postgres psql -U rag_admin -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Security Management

### Access Control

#### User Management
```bash
# Create admin user (if authentication is implemented)
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.auth import create_admin_user
create_admin_user('admin@example.com', 'secure_password')
"
```

#### Network Security
```bash
# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Monitor connections
sudo netstat -tulnp | grep :8000
```

### SSL/TLS Management

#### Certificate Installation
```bash
# Let's Encrypt certificates
sudo certbot certonly --standalone -d yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

#### Certificate Renewal
```bash
# Add to crontab for automatic renewal
0 3 * * * certbot renew --quiet && docker-compose -f /path/to/rag/docker-compose.prod.yml restart nginx
```

### Security Auditing

#### Vulnerability Scanning
```bash
# Scan Docker images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image rag-backend:latest

# System security audit
sudo lynis audit system
```

#### Security Checklist
- [ ] All default passwords changed
- [ ] SSL/TLS properly configured
- [ ] Firewall rules in place
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Access logs monitored
- [ ] Security headers configured

## Backup & Recovery

### Automated Backup

#### Backup Script Configuration
```bash
# Configure automated backups
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/rag/scripts/backup.sh --cron
```

#### Backup Verification
```bash
# Verify backup integrity
./scripts/backup.sh
tar -tzf ./backups/$(date +%Y%m%d)_*.tar.gz | head -10
```

### Disaster Recovery

#### Full System Recovery
```bash
# 1. Stop current services
docker-compose -f docker-compose.prod.yml down

# 2. Restore from backup
./scripts/restore.sh ./backups/20231225_120000.tar.gz

# 3. Verify restoration
./scripts/verify_restoration.sh
```

#### Partial Recovery Scenarios
```bash
# Database only
./scripts/restore.sh ./backups/backup.tar.gz --database-only

# Configuration files only
./scripts/restore.sh ./backups/backup.tar.gz --configs-only

# Uploaded files only
./scripts/restore.sh ./backups/backup.tar.gz --files-only
```

### Backup Storage Management

#### Remote Backup Storage
```bash
# Configure rsync to remote server
rsync -avz --delete ./backups/ backup-server:/backups/rag-system/

# S3 backup (if configured)
aws s3 sync ./backups/ s3://your-backup-bucket/rag-system/
```

## Performance Tuning

### Database Optimization

#### PostgreSQL Tuning
```sql
-- Optimize PostgreSQL configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
SELECT pg_reload_conf();
```

#### Index Optimization
```sql
-- Monitor slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_documents_created_at ON documents(created_at);
CREATE INDEX CONCURRENTLY idx_chunks_document_id ON chunks(document_id);
```

### Application Performance

#### Backend Optimization
```bash
# Adjust worker processes
export WORKERS=4
export WORKER_CLASS=uvicorn.workers.UvicornWorker
export MAX_REQUESTS=1000
```

#### Memory Management
```bash
# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Adjust container memory limits
docker-compose -f docker-compose.prod.yml up -d --scale backend=2
```

### Caching Strategy

#### Redis Optimization
```bash
# Configure Redis for performance
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory 2gb
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Application-Level Caching
```python
# Configure cache settings in application
CACHE_CONFIG = {
    "default_timeout": 3600,  # 1 hour
    "key_prefix": "rag_cache:",
    "redis_url": "redis://redis:6379/0"
}
```

## Troubleshooting

### Common Issues

#### Service Startup Problems
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs --tail=50 backend

# Check resource usage
docker system df
df -h

# Verify network connectivity
docker network ls
docker network inspect rag_default
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check connection limits
docker-compose -f docker-compose.prod.yml exec postgres psql -U rag_admin -c "SELECT count(*) FROM pg_stat_activity;"

# Reset database connections
docker-compose -f docker-compose.prod.yml restart postgres
```

#### Performance Issues
```bash
# Check system resources
htop
iotop
free -h

# Monitor container resource usage
docker stats

# Check disk I/O
iostat -x 1

# Network monitoring
iftop
netstat -i
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set debug environment variables
export LOG_LEVEL=DEBUG
export FASTAPI_DEBUG=true

# Restart services with debug mode
docker-compose -f docker-compose.prod.yml up -d
```

#### Debug Database Issues
```sql
-- Check active queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Check locks
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# daily_maintenance.sh

# Check service health
./scripts/health_check.sh

# Monitor disk usage
df -h | grep -E "(8[0-9]|9[0-9])%"

# Check for errors in logs
docker-compose -f docker-compose.prod.yml logs --since 24h | grep -i error

# Backup verification
ls -la ./backups/ | tail -5
```

#### Weekly Tasks
```bash
#!/bin/bash
# weekly_maintenance.sh

# Update system packages
sudo apt update && sudo apt list --upgradable

# Docker cleanup
docker system prune -f

# Database maintenance
docker-compose -f docker-compose.prod.yml exec postgres psql -U rag_admin -c "VACUUM ANALYZE;"

# Certificate expiry check
openssl x509 -in nginx/ssl/cert.pem -text -noout | grep "Not After"
```

#### Monthly Tasks
```bash
#!/bin/bash
# monthly_maintenance.sh

# Full system update
sudo apt update && sudo apt upgrade -y

# Security audit
./scripts/security_audit.sh

# Performance review
./scripts/performance_report.sh

# Backup cleanup (keep last 3 months)
find ./backups/ -name "*.tar.gz" -mtime +90 -delete
```

### Update Procedures

#### System Updates
```bash
# Update host system
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Verify updates
./scripts/health_check.sh
```

#### Application Updates
```bash
# Backup before update
./scripts/backup.sh

# Pull latest code
git pull origin main

# Rebuild and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run post-update tests
./scripts/integration_tests.sh
```

### Capacity Planning

#### Resource Monitoring
```bash
# CPU usage trend
sar -u 1 60

# Memory usage analysis
free -h
cat /proc/meminfo

# Disk I/O patterns
iostat -x 1 60

# Network utilization
iftop -t -s 60
```

#### Growth Planning
- Monitor user growth and usage patterns
- Track document processing volumes
- Plan storage expansion based on growth trends
- Consider horizontal scaling for high load scenarios

## Emergency Procedures

### Service Recovery

#### Complete System Failure
1. **Assess the situation**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   systemctl status docker
   ```

2. **Emergency backup** (if possible)
   ```bash
   ./scripts/emergency_backup.sh
   ```

3. **Restore from last known good backup**
   ```bash
   ./scripts/restore.sh ./backups/latest_good_backup.tar.gz --force
   ```

#### Data Corruption Recovery
1. **Stop all services immediately**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Assess corruption extent**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres pg_dump --schema-only
   ```

3. **Restore from backup**
   ```bash
   ./scripts/restore.sh ./backups/pre_corruption_backup.tar.gz --database-only
   ```

### Contact Information

#### Escalation Procedures
- **Level 1**: System Administrator (Internal IT)
- **Level 2**: Senior DevOps Engineer
- **Level 3**: Vendor Support / External Consultant

#### Emergency Contacts
- **Internal IT**: +1-XXX-XXX-XXXX
- **DevOps Team**: devops@yourcompany.com
- **Vendor Support**: support@vendor.com

For immediate assistance during critical outages, follow the documented escalation procedures and maintain detailed logs of all recovery actions taken.

---

This guide should be reviewed and updated regularly to reflect system changes and operational lessons learned.