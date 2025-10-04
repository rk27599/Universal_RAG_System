# Secure RAG System - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Secure RAG System in a production environment with complete data sovereignty and enterprise-grade security.

## Prerequisites

### System Requirements

**Minimum Hardware:**
- CPU: 4 cores (8+ recommended)
- RAM: 8GB (16GB+ recommended)
- Storage: 100GB SSD (500GB+ recommended)
- Network: Gigabit Ethernet

**Recommended Hardware:**
- CPU: 8+ cores with GPU support (NVIDIA RTX 3060 or better)
- RAM: 32GB+
- Storage: 1TB NVMe SSD
- Network: 10GbE for high-throughput scenarios

### Software Prerequisites

**Required:**
- Docker Engine 24.0+
- Docker Compose 2.20+
- Git
- Bash shell
- OpenSSL (for SSL certificates)

**Optional:**
- NVIDIA Docker (for GPU acceleration)
- Fail2ban (for additional security)
- UFW/iptables (for firewall management)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd secure-rag-system
```

### 2. Configuration

```bash
# Create environment file from template
cp .env.example .env

# Edit configuration (IMPORTANT: Update all passwords!)
nano .env
```

### 3. Deploy

```bash
# Run deployment script
./scripts/deploy.sh
```

### 4. Access System

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Monitoring**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs

## Detailed Deployment

### Environment Configuration

Edit `.env` file with production values:

```bash
# Database Configuration
POSTGRES_DB=rag_production
POSTGRES_USER=rag_admin
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>

# Redis Configuration
REDIS_PASSWORD=<STRONG_PASSWORD_HERE>

# Application Security
SECRET_KEY=<MINIMUM_32_CHARACTER_SECRET_KEY>
GRAFANA_PASSWORD=<STRONG_PASSWORD_HERE>

# SSL Configuration
ENABLE_SSL=true
SSL_EMAIL=admin@yourdomain.com

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=/var/backups/rag-system

# Monitoring
ENABLE_MONITORING=true
```

### Security Hardening

#### 1. Firewall Configuration

```bash
# Install and configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### 2. SSL Certificates

**Option A: Let's Encrypt (Recommended for production)**
```bash
# Install Certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
```

**Option B: Self-signed (Development/Internal use)**
```bash
# Generate self-signed certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

#### 3. Additional Security Measures

```bash
# Install Fail2ban
sudo apt install fail2ban

# Configure Fail2ban for Docker
sudo tee /etc/fail2ban/jail.d/docker.conf << EOF
[docker-rag]
enabled = true
port = 80,443
protocol = tcp
filter = docker-rag
logpath = ./data/logs/nginx/access.log
bantime = 3600
findtime = 600
maxretry = 5
EOF
```

### Service Management

#### Starting Services
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Start specific service
docker-compose -f docker-compose.prod.yml up -d backend
```

#### Stopping Services
```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop specific service
docker-compose -f docker-compose.prod.yml stop backend
```

#### Viewing Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Monitoring and Alerting

#### Grafana Dashboard Access
1. Navigate to http://localhost:3001
2. Login with admin/password (change immediately)
3. Import pre-configured dashboards
4. Set up alert notifications

#### Prometheus Metrics
- Access: http://localhost:9090
- Monitor system health and performance
- Set up custom alerts

#### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health
curl http://localhost:3000/health

# Database health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
```

## Backup and Recovery

### Automated Backups

#### Setup Cron Job
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/secure-rag-system/scripts/backup.sh --cron
```

#### Manual Backup
```bash
# Create backup
./scripts/backup.sh

# Backup will be saved to ./backups/YYYYMMDD_HHMMSS.tar.gz
```

### Recovery Procedures

#### Full System Recovery
```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
./scripts/restore.sh ./backups/20231225_120000.tar.gz

# Services will restart automatically
```

#### Partial Recovery
```bash
# Database only
./scripts/restore.sh ./backups/20231225_120000.tar.gz --database-only

# Files only
./scripts/restore.sh ./backups/20231225_120000.tar.gz --files-only

# Configurations only
./scripts/restore.sh ./backups/20231225_120000.tar.gz --configs-only
```

## Performance Optimization

### Resource Allocation

#### Docker Resource Limits
Edit `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### PostgreSQL Tuning
```bash
# Edit PostgreSQL configuration
docker-compose -f docker-compose.prod.yml exec postgres \
    bash -c "echo 'shared_buffers = 256MB' >> /var/lib/postgresql/data/postgresql.conf"

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

#### Ollama GPU Acceleration
Ensure GPU support in `docker-compose.prod.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Caching Configuration

#### Redis Configuration
```bash
# Optimize Redis for your workload
docker-compose -f docker-compose.prod.yml exec redis \
    redis-cli CONFIG SET maxmemory 1gb
```

#### Nginx Caching
Static assets are automatically cached. Adjust cache times in `nginx/nginx.conf`.

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check ports
sudo netstat -tlnp | grep :8000
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Reset database
docker-compose -f docker-compose.prod.yml down
docker volume rm rag_postgres_data
docker-compose -f docker-compose.prod.yml up -d
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check system resources
htop
df -h
free -h

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

### Log Analysis

#### Application Logs
```bash
# Backend application logs
docker-compose -f docker-compose.prod.yml logs backend

# Nginx access logs
tail -f ./data/logs/nginx/access.log

# Error logs
tail -f ./data/logs/nginx/error.log
```

#### System Monitoring
```bash
# Container stats
docker stats

# Disk usage
du -sh ./data/*

# Memory usage
free -h

# CPU usage
top
```

## Security Maintenance

### Regular Security Tasks

#### Update System
```bash
# Update host system
sudo apt update && sudo apt upgrade

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### Security Audits
```bash
# Run security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image rag-backend:latest

# Check for vulnerabilities
./scripts/security_audit.sh
```

#### Certificate Renewal
```bash
# Renew Let's Encrypt certificates
sudo certbot renew

# Update certificates in containers
sudo cp /etc/letsencrypt/live/yourdomain.com/* nginx/ssl/
docker-compose -f docker-compose.prod.yml restart nginx
```

### Access Control

#### User Management
- Frontend authentication is handled by the application
- Admin access should be limited and monitored
- Regular password rotation is recommended

#### Network Security
- Use VPN for remote access
- Implement network segmentation
- Monitor access logs regularly

## Scaling and High Availability

### Horizontal Scaling

#### Load Balancer Configuration
```bash
# Add load balancer to docker-compose.prod.yml
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

#### Database Replication
For high availability, consider PostgreSQL streaming replication.

### Monitoring Scaling

#### Resource Monitoring
- Set up alerts for CPU, memory, and disk usage
- Monitor response times and error rates
- Track user activity and system load

## Compliance and Audit

### Data Sovereignty
- All data remains local
- No external API calls or data transfers
- Complete control over data processing

### Audit Trails
- All user actions are logged
- System access is monitored
- Regular security audits are recommended

### Compliance Reporting
- Generate regular compliance reports
- Document security measures
- Maintain backup and recovery procedures

## Support and Maintenance

### Regular Maintenance Tasks
1. Daily: Monitor system health and logs
2. Weekly: Review security alerts and updates
3. Monthly: Perform security audits and updates
4. Quarterly: Review and test backup/recovery procedures

### Performance Monitoring
- Monitor response times
- Track resource utilization
- Review user activity patterns

### Capacity Planning
- Monitor growth trends
- Plan for storage expansion
- Consider performance upgrades

For additional support, refer to the troubleshooting guides and system administration documentation.