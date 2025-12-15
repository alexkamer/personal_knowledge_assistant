# Run Tests

Execute tests for both backend and frontend.

## Backend Tests
```bash
cd backend
source venv/bin/activate
pytest --cov=app --cov-report=html --cov-report=term-missing tests/
```

View coverage report: `open backend/htmlcov/index.html`

## Frontend Tests
```bash
cd frontend
npm test
```

With coverage:
```bash
npm run test:coverage
```

## Run All Tests
```bash
# Backend
cd backend && pytest && cd ..

# Frontend
cd frontend && npm test && cd ..
```
