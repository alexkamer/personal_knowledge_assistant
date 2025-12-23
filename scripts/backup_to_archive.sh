#!/bin/bash

###############################################################################
# Database and ChromaDB Backup Script for External Archive Drive
#
# This script backs up:
# 1. PostgreSQL database (full dump)
# 2. ChromaDB vector database (directory copy)
#
# Backups are stored on external drive with date-based naming.
# Old backups (>28 days) are automatically cleaned up.
#
# Usage: ./scripts/backup_to_archive.sh
###############################################################################

set -e  # Exit on error

# Configuration
ARCHIVE_BASE_PATH="${ARCHIVE_BASE_PATH:-/Volumes/Knowledge-Drive}"
BACKUP_SUBDIR="${BACKUP_SUBDIR:-backups}"
DATABASE_NAME="${DATABASE_NAME:-knowledge_assistant}"
CHROMA_DATA_DIR="${CHROMA_DATA_DIR:-./backend/chroma_data}"
RETENTION_DAYS=28

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Derived paths
BACKUP_DIR="${ARCHIVE_BASE_PATH}/${BACKUP_SUBDIR}"
DATE=$(date +%Y%m%d_%H%M%S)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

###############################################################################
# Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_archive_available() {
    if [ ! -d "$ARCHIVE_BASE_PATH" ]; then
        log_error "Archive drive not mounted at: $ARCHIVE_BASE_PATH"
        log_error "Please mount the external drive and try again."
        exit 1
    fi
    log_info "Archive drive found at: $ARCHIVE_BASE_PATH"
}

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    if [ $? -eq 0 ]; then
        log_info "Backup directory ready: $BACKUP_DIR"
    else
        log_error "Failed to create backup directory"
        exit 1
    fi
}

backup_postgresql() {
    local backup_file="${BACKUP_DIR}/postgres_${DATE}.sql"
    log_info "Backing up PostgreSQL database: $DATABASE_NAME"

    if pg_dump "$DATABASE_NAME" > "$backup_file" 2>/dev/null; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_info "PostgreSQL backup complete: $backup_file ($size)"

        # Compress the backup
        log_info "Compressing PostgreSQL backup..."
        gzip "$backup_file"
        local compressed_size=$(du -h "${backup_file}.gz" | cut -f1)
        log_info "Compression complete: ${backup_file}.gz ($compressed_size)"
        return 0
    else
        log_error "PostgreSQL backup failed"
        return 1
    fi
}

backup_chromadb() {
    local backup_dir="${BACKUP_DIR}/chroma_${DATE}"
    log_info "Backing up ChromaDB from: $CHROMA_DATA_DIR"

    if [ ! -d "$CHROMA_DATA_DIR" ]; then
        log_warn "ChromaDB directory not found: $CHROMA_DATA_DIR"
        log_warn "Skipping ChromaDB backup"
        return 0
    fi

    if cp -r "$CHROMA_DATA_DIR" "$backup_dir" 2>/dev/null; then
        local size=$(du -sh "$backup_dir" | cut -f1)
        log_info "ChromaDB backup complete: $backup_dir ($size)"

        # Create a tar.gz archive
        log_info "Compressing ChromaDB backup..."
        tar -czf "${backup_dir}.tar.gz" -C "$BACKUP_DIR" "chroma_${DATE}" 2>/dev/null
        rm -rf "$backup_dir"
        local compressed_size=$(du -h "${backup_dir}.tar.gz" | cut -f1)
        log_info "Compression complete: ${backup_dir}.tar.gz ($compressed_size)"
        return 0
    else
        log_error "ChromaDB backup failed"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."

    # Clean up PostgreSQL backups
    local pg_deleted=$(find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [ "$pg_deleted" -gt 0 ]; then
        log_info "Deleted $pg_deleted old PostgreSQL backup(s)"
    fi

    # Clean up ChromaDB backups
    local chroma_deleted=$(find "$BACKUP_DIR" -name "chroma_*.tar.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [ "$chroma_deleted" -gt 0 ]; then
        log_info "Deleted $chroma_deleted old ChromaDB backup(s)"
    fi

    if [ "$pg_deleted" -eq 0 ] && [ "$chroma_deleted" -eq 0 ]; then
        log_info "No old backups to clean up"
    fi
}

show_summary() {
    log_info "=========================================="
    log_info "Backup Summary"
    log_info "=========================================="
    log_info "Timestamp: $TIMESTAMP"
    log_info "Backup Location: $BACKUP_DIR"
    log_info ""
    log_info "Recent backups:"
    ls -lh "$BACKUP_DIR" | grep -E "postgres_|chroma_" | tail -5
    log_info "=========================================="
}

###############################################################################
# Main execution
###############################################################################

main() {
    log_info "=========================================="
    log_info "Starting Backup to Archive Drive"
    log_info "=========================================="
    log_info "Timestamp: $TIMESTAMP"

    # Pre-flight checks
    check_archive_available
    create_backup_dir

    # Perform backups
    local pg_success=0
    local chroma_success=0

    if backup_postgresql; then
        pg_success=1
    fi

    if backup_chromadb; then
        chroma_success=1
    fi

    # Cleanup old backups
    cleanup_old_backups

    # Show summary
    show_summary

    # Exit status
    if [ "$pg_success" -eq 1 ] && [ "$chroma_success" -eq 1 ]; then
        log_info "✓ All backups completed successfully"
        exit 0
    elif [ "$pg_success" -eq 1 ] || [ "$chroma_success" -eq 1 ]; then
        log_warn "⚠ Some backups completed with warnings"
        exit 0
    else
        log_error "✗ Backup failed"
        exit 1
    fi
}

# Run main function
main
