# Changelog

All notable changes to the Personal Knowledge Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-12-16

### Added

#### Real-Time RAG Pipeline Feedback
- **Live status updates** during query processing to improve transparency and user experience
- Status messages show pipeline stages:
  - "Analyzing your question..." - Query analysis phase
  - "Searching knowledge base..." - Vector search phase
  - "Found X relevant sources..." - Retrieval complete
  - "Generating answer..." - LLM generation phase
- Animated loading dots for visual feedback
- Server-Sent Events (SSE) streaming for real-time status delivery
- **Files Modified**:
  - Backend: `app/api/v1/endpoints/chat.py` (stream_chat_response function)
  - Frontend: `src/pages/ChatPage.tsx` (status state management and display)
  - Frontend: `src/services/chatService.ts` (onStatus callback support)
- **Tests**: 3 comprehensive frontend tests in `ChatPage.test.tsx`

#### Configurable Source Filtering (Notes Toggle)
- **Toggle button** to control whether personal notes are included in search results
- Two modes:
  - **Reputable Sources Only** (default): Searches only documents and web sources
  - **Including Personal Notes**: Includes personal notes in search results
- Provides clear source distinction for users who want verified information vs. all knowledge
- **Implementation**:
  - Frontend toggle controls `include_notes` boolean parameter
  - Backend `exclude_notes` parameter filters chunks by source type
  - Filtering applied at vector database query level
  - Default behavior: notes excluded for reputable sources only
- **Files Modified**:
  - Backend: `app/services/rag_orchestrator.py` (exclude_notes parameter)
  - Backend: `app/services/rag_service.py` (chunk filtering logic)
  - Frontend: `src/pages/ChatPage.tsx` (toggle UI and state management)
- **Tests**:
  - 5 frontend tests in `ChatPage.test.tsx` (toggle behavior and parameter passing)
  - 3 backend tests in `test_rag_orchestrator.py` (default behavior, explicit true/false)

#### Testing Infrastructure
- **Frontend**: Now at 474 passing tests (up from previous count)
  - Added 8 new tests for loading states and notes toggle features
  - Tests cover happy paths, edge cases, and combined feature interactions
- **Backend**: Now at 351 passing tests with 70% coverage (exceeds 39% requirement)
  - Added 3 new tests for include_notes/exclude_notes parameter
  - Tests verify default behavior and explicit parameter handling

### Changed
- Updated RAG pipeline documentation to reflect new status update stages
- Improved test coverage documentation in README.md and CLAUDE.md
- Enhanced CLAUDE.md with detailed "Recent Features" section including file references

### Documentation
- **README.md**: Updated features list, testing commands, and RAG pipeline architecture
- **CLAUDE.md**:
  - Added "Recent Features" section with implementation details
  - Updated data flow to include status updates and source filtering
  - Updated testing section with current test counts
  - Updated project status to mark Phase 4 as complete
- **CHANGELOG.md**: Created this file to track all changes going forward

## [0.1.0] - 2025-12-15

### Initial Release

#### Core Features
- **Note Management**: Full CRUD operations for Markdown notes
- **Document Processing**: Upload and process PDFs, DOCX, TXT, and Markdown files
- **AI-Powered Q&A**: RAG-based question answering using local LLMs
- **Semantic Search**: Hybrid search combining vector similarity and BM25 keyword matching
- **Chat Interface**: Conversational UI with message history and source citations
- **Source Citations**: Every answer links back to source documents/notes

#### Technical Infrastructure
- **Backend**: FastAPI with async/await, PostgreSQL, ChromaDB
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **AI Models**: Ollama local LLMs (Qwen 2.5 14B, Phi-4 14B, Llama 3.2 3B)
- **Embeddings**: Local sentence-transformers (all-MiniLM-L6-v2, 384 dimensions)
- **100% Local**: No API costs, complete privacy, offline capable

#### Architecture
- **RAG Pipeline**: Document ingestion, chunking (512 tokens), embedding, vector search, re-ranking
- **Query Analyzer**: Intelligent query classification and retrieval strategy selection
- **Agent System**: Specialized agents for different query types (factual, exploratory, etc.)
- **Hybrid Search**: Combines semantic (vector) and keyword (BM25) search with Reciprocal Rank Fusion
- **Re-ranking**: Cross-encoder model for improved result relevance

#### Testing
- Comprehensive test suites for both frontend and backend
- Unit tests, integration tests, and component tests
- Mock external dependencies for reliable testing
- High test coverage across critical paths

---

## Version History Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

## Upcoming Features

See [Future Enhancements](/.claude/CLAUDE.md#future-enhancements) in CLAUDE.md for planned features.
