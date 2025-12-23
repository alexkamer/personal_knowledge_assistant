# Document Archive System

The Personal Knowledge Assistant supports archiving original documents to an external drive while maintaining fast search performance on your internal SSD.

## Overview

**Problem**: Internal SSD storage is limited, but you want to build a comprehensive knowledge base with thousands of documents.

**Solution**: Two-tier storage architecture
- **External Drive** (1TB): Store original documents (PDFs, DOCs, etc.)
- **Internal SSD**: Keep embeddings and ChromaDB index for fast search

**Result**: Unlimited document storage without sacrificing search performance.

## Quick Start

### 1. Initial Setup

```bash
# 1. Mount your external drive
# Make sure it's mounted at /Volumes/Knowledge-Drive (or your preferred path)

# 2. Enable archiving in backend/.env
cat >> backend/.env << 'EOF'

# Document Archive Configuration
ARCHIVE_ENABLED=true
ARCHIVE_BASE_PATH=/Volumes/Knowledge-Drive
ARCHIVE_DOCUMENTS_PATH=documents
ARCHIVE_BACKUPS_PATH=backups
ARCHIVE_FALLBACK_TO_LOCAL=true
EOF

# 3. Run database migration
cd backend
alembic upgrade head

# 4. Verify setup
ls -la /Volumes/Knowledge-Drive/
# Should see: documents/ and backups/
```

### 2. Upload Documents

Documents are automatically archived when you upload them:

```bash
# Upload via API
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@research_paper.pdf"

# Or use the web interface
# Files are automatically saved to both local and archive storage
```

### 3. Backups

```bash
# Manual backup (PostgreSQL + ChromaDB)
./scripts/backup_to_archive.sh

# Automated backups (add to cron)
# Run weekly at 2 AM on Sundays
0 2 * * 0 /path/to/personal_knowledge_assistant/scripts/backup_to_archive.sh
```

### 4. Re-indexing

```bash
# Re-index all documents (useful when upgrading embedding models)
cd backend
python -m app.cli.reindex_from_archive --all

# Re-index specific document
python -m app.cli.reindex_from_archive --document-id abc-123-def

# Dry run (preview without executing)
python -m app.cli.reindex_from_archive --all --dry-run
```

## Architecture Details

### Data Flow: Document Upload

```
1. User uploads PDF via web interface
2. Backend saves to local ./uploads/ directory
3. Text extracted and stored in PostgreSQL
4. If ARCHIVE_ENABLED=true:
   a. Copy original to /Volumes/Knowledge-Drive/documents/YYYY/MM/DD/UUID.pdf
   b. Record archive_path in PostgreSQL
   c. Set storage_location = "archive"
5. Text chunked and embedded
6. Embeddings stored in ChromaDB (on internal SSD)
7. User can search immediately (fast, uses SSD)
```

### Data Flow: Search Query

```
1. User asks question
2. Query embedded using local model (fast, ~50ms)
3. ChromaDB searches embeddings (on SSD, fast)
4. Relevant chunks retrieved from PostgreSQL
5. LLM generates answer with citations
6. Original documents available via archive_path if needed
```

**Key insight**: Search never touches the external drive, only accesses it when user wants to view the original document.

## Directory Structure

```
/Volumes/Knowledge-Drive/
├── documents/                    # Archived documents
│   ├── 2025/
│   │   ├── 12/
│   │   │   ├── 19/
│   │   │   │   ├── a1b2c3d4.pdf
│   │   │   │   ├── e5f6g7h8.docx
│   │   │   │   └── i9j0k1l2.txt
│   │   │   └── 20/
│   │   │       └── ...
│   │   └── ...
│   └── ...
└── backups/                      # Database backups
    ├── postgres_20251219_140530.sql.gz
    ├── chroma_20251219_140530.tar.gz
    ├── postgres_20251212_140530.sql.gz
    └── chroma_20251212_140530.tar.gz
```

**Date-based organization**:
- Easy to navigate and manage
- Simplifies cleanup (delete entire year/month)
- Natural chronological ordering

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARCHIVE_ENABLED` | `false` | Master switch for archiving |
| `ARCHIVE_BASE_PATH` | `/Volumes/Knowledge-Drive` | External drive mount point |
| `ARCHIVE_DOCUMENTS_PATH` | `documents` | Subdirectory for documents |
| `ARCHIVE_BACKUPS_PATH` | `backups` | Subdirectory for backups |
| `ARCHIVE_FALLBACK_TO_LOCAL` | `true` | Continue with local storage if drive unavailable |

### Database Schema

New fields in `documents` table:

```sql
ALTER TABLE documents ADD COLUMN archive_path VARCHAR(500);
ALTER TABLE documents ADD COLUMN storage_location VARCHAR(20) DEFAULT 'local';
CREATE INDEX ix_documents_storage_location ON documents(storage_location);
```

## Use Cases

### 1. Building a Research Library

Store thousands of academic papers without worrying about storage:

```bash
# Enable archiving
ARCHIVE_ENABLED=true

# Upload papers (via API or web interface)
# Papers automatically archived to external drive

# Search remains fast (embeddings on SSD)
# Can still cite and reference original PDFs
```

### 2. Upgrading Embedding Models

Re-index with better models without re-uploading documents:

```bash
# Update embedding model in backend/.env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Re-index all documents from archive
python -m app.cli.reindex_from_archive --all

# New embeddings generated from archived originals
```

### 3. Disaster Recovery

Restore from backups if something goes wrong:

```bash
# Restore PostgreSQL
gunzip /Volumes/Knowledge-Drive/backups/postgres_20251219_140530.sql.gz
psql knowledge_assistant < postgres_20251219_140530.sql

# Restore ChromaDB
tar -xzf /Volumes/Knowledge-Drive/backups/chroma_20251219_140530.tar.gz
cp -r chroma_20251219_140530 backend/chroma_data
```

### 4. Changing Chunking Strategy

Experiment with different chunking without re-uploading:

```bash
# Update chunking settings in backend/.env
CHUNK_SIZE=1024
CHUNK_OVERLAP=100

# Re-index to apply new chunking strategy
python -m app.cli.reindex_from_archive --all
```

## Performance Considerations

### What's Fast ✅
- **Search queries**: Embeddings on SSD, no external drive access
- **Document upload**: Async copy to archive doesn't block response
- **Backup**: Runs in background, doesn't affect app performance

### What's Slower ⚠️
- **Re-indexing**: Reads from PostgreSQL (not external drive), moderate speed
- **Original document retrieval**: Requires external drive access (rare operation)
- **Backup script**: Can take 5-10 minutes for large databases (run off-peak)

### Optimization Tips

1. **Keep ChromaDB on internal SSD** - Never move to external drive
2. **Use fallback mode** - Set `ARCHIVE_FALLBACK_TO_LOCAL=true` for reliability
3. **Schedule backups wisely** - Run during low-usage periods
4. **Monitor drive health** - External drives can fail, verify backups work

## Troubleshooting

### Archive drive not detected

```bash
# Check if drive is mounted
ls -la /Volumes/

# If not mounted, connect the drive
# macOS will auto-mount to /Volumes/[DRIVE_NAME]

# Update ARCHIVE_BASE_PATH if needed
ARCHIVE_BASE_PATH=/Volumes/YourDriveName
```

### Upload fails with archive error

```bash
# Check fallback setting
grep ARCHIVE_FALLBACK_TO_LOCAL backend/.env

# If fallback=true, uploads continue with local storage
# If fallback=false, uploads will fail if drive unavailable

# Recommended: Use fallback=true for reliability
```

### Backup script fails

```bash
# Run with verbose output
bash -x scripts/backup_to_archive.sh

# Common issues:
# 1. PostgreSQL not running: brew services start postgresql@18
# 2. Drive not mounted: Check /Volumes/
# 3. Permissions: Ensure drive is writable

# Test PostgreSQL connection
psql knowledge_assistant -c "SELECT COUNT(*) FROM documents;"
```

### Re-indexing takes too long

```bash
# Re-index in batches (process 100 documents at a time)
# This requires custom implementation, or:

# Re-index specific high-priority documents only
python -m app.cli.reindex_from_archive --document-id doc-1
python -m app.cli.reindex_from_archive --document-id doc-2

# Or run during off-peak hours
0 3 * * 6 cd /path/to/backend && python -m app.cli.reindex_from_archive --all
```

## API Reference

### ArchiveService

```python
from app.services.archive_service import ArchiveService

# Check if archive is available
available = ArchiveService.is_archive_available()

# Save file to archive
archive_path, storage_location = await ArchiveService.save_to_archive(
    source_path="./uploads/temp.pdf",
    filename="document.pdf",
    file_type="pdf",
)

# Retrieve from archive
content = await ArchiveService.retrieve_from_archive(archive_path)

# Delete from archive
deleted = await ArchiveService.delete_from_archive(archive_path)

# Get archive statistics
stats = ArchiveService.get_archive_stats()
# Returns: {
#   "available": True,
#   "total_size": 1234567890,
#   "document_count": 1523,
#   "base_path": "/Volumes/Knowledge-Drive"
# }
```

## FAQ

**Q: What happens if I disconnect the external drive?**
A: If `ARCHIVE_FALLBACK_TO_LOCAL=true`, uploads continue using local storage. Search still works normally since embeddings are on the internal SSD.

**Q: Can I move ChromaDB to the external drive?**
A: Not recommended. ChromaDB needs fast random access for efficient search. Keep it on your internal SSD.

**Q: How much space do I save?**
A: Original documents (PDFs, DOCs) move to external drive. Only extracted text (much smaller) and embeddings (~384 floats per chunk) stay on internal SSD. Typical savings: 95%+ of document file sizes.

**Q: Can I use this with cloud storage (S3, Google Drive)?**
A: The current implementation uses local filesystem paths. Cloud storage would require adapting `ArchiveService` to use cloud provider SDKs.

**Q: What if my external drive fails?**
A: Keep multiple backups! The backup script compresses well (~10:1 ratio). You could store backups on multiple drives or cloud storage for redundancy.

**Q: Does this work on Windows/Linux?**
A: Yes, but you'll need to update `ARCHIVE_BASE_PATH` to match your OS:
- Windows: `D:\\Knowledge-Drive`
- Linux: `/mnt/knowledge-drive`

## Best Practices

1. **Enable fallback mode**: `ARCHIVE_FALLBACK_TO_LOCAL=true` for reliability
2. **Schedule regular backups**: Weekly is good, daily if actively used
3. **Monitor archive size**: Check available space periodically
4. **Test restores**: Verify backups work before you need them
5. **Document your setup**: Note drive names, paths, backup schedules
6. **Keep embeddings on SSD**: Never move ChromaDB to external drive

## Next Steps

- [ ] Set up automated backups with cron
- [ ] Test disaster recovery procedure
- [ ] Monitor archive statistics in admin panel (future feature)
- [ ] Add archive browser in web UI (future feature)
- [ ] Implement cloud storage adapter (future enhancement)

---

**Last Updated**: 2025-12-19
**Version**: 1.0
