# GitHub Actions CI/CD Guide

## Overview

This project uses GitHub Actions for Continuous Integration (CI). Every time you push code or create a pull request, automated tests run to ensure nothing breaks.

## What Gets Tested

### Backend Tests
- **351 tests** with 70% code coverage
- Tests run against a real PostgreSQL 18 database
- Includes unit tests, integration tests, and service tests
- Mock external APIs (Gemini, Ollama) for reliable testing

### Frontend Tests
- **474 tests** covering React components and services
- Type checking with TypeScript compiler
- ESLint code quality checks
- Coverage reports uploaded as artifacts

### Code Quality
- Backend: Black formatting and mypy type checking
- Frontend: ESLint linting and TypeScript validation

## How It Works

### Workflow File
`.github/workflows/ci.yml` defines three jobs:

1. **backend-tests**: Runs pytest with PostgreSQL service
2. **frontend-tests**: Runs npm test and type checking
3. **lint**: Code quality checks for both backend and frontend

### Triggers
Tests run automatically on:
- Pushes to `main` or `develop` branches
- Pull requests targeting `main` or `develop`

## Viewing Results

### 1. GitHub Badge
The badge at the top of README.md shows current build status:
- ✅ Green = All tests passing
- ❌ Red = Tests failing
- 🟡 Yellow = Tests running

### 2. Actions Tab
Visit `https://github.com/alexkamer/personal_knowledge_assistant/actions` to see:
- All workflow runs
- Detailed logs for each job
- Test results and coverage reports

### 3. Pull Request Checks
When you create a PR, you'll see:
- ✅ Checkmarks when tests pass
- ❌ Red X when tests fail
- Click "Details" to see what failed

## Running Tests Locally

Before pushing, run the same tests locally:

```bash
# Backend tests (same as CI)
cd backend
uv run pytest tests/ -v

# Frontend tests (same as CI)
cd frontend
npm test -- --coverage --watchAll=false
npm run type-check
npm run lint
```

## Common Issues

### Backend Tests Failing

**Issue**: Database connection errors
```bash
# Solution: Ensure PostgreSQL is running
brew services start postgresql@18
```

**Issue**: Missing dependencies
```bash
# Solution: Reinstall dependencies
cd backend
uv sync
```

### Frontend Tests Failing

**Issue**: Type errors
```bash
# Solution: Run type check locally first
npm run type-check
```

**Issue**: Outdated snapshots
```bash
# Solution: Update snapshots
npm test -- -u
```

### CI-Specific Failures

If tests pass locally but fail in CI:

1. **Check environment variables**: CI uses mock values for API keys
2. **Check Node/Python versions**: CI uses specific versions (see workflow file)
3. **Check database setup**: CI uses `knowledge_assistant_test` database
4. **Review logs**: Click "Details" in the PR to see full error messages

## Modifying the Workflow

### Adding More Tests

Edit `.github/workflows/ci.yml`:

```yaml
- name: Run new test suite
  working-directory: ./backend
  run: |
    uv run pytest tests/new_tests/ -v
```

### Changing Node/Python Versions

Update the version numbers:

```yaml
- name: Set up Python 3.11
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'  # Change this
```

### Adding New Jobs

Add a new job to the workflow:

```yaml
jobs:
  backend-tests:
    # existing job...

  frontend-tests:
    # existing job...

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    steps:
      # your steps here...
```

## Coverage Reports

Coverage reports are uploaded as artifacts after each run:

1. Go to Actions tab
2. Click on a workflow run
3. Scroll down to "Artifacts"
4. Download `backend-coverage` or `frontend-coverage`
5. Open `index.html` in your browser

## Best Practices

### Before Committing
1. Run tests locally: `npm test` and `pytest`
2. Fix any failing tests
3. Run linters: `npm run lint` and `black`
4. Commit only when tests pass

### Pull Request Workflow
1. Create a feature branch: `git checkout -b feature-name`
2. Make changes and commit
3. Push: `git push origin feature-name`
4. Create PR on GitHub
5. Wait for CI checks to pass ✅
6. Merge when green

### Handling Failures
1. Click "Details" next to the failed check
2. Read the error logs
3. Fix the issue locally
4. Commit the fix
5. Push - CI will re-run automatically

## Disabling CI (Not Recommended)

If you need to skip CI for a commit (use sparingly):

```bash
git commit -m "docs: update README [skip ci]"
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

## Summary

GitHub Actions automatically ensures code quality by:
- ✅ Running all 825 tests on every push
- ✅ Checking code formatting and types
- ✅ Providing fast feedback (usually < 5 minutes)
- ✅ Preventing broken code from being merged

This saves time, reduces bugs, and gives confidence when making changes!
