#!/bin/bash
# Backup the knowledge library database

BACKUP_DIR="$(dirname "$0")/../backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/knowledge_library_${TIMESTAMP}.sql"

echo "Backing up knowledge library..."
pg_dump knowledge_assistant > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Backup created: $BACKUP_FILE"
    echo "  Size: $(du -h "$BACKUP_FILE" | cut -f1)"

    # Keep only the 3 most recent backups
    cd "$BACKUP_DIR"
    ls -t knowledge_library_*.sql | tail -n +4 | xargs rm -f 2>/dev/null
    echo "  Kept 3 most recent backups"
else
    echo "✗ Backup failed"
    exit 1
fi
