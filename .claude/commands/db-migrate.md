# Database Migrations

Manage database schema with Alembic.

## Create a New Migration
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "description of changes"
```

## Apply Migrations
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## Rollback Last Migration
```bash
cd backend
source venv/bin/activate
alembic downgrade -1
```

## View Migration History
```bash
cd backend
source venv/bin/activate
alembic history
```

## Check Current Version
```bash
cd backend
source venv/bin/activate
alembic current
```

## Reset Database (DESTRUCTIVE)
```bash
dropdb knowledge_assistant
createdb knowledge_assistant
cd backend
alembic upgrade head
```
