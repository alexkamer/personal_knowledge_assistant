# Quick Start Guide

This guide shows you how to start the Personal Knowledge Assistant application.

## Prerequisites

Before starting, ensure you have:
- PostgreSQL 18 running
- Ollama installed with models pulled (llama3.2:3b, qwen2.5:14b, phi4:14b)
- Node.js installed (for frontend)
- Python 3.11+ with uv (for backend)

## Starting the Application

### 1. Start PostgreSQL (if not running)

```bash
brew services start postgresql@18
```

Verify it's running:
```bash
brew services list | grep postgresql
```

### 2. Start Backend (FastAPI)

Open a terminal and run:

```bash
cd backend
source .venv/bin/activate  # or: source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

The backend API will be available at:
- API: http://localhost:8000/api/v1/
- OpenAPI docs: http://localhost:8000/docs

### 3. Start Frontend (React + Vite)

Open a **new terminal** and run:

```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

The frontend will be available at: http://localhost:5173/

### 4. Access the Application

Open your browser and go to:
```
http://localhost:5173/
```

## Stopping the Application

### Stop Backend
In the backend terminal, press: `CTRL+C`

### Stop Frontend
In the frontend terminal, press: `CTRL+C`

### Stop PostgreSQL (optional)
```bash
brew services stop postgresql@18
```

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```bash
lsof -ti:8000 | xargs kill -9
```

**Frontend (port 5173):**
```bash
lsof -ti:5173 | xargs kill -9
```

### PostgreSQL Not Running
```bash
brew services start postgresql@18
```

### Backend Virtual Environment Not Found
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
uv sync  # Install dependencies
```

### Ollama Models Not Loading
First load will be slow (models on external drive). Subsequent loads are faster due to caching.

Check models are available:
```bash
ollama list
```

Should show:
- llama3.2:3b
- qwen2.5:14b
- phi4:14b

### Database Issues
Run migrations:
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## Quick Commands Reference

```bash
# Start everything
Terminal 1: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
Terminal 2: cd frontend && npm run dev

# Run tests
Backend:  cd backend && uv run python -m pytest tests/ -v
Frontend: cd frontend && npm test

# Database migrations
cd backend && alembic upgrade head
```

## Environment Files

Ensure you have these files configured:

**backend/.env**:
```env
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/knowledge_assistant
OLLAMA_HOST=http://localhost:11434
CHROMA_PERSIST_DIRECTORY=./chroma_data
```

**frontend/.env**:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Need Help?

- Backend logs: Check the terminal where uvicorn is running
- Frontend logs: Check browser DevTools console
- API documentation: http://localhost:8000/docs
- Full project docs: See `.claude/CLAUDE.md`
