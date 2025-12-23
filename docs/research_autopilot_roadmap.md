# Research Autopilot Implementation Roadmap

## Status: Phase 1 Complete ✅

**Last Updated**: 2025-12-18

## Overview

This document tracks the implementation progress of Research Autopilot, the autonomous research system that makes the Personal Knowledge Assistant stand out from competitors.

## Completed Work

### ✅ Phase 0: Foundation (Complete)
- [x] Architecture design document created
- [x] Database schema designed
- [x] SQLAlchemy models created:
  - `ResearchProject` (research_projects table)
  - `ResearchBriefing` (research_briefings table)
  - `ResearchTask` enhanced with project relationship
- [x] Database migration created and executed
- [x] Pydantic schemas created:
  - `research_project.py` (16 schemas)
  - `research_briefing.py` (6 schemas)

## Next Steps: MVP Implementation

### Phase 1: Core Services (Week 1) 🎯 CURRENT
**Goal**: Implement backend services for project management and task generation

#### 1.1 Research Project Service
**File**: `backend/app/services/research_project_service.py`

**Features**:
```python
class ResearchProjectService:
    # CRUD operations
    async def create_project(db, project_data: ResearchProjectCreate) -> ResearchProject
    async def get_project(db, project_id: str) -> ResearchProject
    async def list_projects(db, status=None, limit=20, offset=0) -> List[ResearchProject]
    async def update_project(db, project_id: str, updates: ResearchProjectUpdate) -> ResearchProject
    async def delete_project(db, project_id: str, delete_tasks=False) -> None

    # Progress tracking
    async def get_project_progress(db, project_id: str) -> ResearchProjectProgress
    async def update_project_stats(db, project_id: str) -> None  # Recalculate stats from tasks

    # Task generation (LLM-powered)
    async def generate_task_queries(db, project_id: str, count=5) -> List[str]
    async def create_tasks_from_queries(db, project_id: str, queries: List[str]) -> List[ResearchTask]
```

**Implementation Steps**:
1. Create service class with dependency injection
2. Implement CRUD methods
3. Implement progress calculation
4. Implement LLM-based task generation:
   - Analyze project goal
   - Generate diverse research queries
   - Check for duplicates against existing tasks
   - Return 5-10 suggested queries
5. Write unit tests (>80% coverage)

**Estimated Time**: 1 day

---

#### 1.2 Research Scheduler Service
**File**: `backend/app/services/research_scheduler_service.py`

**Features**:
```python
class ResearchSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    # Lifecycle
    async def start(self) -> None
    async def shutdown(self) -> None

    # Schedule management
    async def schedule_project(db, project_id: str) -> str  # Returns job_id
    async def unschedule_project(project_id: str) -> None
    async def reschedule_project(db, project_id: str) -> str

    # Manual execution
    async def run_project_now(db, project_id: str) -> List[str]  # Returns task_ids

    # Job execution (called by scheduler)
    async def _execute_project_run(project_id: str) -> None
```

**Implementation Steps**:
1. Install APScheduler: `pip install apscheduler==3.10.4`
2. Create scheduler service with AsyncIOScheduler
3. Implement schedule parsing (daily, weekly, monthly, cron)
4. Implement job registration/cancellation
5. Implement project execution logic:
   - Generate new tasks (if auto_generate_tasks=true)
   - Or run existing queued tasks
   - Limit to max_tasks_per_run
   - Update project.last_run_at and next_run_at
6. Add scheduler lifecycle hooks to FastAPI app startup/shutdown
7. Configure job persistence (SQLAlchemyJobStore)
8. Write unit tests with mocked scheduler

**Estimated Time**: 2 days

---

#### 1.3 Briefing Generator Service
**File**: `backend/app/services/briefing_generator_service.py`

**Features**:
```python
class BriefingGeneratorService:
    async def generate_briefing(db, project_id: str, task_ids: List[str] = None) -> ResearchBriefing

    # Analysis methods
    async def _synthesize_findings(sources: List[Dict]) -> Dict
    async def _identify_contradictions(sources: List[Dict]) -> List[Dict]
    async def _identify_knowledge_gaps(db, project_id: str, sources: List[Dict]) -> List[str]
    async def _suggest_follow_up_tasks(db, project_id: str, findings: Dict) -> List[str]

    # Export
    async def format_briefing_markdown(briefing: ResearchBriefing) -> str
```

**Implementation Steps**:
1. Create service with LLM integration
2. Implement briefing generation:
   - Collect all sources from specified tasks
   - Send to LLM with synthesis prompt
   - Parse structured response (JSON)
3. Implement contradiction detection:
   - Find opposing statements across sources
   - Rank by confidence
4. Implement knowledge gap analysis:
   - Compare project goal vs collected sources
   - Identify missing topics/subtopics
5. Implement follow-up task suggestion:
   - Generate 3-5 new research questions
   - Focus on gaps and contradictions
6. Implement markdown export
7. Write unit tests with mocked LLM

**Estimated Time**: 2 days

---

### Phase 2: API Endpoints (Week 1-2)
**Goal**: Expose research project functionality via REST API

#### 2.1 Research Projects API
**File**: `backend/app/api/v1/endpoints/research_projects.py`

**Endpoints**:
```python
# CRUD
POST   /api/v1/research/projects              - Create project
GET    /api/v1/research/projects              - List projects (paginated, filterable)
GET    /api/v1/research/projects/{id}         - Get project details
PUT    /api/v1/research/projects/{id}         - Update project
DELETE /api/v1/research/projects/{id}         - Delete project

# Tasks
POST   /api/v1/research/projects/{id}/tasks/generate  - Generate task queries
POST   /api/v1/research/projects/{id}/tasks           - Create tasks from queries
GET    /api/v1/research/projects/{id}/tasks           - List project tasks

# Progress
GET    /api/v1/research/projects/{id}/progress        - Get progress summary

# Scheduling
POST   /api/v1/research/projects/{id}/schedule        - Update schedule
DELETE /api/v1/research/projects/{id}/schedule        - Remove schedule (set to manual)
POST   /api/v1/research/projects/{id}/run             - Run now (manual trigger)
POST   /api/v1/research/projects/{id}/pause           - Pause scheduling
POST   /api/v1/research/projects/{id}/resume          - Resume scheduling
```

**Implementation Steps**:
1. Create router with proper dependency injection
2. Implement all CRUD endpoints
3. Implement task generation endpoints
4. Implement scheduling endpoints
5. Implement manual run endpoint
6. Add proper error handling and status codes
7. Write integration tests

**Estimated Time**: 1.5 days

---

#### 2.2 Research Briefings API
**File**: `backend/app/api/v1/endpoints/research_briefings.py`

**Endpoints**:
```python
GET    /api/v1/research/briefings                     - List all briefings
GET    /api/v1/research/briefings/{id}                - Get briefing details
POST   /api/v1/research/projects/{id}/briefings       - Generate new briefing
GET    /api/v1/research/projects/{id}/briefings       - Get project briefings
DELETE /api/v1/research/briefings/{id}                - Delete briefing
GET    /api/v1/research/briefings/{id}/markdown       - Export as markdown
POST   /api/v1/research/briefings/{id}/view           - Mark briefing as viewed
```

**Implementation Steps**:
1. Create router
2. Implement all endpoints
3. Add markdown export functionality
4. Write integration tests

**Estimated Time**: 1 day

---

#### 2.3 Update main.py
**File**: `backend/app/main.py`

**Changes**:
1. Import and include new routers
2. Add scheduler lifecycle hooks:
```python
from app.services.research_scheduler_service import get_research_scheduler

@app.on_event("startup")
async def startup_scheduler():
    scheduler = get_research_scheduler()
    await scheduler.start()

@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler = get_research_scheduler()
    await scheduler.shutdown()
```

**Estimated Time**: 30 minutes

---

### Phase 3: Frontend UI (Week 2-3)
**Goal**: Build user interface for Research Autopilot

#### 3.1 API Client Layer
**File**: `frontend/src/services/research-api.ts`

**Features**:
```typescript
// Projects
export const researchProjectsApi = {
  createProject: (data: ResearchProjectCreate) => Promise<ResearchProjectResponse>
  listProjects: (params?: ListParams) => Promise<ResearchProjectList>
  getProject: (id: string) => Promise<ResearchProjectResponse>
  updateProject: (id: string, data: ResearchProjectUpdate) => Promise<ResearchProjectResponse>
  deleteProject: (id: string, deleteTasks?: boolean) => Promise<void>

  // Tasks
  generateTasks: (id: string, count: number) => Promise<TaskGenerationResponse>
  createTasks: (id: string, queries: string[]) => Promise<ResearchTask[]>
  getProjectTasks: (id: string) => Promise<ResearchTask[]>

  // Progress
  getProgress: (id: string) => Promise<ResearchProjectProgress>

  // Scheduling
  updateSchedule: (id: string, schedule: ScheduleUpdateRequest) => Promise<ResearchProjectResponse>
  runNow: (id: string) => Promise<RunProjectResponse>
  pauseProject: (id: string) => Promise<ResearchProjectResponse>
  resumeProject: (id: string) => Promise<ResearchProjectResponse>
}

// Briefings
export const researchBriefingsApi = {
  listBriefings: (params?: ListParams) => Promise<ResearchBriefingList>
  getBriefing: (id: string) => Promise<ResearchBriefingResponse>
  generateBriefing: (projectId: string, taskIds?: string[]) => Promise<ResearchBriefingResponse>
  getProjectBriefings: (projectId: string) => Promise<ResearchBriefingList>
  deleteBriefing: (id: string) => Promise<void>
  exportMarkdown: (id: string) => Promise<BriefingMarkdown>
  markAsViewed: (id: string) => Promise<void>
}
```

**Estimated Time**: 1 day

---

#### 3.2 React Query Hooks
**File**: `frontend/src/hooks/useResearchProjects.ts`

**Features**:
```typescript
// Queries
export const useResearchProjects = (params?) => { /* list projects */ }
export const useResearchProject = (id: string) => { /* get project */ }
export const useProjectProgress = (id: string) => { /* get progress */ }
export const useProjectTasks = (id: string) => { /* get tasks */ }
export const useProjectBriefings = (id: string) => { /* get briefings */ }

// Mutations
export const useCreateProject = () => { /* create project */ }
export const useUpdateProject = () => { /* update project */ }
export const useDeleteProject = () => { /* delete project */ }
export const useGenerateTasks = () => { /* generate tasks */ }
export const useRunProject = () => { /* manual run */ }
export const useUpdateSchedule = () => { /* update schedule */ }
export const useGenerateBriefing = () => { /* generate briefing */ }
```

**Estimated Time**: 1 day

---

#### 3.3 Research Projects Dashboard
**File**: `frontend/src/pages/Research/ResearchDashboard.tsx`

**Features**:
- Project list with status indicators
- Filter by status (active, paused, completed, archived)
- Quick stats (total projects, active tasks, sources added)
- Create new project button
- Project cards with:
  - Name, goal summary
  - Next run time
  - Progress bar
  - Quick actions (View, Edit, Run Now, Pause)

**Estimated Time**: 2 days

---

#### 3.4 Project Creation Wizard
**File**: `frontend/src/pages/Research/CreateProjectWizard.tsx`

**Features**:
- Multi-step form:
  - Step 1: Basic info (name, goal, description)
  - Step 2: Research settings (sources, depth, types)
  - Step 3: Schedule configuration
  - Step 4: Initial task generation (optional)
- Form validation
- Preview before creation
- Success confirmation with redirect

**Estimated Time**: 2 days

---

#### 3.5 Project Detail Page
**File**: `frontend/src/pages/Research/ProjectDetail.tsx`

**Features**:
- Tabs:
  - **Overview**: Progress, stats, timeline, quick actions
  - **Tasks**: List of all tasks with status, filterable
  - **Briefings**: Generated briefings list
  - **Sources**: All collected sources, searchable
  - **Settings**: Edit project configuration
- Real-time progress updates (polling)
- Manual run button with confirmation
- Schedule management UI

**Estimated Time**: 3 days

---

#### 3.6 Briefing Viewer
**File**: `frontend/src/pages/Research/BriefingViewer.tsx`

**Features**:
- Structured briefing display:
  - Executive summary
  - Key findings with source citations
  - Contradictions (if any)
  - Knowledge gaps
  - Suggested follow-ups
- Export options (PDF, Markdown)
- Generate new briefing button
- Mark as viewed (auto-tracks)
- Citation links to original sources

**Estimated Time**: 2 days

---

#### 3.7 Navigation Updates
**Files**:
- `frontend/src/App.tsx`
- `frontend/src/components/layout/Sidebar.tsx`

**Changes**:
1. Add `/research` route
2. Add "Research Projects" to sidebar navigation
3. Add icon (microscope or search icon)

**Estimated Time**: 30 minutes

---

### Phase 4: Testing & Polish (Week 3-4)
**Goal**: Ensure quality and reliability

#### 4.1 Backend Tests
**Files**: `backend/tests/unit/test_research_*.py`

**Test Coverage**:
- Research Project Service (>80%)
- Research Scheduler Service (>80%)
- Briefing Generator Service (>80%)
- API endpoints integration tests
- Database model tests

**Estimated Time**: 2 days

---

#### 4.2 Frontend Tests
**Files**: `frontend/src/**/*.test.tsx`

**Test Coverage**:
- Component tests (>70%)
- Hook tests
- API client tests
- Integration tests for key flows

**Estimated Time**: 2 days

---

#### 4.3 End-to-End Testing
**Manual Testing Scenarios**:
1. Create project → auto-generate tasks → schedule daily
2. Run project manually → monitor progress → view results
3. Generate briefing → review findings → export markdown
4. Edit project schedule → verify next_run_at updates
5. Delete project → verify cascade deletes work
6. Pause/resume project → verify scheduler updates

**Estimated Time**: 1 day

---

#### 4.4 Documentation Updates
**Files**:
- `docs/research_autopilot_user_guide.md` (new)
- `.claude/CLAUDE.md` (update with Research Autopilot section)
- `README.md` (add Research Autopilot to features)

**Estimated Time**: 1 day

---

## Future Enhancements (Post-MVP)

### Phase 5: Advanced Features
- **Email/Push Notifications**: Briefing delivery via email
- **Project Templates**: Pre-configured research projects
- **Knowledge Graph View**: Visual connections between sources
- **Source Whitelist/Blacklist**: User-controlled domain filtering
- **Advanced Analytics**: Source quality trends, topic evolution
- **Collaborative Projects**: Multi-user research projects
- **Research Impact Tracking**: Monitor cited sources for updates

### Phase 6: AI Enhancements
- **Automatic Query Refinement**: Improve search based on results
- **Cross-Project Insights**: Find connections between projects
- **Proactive Suggestions**: "You might be interested in..."
- **Smart Scheduling**: Optimize run times based on user activity
- **Source Quality Learning**: Improve credibility scoring over time

---

## Dependencies to Install

### Backend
```bash
pip install apscheduler==3.10.4
```

### Frontend
No new dependencies needed (using existing React Query, axios)

---

## Configuration

### Environment Variables (.env)
```bash
# Research Autopilot Settings
RESEARCH_SCHEDULER_ENABLED=true
RESEARCH_SCHEDULER_TIMEZONE=America/Los_Angeles
RESEARCH_DEFAULT_SCHEDULE_TIME=02:00
RESEARCH_MAX_CONCURRENT_TASKS=3
RESEARCH_SCRAPE_DELAY_SECONDS=3
```

---

## Success Metrics

### MVP Launch Goals (4 weeks)
- [ ] 5 test projects created and running successfully
- [ ] 100+ sources collected autonomously
- [ ] 10+ briefings generated
- [ ] <1% task failure rate
- [ ] All tests passing (>80% backend, >70% frontend)
- [ ] Complete documentation

### User Adoption Goals (3 months)
- [ ] Average 2 active projects per user
- [ ] 80% of briefings marked as viewed
- [ ] 50% of suggested tasks accepted
- [ ] User reports time saved vs manual research

---

## Risk Mitigation

### Technical Risks
1. **Scheduler reliability**: Use persistent job store, implement health checks
2. **LLM failures**: Graceful degradation, fallback to simple summaries
3. **Rate limiting from sources**: Respect robots.txt, add delays, implement backoff
4. **Database performance**: Index critical fields, monitor query performance

### User Experience Risks
1. **Complexity**: Progressive disclosure, good defaults, wizard UX
2. **Misleading results**: Show credibility scores, mark auto-generated content
3. **Information overload**: Limit briefing length, highlight key findings

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Foundation | 1 day | ✅ Complete |
| Phase 1: Core Services | 5 days | 🎯 In Progress |
| Phase 2: API Endpoints | 3 days | ⏳ Pending |
| Phase 3: Frontend UI | 10 days | ⏳ Pending |
| Phase 4: Testing & Polish | 6 days | ⏳ Pending |
| **Total MVP** | **~4 weeks** | 20% Complete |

---

## Next Immediate Actions

1. ✅ Install APScheduler
2. 🎯 Implement ResearchProjectService
3. 🎯 Implement ResearchSchedulerService
4. 🎯 Implement BriefingGeneratorService
5. ⏳ Create API endpoints
6. ⏳ Build frontend dashboard

**Current Focus**: Backend services implementation (Phase 1)
