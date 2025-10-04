#!/bin/bash

# Recovery Script for Secure RAG System
# Restores system from backup archives

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Show usage
show_usage() {
    echo "Usage: $0 <backup_file> [options]"
    echo ""
    echo "Options:"
    echo "  --database-only    Restore only the database"
    echo "  --files-only       Restore only uploaded files"
    echo "  --configs-only     Restore only configuration files"
    echo "  --volumes-only     Restore only Docker volumes"
    echo "  --force            Skip confirmation prompts"
    echo "  --help             Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 ./backups/20231225_120000.tar.gz"
    echo "  $0 ./backups/20231225_120000.tar.gz --database-only"
    echo ""
}

# Parse command line arguments
parse_arguments() {
    BACKUP_FILE=""
    DATABASE_ONLY=false
    FILES_ONLY=false
    CONFIGS_ONLY=false
    VOLUMES_ONLY=false
    FORCE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --database-only)
                DATABASE_ONLY=true
                shift
                ;;
            --files-only)
                FILES_ONLY=true
                shift
                ;;
            --configs-only)
                CONFIGS_ONLY=true
                shift
                ;;
            --volumes-only)
                VOLUMES_ONLY=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                ;;
            *)
                if [ -z "$BACKUP_FILE" ]; then
                    BACKUP_FILE="$1"
                else
                    error "Multiple backup files specified"
                fi
                shift
                ;;
        esac
    done

    if [ -z "$BACKUP_FILE" ]; then
        show_usage
        exit 1
    fi
}

# Validate backup file
validate_backup() {
    log "Validating backup file: $BACKUP_FILE"

    if [ ! -f "$BACKUP_FILE" ]; then
        error "Backup file not found: $BACKUP_FILE"
    fi

    # Test if the archive is valid
    if ! tar tzf "$BACKUP_FILE" >/dev/null 2>&1; then
        error "Invalid or corrupted backup file: $BACKUP_FILE"
    fi

    log "Backup file validation successful ✅"
}

# Extract backup
extract_backup() {
    TEMP_DIR=$(mktemp -d)
    log "Extracting backup to temporary directory: $TEMP_DIR"

    tar xzf "$BACKUP_FILE" -C "$TEMP_DIR"

    # Find the backup directory (should be the only directory in temp)
    BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d ! -path "$TEMP_DIR" | head -1)

    if [ -z "$BACKUP_DIR" ]; then
        error "Could not find backup directory in archive"
    fi

    log "Backup extracted successfully ✅"
}

# Show backup information
show_backup_info() {
    log "Backup Information:"

    if [ -f "$BACKUP_DIR/backup_info.json" ]; then
        echo "----------------------------------------"
        echo "Backup Date: $(jq -r '.backup_date' "$BACKUP_DIR/backup_info.json")"
        echo "Hostname: $(jq -r '.system_info.hostname' "$BACKUP_DIR/backup_info.json")"
        echo "Contents:"
        echo "  Database: $(jq -r '.backup_contents.database' "$BACKUP_DIR/backup_info.json")"
        echo "  Files: $(jq -r '.backup_contents.files' "$BACKUP_DIR/backup_info.json")"
        echo "  Configs: $(jq -r '.backup_contents.configs' "$BACKUP_DIR/backup_info.json")"
        echo "  Volumes: $(jq -r '.backup_contents.volumes' "$BACKUP_DIR/backup_info.json")"
        echo "----------------------------------------"
    else
        warn "Backup metadata not found"
    fi
}

# Confirm restoration
confirm_restore() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    echo ""
    warn "⚠️  WARNING: This will overwrite existing data!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Restoration cancelled by user"
        cleanup_temp
        exit 0
    fi
}

# Stop services
stop_services() {
    log "Stopping services..."

    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml down
        log "Services stopped ✅"
    else
        warn "docker-compose.prod.yml not found, skipping service stop"
    fi
}

# Restore database
restore_database() {
    if [ "$DATABASE_ONLY" = false ] && [ "$FILES_ONLY" = true ] && [ "$CONFIGS_ONLY" = true ] && [ "$VOLUMES_ONLY" = true ]; then
        return 0
    fi

    log "Restoring database..."

    if [ -f "$BACKUP_DIR/database.sql" ]; then
        # Start only PostgreSQL for restoration
        docker-compose -f docker-compose.prod.yml up -d postgres

        # Wait for PostgreSQL to be ready
        echo -n "Waiting for PostgreSQL..."
        while ! docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U "${POSTGRES_USER:-rag_user}" >/dev/null 2>&1; do
            echo -n "."
            sleep 2
        done
        echo " ✅"

        # Restore database
        docker-compose -f docker-compose.prod.yml exec -T postgres psql \
            -U "${POSTGRES_USER:-rag_user}" \
            -d "${POSTGRES_DB:-rag_system}" \
            < "$BACKUP_DIR/database.sql"

        log "Database restoration completed ✅"
    else
        warn "Database backup not found, skipping database restoration"
    fi
}

# Restore files
restore_files() {
    if [ "$FILES_ONLY" = false ] && [ "$DATABASE_ONLY" = true ] && [ "$CONFIGS_ONLY" = true ] && [ "$VOLUMES_ONLY" = true ]; then
        return 0
    fi

    log "Restoring uploaded files..."

    if [ -d "$BACKUP_DIR/uploads" ]; then
        # Create uploads directory if it doesn't exist
        mkdir -p "./data/uploads"

        # Restore files
        cp -r "$BACKUP_DIR/uploads/"* "./data/uploads/"

        log "Files restoration completed ✅"
    else
        warn "Files backup not found, skipping files restoration"
    fi
}

# Restore configurations
restore_configs() {
    if [ "$CONFIGS_ONLY" = false ] && [ "$DATABASE_ONLY" = true ] && [ "$FILES_ONLY" = true ] && [ "$VOLUMES_ONLY" = true ]; then
        return 0
    fi

    log "Restoring configuration files..."

    if [ -d "$BACKUP_DIR/configs" ]; then
        # Restore .env file
        if [ -f "$BACKUP_DIR/configs/.env" ]; then
            cp "$BACKUP_DIR/configs/.env" "./"
            log ".env file restored"
        fi

        # Restore docker-compose.prod.yml
        if [ -f "$BACKUP_DIR/configs/docker-compose.prod.yml" ]; then
            cp "$BACKUP_DIR/configs/docker-compose.prod.yml" "./"
            log "Docker compose file restored"
        fi

        # Restore nginx configuration
        if [ -d "$BACKUP_DIR/configs/nginx" ]; then
            cp -r "$BACKUP_DIR/configs/nginx" "./"
            log "Nginx configuration restored"
        fi

        # Restore monitoring configuration
        if [ -d "$BACKUP_DIR/configs/monitoring" ]; then
            cp -r "$BACKUP_DIR/configs/monitoring" "./"
            log "Monitoring configuration restored"
        fi

        log "Configuration restoration completed ✅"
    else
        warn "Configuration backup not found, skipping configuration restoration"
    fi
}

# Restore Docker volumes
restore_volumes() {
    if [ "$VOLUMES_ONLY" = false ] && [ "$DATABASE_ONLY" = true ] && [ "$FILES_ONLY" = true ] && [ "$CONFIGS_ONLY" = true ]; then
        return 0
    fi

    log "Restoring Docker volumes..."

    if [ -d "$BACKUP_DIR/volumes" ]; then
        # Restore PostgreSQL volume
        if [ -f "$BACKUP_DIR/volumes/postgres_data.tar.gz" ]; then
            docker volume create rag_postgres_data
            docker run --rm \
                -v rag_postgres_data:/target \
                -v "$(pwd)/$BACKUP_DIR/volumes":/backup \
                alpine sh -c "cd /target && tar xzf /backup/postgres_data.tar.gz"
            log "PostgreSQL volume restored"
        fi

        # Restore Redis volume
        if [ -f "$BACKUP_DIR/volumes/redis_data.tar.gz" ]; then
            docker volume create rag_redis_data
            docker run --rm \
                -v rag_redis_data:/target \
                -v "$(pwd)/$BACKUP_DIR/volumes":/backup \
                alpine sh -c "cd /target && tar xzf /backup/redis_data.tar.gz"
            log "Redis volume restored"
        fi

        # Restore Ollama volume
        if [ -f "$BACKUP_DIR/volumes/ollama_data.tar.gz" ]; then
            docker volume create rag_ollama_data
            docker run --rm \
                -v rag_ollama_data:/target \
                -v "$(pwd)/$BACKUP_DIR/volumes":/backup \
                alpine sh -c "cd /target && tar xzf /backup/ollama_data.tar.gz"
            log "Ollama volume restored"
        fi

        log "Volume restoration completed ✅"
    else
        warn "Volume backup not found, skipping volume restoration"
    fi
}

# Start services
start_services() {
    log "Starting services..."

    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml up -d
        log "Services started ✅"
    else
        warn "docker-compose.prod.yml not found, cannot start services"
    fi
}

# Cleanup temporary files
cleanup_temp() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
        log "Temporary files cleaned up ✅"
    fi
}

# Verify restoration
verify_restoration() {
    log "Verifying restoration..."

    # Wait for services to be ready
    sleep 10

    # Check if backend is responding
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        log "Backend health check passed ✅"
    else
        warn "Backend health check failed"
    fi

    # Check if frontend is accessible
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        log "Frontend accessibility check passed ✅"
    else
        warn "Frontend accessibility check failed"
    fi

    log "Verification completed"
}

# Main restoration function
main() {
    log "Starting restoration of Secure RAG System..."

    validate_backup
    extract_backup
    show_backup_info
    confirm_restore
    stop_services
    restore_database
    restore_files
    restore_configs
    restore_volumes
    start_services
    verify_restoration
    cleanup_temp

    echo ""
    log "🎉 Restoration completed successfully!"
    echo ""
    info "Access your restored Secure RAG System:"
    info "• Frontend: http://localhost:3000"
    info "• Backend API: http://localhost:8000"
    info "• Monitoring: http://localhost:3001"
    echo ""
}

# Parse arguments and run
parse_arguments "$@"

# Set cleanup trap
trap cleanup_temp EXIT

# Run main function
main