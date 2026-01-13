# Backend Scripts

Utility scripts for maintenance, testing, and development tasks.

## Active Scripts

### Production/Maintenance Scripts

#### `cleanup_orphaned_chunks.py`
**Purpose**: Database maintenance - removes orphaned chunks from ChromaDB that no longer have corresponding documents in PostgreSQL.

**When to use**:
- After bulk document deletions
- Database cleanup after errors during document processing
- When chunks count doesn't match expected values

**Usage**:
```bash
cd backend
python scripts/cleanup_orphaned_chunks.py
```

**Dependencies**: Requires running PostgreSQL and ChromaDB instances.

---

#### `backup_library.sh`
**Purpose**: Creates a backup of the document library and database.

**When to use**:
- Before major migrations or schema changes
- Periodic backups of knowledge base
- Before bulk document processing operations

**Usage**:
```bash
cd backend/scripts
./backup_library.sh
```

---

#### `restore_library.sh`
**Purpose**: Restores document library from backup.

**When to use**:
- Recovery after data corruption
- Rollback after failed migration
- Restoring previous state of knowledge base

**Usage**:
```bash
cd backend/scripts
./restore_library.sh <backup_file>
```

---

### Testing/Development Scripts

#### `test_agent_mode.py`
**Purpose**: Quick test for agentic RAG mode - verifies agent can make tool calls and search the knowledge base.

**When to use**:
- Testing agent mode functionality after changes
- Debugging agent tool execution
- Verifying knowledge search tool integration

**Usage**:
```bash
cd backend
python scripts/test_agent_mode.py
```

**Requirements**: Running backend with Ollama models available.

---

#### `test_prompt_models.py`
**Purpose**: Benchmark different LLM models (Llama 3.2 3B, Qwen 2.5 14B, Phi-4 14B) for prompt refinement and question generation.

**When to use**:
- Evaluating model performance for specific tasks
- Comparing speed vs quality trade-offs
- Selecting optimal model for image generation prompts

**Usage**:
```bash
cd backend
python scripts/test_prompt_models.py
```

**Output**: Speed metrics and quality comparison for each model.

---

#### `stress_test_ollama.py`
**Purpose**: Stress test for Ollama models - runs concurrent requests to test external hard drive stability and model performance under load.

**When to use**:
- Testing system stability before production use
- Benchmarking concurrent request handling
- Verifying external storage (if models stored on external drive)

**Usage**:
```bash
cd backend
python scripts/stress_test_ollama.py
```

**Configuration**: Edit script to adjust:
- `CONCURRENT_REQUESTS`: Number of parallel requests
- `ITERATIONS`: Number of test iterations
- `MODELS_TO_TEST`: Which Ollama models to test

---

## Archive

Historical scripts kept for reference but not actively maintained.

### `archive/knowledge_library_expansion/`
Scripts used for one-time batch import of Wikipedia articles and academic sources to build the initial knowledge library (~200+ documents).

**Scripts**:
- `build_comprehensive_library.py`: Wikipedia topic imports
- `expand_knowledge_library.py`: Academic source expansion
- `expand_to_200plus.py`: Batch expansion to 200+ docs
- `expand_with_reputable_sources.py`: Stanford Encyclopedia imports
- `build_library_batch.py`: Batch processing utility

**Note**: These were used during initial library setup. For ongoing document management, use the web UI or API endpoints.

---

### `archive/one_time_migrations/`
Database migration scripts for schema changes and backfilling data.

**Scripts**:
- `clear_and_reprocess.py`: Clear chunks and reprocess with semantic metadata
- `reprocess_documents_with_metadata.py`: Backfill metadata on existing docs
- `categorize_existing_documents.py`: Backfill categories using AI categorization
- `reformat_documents.py`: Reformat document structure

**Note**: These were run once during feature development. Use Alembic for future schema migrations.

---

## Creating New Scripts

When adding new scripts:

1. **Add executable permission** if it's a shell script:
   ```bash
   chmod +x backend/scripts/your_script.sh
   ```

2. **Add docstring** at the top explaining purpose and usage

3. **Update this README** with script description and usage instructions

4. **Use consistent imports** for backend modules:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))

   from app.core.database import AsyncSessionLocal
   # ... other imports
   ```

5. **Add error handling** and logging for production scripts

6. **Test thoroughly** before committing

---

## Best Practices

- **Idempotency**: Scripts should be safe to run multiple times
- **Confirmation prompts**: Add prompts for destructive operations
- **Dry-run mode**: Consider adding `--dry-run` flag for testing
- **Logging**: Use Python's `logging` module for output
- **Error handling**: Gracefully handle database connection errors
- **Documentation**: Keep this README updated

---

## Questions?

For issues or questions about these scripts:
1. Check script docstrings for detailed documentation
2. Review git history for context: `git log -- backend/scripts/<script_name>`
3. Open an issue in the project repository
