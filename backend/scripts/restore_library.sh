#!/bin/bash
# Restore the knowledge library from backup

BACKUP_DIR="$(dirname "$0")/../backups"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/knowledge_library_*.sql 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring knowledge library from: $BACKUP_FILE"
echo "This will replace all current data. Continue? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # Drop and recreate database
    dropdb knowledge_assistant 2>/dev/null
    createdb knowledge_assistant

    # Restore from backup
    psql knowledge_assistant < "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo "✓ Library restored successfully"
    else
        echo "✗ Restore failed"
        exit 1
    fi
else
    echo "Restore cancelled"
    exit 0
fi
