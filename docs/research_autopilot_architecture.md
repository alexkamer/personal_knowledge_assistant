# Research Autopilot Architecture

## Overview

The Research Autopilot extends the existing Web Researcher Agent with **scheduled, automated research projects** that run in the background. Users can define long-term research goals and the system autonomously expands their knowledge base while they sleep, work, or do other tasks.

## Core Concept

**Research Projects** are collections of related research tasks that run on a schedule:
- User creates a project: "Learn about climate change policy"
- System breaks it down into tasks: "Paris Agreement details", "Carbon pricing mechanisms", "Renewable energy policies"
- Tasks run on schedule (nightly, weekly, custom)
- Results are automatically added to knowledge base
- User receives morning briefing with findings

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend UI Layer                        │
│  - Research Projects Dashboard                              │
│  - Project Creation Wizard                                  │
│  - Task Progress Monitoring                                 │
│  - Research Briefing Viewer                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  - /api/v1/research/projects (CRUD)                         │
│  - /api/v1/research/projects/{id}/tasks                     │
│  - /api/v1/research/projects/{id}/schedule                  │
│  - /api/v1/research/briefings                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Service Layer (Business Logic)               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Research Project Service                            │   │
│  │  - Project lifecycle management                     │   │
│  │  - Task generation from project goals               │   │
│  │  - Progress aggregation                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Research Scheduler Service (APScheduler)            │   │
│  │  - Cron-based task scheduling                       │   │
│  │  - Background job queue management                  │   │
│  │  - Retry logic for failed tasks                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Research Orchestrator (existing)                    │   │
│  │  - Web search, scraping, credibility scoring        │   │
│  │  - Document creation and RAG processing             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Briefing Generator Service                          │   │
│  │  - Synthesize findings from multiple tasks          │   │
│  │  - Identify contradictions and gaps                 │   │
│  │  - Generate follow-up suggestions                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer (PostgreSQL)                    │
│  - research_projects                                        │
│  - research_tasks (existing, enhanced)                      │
│  - research_sources (existing)                              │
│  - research_briefings (new)                                 │
│  - documents (existing)                                     │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### New Tables

#### `research_projects`
```sql
CREATE TABLE research_projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    goal TEXT NOT NULL,  -- Main research objective
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, paused, completed, archived

    -- Scheduling
    schedule_type VARCHAR(20) NOT NULL DEFAULT 'manual',  -- manual, daily, weekly, monthly, custom
    schedule_cron VARCHAR(100),  -- Custom cron expression
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,

    -- Task generation settings
    auto_generate_tasks BOOLEAN DEFAULT true,  -- Auto-generate tasks from goal
    max_tasks_per_run INTEGER DEFAULT 5,  -- Max tasks to run per scheduled execution

    -- Research settings (defaults for generated tasks)
    default_max_sources INTEGER DEFAULT 10,
    default_depth VARCHAR(20) DEFAULT 'thorough',
    default_source_types TEXT[],

    -- Progress tracking
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    total_sources_added INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `research_briefings`
```sql
CREATE TABLE research_briefings (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES research_projects(id) ON DELETE CASCADE,

    -- Briefing content
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    key_findings JSONB,  -- Structured findings
    contradictions JSONB[],  -- Contradictions found across sources
    knowledge_gaps TEXT[],  -- Identified gaps in research
    suggested_tasks TEXT[],  -- Suggested follow-up research tasks

    -- Related tasks
    task_ids UUID[],  -- Tasks included in this briefing
    sources_count INTEGER DEFAULT 0,

    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    viewed_at TIMESTAMP WITH TIME ZONE
);
```

### Enhanced Tables

#### `research_tasks` (add project relation)
```sql
ALTER TABLE research_tasks
ADD COLUMN project_id UUID REFERENCES research_projects(id) ON DELETE CASCADE,
ADD COLUMN auto_generated BOOLEAN DEFAULT false,
ADD COLUMN scheduled_at TIMESTAMP WITH TIME ZONE,
ADD INDEX idx_project_id (project_id);
```

## Service Details

### 1. Research Project Service

**Purpose**: Manage research project lifecycle and task generation.

**Key Methods**:
```python
class ResearchProjectService:
    async def create_project(db, project_data) -> ResearchProject
    async def get_project(db, project_id) -> ResearchProject
    async def list_projects(db, status=None, limit=20, offset=0) -> List[ResearchProject]
    async def update_project(db, project_id, updates) -> ResearchProject
    async def delete_project(db, project_id, delete_tasks=False) -> None

    # Task generation
    async def generate_tasks_from_goal(db, project_id) -> List[ResearchTask]
    async def suggest_next_tasks(db, project_id, count=5) -> List[str]

    # Progress
    async def get_project_progress(db, project_id) -> Dict
    async def get_project_timeline(db, project_id) -> List[Dict]
```

**Task Generation Strategy**:
1. Analyze project goal with LLM
2. Break into subtopics/research questions
3. Consider existing tasks to avoid duplicates
4. Generate diverse, complementary queries
5. Prioritize based on knowledge gaps

### 2. Research Scheduler Service

**Purpose**: Schedule and execute research tasks automatically.

**Technology**: APScheduler (async-compatible scheduler)

**Key Methods**:
```python
class ResearchSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self) -> None  # Start scheduler on app startup
    async def shutdown(self) -> None  # Graceful shutdown

    # Schedule management
    async def schedule_project(db, project_id) -> str  # Returns job_id
    async def unschedule_project(project_id) -> None
    async def reschedule_project(db, project_id, new_schedule) -> str

    # Manual execution
    async def run_project_now(db, project_id) -> None

    # Job execution
    async def execute_project_run(project_id) -> None
```

**Scheduler Implementation**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Example: Daily at 2 AM
scheduler.add_job(
    execute_project_run,
    CronTrigger(hour=2, minute=0),
    args=[project_id],
    id=f"project_{project_id}",
    replace_existing=True
)
```

### 3. Briefing Generator Service

**Purpose**: Synthesize research findings into actionable briefings.

**Key Methods**:
```python
class BriefingGeneratorService:
    async def generate_briefing(db, project_id, task_ids) -> ResearchBriefing
    async def identify_contradictions(sources) -> List[Dict]
    async def identify_knowledge_gaps(db, project_id) -> List[str]
    async def suggest_follow_up_tasks(db, project_id, findings) -> List[str]
    async def format_briefing_markdown(briefing) -> str
```

**LLM-Powered Synthesis**:
1. Collect all sources from completed tasks
2. Send to LLM with synthesis prompt
3. Extract:
   - Key findings (structured)
   - Contradictions between sources
   - Confidence scores
   - Knowledge gaps
   - Suggested follow-ups

**Synthesis Prompt Template**:
```
You are a research analyst synthesizing findings from multiple sources.

Project Goal: {project.goal}
Completed Tasks: {task_count}
Sources Analyzed: {source_count}

Sources:
{formatted_sources}

Generate a comprehensive research briefing with:
1. Executive Summary (2-3 paragraphs)
2. Key Findings (bullet points with source citations)
3. Contradictions Found (if any, with details)
4. Knowledge Gaps (areas needing more research)
5. Suggested Follow-up Questions (3-5 questions)

Format as structured JSON.
```

## API Endpoints

### Research Projects

```
POST   /api/v1/research/projects              - Create project
GET    /api/v1/research/projects              - List projects (paginated)
GET    /api/v1/research/projects/{id}         - Get project details
PUT    /api/v1/research/projects/{id}         - Update project
DELETE /api/v1/research/projects/{id}         - Delete project

POST   /api/v1/research/projects/{id}/tasks/generate  - Generate tasks from goal
GET    /api/v1/research/projects/{id}/tasks           - List project tasks
GET    /api/v1/research/projects/{id}/progress        - Get progress summary
GET    /api/v1/research/projects/{id}/timeline        - Get execution timeline

POST   /api/v1/research/projects/{id}/schedule        - Update schedule
POST   /api/v1/research/projects/{id}/run             - Run now (manual trigger)
POST   /api/v1/research/projects/{id}/pause           - Pause scheduling
POST   /api/v1/research/projects/{id}/resume          - Resume scheduling
```

### Research Briefings

```
GET    /api/v1/research/briefings                     - List all briefings
GET    /api/v1/research/briefings/{id}                - Get briefing details
GET    /api/v1/research/projects/{id}/briefings       - Get project briefings
POST   /api/v1/research/projects/{id}/briefings       - Generate new briefing
DELETE /api/v1/research/briefings/{id}                - Delete briefing
```

## Frontend Components

### 1. Research Projects Dashboard (`/research`)

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│  Research Projects                    [+ New Project]    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Active Projects (3)                                     │
│  ┌────────────────────────────────────────────────┐    │
│  │ 📊 Climate Change Policy Research              │    │
│  │ Next run: Tonight at 2:00 AM                   │    │
│  │ Progress: ████████░░ 15/20 tasks (75%)         │    │
│  │ Sources: 142 added | Last run: 12 hours ago    │    │
│  │ [View] [Edit] [Run Now] [⋮]                    │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ 🧬 Machine Learning Advances                   │    │
│  │ Schedule: Weekly (Sundays 3:00 AM)             │    │
│  │ Progress: ████░░░░░░ 8/40 tasks (20%)          │    │
│  │ Sources: 67 added | Last run: 2 days ago       │    │
│  │ [View] [Edit] [Run Now] [⋮]                    │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Paused Projects (1)                                     │
│  Completed Projects (5)                                  │
└──────────────────────────────────────────────────────────┘
```

### 2. Project Creation Wizard

**Step 1: Project Basics**
- Name
- Goal (multiline)
- Description (optional)

**Step 2: Research Settings**
- Max sources per task (slider: 5-50)
- Research depth (quick/thorough/deep)
- Source type preferences (checkboxes)

**Step 3: Scheduling**
- Manual only
- Daily (time picker)
- Weekly (day + time)
- Custom cron expression

**Step 4: Task Generation**
- Auto-generate initial tasks (checkbox)
- Review generated tasks (editable list)

### 3. Project Detail View

**Tabs**:
- **Overview**: Progress, stats, recent activity
- **Tasks**: List of all tasks (filterable by status)
- **Briefings**: Generated research briefings
- **Sources**: All collected sources (searchable)
- **Settings**: Edit project configuration

### 4. Research Briefing Viewer

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│  Climate Change Policy Research - Briefing #12          │
│  Generated: 2025-12-18 6:00 AM | 5 tasks | 42 sources   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📋 Executive Summary                                    │
│  [AI-generated summary paragraph...]                    │
│                                                          │
│  🎯 Key Findings                                         │
│  • Paris Agreement implementation challenges [1][2]     │
│  • Carbon pricing adoption in EU vs US [3][4]           │
│  • Renewable energy cost trends [5][6][7]               │
│                                                          │
│  ⚠️ Contradictions Found (2)                             │
│  1. Nuclear energy role: Source [2] claims critical,    │
│     Source [8] argues phase-out is optimal              │
│  2. Economic impact: [3] positive, [9] negative         │
│                                                          │
│  ❓ Knowledge Gaps                                       │
│  • Limited data on developing nations' policies         │
│  • Recent legislative changes (2024-2025) missing       │
│                                                          │
│  💡 Suggested Follow-ups                                 │
│  • Research India and China climate policies            │
│  • Investigate 2024 COP29 outcomes                      │
│                                                          │
│  [Export as PDF] [Share] [Generate New Briefing]        │
└──────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
1. ✅ Database migrations (research_projects, briefings)
2. ✅ Project CRUD service + API endpoints
3. ✅ Basic project creation UI
4. ✅ Project list/detail views

### Phase 2: Task Scheduling (Week 2)
1. ✅ APScheduler integration
2. ✅ Scheduler service implementation
3. ✅ Schedule management API endpoints
4. ✅ Schedule configuration UI
5. ✅ Manual "Run Now" functionality

### Phase 3: Intelligent Task Generation (Week 3)
1. ✅ LLM-based task generation from project goals
2. ✅ Knowledge gap analysis
3. ✅ Task deduplication logic
4. ✅ Task suggestion API + UI

### Phase 4: Briefing System (Week 4)
1. ✅ Briefing generator service
2. ✅ Multi-source synthesis with LLM
3. ✅ Contradiction detection
4. ✅ Briefing viewer UI
5. ✅ Export functionality (PDF, Markdown)

### Phase 5: Polish & Advanced Features (Week 5+)
1. ✅ Email notifications for completed briefings
2. ✅ Project templates (pre-configured research goals)
3. ✅ Knowledge graph visualization
4. ✅ Advanced analytics dashboard
5. ✅ Research history comparison

## Technical Considerations

### Background Job Processing

**Current**: FastAPI `BackgroundTasks` (simple, works for MVP)
**Future**: Consider Redis + RQ/Celery for:
- Better failure handling
- Job priority queues
- Distributed processing
- Job result inspection

### Scheduler Persistence

APScheduler with SQLAlchemy job store:
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='postgresql+asyncpg://...')
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
```

**Benefits**:
- Jobs persist across restarts
- No manual state management
- Automatic recovery

### Rate Limiting

Prevent overwhelming external services:
- Respect robots.txt
- Add delays between scrapes (2-5 seconds)
- Implement exponential backoff for failures
- Consider proxy rotation for large projects

### Cost Management

Even with local LLMs, consider:
- Embedding cache (avoid re-embedding same content)
- Incremental updates (only process new sources)
- Deduplication at URL level
- Content similarity checks before processing

### Error Handling

**Graceful Degradation**:
- Task fails → mark as failed, continue with others
- Scraping fails → retry with backoff, then skip
- LLM synthesis fails → generate simple summary
- Scheduler fails → log error, retry on next cycle

### Monitoring & Observability

Key metrics to track:
- Tasks completed/failed per project
- Sources added per day
- Average task duration
- Scheduler uptime
- Storage growth rate
- LLM token usage

Implement:
- Structured logging (JSON format)
- Prometheus metrics endpoint
- Health check endpoint
- Admin dashboard for job inspection

## User Workflows

### Workflow 1: Create Overnight Research Project

1. User navigates to `/research`
2. Clicks "New Project"
3. Enters:
   - Name: "AI Safety Research"
   - Goal: "Understand current approaches to AI alignment and safety"
   - Schedule: Daily at 2 AM
4. System generates 5 initial tasks
5. User reviews, edits if needed
6. Clicks "Create Project"
7. That night at 2 AM, first task runs
8. Next morning, user sees briefing with findings
9. User can ask questions about findings in chat

### Workflow 2: Monitor Long-Term Research

1. User has active project running for 2 weeks
2. Visits project detail page
3. Sees timeline of 14 completed runs
4. Views latest briefing showing:
   - 127 sources collected
   - 12 key findings
   - 3 contradictions identified
   - 5 suggested follow-ups
5. Clicks "Generate Tasks" from suggestions
6. System auto-creates new tasks based on gaps
7. Research continues autonomously

### Workflow 3: Quick Manual Research Run

1. User has urgent research need
2. Creates project with immediate goal
3. Sets to "Manual" scheduling
4. Clicks "Run Now"
5. Monitors progress in real-time
6. Receives results in 5-10 minutes
7. Pauses or archives project when done

## Success Metrics

**User Engagement**:
- Number of active projects per user
- Average tasks per project
- Briefing view rate
- Follow-up task generation rate

**System Performance**:
- Task success rate (target: >85%)
- Average task completion time
- Sources added per task
- Scheduler reliability (target: >99%)

**Content Quality**:
- User satisfaction with briefings
- Source credibility average (target: >0.7)
- Contradiction detection accuracy
- Knowledge gap identification usefulness

## Future Enhancements

### Near-Term
- Browser extension for manual source addition
- Research project sharing with other users
- Custom source whitelists/blacklists
- Advanced filtering (date ranges, domains)

### Long-Term
- Multi-user collaboration on projects
- Research project marketplace (templates)
- Integration with citation managers (Zotero, Mendeley)
- Academic paper PDF processing
- Research impact tracking (citations, updates)
- AI research assistant that proactively suggests projects

## Comparison with Competitors

| Feature | Research Autopilot | Perplexity | ChatGPT | Notion AI |
|---------|-------------------|------------|---------|-----------|
| **Local/Private** | ✅ Fully local | ❌ Cloud | ❌ Cloud | ❌ Cloud |
| **Scheduled Research** | ✅ Cron-based | ❌ Manual | ❌ Manual | ❌ Manual |
| **Long-term Projects** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Autonomous Operation** | ✅ Background | ❌ Interactive | ❌ Interactive | ❌ Interactive |
| **Source Credibility** | ✅ Scored | ⚠️ Implicit | ⚠️ Implicit | ❌ No |
| **Contradiction Detection** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Knowledge Graph** | 🔜 Phase 5 | ❌ No | ❌ No | ❌ No |
| **RAG Integration** | ✅ Built-in | ⚠️ Limited | ❌ No | ⚠️ Limited |

## Positioning & Marketing

**Tagline**: "Your AI researcher that never sleeps"

**Key Messages**:
1. **Privacy-First**: Research runs on your machine, data never leaves
2. **Autonomous**: Set it and forget it - wake up smarter
3. **Intelligent**: Detects contradictions, identifies gaps
4. **Proactive**: Suggests follow-up research automatically
5. **Local AI**: No API costs, no rate limits, fully offline

**Target Users**:
- Researchers and academics
- Knowledge workers and analysts
- Students writing theses
- Curious lifelong learners
- Privacy-conscious professionals

**Use Cases**:
- Academic literature review
- Market research automation
- Competitive intelligence gathering
- Technology trend monitoring
- Policy and regulation tracking
- Historical research projects

## Technical Stack Summary

**New Dependencies**:
```
# Backend
apscheduler==3.10.4  # Async job scheduling
python-crontab==3.0.0  # Cron expression parsing

# Optional (Phase 5+)
reportlab==4.0.7  # PDF generation
markdown2==2.4.10  # Markdown to HTML
```

**Configuration** (`.env`):
```
# Research Autopilot
RESEARCH_SCHEDULER_ENABLED=true
RESEARCH_SCHEDULER_TIMEZONE=America/Los_Angeles
RESEARCH_MAX_CONCURRENT_TASKS=3
RESEARCH_DEFAULT_SCHEDULE_TIME=02:00

# Rate limiting
RESEARCH_SCRAPE_DELAY_SECONDS=3
RESEARCH_MAX_RETRIES=3
```

## Security Considerations

**Input Validation**:
- Sanitize project names and descriptions
- Validate cron expressions before scheduling
- Limit project goal length (max 2000 chars)
- Prevent SSRF attacks in URL scraping

**Rate Limiting**:
- Max 10 active projects per user (future: when multi-user)
- Max 100 tasks per project
- Max 50 sources per task

**Resource Management**:
- Timeout long-running tasks (30 min default)
- Limit total storage per project (1 GB)
- Auto-archive old projects (90 days inactive)

**Data Privacy**:
- All research data stays local
- Optional encryption for sensitive projects
- Clear data retention policies

## Conclusion

The Research Autopilot transforms the existing Web Researcher Agent from a reactive tool into a **proactive research partner**. By combining scheduled automation, intelligent task generation, and comprehensive synthesis, it creates a unique value proposition that no competitor currently offers.

**Key Differentiators**:
1. **Only local AI solution** with autonomous research
2. **Only system** that researches while you sleep
3. **Only tool** with contradiction detection + gap analysis
4. **Zero API costs**, unlimited usage

This positions the Personal Knowledge Assistant as **the premier tool for serious researchers who value privacy, depth, and automation**.
