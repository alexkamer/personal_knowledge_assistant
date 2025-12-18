# Web Researcher Agent - Implementation Specification

## Overview

An autonomous background agent that researches topics across the web, automatically adds findings to your knowledge base, and keeps information updated. This transforms your knowledge assistant from a passive repository into an active research tool.

---

## User Experience

### Primary Workflow

```
1. User clicks "🔍 Start Research" button on Chat/Research page
2. Modal opens: "What would you like me to research?"
3. User enters topic: "Latest developments in transformer optimization 2024"
4. Optional settings:
   - Max sources: 5-20 (default: 10)
   - Depth: Quick / Thorough / Deep (default: Thorough)
   - Source types: Academic, News, Blogs, Reddit, All (default: All)
5. Click "Start Research" → Task begins in background
6. User sees progress panel:
   ┌─────────────────────────────────────────┐
   │ 🔍 Research in Progress                 │
   │ "Transformer optimization 2024"         │
   │                                         │
   │ ⚡ Searching web... (15 results found)  │
   │ 📄 Scraping sources... (3/15 complete)  │
   │ 🧠 Analyzing content... (1/3 analyzed)  │
   │                                         │
   │ Estimated: 8 minutes remaining          │
   │ [Cancel Research]                       │
   └─────────────────────────────────────────┘
7. Notification when complete: "Research complete! Added 8 new sources"
8. Results panel opens showing summary
```

### Research Results Panel

```
┌──────────────────────────────────────────────┐
│ ✅ Research Complete                         │
│ "Transformer optimization 2024"              │
│                                              │
│ 📊 Summary                                   │
│ • 15 web pages searched                      │
│ • 8 sources successfully added               │
│ • 3 sources failed (paywalls, rate limits)   │
│ • 4 sources skipped (low credibility)        │
│                                              │
│ 🎯 Key Findings                              │
│ • Flash Attention 2 reduces memory by 40%    │
│ • Ring Attention enables 1M+ context         │
│ • Mixture of Experts (MoE) cuts costs 8x     │
│                                              │
│ 📚 Sources Added (8)                         │
│ ┌────────────────────────────────────────┐  │
│ │ ⭐⭐⭐⭐⭐ Flash Attention 2 Paper      │  │
│ │ arXiv • 2024-03-15 • High credibility  │  │
│ │ [View] [Edit] [Delete]                 │  │
│ └────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────┐  │
│ │ ⭐⭐⭐⭐ Ring Attention Implementation   │  │
│ │ GitHub • 2024-06-20 • Medium cred.     │  │
│ │ [View] [Edit] [Delete]                 │  │
│ └────────────────────────────────────────┘  │
│ ... (6 more)                                 │
│                                              │
│ ⚠️ Contradictions Found (2)                  │
│ • Flash Attention speedup: 2x vs 4x claims   │
│ • Context window limits: conflicting numbers │
│                                              │
│ 🔮 Suggested Follow-ups                      │
│ • "How to implement Flash Attention in PyT…" │
│ • "What are the tradeoffs of MoE architect…" │
│ • "Compare Ring Attention vs vanilla Trans…" │
│                                              │
│ [Ask Question About Research] [New Research] │
└──────────────────────────────────────────────┘
```

---

## Architecture

### Tech Stack Decisions

Based on research recommendations:

1. **Web Search**: DuckDuckGo (existing) + optional Brave Search API upgrade
2. **Web Scraping**:
   - Playwright (for JavaScript-heavy sites)
   - httpx + BeautifulSoup (for static HTML)
   - Trafilatura (content extraction)
3. **Background Tasks**: Redis Queue (RQ) - simpler than Celery for MVP
4. **Content Processing**: Existing embedding + chunking pipeline

### System Components

```
┌─────────────┐
│   Frontend  │ (React)
└──────┬──────┘
       │ POST /api/v1/research/start
       ↓
┌─────────────┐
│   FastAPI   │
│  Endpoint   │
└──────┬──────┘
       │ enqueue task
       ↓
┌─────────────┐
│ Redis Queue │ (RQ)
└──────┬──────┘
       │ task: deep_research
       ↓
┌─────────────────────────────────────────┐
│    Research Worker (Background)         │
│  ┌────────────────────────────────────┐ │
│  │ 1. Web Search (DuckDuckGo/Brave)   │ │
│  │ 2. Credibility Filtering           │ │
│  │ 3. Content Scraping (Playwright)   │ │
│  │ 4. Content Extraction (Trafilatura)│ │
│  │ 5. Deduplication                   │ │
│  │ 6. Chunking (existing service)     │ │
│  │ 7. Embedding (existing service)    │ │
│  │ 8. Vector DB Storage (ChromaDB)    │ │
│  │ 9. PostgreSQL Storage              │ │
│  │ 10. Contradiction Detection        │ │
│  │ 11. Generate Summary               │ │
│  └────────────────────────────────────┘ │
└─────────────┬───────────────────────────┘
              │ task complete
              ↓
┌─────────────────────┐
│   PostgreSQL DB     │
│  - research_tasks   │
│  - documents (new)  │
│  - chunks (new)     │
└─────────────────────┘
```

---

## Database Schema

### New Tables

#### `research_tasks`
```sql
CREATE TABLE research_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'queued', 'running', 'completed', 'failed', 'cancelled'

    -- Settings
    max_sources INTEGER DEFAULT 10,
    depth VARCHAR(20) DEFAULT 'thorough',  -- 'quick', 'thorough', 'deep'
    source_types TEXT[],  -- ['academic', 'news', 'blogs', 'reddit']

    -- Progress tracking
    sources_found INTEGER DEFAULT 0,
    sources_scraped INTEGER DEFAULT 0,
    sources_added INTEGER DEFAULT 0,
    sources_failed INTEGER DEFAULT 0,
    sources_skipped INTEGER DEFAULT 0,

    current_step VARCHAR(100),  -- "Searching web...", "Scraping page 5/10..."
    progress_percentage INTEGER DEFAULT 0,
    estimated_time_remaining INTEGER,  -- seconds

    -- Results
    summary TEXT,  -- Key findings summary
    key_findings JSONB,  -- Structured findings
    contradictions_found INTEGER DEFAULT 0,
    suggested_followups TEXT[],

    -- Metadata
    job_id VARCHAR(255),  -- RQ job ID for monitoring
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_research_tasks_status ON research_tasks(status);
CREATE INDEX idx_research_tasks_created_at ON research_tasks(created_at DESC);
```

#### `research_sources`
```sql
CREATE TABLE research_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    research_task_id UUID REFERENCES research_tasks(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,  -- Created document

    -- Source info
    url TEXT NOT NULL,
    title TEXT,
    domain VARCHAR(255),
    source_type VARCHAR(50),  -- 'academic', 'news', 'blog', 'reddit', 'github'

    -- Credibility
    credibility_score FLOAT,  -- 0.0 - 1.0
    credibility_reasons TEXT[],  -- ['Academic domain', 'Recent publication']

    -- Status
    status VARCHAR(20) NOT NULL,  -- 'scraped', 'failed', 'skipped'
    failure_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_research_sources_task ON research_sources(research_task_id);
CREATE INDEX idx_research_sources_status ON research_sources(status);
```

#### Extend `documents` table
```sql
-- Add new columns to existing documents table
ALTER TABLE documents ADD COLUMN source_type VARCHAR(50) DEFAULT 'upload';
-- Values: 'upload', 'web_research', 'youtube', 'manual_entry'

ALTER TABLE documents ADD COLUMN source_url TEXT;
ALTER TABLE documents ADD COLUMN author VARCHAR(255);
ALTER TABLE documents ADD COLUMN published_date DATE;
ALTER TABLE documents ADD COLUMN credibility_score FLOAT;
ALTER TABLE documents ADD COLUMN research_task_id UUID REFERENCES research_tasks(id) ON DELETE SET NULL;
```

---

## Backend Implementation

### File Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── research.py               # NEW: Research API endpoints
│   ├── models/
│   │   ├── research_task.py          # NEW: ResearchTask model
│   │   └── research_source.py        # NEW: ResearchSource model
│   ├── schemas/
│   │   └── research.py               # NEW: Pydantic schemas
│   ├── services/
│   │   ├── web_search_service.py     # EXISTS: Enhance with Brave API
│   │   ├── web_scraper_service.py    # NEW: Playwright + BS4 scraping
│   │   ├── credibility_service.py    # NEW: Source credibility scoring
│   │   ├── research_orchestrator.py  # NEW: Orchestrates research workflow
│   │   └── research_task_service.py  # NEW: Task CRUD operations
│   └── workers/
│       └── research_worker.py        # NEW: RQ background worker
└── requirements.txt                  # Add: rq, playwright, trafilatura
```

### API Endpoints

#### `POST /api/v1/research/start`
Start a new research task.

**Request:**
```json
{
  "query": "Latest transformer optimization techniques 2024",
  "max_sources": 10,
  "depth": "thorough",
  "source_types": ["academic", "blogs", "github"]
}
```

**Response:**
```json
{
  "task_id": "uuid-here",
  "status": "queued",
  "message": "Research task started. You'll be notified when complete."
}
```

#### `GET /api/v1/research/tasks`
List all research tasks (with pagination).

**Response:**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "query": "Transformer optimization",
      "status": "completed",
      "sources_added": 8,
      "created_at": "2024-12-17T10:30:00Z",
      "completed_at": "2024-12-17T10:38:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/v1/research/tasks/{task_id}`
Get detailed task status and progress.

**Response:**
```json
{
  "id": "uuid",
  "query": "Transformer optimization",
  "status": "running",
  "progress": {
    "current_step": "Scraping sources (5/10)",
    "percentage": 50,
    "estimated_time_remaining": 240
  },
  "sources_found": 15,
  "sources_scraped": 5,
  "sources_added": 3,
  "sources_failed": 1,
  "sources_skipped": 1
}
```

#### `GET /api/v1/research/tasks/{task_id}/results`
Get research results summary.

**Response:**
```json
{
  "task_id": "uuid",
  "query": "Transformer optimization",
  "summary": "Research found 8 high-quality sources...",
  "key_findings": [
    "Flash Attention 2 reduces memory by 40%",
    "Ring Attention enables 1M+ context windows"
  ],
  "sources": [
    {
      "id": "uuid",
      "title": "Flash Attention 2 Paper",
      "url": "https://arxiv.org/abs/...",
      "domain": "arxiv.org",
      "credibility_score": 0.95,
      "source_type": "academic",
      "document_id": "uuid"
    }
  ],
  "contradictions_found": 2,
  "suggested_followups": [
    "How to implement Flash Attention in PyTorch?",
    "What are MoE architecture tradeoffs?"
  ]
}
```

#### `POST /api/v1/research/tasks/{task_id}/cancel`
Cancel a running research task.

**Response:**
```json
{
  "message": "Research task cancelled"
}
```

#### `DELETE /api/v1/research/tasks/{task_id}`
Delete a research task and optionally its sources.

**Request:**
```json
{
  "delete_sources": false  // If true, also deletes created documents
}
```

---

## Services Implementation

### 1. `research_orchestrator.py` (Core Logic)

```python
"""
Orchestrates the entire research workflow.
"""
from typing import List, Dict
import logging

from app.services.web_search_service import WebSearchService
from app.services.web_scraper_service import WebScraperService
from app.services.credibility_service import CredibilityService
from app.services.document_service import DocumentService
from app.services.chunk_processing_service import ChunkProcessingService
from app.services.embedding_service import EmbeddingService
from app.services.contradiction_service import ContradictionService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates autonomous web research."""

    async def deep_research(
        self,
        task_id: str,
        query: str,
        max_sources: int = 10,
        depth: str = "thorough",
        source_types: List[str] = None
    ) -> Dict:
        """
        Perform deep research on a query.

        Steps:
        1. Web search
        2. Filter by credibility
        3. Scrape content
        4. Extract and clean
        5. Chunk and embed
        6. Store in DB
        7. Detect contradictions
        8. Generate summary

        Args:
            task_id: Research task UUID
            query: Research question
            max_sources: Max sources to process
            depth: 'quick' (5 sources), 'thorough' (10), 'deep' (20)
            source_types: Filter by type (academic, news, blogs, etc.)

        Returns:
            Research results summary
        """
        # Update task status
        await self._update_task(task_id, status="running", current_step="Searching web...")

        # 1. Web Search
        search_results = await self._web_search(query, max_sources * 2)  # Get 2x for filtering
        await self._update_task(task_id, sources_found=len(search_results))

        # 2. Credibility Filtering
        await self._update_task(task_id, current_step="Filtering sources...")
        credible_sources = await self._filter_by_credibility(search_results, source_types)
        credible_sources = credible_sources[:max_sources]

        # 3. Scrape and Process
        documents_created = []
        failed_count = 0
        skipped_count = 0

        for i, source in enumerate(credible_sources):
            await self._update_task(
                task_id,
                current_step=f"Scraping source {i+1}/{len(credible_sources)}...",
                progress_percentage=int((i / len(credible_sources)) * 70)  # 0-70%
            )

            try:
                # Scrape
                content = await self._scrape_source(source["url"])

                if not content:
                    skipped_count += 1
                    continue

                # Create document
                doc = await self._create_document(
                    task_id=task_id,
                    url=source["url"],
                    title=source["title"],
                    content=content,
                    credibility_score=source["credibility_score"],
                    source_type=source["source_type"]
                )

                # Chunk and embed
                await self._process_document(doc)

                documents_created.append(doc)
                await self._update_task(task_id, sources_added=len(documents_created))

            except Exception as e:
                logger.error(f"Failed to process source {source['url']}: {e}")
                failed_count += 1
                await self._update_task(task_id, sources_failed=failed_count)

        # 4. Detect contradictions
        await self._update_task(
            task_id,
            current_step="Analyzing for contradictions...",
            progress_percentage=80
        )
        contradictions = await self._detect_contradictions(documents_created)

        # 5. Generate summary
        await self._update_task(
            task_id,
            current_step="Generating summary...",
            progress_percentage=90
        )
        summary = await self._generate_summary(query, documents_created)
        key_findings = await self._extract_key_findings(documents_created)
        followups = await self._generate_followup_questions(query, documents_created)

        # 6. Complete task
        await self._update_task(
            task_id,
            status="completed",
            current_step="Complete",
            progress_percentage=100,
            summary=summary,
            key_findings=key_findings,
            suggested_followups=followups,
            contradictions_found=len(contradictions),
            sources_skipped=skipped_count
        )

        return {
            "task_id": task_id,
            "sources_added": len(documents_created),
            "sources_failed": failed_count,
            "sources_skipped": skipped_count,
            "contradictions_found": len(contradictions),
            "summary": summary
        }
```

### 2. `web_scraper_service.py` (NEW)

```python
"""
Web scraping service using Playwright and BeautifulSoup.
"""
from typing import Optional
import logging
import asyncio

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx
import trafilatura

logger = logging.getLogger(__name__)


class WebScraperService:
    """Scrapes web content using Playwright or httpx."""

    async def scrape(self, url: str) -> Optional[str]:
        """
        Scrape content from a URL.

        Tries httpx first (fast for static pages),
        falls back to Playwright for JS-heavy sites.

        Args:
            url: URL to scrape

        Returns:
            Clean text content or None if failed
        """
        try:
            # Try fast static scrape first
            content = await self._scrape_static(url)
            if content:
                return content

            # Fallback to Playwright for JS sites
            return await self._scrape_dynamic(url)

        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return None

    async def _scrape_static(self, url: str) -> Optional[str]:
        """Scrape static HTML with httpx + trafilatura."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()

                # Extract main content with trafilatura
                content = trafilatura.extract(response.text)
                return content

        except Exception as e:
            logger.debug(f"Static scrape failed: {e}")
            return None

    async def _scrape_dynamic(self, url: str) -> Optional[str]:
        """Scrape JavaScript-heavy sites with Playwright."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until="networkidle", timeout=30000)
                content = await page.content()

                await browser.close()

                # Extract main content
                return trafilatura.extract(content)

        except Exception as e:
            logger.error(f"Dynamic scrape failed: {e}")
            return None
```

### 3. `credibility_service.py` (NEW)

```python
"""
Source credibility scoring service.
"""
from typing import Dict, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class CredibilityService:
    """Scores source credibility."""

    # High-trust domains
    ACADEMIC_DOMAINS = {
        ".edu", "arxiv.org", "scholar.google.com", "jstor.org",
        "ieee.org", "acm.org", "nature.com", "science.org"
    }

    NEWS_ORGS = {
        "nytimes.com", "reuters.com", "apnews.com", "bbc.com",
        "theguardian.com", "economist.com", "wsj.com"
    }

    TECH_BLOGS = {
        "github.com", "stackoverflow.com", "medium.com",
        "dev.to", "hackernoon.com", "towardsdatascience.com"
    }

    def score_source(self, url: str, title: str, snippet: str) -> Dict:
        """
        Score source credibility (0.0 - 1.0).

        Returns:
            {
                "score": 0.85,
                "reasons": ["Academic domain", "HTTPS"],
                "source_type": "academic"
            }
        """
        score = 0.5  # Neutral baseline
        reasons = []
        source_type = "general"

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Domain checks
        if any(d in domain for d in self.ACADEMIC_DOMAINS):
            score += 0.4
            reasons.append("Academic domain")
            source_type = "academic"
        elif domain in self.NEWS_ORGS:
            score += 0.3
            reasons.append("Reputable news organization")
            source_type = "news"
        elif domain in self.TECH_BLOGS:
            score += 0.2
            reasons.append("Known tech community site")
            source_type = "blog"

        # HTTPS
        if parsed.scheme == "https":
            score += 0.1
            reasons.append("Secure connection")

        # Content signals (basic)
        if len(snippet) > 100:
            score += 0.05
            reasons.append("Substantial content")

        # Clamp score
        score = min(max(score, 0.0), 1.0)

        return {
            "score": score,
            "reasons": reasons,
            "source_type": source_type
        }
```

---

## Frontend Implementation

### File Structure

```
frontend/
├── src/
│   ├── pages/
│   │   └── ResearchPage.tsx           # NEW: Main research interface
│   ├── components/research/
│   │   ├── ResearchForm.tsx           # NEW: Start research modal
│   │   ├── ResearchProgressPanel.tsx  # NEW: Live progress display
│   │   ├── ResearchResultsPanel.tsx   # NEW: Results view
│   │   └── ResearchTasksList.tsx      # NEW: Past research tasks
│   ├── services/
│   │   └── researchService.ts         # NEW: API client
│   └── hooks/
│       └── useResearch.ts             # NEW: React Query hooks
```

### Key Components

#### `ResearchPage.tsx`
- Primary interface for starting and viewing research
- Two tabs: "New Research" and "Research History"
- Real-time progress updates via polling or SSE

#### `ResearchProgressPanel.tsx`
- Live progress bar
- Current step display
- Estimated time remaining
- Cancel button

#### `ResearchResultsPanel.tsx`
- Summary of findings
- List of sources added (with credibility stars)
- Contradictions detected
- Suggested follow-up questions
- Actions: View source, edit, delete

---

## Implementation Phases

### Phase 1: MVP (1 week)
**Goal**: Basic autonomous research working end-to-end

1. **Backend** (3-4 days):
   - Database migrations (research_tasks, research_sources)
   - Research API endpoints
   - Web scraper service (httpx + trafilatura only)
   - Basic credibility scoring (domain-based)
   - Research orchestrator (simplified flow)
   - RQ worker setup

2. **Frontend** (2-3 days):
   - Research page with form
   - Progress display (polling every 5 seconds)
   - Results panel (basic)

3. **Testing** (1 day):
   - End-to-end test of research flow
   - Handle failures gracefully

**MVP Features**:
- ✅ Start research task
- ✅ Background processing
- ✅ Scrape 5-10 sources
- ✅ Add documents to knowledge base
- ✅ View results summary
- ✅ Basic credibility filtering

**MVP Limitations**:
- No Playwright (static pages only)
- No contradiction detection
- No follow-up suggestions
- Simple progress updates

---

### Phase 2: Enhanced (1 week)
**Goal**: Production-quality with advanced features

1. **Backend Enhancements** (3 days):
   - Add Playwright for JS-heavy sites
   - Improve credibility scoring (ML-based)
   - Integrate contradiction detection
   - LLM-generated summaries
   - Follow-up question generation

2. **Frontend Polish** (2 days):
   - SSE for real-time updates (no polling)
   - Research history with search/filter
   - Better results visualization
   - Edit research sources before saving

3. **Testing & Optimization** (2 days):
   - Comprehensive tests
   - Performance optimization
   - Error handling

**Phase 2 Features**:
- ✅ Playwright support
- ✅ Real-time SSE updates
- ✅ Contradiction detection
- ✅ AI-generated summaries
- ✅ Follow-up suggestions
- ✅ Research history management

---

### Phase 3: Advanced (Future)
**Optional enhancements for later**

- Scheduled research (daily/weekly updates)
- Multi-language support
- Custom scraping rules per domain
- Citation graph visualization
- Research templates
- Collaborative research (multi-user)
- Browser extension integration
- Mobile app support

---

## Technical Considerations

### Rate Limiting
- Respect robots.txt
- Add delays between requests (1-2 seconds)
- Implement exponential backoff for failures
- Track rate limits per domain

### Error Handling
- Graceful degradation (some sources fail = OK)
- Retry logic with backoff
- Store failure reasons for debugging
- Notify user of partial results

### Performance
- Process sources in parallel (asyncio.gather)
- Limit concurrent scrapers (semaphore)
- Cache scraped content temporarily
- Optimize embedding batch size

### Security
- Validate URLs before scraping
- Sanitize scraped content
- Rate limit research tasks per user (when auth added)
- Scan for malicious content

### Privacy
- User can delete research tasks + sources
- Option to not save sources (research-only mode)
- Clear data retention policy

---

## Testing Strategy

### Backend Tests

1. **Unit Tests**:
   - `test_web_scraper_service.py` - Mock Playwright/httpx
   - `test_credibility_service.py` - Domain scoring logic
   - `test_research_orchestrator.py` - Workflow steps

2. **Integration Tests**:
   - `test_research_api.py` - Full API workflow
   - `test_research_worker.py` - RQ task execution

3. **E2E Tests**:
   - Start research → Wait for completion → Verify documents created

### Frontend Tests

1. **Component Tests**:
   - ResearchForm submission
   - Progress panel updates
   - Results display

2. **Integration Tests**:
   - Full research flow from UI

---

## Success Metrics

### MVP Success
- ✅ Research task completes in <10 minutes for 10 sources
- ✅ 70%+ of sources successfully scraped
- ✅ Documents correctly added to RAG pipeline
- ✅ User can query new sources immediately

### Phase 2 Success
- ✅ Real-time progress updates feel instant
- ✅ Contradiction detection finds obvious conflicts
- ✅ AI summaries are accurate and useful
- ✅ 90%+ uptime for background workers

---

## Known Limitations & Future Work

### Current Limitations
- No PDF download/parsing (web pages only)
- No image/video content extraction
- Limited to English content
- Single-user (no collaboration)

### Future Enhancements
- Academic paper PDF parsing
- Scheduled research updates
- Research templates
- Citation network visualization
- Export research as report

---

## Dependencies to Add

### Backend
```
# requirements.txt additions
rq==1.15.1              # Redis Queue for background tasks
playwright==1.40.0      # Browser automation
trafilatura==1.7.0      # Content extraction
httpx==0.25.2           # Async HTTP client
beautifulsoup4==4.12.2  # HTML parsing
```

### Frontend
```json
// package.json additions
{
  "react-query": "^5.0.0",  // Already exists
  "lucide-react": "^0.300.0" // Already exists
}
```

---

## Migration Script

```sql
-- Alembic migration: add research tables

-- 1. Create research_tasks table
CREATE TABLE research_tasks (
    -- [See schema above]
);

-- 2. Create research_sources table
CREATE TABLE research_sources (
    -- [See schema above]
);

-- 3. Extend documents table
ALTER TABLE documents
ADD COLUMN source_type VARCHAR(50) DEFAULT 'upload',
ADD COLUMN source_url TEXT,
ADD COLUMN author VARCHAR(255),
ADD COLUMN published_date DATE,
ADD COLUMN credibility_score FLOAT,
ADD COLUMN research_task_id UUID REFERENCES research_tasks(id) ON DELETE SET NULL;

-- 4. Create indexes
CREATE INDEX idx_documents_research_task ON documents(research_task_id);
```

---

## Example Usage Flow

```python
# 1. User starts research
POST /api/v1/research/start
{
  "query": "What are the latest transformer optimizations?",
  "max_sources": 10,
  "depth": "thorough"
}

# Response: { "task_id": "uuid-123" }

# 2. Frontend polls progress
GET /api/v1/research/tasks/uuid-123
# Response: { "status": "running", "progress": 45, ... }

# 3. Task completes
# Response: { "status": "completed", ... }

# 4. View results
GET /api/v1/research/tasks/uuid-123/results
# Response: { "sources": [...], "summary": "...", ... }

# 5. User asks questions about research
POST /api/v1/chat
{
  "message": "Explain Flash Attention from the research",
  "conversation_id": "conv-uuid"
}

# RAG retrieves from newly added sources!
```

---

## Conclusion

The Web Researcher Agent transforms your Personal Knowledge Assistant from a passive repository into an **active research tool**. Users can delegate time-consuming research to an AI agent that:

1. Searches the web autonomously
2. Evaluates source credibility
3. Extracts and processes content
4. Integrates findings into your knowledge base
5. Detects contradictions and suggests follow-ups

This feature is **genuinely innovative** - no other personal knowledge tool offers autonomous background research with this level of integration.

**Estimated Development Time**:
- MVP (Phase 1): 1 week
- Enhanced (Phase 2): 1 week
- Total: 2 weeks for production-ready feature

Ready to implement? 🚀
