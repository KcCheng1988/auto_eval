# Database Layer

This directory contains database schema definitions and initialization utilities.

## Single Source of Truth Principle

**⚠️ IMPORTANT: `schema_sqlite.sql` is the ONLY source of truth for database schema.**

### ❌ Anti-Pattern (Don't Do This)

```python
# BAD: Duplicating schema in repository code
class MyRepository:
    def __init__(self, db_path):
        self._init_tables()  # ❌ Schema defined in Python code

    def _init_tables(self):
        conn.execute('''
            CREATE TABLE IF NOT EXISTS my_table (...)  # ❌ Duplicate schema!
        ''')
```

**Problems:**
- Two sources of truth (SQL file AND Python code)
- Schema drift: SQL file updated but Python code forgotten
- Hard to maintain: Changes must be made in multiple places
- No version control: Can't track schema changes easily
- Migration nightmares: No clear migration path

### ✅ Correct Pattern (Do This)

```python
# GOOD: Repository only uses the database, doesn't create it
class MyRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        # NO _init_tables() method!
        # Schema is managed by DatabaseInitializer

    def create(self, entity):
        # Just use the database, assume schema exists
        conn = sqlite3.connect(self.db_path)
        # ... CRUD operations ...
```

**Benefits:**
- ✅ Single source of truth: `schema_sqlite.sql`
- ✅ Clear separation: Initialization vs. Usage
- ✅ Version control: SQL file tracks all schema changes
- ✅ Easier migrations: SQL-based migration files
- ✅ Database-agnostic repositories

---

## Files

### `schema_sqlite.sql`
**The single source of truth for database schema.**

Contains:
- Table definitions
- Indexes
- Triggers
- Views
- Default data
- Schema version tracking

**When to modify:**
- Adding/removing tables
- Changing column definitions
- Adding indexes
- Creating views

**How to apply changes:**
```bash
# Option 1: Auto-initialize on startup (development)
python -m proposed_architecture.database.database_initialization

# Option 2: Manual initialization (production)
sqlite3 evaluation.db < proposed_architecture/database/schema_sqlite.sql
```

### `schema.sql`
PostgreSQL schema (for future production deployment).
Currently SQLite is used for development/testing.

### `database_initialization.py`
**Database initialization utility.**

Provides three initialization strategies:

#### 1. One-Time Manual Initialization
```python
from proposed_architecture.database.database_initialization import DatabaseInitializer

# Run once during setup
initializer = DatabaseInitializer('data/evaluation.db')
initializer.initialize_once()
```

**Use when:**
- Initial project setup
- Development environment setup
- You want manual control

#### 2. Auto-Initialize on Startup (Recommended for Simple Apps)
```python
from proposed_architecture.database.database_initialization import initialize_on_app_startup

# In your main.py or FastAPI app
@app.on_event("startup")
async def startup():
    initialize_on_app_startup('data/evaluation.db')
    # Safe to call every time - uses CREATE TABLE IF NOT EXISTS
```

**Use when:**
- Simple applications
- Development/testing
- Docker containers (ephemeral databases)

**Benefits:**
- Idempotent (safe to run multiple times)
- No manual setup required
- Works with `CREATE TABLE IF NOT EXISTS` in schema

#### 3. Migration-Based (Recommended for Production)
```python
from proposed_architecture.database.database_initialization import DatabaseInitializer

# During deployment
initializer = DatabaseInitializer('data/evaluation.db')
initializer.apply_migrations()  # Applies only new migrations
```

**Use when:**
- Production deployments
- Team environments
- Need schema versioning
- Complex schema evolution

**Migration file structure:**
```
database/migrations/
├── 001_initial_schema.sql
├── 002_add_model_evaluation_table.sql
├── 003_add_state_history_indexes.sql
└── 004_add_quality_check_results.sql
```

**Creating a migration:**
```bash
# 1. Create migration file
cat > database/migrations/005_add_new_column.sql <<EOF
-- Add column to existing table
ALTER TABLE model_evaluations ADD COLUMN new_field TEXT;
EOF

# 2. Apply migration
python -m proposed_architecture.database.database_initialization --migrate
```

---

## Repository Initialization Pattern

### ❌ Old Pattern (Removed)

```python
# repositories/my_repository.py
class MyRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_tables()  # ❌ Each repository initializes its own tables

    def _init_tables(self):
        # Duplicate schema definition ❌
        conn.execute('CREATE TABLE IF NOT EXISTS ...')
```

### ✅ New Pattern (Current)

```python
# repositories/my_repository.py
class MyRepository:
    """
    Repository for managing X entities.

    Note: Database schema is managed by DatabaseInitializer,
    not by this repository. See database/schema_sqlite.sql.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        # No _init_tables() - schema managed centrally ✅

    def create(self, entity):
        # Just use the database ✅
        conn = sqlite3.connect(self.db_path)
        # ...
```

**Application startup:**

```python
# main.py or app.py
from proposed_architecture.database.database_initialization import initialize_on_app_startup

def startup():
    # Initialize database ONCE at application level
    initialize_on_app_startup('data/evaluation.db')

    # Now repositories can use the database
    from proposed_architecture.repositories import ModelEvaluationRepository
    model_repo = ModelEvaluationRepository('data/evaluation.db')
    # Schema already exists!
```

---

## Schema Evolution

### Making Schema Changes

1. **Update `schema_sqlite.sql`** (source of truth)
2. **Create migration file** (if using migration-based approach)
3. **Apply changes** (one of three methods below)

### Method 1: Recreate Database (Development Only!)

```bash
# ⚠️ WARNING: Destroys all data!
rm data/evaluation.db
python -m proposed_architecture.database.database_initialization
```

### Method 2: Manual SQL (Quick fixes)

```bash
sqlite3 data/evaluation.db
> ALTER TABLE model_evaluations ADD COLUMN new_field TEXT;
> .quit
```

Then update `schema_sqlite.sql` to match!

### Method 3: Migration File (Production)

```bash
# 1. Create migration file
cat > database/migrations/005_add_new_column.sql <<EOF
-- Migration: Add new_field to model_evaluations
ALTER TABLE model_evaluations ADD COLUMN new_field TEXT DEFAULT '';
UPDATE model_evaluations SET new_field = 'default_value';
EOF

# 2. Update schema_sqlite.sql to include new column

# 3. Apply migration
python -m proposed_architecture.database.database_initialization --migrate
```

---

## CLI Usage

```bash
# Initialize database
python -m proposed_architecture.database.database_initialization

# Force recreate (⚠️ destroys data!)
python -m proposed_architecture.database.database_initialization --force

# Apply migrations
python -m proposed_architecture.database.database_initialization --migrate

# Check schema version
python -m proposed_architecture.database.database_initialization --version
```

---

## Schema Version Tracking

The `schema_migrations` table tracks all schema changes:

```sql
SELECT * FROM schema_migrations;
```

Output:
```
id | version | name                      | applied_at          | checksum
---+---------+---------------------------+---------------------+---------
1  | 1.0.0   | initial_schema            | 2024-01-15 10:30:00 | abc123
2  | 2.0.0   | add_model_evaluation      | 2024-01-20 14:15:00 | def456
3  | 3.0.0   | add_state_history_indexes | 2024-01-25 09:00:00 | ghi789
```

---

## Best Practices

### ✅ DO

1. **Always update `schema_sqlite.sql` first** - It's the source of truth
2. **Use migration files for production** - Track schema evolution
3. **Initialize database at application level** - Not in repositories
4. **Document schema changes** - Use migration file comments
5. **Version your schema** - Track in `schema_migrations` table
6. **Test migrations on copy of production data** - Before deploying

### ❌ DON'T

1. **Don't duplicate schema in repository code** - Single source of truth!
2. **Don't initialize tables in `__init__()`** - Separation of concerns
3. **Don't modify production database manually** - Use migrations
4. **Don't forget to update schema.sql** - After manual changes
5. **Don't delete migration files** - They're your schema history
6. **Don't run destructive operations in production** - Back up first!

---

## Troubleshooting

### "Table doesn't exist" error

```python
# Problem: Repository expects table that doesn't exist
# Solution: Initialize database first

from proposed_architecture.database.database_initialization import initialize_on_app_startup
initialize_on_app_startup('data/evaluation.db')
```

### Schema drift (SQL file doesn't match database)

```bash
# Option 1: Recreate database (development only, loses data!)
rm data/evaluation.db
python -m proposed_architecture.database.database_initialization

# Option 2: Compare and fix manually
sqlite3 data/evaluation.db .schema > actual_schema.sql
diff actual_schema.sql database/schema_sqlite.sql
# Fix differences manually
```

### Migration failed midway

```sql
-- Check schema_migrations to see what was applied
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- If migration failed, it won't be recorded
-- Fix the migration file and try again
```

---

## Related Documentation

- [Repositories](../repositories/README.md) - Data access layer
- [Domain](../domain/README.md) - Domain models
- [Services](../services/README.md) - Business logic layer
