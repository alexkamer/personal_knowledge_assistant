# Personal Knowledge Assistant

A full-featured knowledge management system with AI-powered question answering, note-taking, and semantic search capabilities.

## Features

- **Note Management**: Create, edit, and organize notes with Markdown support
- **AI-Powered Q&A**: Ask questions about your knowledge base using RAG (Retrieval-Augmented Generation)
- **Real-Time Pipeline Feedback**: See live status updates as the RAG pipeline processes your question
  - "Analyzing your question..."
  - "Searching knowledge base..."
  - "Found X relevant sources..."
  - "Generating answer..."
- **Configurable Source Filtering**: Toggle between:
  - **Reputable Sources Only** (default): Search only documents and web sources
  - **Including Personal Notes**: Include your personal notes in search results
- **Semantic Search**: Find relevant information across all your notes and documents
- **Document Processing**: Upload and process PDFs, DOCX, TXT, and Markdown files
- **YouTube Learning**: Process YouTube videos with AI-powered features:
  - Automatic transcript fetching with timestamps
  - AI-generated video summaries with key points and topics
  - Interactive transcript with clickable timestamps
  - Search within transcripts
  - Markdown export functionality
- **Chat Interface**: Natural conversation with your knowledge base
- **Source Citations**: Every AI answer includes links to source material
- **5 Unique Learning Innovations**: Cutting-edge features that don't exist in other knowledge tools (see below)
- **Comprehensive Testing**: 474 frontend tests + 351 backend tests (70% coverage)

## 🚀 5 Unique Learning Innovations

These innovations transform passive knowledge consumption into active, deep learning. No other knowledge management tool offers these features.

### 1. 🔍 Contradiction Detective

**What**: Automatically detects logical contradictions between your sources.

**Why it's innovative**: Most tools just retrieve information. This analyzes **consistency** across your knowledge base, identifying when sources disagree.

**How it works**:
- Uses semantic search to find related content
- AI analyzes pairs of sources for logical conflicts
- Categorizes contradictions by type: factual, methodological, conceptual, temporal
- Displays severity levels (high/medium/low) and confidence scores

**Where to find it**: Appears automatically in the Context Panel when viewing notes or documents with contradictory information.

**Example**: If one source says "Python is dynamically typed" and another says "Python requires type declarations", the Contradiction Detective flags this with an explanation.

---

### 2. 🎓 Socratic Learning Mode

**What**: Teaches through guided questions instead of providing direct answers.

**Why it's innovative**: Other AI assistants just answer questions. This **teaches you to think** by asking strategic questions that guide discovery.

**How it works**:
- Toggle Socratic Mode in the chat interface
- AI responds with probing questions instead of answers
- 4-level progressive hint system if you get stuck (subtle → direct)
- Develops critical thinking and problem-solving skills

**Where to find it**: Purple toggle button in chat interface labeled "🎓 Socratic Mode".

**Example**:
- **You ask**: "What is the capital of France?"
- **Socratic Mode**: "What country are we talking about? What do you know about its geography and major cities?"
- **Direct Mode**: "The capital of France is Paris."

---

### 3. 💡 Learning Gaps Detector

**What**: Analyzes your questions to identify missing foundational knowledge.

**Why it's innovative**: Other tools assume you have the background knowledge. This **identifies prerequisites** you need to learn first.

**How it works**:
- Click "Detect Learning Gaps" after asking a question
- AI analyzes your question for assumed knowledge
- Generates personalized learning path with:
  - Topics you need to learn (prioritized by importance: critical/important/helpful)
  - Clear explanations of why each gap matters
  - Learning resources and estimated time for each
  - Sequenced learning path from fundamentals to advanced

**Where to find it**: Orange/yellow gradient button in chat interface (appears when conversation has messages).

**Example**: You ask about "How does backpropagation work?" → Detector identifies gaps in linear algebra, calculus derivatives, and neural network basics, then creates a learning path starting with prerequisites.

---

### 4. 🧠 Cognitive Metabolization

**What**: Interactive comprehension quizzes that ensure you truly understand content (not just read it).

**Why it's innovative**: Most apps let you passively consume content. This **forces active engagement** and tests real understanding.

**How it works**:
- Click "Quiz Me" after a conversation
- AI generates 3-5 comprehension questions covering:
  - **Recall**: Remember key facts
  - **Comprehension**: Explain concepts in your own words
  - **Application**: Apply knowledge to new situations
  - **Synthesis**: Connect ideas and identify gaps
- AI evaluates your answers and provides feedback
- Must score 80%+ to mark content as "metabolized"

**Where to find it**: Purple/blue gradient "Quiz Me" button in chat interface.

**Example**: After learning about React hooks, quiz asks: "How would you explain useState to someone unfamiliar with React?" Then evaluates your answer for accuracy and understanding depth.

---

### 5. ⏱️ Knowledge Evolution Timeline

**What**: Tracks how your understanding of topics evolves over time, showing "thought diffs" like git diffs but for concepts.

**Why it's innovative**: No other tool tracks **learning progress** or shows **how understanding changes**. This creates awareness of intellectual growth.

**How it works**:
- Click "Capture Snapshot" to save your current understanding
- Snapshots include: key concepts understood, misconceptions, confidence level, questions asked
- Click "View Evolution" to see timeline of all learning sessions
- See "thought diffs" showing:
  - ✅ New concepts learned (green)
  - ❌ Misconceptions corrected (red strikethrough)
  - 📈 Confidence changes over time
  - 💡 Learning velocity and insights

**Where to find it**:
- Green/teal "Capture Snapshot" button (saves current understanding)
- Indigo/purple "View Evolution" button (opens timeline)

**Example**: Your first snapshot on "machine learning" shows 40% confidence with misconception about neural networks. Second snapshot two weeks later shows 75% confidence, misconception corrected, 5 new concepts learned.

---

## 🎯 Why These Innovations Matter

**Traditional knowledge tools** (Notion, Obsidian, Roam):
- ❌ Let you passively store and retrieve information
- ❌ Don't check for consistency or contradictions
- ❌ Don't identify knowledge gaps
- ❌ Don't test comprehension
- ❌ Don't track learning progress

**This Personal Knowledge Assistant**:
- ✅ **Active Learning**: Forces engagement through quizzes and Socratic questioning
- ✅ **Quality Control**: Detects contradictions in your knowledge base
- ✅ **Gap Analysis**: Identifies missing prerequisites
- ✅ **Progress Tracking**: Shows how understanding evolves
- ✅ **Metacognition**: Makes you aware of what you know and don't know

**Result**: Transform from information hoarder to actual learner with measurable progress.

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

Run specific test files:
```bash
# Frontend - specific test file
npm test -- ChatPage.test.tsx

# Backend - specific test file
uv run python -m pytest tests/unit/test_rag_orchestrator.py -v
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

# YouTube Proxy Configuration (optional)
# Use rotating residential proxies to bypass YouTube rate limiting
WEBSHARE_PROXY_USERNAME=
WEBSHARE_PROXY_PASSWORD=

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

**Ingestion**:
1. Documents are uploaded and processed
2. Text is split into 512-token chunks with 50-token overlap
3. Chunks are embedded using sentence-transformers
4. Embeddings stored in ChromaDB, metadata in PostgreSQL

**Retrieval** (with real-time status updates):
1. **"Analyzing your question..."** - Query is analyzed for type and complexity
2. **"Searching knowledge base..."** - Query is embedded and semantic search is performed
3. **"Found X relevant sources..."** - Top results are retrieved and re-ranked
4. **"Generating answer..."** - Context is assembled from chunks
5. Sources are filtered based on user preference (documents only or including notes)
6. Top results are sent to Ollama (local LLM) for answer generation
7. Response is streamed back with source citations

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

### YouTube Rate Limiting

If you encounter "YouTube is blocking requests from your IP" errors:

**Short-term solution**: Wait 15-30 minutes for the rate limit to clear.

**Long-term solution**: Use rotating residential proxies via Webshare:

1. Sign up at https://www.webshare.io/ (free tier available)
2. Get your proxy credentials
3. Add them to `backend/.env`:
   ```env
   WEBSHARE_PROXY_USERNAME=your_username
   WEBSHARE_PROXY_PASSWORD=your_password
   ```
4. Restart the backend server

The system will automatically use proxies when credentials are configured.

## Contributing

This is a personal project, but feel free to fork and customize for your own use!

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please check the documentation in `/docs` or open an issue in the repository.
