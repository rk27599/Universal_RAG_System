#!/bin/bash

# Backup Script for Secure RAG System
# Creates comprehensive backups of database, uploaded files, and configurations

set -e

# Configuration
BACKUP_BASE_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE_DIR/$TIMESTAMP"
ENV_FILE=".env"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Create backup directory
create_backup_dir() {
    log "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

# Backup database
backup_database() {
    log "Backing up PostgreSQL database..."

    if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
        docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
            -U "${POSTGRES_USER:-rag_user}" \
            -d "${POSTGRES_DB:-rag_system}" \
            --no-password \
            > "$BACKUP_DIR/database.sql"

        log "Database backup completed ✅"
    else
        warn "PostgreSQL container is not running, skipping database backup"
    fi
}

# Backup uploaded files
backup_files() {
    log "Backing up uploaded files..."

    if [ -d "./data/uploads" ]; then
        cp -r ./data/uploads "$BACKUP_DIR/"
        log "Files backup completed ✅"
    else
        warn "No uploads directory found, skipping files backup"
    fi
}

# Backup configuration files
backup_configs() {
    log "Backing up configuration files..."

    # Create configs directory
    mkdir -p "$BACKUP_DIR/configs"

    # Backup important configuration files
    cp "$ENV_FILE" "$BACKUP_DIR/configs/" 2>/dev/null || warn ".env file not found"
    cp docker-compose.prod.yml "$BACKUP_DIR/configs/" 2>/dev/null || warn "docker-compose.prod.yml not found"
    cp -r nginx/ "$BACKUP_DIR/configs/" 2>/dev/null || warn "nginx directory not found"
    cp -r monitoring/ "$BACKUP_DIR/configs/" 2>/dev/null || warn "monitoring directory not found"

    log "Configuration backup completed ✅"
}

# Backup Docker volumes
backup_volumes() {
    log "Backing up Docker volumes..."

    # Create volumes backup directory
    mkdir -p "$BACKUP_DIR/volumes"

    # Backup PostgreSQL data
    if docker volume inspect rag_postgres_data >/dev/null 2>&1; then
        docker run --rm \
            -v rag_postgres_data:/source:ro \
            -v "$(pwd)/$BACKUP_DIR/volumes":/backup \
            alpine tar czf /backup/postgres_data.tar.gz -C /source .
        log "PostgreSQL volume backed up ✅"
    fi

    # Backup Redis data
    if docker volume inspect rag_redis_data >/dev/null 2>&1; then
        docker run --rm \
            -v rag_redis_data:/source:ro \
            -v "$(pwd)/$BACKUP_DIR/volumes":/backup \
            alpine tar czf /backup/redis_data.tar.gz -C /source .
        log "Redis volume backed up ✅"
    fi

    # Backup Ollama data
    if docker volume inspect rag_ollama_data >/dev/null 2>&1; then
        docker run --rm \
            -v rag_ollama_data:/source:ro \
            -v "$(pwd)/$BACKUP_DIR/volumes":/backup \
            alpine tar czf /backup/ollama_data.tar.gz -C /source .
        log "Ollama volume backed up ✅"
    fi
}

# Create backup metadata
create_metadata() {
    log "Creating backup metadata..."

    cat > "$BACKUP_DIR/backup_info.json" << EOF
{
    "backup_timestamp": "$TIMESTAMP",
    "backup_date": "$(date -Iseconds)",
    "system_info": {
        "hostname": "$(hostname)",
        "docker_version": "$(docker --version | cut -d' ' -f3 | cut -d',' -f1)",
        "compose_version": "$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)"
    },
    "services_status": {
$(docker-compose -f docker-compose.prod.yml ps --format json 2>/dev/null | jq -s '.' || echo '[]')
    },
    "backup_contents": {
        "database": $([ -f "$BACKUP_DIR/database.sql" ] && echo "true" || echo "false"),
        "files": $([ -d "$BACKUP_DIR/uploads" ] && echo "true" || echo "false"),
        "configs": $([ -d "$BACKUP_DIR/configs" ] && echo "true" || echo "false"),
        "volumes": $([ -d "$BACKUP_DIR/volumes" ] && echo "true" || echo "false")
    }
}
EOF

    log "Backup metadata created ✅"
}

# Compress backup
compress_backup() {
    log "Compressing backup..."

    cd "$BACKUP_BASE_DIR"
    tar czf "${TIMESTAMP}.tar.gz" "$TIMESTAMP"
    rm -rf "$TIMESTAMP"

    log "Backup compressed: ${BACKUP_BASE_DIR}/${TIMESTAMP}.tar.gz ✅"
}

# Cleanup old backups
cleanup_old_backups() {
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    log "Cleaning up backups older than $retention_days days..."

    find "$BACKUP_BASE_DIR" -name "*.tar.gz" -type f -mtime +$retention_days -delete

    log "Old backups cleaned up ✅"
}

# Verify backup
verify_backup() {
    log "Verifying backup..."

    local backup_file="${BACKUP_BASE_DIR}/${TIMESTAMP}.tar.gz"

    if [ -f "$backup_file" ]; then
        # Test if the archive is valid
        if tar tzf "$backup_file" >/dev/null 2>&1; then
            local size=$(du -h "$backup_file" | cut -f1)
            log "Backup verification successful ✅ (Size: $size)"
        else
            error "Backup archive is corrupted!"
        fi
    else
        error "Backup file not found!"
    fi
}

# Main backup function
main() {
    log "Starting backup of Secure RAG System..."

    create_backup_dir
    backup_database
    backup_files
    backup_configs
    backup_volumes
    create_metadata
    compress_backup
    verify_backup
    cleanup_old_backups

    echo ""
    log "🎉 Backup completed successfully!"
    log "Backup location: ${BACKUP_BASE_DIR}/${TIMESTAMP}.tar.gz"
    echo ""
}

# Check if this is a scheduled backup
if [ "$1" = "--cron" ]; then
    # Redirect output to log file for cron jobs
    exec > >(tee -a "$BACKUP_BASE_DIR/backup.log")
    exec 2>&1
fi

# Run main function
main "$@"