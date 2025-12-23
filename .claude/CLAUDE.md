# Project Context: Personal Knowledge Assistant

## Project Overview

A personal knowledge assistant webapp that combines note-taking with AI-powered question answering using RAG (Retrieval-Augmented Generation). Users can store notes and documents, then ask natural language questions to get contextual answers with source citations.

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI (Python 3.11+) + SQLAlchemy + Alembic
- **Databases**:
  - PostgreSQL 18 (structured data: notes, documents, chunks, conversations)
  - ChromaDB (vector embeddings for semantic search)
- **AI**: Ollama local LLMs (Qwen 2.5 14B, Phi-4 14B, Llama 3.2 3B)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (local model, 384 dimensions)

## Architecture

### Monorepo Structure
- `/backend` - FastAPI Python application
- `/frontend` - React TypeScript application
- `/docs` - Documentation
- `/shared` - Shared types between frontend/backend
- `/.claude` - Claude Code configuration

### Communication
- REST API: Frontend → Backend via axios
- API base: `http://localhost:8000/api/v1/`
- Backend serves OpenAPI docs at `/docs`

### Data Flow

**Ingestion**:
1. User creates note or uploads document
2. Text extracted and stored in PostgreSQL
3. Text chunked (512 tokens, 50 token overlap)
4. Chunks embedded using sentence-transformers
5. Embeddings stored in ChromaDB
6. Chunk metadata links to PostgreSQL

**Retrieval (RAG)** - with real-time status updates:
1. User asks question via chat interface
2. User can toggle "Include Personal Notes" (default: OFF for reputable sources only)
3. **Status: "Analyzing your question..."** - Query analyzer determines query type, complexity, and retrieval strategy
4. **Status: "Searching knowledge base..."** - Question embedded using sentence-transformers
5. ChromaDB hybrid search (semantic + BM25) retrieves top K chunks (default: 10)
6. Chunks filtered based on `include_notes` parameter:
   - `include_notes=false` (default): Only documents and web sources
   - `include_notes=true`: Includes personal notes in results
7. **Status: "Found X relevant sources..."** - Results re-ranked using cross-encoder
8. Full chunks fetched from PostgreSQL with metadata
9. **Status: "Generating answer..."** - Context assembled with source deduplication
10. Context + query sent to Ollama (local LLM)
11. Response streamed back in real-time with citations
12. Sources displayed with links to original content

## Development Workflow

### Starting the App

1. **Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Testing

Backend (351 tests, 70% coverage):
```bash
cd backend
uv run python -m pytest tests/ -v
```

Frontend (474 tests):
```bash
cd frontend
npm test
```

Run specific test suites:
```bash
# Backend - RAG orchestrator tests (includes include_notes tests)
uv run python -m pytest tests/unit/test_rag_orchestrator.py -v

# Frontend - ChatPage tests (includes loading states and notes toggle tests)
npm test -- ChatPage.test.tsx
```

## Key Design Decisions

### Vector Database: ChromaDB
- Local-first (no external services needed)
- Easy Python integration
- Good enough for <100k documents
- Can migrate to Pinecone/Weaviate later

### Chunking Strategy
- 512 tokens per chunk (~2048 characters)
- 50 token overlap (10%)
- Recursive splitting: paragraphs → sentences → characters
- Preserves semantic boundaries

### Embeddings: Local sentence-transformers
- Free (no API costs)
- Fast (~50ms per embedding)
- 384 dimensions (smaller = faster search)
- Quality sufficient for personal use
- Fallback: Azure OpenAI embeddings if needed

### LLM: Ollama with Multiple Local Models
- **Primary**: Qwen 2.5 14B (best reasoning, handles complex queries)
- **Reasoning**: Phi-4 14B (rivals larger models, optimized for reasoning)
- **Fast**: Llama 3.2 3B (quick responses for simple queries)
- **Benefits**: Zero API costs, complete privacy, offline capable
- **RAM**: Works well on 16GB system
- **Context**: 4k-32k tokens depending on model

## Important Conventions

### Git Commits

- **Never include co-authorship**: Do not add "Co-Authored-By: Claude" or "Generated with Claude Code" in commit messages
- **Clear and concise**: Write descriptive commit messages explaining what changed and why
- **Conventional commits**: Use standard prefixes when appropriate (feat:, fix:, docs:, etc.)

### Backend

- **Async/await**: Use for all I/O operations
- **Type hints**: Required on all functions
- **Pydantic**: Use for request/response validation
- **Service layer**: Business logic lives in `/services`
- **Error handling**: Proper HTTP status codes + descriptive messages
- **Logging**: Use Python logging module, structured logs
- **Testing**: >80% coverage, pytest fixtures for DB

### Frontend

- **Functional components**: No class components
- **TypeScript**: Strict mode enabled, no `any` types
- **React Query**: For all server state management
- **Path aliases**: Use `@/` imports
- **Error boundaries**: Catch and display errors gracefully
- **Loading states**: Show spinners/skeletons during async ops
- **Testing**: >70% coverage, Testing Library patterns

### API Design

- **Versioning**: `/api/v1/` prefix
- **RESTful**: Use standard HTTP methods
- **Pagination**: Use `limit` and `offset` query params
- **Filtering**: Use query params for filters
- **Error responses**: Consistent JSON format with `detail` field
- **Status codes**:
  - 200: Success
  - 201: Created
  - 400: Bad request
  - 404: Not found
  - 500: Server error

### Database

- **Models**: SQLAlchemy ORM, async session
- **Migrations**: Alembic for schema changes
- **UUIDs**: Use for primary keys
- **Timestamps**: `created_at` and `updated_at` on all models
- **Indexes**: Add for frequently queried fields
- **Foreign keys**: Proper relationships and cascades

## Critical Files

### Backend
- `app/main.py` - FastAPI app entry point
- `app/core/database.py` - PostgreSQL setup
- `app/core/vector_db.py` - ChromaDB initialization
- `app/services/rag_service.py` - RAG pipeline orchestration
- `app/services/llm_service.py` - Azure OpenAI integration
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas

### Frontend
- `src/services/api.ts` - Axios API client
- `src/App.tsx` - Main app component
- `src/pages/` - Route components
- `src/components/` - Reusable UI components

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/knowledge_assistant
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
CHROMA_PERSIST_DIRECTORY=./chroma_data
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Document Archive System (External Drive)

The application supports archiving original documents to an external drive while keeping fast embeddings on the internal SSD. This enables building a large document library without storage constraints.

### Architecture

**Two-Tier Storage**:
- **External Drive**: Original documents (PDFs, DOCs, etc.) in date-based folders
- **Internal SSD**: Extracted text, embeddings, and ChromaDB index for fast retrieval

**Benefits**:
- Store hundreds of thousands of documents without internal storage limits
- Preserve originals for re-processing if chunking/embedding strategies improve
- Automatic backups of PostgreSQL + ChromaDB to external drive
- Fast search remains on SSD (no performance penalty)

### Setup Instructions

1. **Mount your external drive** (e.g., `/Volumes/Knowledge-Drive`)

2. **Enable archiving** in `backend/.env`:
   ```bash
   # Document Archive Configuration
   ARCHIVE_ENABLED=true
   ARCHIVE_BASE_PATH=/Volumes/Knowledge-Drive
   ARCHIVE_DOCUMENTS_PATH=documents
   ARCHIVE_BACKUPS_PATH=backups
   ARCHIVE_FALLBACK_TO_LOCAL=true
   ```

3. **Run database migration**:
   ```bash
   cd backend
   alembic upgrade head
   ```

4. **Verify setup**:
   ```bash
   # Check that archive directories are created
   ls -la /Volumes/Knowledge-Drive/
   # Should see: documents/ and backups/
   ```

### Usage

**Document Upload (Automatic)**:
- When `ARCHIVE_ENABLED=true`, all uploaded documents are automatically archived
- Original files saved to: `/Volumes/Knowledge-Drive/documents/YYYY/MM/DD/UUID.ext`
- Extracted text and embeddings remain on internal SSD for fast search
- If external drive unavailable, falls back to local storage (configurable)

**Backup Database & ChromaDB**:
```bash
# Manual backup
./scripts/backup_to_archive.sh

# Schedule with cron (weekly backup at 2 AM Sunday)
0 2 * * 0 /path/to/personal_knowledge_assistant/scripts/backup_to_archive.sh
```

**Re-index Documents from Archive**:
```bash
# Re-index all documents (rebuilds embeddings from archived originals)
cd backend
python -m app.cli.reindex_from_archive --all

# Re-index specific document
python -m app.cli.reindex_from_archive --document-id abc-123-def

# Dry run (see what would be re-indexed without doing it)
python -m app.cli.reindex_from_archive --all --dry-run
```

### Use Cases

1. **Upgrade Embedding Models**: Re-index with better models without re-uploading
2. **Change Chunking Strategy**: Adjust chunk size and rebuild index from originals
3. **Disaster Recovery**: Restore from backups if local database corrupted
4. **Research Archives**: Build domain-specific libraries (academic papers, legal docs, etc.)

### Archive Structure

```
/Volumes/Knowledge-Drive/
├── documents/           # Archived original documents
│   └── 2025/
│       └── 12/
│           └── 19/
│               ├── UUID-1.pdf
│               ├── UUID-2.docx
│               └── UUID-3.txt
└── backups/            # Database backups
    ├── postgres_20251219_140530.sql.gz
    ├── chroma_20251219_140530.tar.gz
    ├── postgres_20251212_140530.sql.gz
    └── chroma_20251212_140530.tar.gz
```

### Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `ARCHIVE_ENABLED` | `false` | Enable/disable document archiving |
| `ARCHIVE_BASE_PATH` | `/Volumes/Knowledge-Drive` | External drive mount point |
| `ARCHIVE_DOCUMENTS_PATH` | `documents` | Subdirectory for documents |
| `ARCHIVE_BACKUPS_PATH` | `backups` | Subdirectory for backups |
| `ARCHIVE_FALLBACK_TO_LOCAL` | `true` | Use local storage if drive unavailable |

### Important Notes

- **Performance**: Archived documents don't slow down search (embeddings stay on SSD)
- **Fallback**: If external drive unmounted, system continues with local storage
- **Backups**: Kept for 28 days (configurable in `backup_to_archive.sh`)
- **Re-indexing**: Uses existing extracted text from PostgreSQL (doesn't re-extract from archived files)

## Common Tasks

### Add a new API endpoint

1. Define Pydantic schema in `app/schemas/`
2. Add endpoint in `app/api/v1/endpoints/`
3. Implement business logic in `app/services/`
4. Write tests in `tests/`
5. Update OpenAPI docs (automatic)

### Add a new React page

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Create API service method in `src/services/`
4. Create React Query hook in `src/hooks/`
5. Write component tests

### Debug issues

- Backend logs: Check console output
- Frontend: Browser DevTools console
- API calls: Check Network tab
- Database: `psql -d knowledge_assistant`
- ChromaDB: Check `./backend/chroma_data/`

## Quality Standards

### Code Quality
- Backend: Black formatting, mypy type checking
- Frontend: ESLint + Prettier
- No warnings in build/lint
- Code reviews before merge (when team grows)

### Testing
- **Backend**: 351 tests with 70% coverage
  - Unit tests for all services (RAG, orchestrator, agents, embeddings, etc.)
  - Integration tests for API endpoints
  - Mock external dependencies (Ollama, ChromaDB in tests)
- **Frontend**: 474 tests
  - Component tests for all UI components
  - Service tests for API client
  - Hook tests for React Query integration
  - Feature tests for loading states and notes toggle
- **Test Quality**: Comprehensive coverage of happy paths, edge cases, and error handling

### Documentation
- Docstrings on all public functions
- Inline comments for complex logic
- Keep README.md updated
- API docs auto-generated

## Known Limitations

- Single user (no authentication yet)
- Local deployment only
- ChromaDB performance limited to ~100k documents
- No real-time collaboration
- No mobile app

## Future Enhancements

- User authentication (JWT)
- Multi-user support
- Real-time collaboration
- Mobile app (React Native)
- Graph view of note connections
- Browser extension for web clipping
- Spaced repetition for learning

## Troubleshooting

### PostgreSQL not running
```bash
brew services list
brew services start postgresql@18
```

### Port already in use
```bash
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

### ChromaDB issues
```bash
rm -rf backend/chroma_data
# Restart backend to reinitialize
```

### Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Node dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Development Principles

1. **Build it right**: Quality-first approach with comprehensive testing
2. **No premature optimization**: Make it work, then make it fast
3. **YAGNI**: Don't build features until they're needed
4. **DRY**: Don't repeat yourself, use abstractions wisely
5. **Fail fast**: Validate early, provide clear error messages
6. **Document decisions**: Keep this file updated with key choices

---

## Available MCP Servers

This project has access to several Model Context Protocol (MCP) servers that extend Claude's capabilities. Use these tools when appropriate for the task at hand.

### 1. **chrome-devtools** (Browser Automation)

**Purpose**: Interact with web pages, test frontend, capture screenshots, debug browser issues.

**When to use**:
- Testing the React frontend UI
- Debugging browser-specific issues
- Taking screenshots of the application
- Inspecting network requests
- Checking console errors
- Interacting with the UI (clicking, filling forms)

**Common operations**:
```
- browser_navigate: Navigate to a URL
- browser_snapshot: Get page content/structure
- browser_take_screenshot: Capture visual state
- browser_click: Interact with elements
- browser_console_messages: Check JS errors
- browser_network_requests: Debug API calls
```

**Example use cases**:
- "Check if the notes page loads correctly"
- "Take a screenshot of the chat interface"
- "Debug why the API call is failing in the browser"
- "Test the form submission flow"

---

### 2. **context7** (Library Documentation)

**Purpose**: Fetch up-to-date documentation for any library or framework.

**When to use**:
- Learning how to use a new library (FastAPI, React Query, ChromaDB, etc.)
- Looking up API documentation
- Finding code examples for a specific feature
- Understanding best practices for a library

**Common operations**:
```
- resolve-library-id: Find the correct library identifier
- get-library-docs: Fetch documentation for specific topics
```

**Supported libraries in this project**:
- FastAPI (API framework)
- React (frontend framework)
- SQLAlchemy (database ORM)
- ChromaDB (vector database)
- React Query / TanStack Query (data fetching)
- Ollama (LLM integration)
- Pydantic (data validation)
- Alembic (migrations)

**Example use cases**:
- "How do I use FastAPI dependency injection?"
- "Show me React Query mutation examples"
- "What's the best way to handle async operations in SQLAlchemy?"
- "How do I configure Alembic for PostgreSQL?"

---

### 3. **reddit-mcp-buddy** (Reddit Integration)

**Purpose**: Browse Reddit for research, gather community feedback, find solutions to technical problems.

**When to use**:
- Researching best practices from developer communities
- Finding solutions to specific errors or issues
- Gathering user feedback on similar projects
- Exploring implementation ideas from r/MachineLearning, r/LocalLLaMA, r/Python, etc.

**Common operations**:
```
- browse_subreddit: Browse posts from specific subreddits
- search_reddit: Search across Reddit
- get_post_details: Get full post with comments
- user_analysis: Analyze user's posting history
```

**Relevant subreddits for this project**:
- r/LocalLLaMA (local LLM discussion)
- r/Python (Python best practices)
- r/FastAPI (FastAPI specific help)
- r/react (React frontend help)
- r/MachineLearning (RAG and ML topics)
- r/selfhosted (self-hosted app inspiration)

**Example use cases**:
- "Search r/LocalLLaMA for Ollama best practices"
- "Find Reddit discussions about RAG implementation challenges"
- "Look up common FastAPI + PostgreSQL issues"
- "Research React component patterns in r/react"

---

### 4. **playwright** (Advanced Browser Automation)

**Purpose**: End-to-end testing, complex browser interactions, automated testing workflows.

**When to use**:
- Writing end-to-end tests
- Complex multi-step user flows
- Testing across different browser states
- Automated UI testing
- Form submission testing
- File upload testing

**Common operations**:
```
- browser_navigate: Go to URLs
- browser_click: Click elements
- browser_type: Type into fields
- browser_fill_form: Fill multiple form fields
- browser_take_screenshot: Visual regression testing
- browser_evaluate: Run JavaScript in page
```

**Example use cases**:
- "Test the complete note creation flow"
- "Verify the chat interface works end-to-end"
- "Test file upload with drag-and-drop"
- "Create automated test for search functionality"

---

## MCP Usage Guidelines

### When NOT to use MCP servers:
- Don't use browser tools for simple file reading/editing
- Don't fetch documentation if you already know the answer
- Don't search Reddit for every minor question
- Use built-in tools (Read, Edit, Grep) for codebase work

### When TO use MCP servers:
- You need current information not in your training data
- Testing requires browser interaction
- User asks for community opinions or solutions
- Documentation lookup saves implementation time
- Complex browser automation is needed

### Best Practices:
1. **Be specific**: Narrow searches to relevant subreddits or documentation sections
2. **Use context**: Mention project context when searching
3. **Verify**: Cross-reference information from multiple sources
4. **Document**: If you learn something useful, add it to project docs
5. **Test locally**: Always test browser interactions on localhost first

---

## Example MCP Workflows

### Research FastAPI + Ollama Integration
```
1. Use context7 to get FastAPI async documentation
2. Search r/LocalLLaMA for Ollama Python client best practices
3. Implement based on findings
4. Test with chrome-devtools
```

### Debug Frontend Issue
```
1. Use chrome-devtools to navigate to the page
2. Take screenshot to see visual state
3. Check console messages for errors
4. Inspect network requests
5. Fix issue and verify
```

### Learn New Library Feature
```
1. Use context7 to get official docs
2. Search Reddit for real-world usage examples
3. Read code examples from docs
4. Implement in project
```

## Recent Features

### AI-Powered Autocomplete (2025-12-18)
- **What**: GitHub Copilot-style inline autocomplete for notes editor with ghost text suggestions
- **Why**: Accelerates note-taking with contextually relevant AI completions
- **How**:
  - Powered by local Ollama LLM (Llama 3.2 3B) for privacy and speed
  - Inline ghost text overlay appears after 500ms typing pause
  - Tab to accept, Escape to dismiss suggestion
  - Smart triggering: no suggestions immediately after sentence punctuation
  - Context-aware: uses previous 1-2 sentences for better completions
  - Sentence-aware capitalization after `.!?`
- **Performance**: ~300ms response time, 5-second timeout with graceful degradation
- **Files**:
  - Backend: `app/api/v1/endpoints/autocomplete.py`, `app/schemas/autocomplete.py`
  - Frontend: `src/components/notes/AIAutocompletePlugin.tsx`, `src/services/autocompleteService.ts`
  - Integration: `src/components/notes/LexicalOutlinerEditor.tsx:286`

### Real-Time RAG Pipeline Feedback (2025-12-16)
- **What**: Live status updates during query processing
- **Why**: Improves user experience by showing what's happening behind the scenes
- **How**:
  - Backend sends `onStatus` callbacks through SSE streaming
  - Frontend displays status messages with animated loading dots
  - Status updates: "Analyzing..." → "Searching..." → "Found X sources..." → "Generating..."
- **Files**:
  - Backend: `app/api/v1/endpoints/chat.py:372-373` (stream_chat_response)
  - Frontend: `src/pages/ChatPage.tsx:78-80, 164-172`
- **Tests**: `frontend/src/pages/ChatPage.test.tsx:94-221` (3 tests)

### Configurable Source Filtering (Notes Toggle) (2025-12-16)
- **What**: Users can choose to include or exclude personal notes from search results
- **Why**: Separates verified/reputable sources (documents, web) from personal thoughts (notes)
- **Default**: Notes excluded (reputable sources only)
- **How**:
  - Frontend toggle button controls `include_notes` parameter
  - Backend `exclude_notes` parameter filters chunks by source type
  - Filters applied at vector search level (ChromaDB + PostgreSQL)
- **Files**:
  - Backend: `app/services/rag_orchestrator.py:31, 83`, `app/services/rag_service.py:93-103`
  - Frontend: `src/pages/ChatPage.tsx:60-62, 201-209`
- **Tests**:
  - Frontend: `frontend/src/pages/ChatPage.test.tsx:223-348` (5 tests)
  - Backend: `backend/tests/unit/test_rag_orchestrator.py:492-633` (3 tests)

## Project Status

- [x] Phase 1: Foundation - Infrastructure setup
- [x] Phase 2: Note Management - CRUD operations
- [x] Phase 3: Document Processing - Upload and embedding pipeline
- [x] Phase 4: RAG & Chat - AI-powered Q&A with real-time feedback
- [ ] Phase 5: Polish - UI/UX improvements and optimization

Last updated: 2025-12-16
