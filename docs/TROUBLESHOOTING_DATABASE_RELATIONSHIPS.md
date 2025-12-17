# Troubleshooting: SQLAlchemy Circular Relationship Issues

## Problem Summary

When adding a new model (`ConceptualSnapshot`) with a bidirectional relationship to an existing model (`Conversation`), the backend failed to start with the error:

```
sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize - can't proceed with initialization of other mappers. Triggering mapper: 'Mapper[Conversation(conversations)]'. Original exception was: When initializing mapper Mapper[Conversation(conversations)], expression 'ConceptualSnapshot' failed to locate a name ('ConceptualSnapshot'). If this is a class name, consider adding this relationship() to the <class 'app.models.conversation.Conversation'> class after both dependent classes have been defined.
```

This occurred even after importing `ConceptualSnapshot` before `Conversation` in `app/models/__init__.py`.

## Root Cause

**Bidirectional relationships with `back_populates` create circular dependencies** that SQLAlchemy sometimes cannot resolve, especially when:
1. Both models use string references in `relationship()`
2. Models are in separate files
3. The import order matters but doesn't always fix the issue

## The Solution: Remove Unnecessary Back-Relationship

Instead of having bidirectional relationships:

```python
# ❌ CAUSES ISSUES - Bidirectional with back_populates

# In conversation.py
class Conversation(Base):
    conceptual_snapshots: Mapped[list["ConceptualSnapshot"]] = relationship(
        "ConceptualSnapshot",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

# In conceptual_snapshot.py
class ConceptualSnapshot(Base):
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="conceptual_snapshots")
```

Use a **unidirectional relationship** from the child model only:

```python
# ✅ WORKS - Unidirectional relationship

# In conversation.py
class Conversation(Base):
    # No relationship to ConceptualSnapshot defined here
    pass

# In conceptual_snapshot.py
class ConceptualSnapshot(Base):
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    conversation = relationship("Conversation")  # No back_populates
```

## Why This Works

1. **No circular dependency**: `Conversation` doesn't need to know about `ConceptualSnapshot`
2. **One-way navigation**: You can still access `snapshot.conversation`, which is all you need
3. **Querying backwards works fine**: You can still query from `Conversation` to `ConceptualSnapshot`:
   ```python
   snapshots = await db.execute(
       select(ConceptualSnapshot)
       .where(ConceptualSnapshot.conversation_id == conversation.id)
   )
   ```

## Additional Issues Encountered & Fixed

### Issue 1: Foreign Key Type Mismatch

**Error**:
```
asyncpg.exceptions.DatatypeMismatchError: foreign key constraint "conceptual_snapshots_conversation_id_fkey" cannot be implemented
DETAIL: Key columns "conversation_id" and "id" are of incompatible types: uuid and character varying.
```

**Cause**:
- The `ConceptualSnapshot` model used `UUID` for `conversation_id`
- But the `conversations.id` column was actually `VARCHAR(36)`

**Fix**:
```python
# ❌ WRONG - Type mismatch
conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"))

# ✅ CORRECT - Match the target column type
conversation_id = Column(String(36), ForeignKey("conversations.id"))
```

**Lesson**: Always check the actual database schema before creating foreign keys:
```bash
psql -d knowledge_assistant -c "\d conversations"
```

### Issue 2: Empty Migration Generated

**Problem**: Running `alembic revision --autogenerate` created an empty migration with no table creation code.

**Cause**: SQLAlchemy couldn't see the model due to the circular import issue.

**Fix**:
1. First fix the import/relationship issues
2. Then either:
   - Re-generate the migration after fixing imports, OR
   - Manually write the migration if autogenerate still fails

## Step-by-Step Debugging Process

When you encounter similar issues, follow these steps:

### 1. Check Database Schema

Before creating foreign keys, verify the target column type:

```bash
psql -d knowledge_assistant -c "\d parent_table_name"
```

Look for:
- Column type (UUID vs VARCHAR vs INTEGER)
- Column name spelling
- Whether column is nullable

### 2. Fix Type Mismatches

Match your foreign key type to the target column:

```python
# If target is VARCHAR(36):
conversation_id = Column(String(36), ForeignKey("conversations.id"))

# If target is UUID:
conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"))

# If target is INTEGER:
conversation_id = Column(Integer, ForeignKey("parent_table.id"))
```

### 3. Simplify Relationships

Remove `back_populates` if not absolutely necessary:

```python
# Instead of bidirectional:
conversation = relationship("Conversation", back_populates="snapshots")

# Use unidirectional:
conversation = relationship("Conversation")
```

### 4. Check Import Order

Ensure new models are imported in `app/models/__init__.py`:

```python
from app.models.conceptual_snapshot import ConceptualSnapshot

__all__ = [
    # ... other models ...
    "ConceptualSnapshot",
]
```

### 5. Manually Write Migration if Needed

If `alembic revision --autogenerate` generates empty migrations:

```python
def upgrade() -> None:
    op.create_table(
        'table_name',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('foreign_key_id', sa.String(length=36), nullable=False),
        # ... other columns ...
        sa.ForeignKeyConstraint(['foreign_key_id'], ['parent_table.id']),
        sa.PrimaryKeyConstraint('id')
    )
```

### 6. Test the Migration

```bash
source venv/bin/activate
alembic upgrade head
```

### 7. Restart Backend

```bash
# Kill old process
lsof -ti:8000 | xargs kill -9

# Start fresh
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 8. Verify API Works

```bash
curl -sL "http://localhost:8000/api/v1/endpoint/" | python3 -c "import json, sys; print(json.load(sys.stdin))"
```

## Prevention Tips

### 1. Use Unidirectional Relationships by Default

Only add bidirectional relationships when you **need** to navigate from both directions in your code.

### 2. Match Database Types Carefully

When creating foreign keys, always:
1. Check the target table schema first
2. Use the exact same type
3. Test the migration on a copy of the database first

### 3. Test Imports Early

After creating a new model:
1. Import it in `__init__.py`
2. Restart the backend immediately
3. Check for import errors before writing migrations

### 4. Keep Migrations Simple

If autogenerate fails:
1. Don't spend time debugging why
2. Just write the migration manually
3. It's faster and you have full control

## Quick Reference: Common Patterns

### Pattern 1: One-to-Many Relationship (Recommended)

```python
# Parent Model (e.g., Conversation)
class Parent(Base):
    __tablename__ = "parents"
    id = Column(String(36), primary_key=True)
    # No relationship defined here

# Child Model (e.g., ConceptualSnapshot)
class Child(Base):
    __tablename__ = "children"
    id = Column(String(36), primary_key=True)
    parent_id = Column(String(36), ForeignKey("parents.id"), nullable=False)
    parent = relationship("Parent")  # One-way only

# Usage:
# Access parent from child: child.parent
# Access children from parent: db.execute(select(Child).where(Child.parent_id == parent.id))
```

### Pattern 2: Bidirectional (Use Only When Necessary)

```python
# Parent Model
class Parent(Base):
    __tablename__ = "parents"
    id = Column(String(36), primary_key=True)
    children = relationship("Child", back_populates="parent")

# Child Model
class Child(Base):
    __tablename__ = "children"
    id = Column(String(36), primary_key=True)
    parent_id = Column(String(36), ForeignKey("parents.id"))
    parent = relationship("Parent", back_populates="children")

# IMPORTANT: Ensure both models are imported BEFORE any model that uses them
```

## Time Saved

This debugging took approximately **30 minutes** due to:
1. Mismatched UUID vs VARCHAR types (10 min)
2. Empty migrations (5 min)
3. Circular import issues (15 min)

Following this guide should reduce similar issues to **< 5 minutes**.

## Summary

**The Golden Rule**: When adding a new model with a relationship to an existing model:

1. ✅ **Check target column type first** (`\d table_name`)
2. ✅ **Use unidirectional relationships** (no `back_populates`)
3. ✅ **Import new model in `__init__.py`**
4. ✅ **Write migration manually** if autogenerate fails
5. ✅ **Test immediately** after each step

**Don't**:
- ❌ Assume column types match your expectations
- ❌ Add bidirectional relationships by default
- ❌ Spend time debugging autogenerate failures
- ❌ Make multiple changes before testing

---

**Last Updated**: 2025-12-16
**Issue Context**: Adding ConceptualSnapshot model for Knowledge Evolution Timeline (Innovation 5)
