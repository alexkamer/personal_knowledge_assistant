# Feature Integration Agent

A Claude-powered agent that builds features end-to-end across the full stack (backend + frontend + tests).

## What It Does

This agent takes a feature specification and automatically generates:

### Backend
- ✅ Service layer (`app/services/{feature}_service.py`)
- ✅ API endpoints (`app/api/v1/endpoints/{feature}.py`)
- ✅ Pydantic schemas (`app/schemas/{feature}.py`)
- ✅ Database models (if needed)
- ✅ Unit and integration tests

### Frontend
- ✅ API service (`src/services/{feature}Service.ts`)
- ✅ React components (`src/components/{feature}/`)
- ✅ Custom hooks (`src/hooks/use{Feature}.ts`)
- ✅ Component tests

### Documentation
- ✅ API documentation
- ✅ Component documentation
- ✅ Integration guides

## Installation

```bash
cd agents/feature-integration
pip install -r requirements.txt
```

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

### Basic Usage

```bash
python agent.py \
  --feature "knowledge_evolution" \
  --spec "innovation5_spec.md"
```

### What Happens

1. **Analysis**: Agent reads the spec and breaks it into structured tasks
2. **Backend Generation**: Creates service, endpoints, and schemas
3. **Frontend Generation**: Creates service, components, and hooks
4. **Test Generation**: Creates comprehensive tests for both layers
5. **Output**: All files are written to the project directories

### Output Structure

```
backend/
  app/
    services/{feature}_service.py      # Business logic
    api/v1/endpoints/{feature}.py      # REST endpoints
    schemas/{feature}.py               # Pydantic models
  tests/
    unit/test_{feature}_service.py     # Service tests
    integration/test_{feature}_api.py  # API tests

frontend/
  src/
    services/{feature}Service.ts       # API client
    components/{feature}/              # React components
      {Feature}Component.tsx
    hooks/use{Feature}.ts              # Custom hooks
    components/{feature}/
      {Feature}.test.tsx               # Component tests
```

## Feature Specification Format

Create a markdown file with these sections:

```markdown
# Feature Name - Specification

## Overview
Brief description of the feature

## Backend Requirements
- List of backend tasks
- Service methods needed
- API endpoints (with HTTP methods and paths)
- Database models (if any)

## Frontend Requirements
- React components needed
- Service methods for API calls
- UI/UX considerations
- State management needs

## Testing Requirements
- Backend tests needed
- Frontend tests needed
- E2E scenarios

## Integration Points
- Where this feature connects to existing code
```

See `innovation5_spec.md` for a complete example.

## Advanced Usage

### Generate Only Backend

Modify the spec to include only backend requirements, and the agent will skip frontend generation.

### Generate Only Frontend

Provide backend API documentation in the spec, and the agent will generate only frontend code.

### Custom Model

The agent uses `claude-opus-4-5-20251101` by default. You can modify the model in `agent.py`:

```python
response = self.client.messages.create(
    model="claude-opus-4-5-20251101",  # Change this
    max_tokens=8000,
    messages=[...]
)
```

## Examples

### Example 1: Build Innovation 5 (Knowledge Evolution)

```bash
python agent.py \
  --feature "knowledge_evolution" \
  --spec "innovation5_spec.md"
```

This generates the complete Knowledge Evolution Timeline feature with:
- Backend service for snapshot creation and analysis
- API endpoints for CRUD operations
- Frontend timeline component with thought diffs
- Comprehensive tests

### Example 2: Build a New Feature

Create a spec file `my_feature_spec.md`, then:

```bash
python agent.py \
  --feature "my_feature" \
  --spec "my_feature_spec.md"
```

## Post-Generation Steps

After the agent runs:

1. **Review Generated Code**: Check that it matches your requirements
2. **Run Tests**:
   ```bash
   cd backend && pytest tests/
   cd frontend && npm test
   ```
3. **Register Router**: Add to `backend/app/api/v1/api.py`:
   ```python
   from app.api.v1.endpoints import my_feature
   api_router.include_router(my_feature.router, prefix="/my-feature", tags=["my_feature"])
   ```
4. **Import Components**: Use in your React pages:
   ```typescript
   import { MyFeatureComponent } from '@/components/my_feature/MyFeatureComponent';
   ```
5. **Create Migration**: If database models were added:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add my_feature models"
   alembic upgrade head
   ```

## How It Works

The agent uses Claude Opus 4.5 with a multi-step process:

1. **Feature Analysis** (Opus 4.5)
   - Breaks down spec into structured tasks
   - Identifies dependencies
   - Creates implementation order

2. **Code Generation** (Opus 4.5)
   - Reads existing project patterns
   - Generates code matching project style
   - Uses proper type hints and docstrings

3. **Test Generation** (Opus 4.5)
   - Creates comprehensive test suites
   - Covers happy paths and edge cases
   - Uses project testing patterns

4. **File Writing**
   - Writes all generated files to project directories
   - Creates directories as needed
   - Reports progress

## Limitations

- **Requires Manual Integration**: Generated code needs to be imported/registered manually
- **No Database Migrations**: You need to run Alembic manually if models are created
- **Limited Context**: Agent sees examples but not the entire codebase
- **Review Required**: Always review generated code before committing

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Failed to parse plan"
The agent couldn't extract JSON from Claude's response. Check the spec format and try again.

### "Could not read file"
The agent looks for example files in the project. Ensure you're running from the project root.

### Generated Code Has Errors
Review and fix manually. The agent generates based on patterns but may need adjustments.

## Cost Estimation

- **Claude Opus 4.5**: $15/1M input tokens, $75/1M output tokens
- **Typical feature**: ~20-30K tokens (input + output)
- **Cost per feature**: ~$1-3

## Future Enhancements

- [ ] Add database migration generation
- [ ] Auto-register routers and components
- [ ] Support for GraphQL endpoints
- [ ] Visual spec creator (web UI)
- [ ] Integration with CI/CD
- [ ] Cost estimation before generation
- [ ] Incremental updates to existing features

## Contributing

This agent is part of the Personal Knowledge Assistant project. Improvements welcome!

## License

Same as the main project.
