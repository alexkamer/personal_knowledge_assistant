# Personal Knowledge Assistant

A full-featured knowledge management system with AI-powered question answering, note-taking, and semantic search capabilities.

## Features

- **Note Management**: Create, edit, and organize notes with Markdown support
- **AI-Powered Q&A**: Ask questions about your knowledge base using RAG (Retrieval-Augmented Generation)
- **Semantic Search**: Find relevant information across all your notes and documents
- **Document Processing**: Upload and process PDFs, DOCX, TXT, and Markdown files
- **Chat Interface**: Natural conversation with your knowledge base
- **Source Citations**: Every AI answer includes links to source material

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy
- **Databases**:
  - PostgreSQL 18 (structured data and metadata)
  - ChromaDB (vector embeddings for semantic search)
- **AI**: Ollama (local LLMs - Qwen 2.5, Phi-4, Llama 3.2) with RAG
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (local model)
- **100% Local**: No API costs, complete privacy, works offline

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 18
- Ollama (for local LLMs)
- 16GB+ RAM recommended

## Quick Start

### 1. Install PostgreSQL

```bash
brew install postgresql@18
brew services start postgresql@18
echo 'export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Install & Configure Ollama

```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# In a new terminal, pull required models (this will take some time)
ollama pull qwen2.5:14b      # Primary model (~8GB)
ollama pull phi4:14b          # Reasoning model (~8GB)
ollama pull llama3.2:3b       # Fast model (~2GB)
```

### 3. Create Database

```bash
createdb knowledge_assistant
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env - Ollama models are configured by default, adjust if needed

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## Project Structure

```
personal_knowledge_assistant/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── core/         # Database & config
│   │   └── utils/        # Utilities
│   ├── tests/            # Backend tests
│   └── requirements.txt
├── frontend/             # React TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API client
│   │   ├── hooks/        # Custom hooks
│   │   └── types/        # TypeScript types
│   └── package.json
├── docs/                 # Documentation
├── .claude/              # Claude Code configuration
└── README.md
```

## Development

### Running Tests

Backend:
```bash
cd backend
pytest --cov=app tests/
```

Frontend:
```bash
cd frontend
npm test
```

### Code Quality

Backend (auto-format):
```bash
cd backend
black app/ tests/
mypy app/
```

Frontend (auto-format):
```bash
cd frontend
npm run lint
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Configuration

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/knowledge_assistant

# Ollama (Local LLMs)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_PRIMARY_MODEL=qwen2.5:14b
OLLAMA_REASONING_MODEL=phi4:14b
OLLAMA_FAST_MODEL=llama3.2:3b

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_data
CHROMA_COLLECTION_NAME=knowledge_base

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# App Settings
APP_NAME=Personal Knowledge Assistant
ENVIRONMENT=development
DEBUG=True
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Personal Knowledge Assistant
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## Architecture

### RAG Pipeline

1. **Ingestion**: Documents are uploaded and processed
2. **Chunking**: Text is split into 512-token chunks with 50-token overlap
3. **Embedding**: Chunks are embedded using sentence-transformers
4. **Storage**: Embeddings stored in ChromaDB, metadata in PostgreSQL
5. **Retrieval**: User queries are embedded and matched against stored embeddings
6. **Generation**: Top results are sent to Azure OpenAI for answer generation

### Key Components

- **FastAPI Backend**: RESTful API with automatic OpenAPI documentation
- **PostgreSQL**: Stores notes, documents, chunks, and conversation history
- **ChromaDB**: Vector database for semantic search
- **Azure OpenAI**: GPT-4 Turbo for natural language understanding and generation
- **React Frontend**: Modern, responsive UI with TypeScript
- **React Query**: Efficient data fetching and caching

## Troubleshooting

### PostgreSQL Connection Issues

Check if PostgreSQL is running:
```bash
brew services list | grep postgresql
```

Restart if needed:
```bash
brew services restart postgresql@18
```

### Port Already in Use

Backend (port 8000):
```bash
lsof -ti:8000 | xargs kill -9
```

Frontend (port 5173):
```bash
lsof -ti:5173 | xargs kill -9
```

### ChromaDB Issues

Delete and reinitialize:
```bash
rm -rf backend/chroma_data
# Restart backend to reinitialize
```

## Contributing

This is a personal project, but feel free to fork and customize for your own use!

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please check the documentation in `/docs` or open an issue in the repository.
