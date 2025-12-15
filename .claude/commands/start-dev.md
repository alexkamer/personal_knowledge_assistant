# Start Development Servers

Start both the backend and frontend development servers.

## Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

## Access Points
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
