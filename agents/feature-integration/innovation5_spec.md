# Innovation 5: Knowledge Evolution Timeline - Feature Specification

## Overview
A visual timeline that tracks how a user's understanding of topics evolves over time, showing "thought diffs" like git diffs but for concepts. This creates awareness of learning progress and reveals how perspectives shift.

## Backend Requirements

### Service: `knowledge_evolution_service.py` (ALREADY EXISTS)
- ✅ Service already implemented
- Methods:
  - `create_conceptual_snapshot()` - Creates snapshot of current understanding
  - `analyze_evolution()` - Compares two snapshots to show learning progress
  - `generate_thought_diff()` - Creates git-diff-style visualization

### API Endpoints Needed
**Router**: `/api/v1/knowledge-evolution`

1. **POST /snapshots**
   - Create a new conceptual snapshot
   - Request: `{ topic, conversation_messages, conversation_id, timestamp }`
   - Response: Snapshot object with understanding analysis

2. **GET /snapshots/topic/{topic}**
   - Get all snapshots for a specific topic
   - Response: List of snapshots ordered by timestamp

3. **GET /evolution/{topic}**
   - Get evolution analysis between earliest and latest snapshots
   - Query params: `start_date`, `end_date` (optional)
   - Response: Evolution analysis with thought diffs

4. **GET /timeline**
   - Get timeline of all topics user has learned about
   - Response: List of topics with snapshot counts and date ranges

### Database Models Needed
**Model**: `ConceptualSnapshot`
```python
class ConceptualSnapshot(Base):
    __tablename__ = "conceptual_snapshots"

    id = UUID(primary_key=True)
    topic = String(500)  # What topic this snapshot is about
    understanding = Text  # LLM-generated summary of understanding
    key_concepts = ARRAY(String)  # List of concepts understood
    misconceptions = ARRAY(String)  # List of incorrect beliefs
    confidence = Float  # 0.0-1.0 confidence score
    questions_asked = ARRAY(String)  # Questions they asked

    conversation_id = UUID(ForeignKey("conversations.id"))
    timestamp = DateTime(timezone=True)

    created_at = DateTime(timezone=True, server_default=func.now())
```

## Frontend Requirements

### Service: `knowledgeEvolutionService.ts`
- API client methods:
  - `createSnapshot(topic, conversationMessages, conversationId)`
  - `getSnapshotsByTopic(topic)`
  - `getEvolution(topic, startDate?, endDate?)`
  - `getTimeline()`

### React Components

#### 1. **KnowledgeEvolutionTimeline.tsx**
Main timeline component showing learning journey
- **Location**: `src/components/learning/KnowledgeEvolutionTimeline.tsx`
- **Props**:
  - `isOpen: boolean` - Modal visibility
  - `onClose: () => void` - Close handler
  - `initialTopic?: string` - Pre-select a topic
- **Features**:
  - Vertical timeline with date markers
  - Topic cards showing snapshot dates
  - Click to expand and see evolution details
  - Filter by date range
  - Search topics
- **UI Elements**:
  - Timeline icon from lucide-react
  - Date badges with relative time ("2 weeks ago")
  - Topic badges with color coding
  - Expandable sections for each topic

#### 2. **ThoughtDiffViewer.tsx**
Component showing git-diff-style comparison of understanding
- **Location**: `src/components/learning/ThoughtDiffViewer.tsx`
- **Props**:
  - `earlierSnapshot: ConceptualSnapshot`
  - `laterSnapshot: ConceptualSnapshot`
  - `evolutionAnalysis: EvolutionAnalysis`
- **Features**:
  - Side-by-side comparison ("Before" vs "After")
  - Red/green highlighting for changes (like git diff)
  - Show added concepts (green), removed misconceptions (red strikethrough)
  - Confidence score visualization (progress bar)
  - Evolution metrics (concepts gained, misconceptions corrected)
- **UI Style**:
  - Monospace font for diff-like appearance
  - `+ Added concept` in green
  - `- Removed misconception` in red strikethrough
  - `~ Modified understanding` in yellow

#### 3. **EvolutionMetrics.tsx**
Component showing learning progress statistics
- **Location**: `src/components/learning/EvolutionMetrics.tsx`
- **Props**:
  - `snapshots: ConceptualSnapshot[]`
  - `topic: string`
- **Features**:
  - Line chart showing confidence over time
  - Bar chart showing concepts learned
  - Pie chart showing question types asked
  - Summary statistics (total snapshots, learning velocity)
- **Tech**: Could use recharts or simple CSS-based charts

### Custom Hook: `useKnowledgeEvolution`
- **Location**: `src/hooks/useKnowledgeEvolution.ts`
- **Features**:
  - Fetches snapshots for a topic
  - Fetches evolution analysis
  - Manages loading/error states
  - Uses React Query for caching

### Page Integration
Add "View Evolution" button to ChatPage that:
1. Detects current conversation topic
2. Opens KnowledgeEvolutionTimeline modal
3. Pre-selects the current topic
4. Optionally creates a snapshot before showing timeline

## Testing Requirements

### Backend Tests
1. **Unit tests** (`tests/unit/test_knowledge_evolution_service.py`):
   - Test snapshot creation with various conversation types
   - Test evolution analysis between snapshots
   - Test thought diff generation
   - Test edge cases (no snapshots, single snapshot)

2. **Integration tests** (`tests/integration/test_knowledge_evolution_api.py`):
   - Test POST /snapshots endpoint
   - Test GET /snapshots/topic/{topic}
   - Test GET /evolution/{topic}
   - Test GET /timeline
   - Test database persistence

### Frontend Tests
1. **Component tests**:
   - `KnowledgeEvolutionTimeline.test.tsx` - Timeline rendering and interactions
   - `ThoughtDiffViewer.test.tsx` - Diff visualization
   - `EvolutionMetrics.test.tsx` - Chart rendering

2. **Service tests**:
   - `knowledgeEvolutionService.test.ts` - API calls and error handling

3. **Hook tests**:
   - `useKnowledgeEvolution.test.ts` - Data fetching and state management

## UI/UX Considerations

### Visual Design
- **Timeline**: Vertical line with circular nodes
- **Colors**:
  - Green for learning progress/new concepts
  - Red for corrected misconceptions
  - Yellow for modified understanding
  - Blue for neutral timeline elements
- **Icons**:
  - 📚 for snapshots
  - 🎯 for evolution milestones
  - 💡 for insights
  - ⏱️ for timeline

### User Flow
1. User has conversation about a topic
2. Click "Capture Snapshot" button in chat
3. Snapshot created and saved
4. Continue learning, ask more questions
5. Click "View Evolution" to see timeline
6. See how understanding has grown over time
7. View thought diffs between snapshots

### Accessibility
- ARIA labels for all interactive elements
- Keyboard navigation for timeline
- Screen reader announcements for snapshot creation
- High contrast mode support

## Integration Points

### Chat Page Integration
Add buttons to ChatPage:
```typescript
// After a conversation has messages
<button onClick={handleCreateSnapshot}>
  📚 Capture Understanding Snapshot
</button>

<button onClick={handleViewEvolution}>
  ⏱️ View Knowledge Evolution
</button>
```

### Context Panel Integration
Show mini evolution preview in Context Panel:
- "You've learned about this topic 3 times"
- "Last snapshot: 2 days ago"
- "View full timeline" link

## Success Criteria
- [ ] User can create snapshots from chat conversations
- [ ] Snapshots are persisted in database
- [ ] Timeline displays all learning sessions
- [ ] Thought diffs clearly show learning progress
- [ ] Evolution metrics provide meaningful insights
- [ ] UI is responsive and accessible
- [ ] All tests pass (>80% coverage)

## Future Enhancements
- Export timeline as markdown/PDF
- Share learning journey with others
- Set learning goals and track progress
- Spaced repetition based on confidence scores
- AI-generated learning recommendations
