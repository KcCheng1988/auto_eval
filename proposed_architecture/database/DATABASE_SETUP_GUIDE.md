# Database Setup Guide

## Your Question: "Is schema_sqlite.sql triggered just once?"

**Answer**: **It depends on your strategy!** There are three main approaches:

---

## Approach 1: Manual One-Time Setup (Simplest)

### When to Use

- Development/testing
- Proof-of-concept
- Small projects
- You want manual control

### How It Works

**Run the schema file ONCE manually when setting up:**

```bash
# Option 1: Using sqlite3 command line
sqlite3 evaluation.db < database/schema_sqlite.sql

# Option 2: Using Python script
python -c "from database.database_initialization import DatabaseInitializer; \
           DatabaseInitializer('evaluation.db').initialize_once()"

# Option 3: Using provided CLI
python database/database_initialization.py
```

### Characteristics

- ✅ Simple and explicit
- ✅ Full control over when schema is created
- ❌ Must remember to run on new environments
- ❌ Manual process for new developers
- ❌ No schema versioning

### When Schema Runs

**Once** - When you manually execute it

---

## Approach 2: Auto-Initialize on Startup (Recommended for Simple Apps)

### When to Use

- Small to medium applications
- Development environments
- When you want "it just works" behavior
- Single-server deployments

### How It Works

**Schema runs automatically on first startup:**

```python
# In your main.py or app.py
from database.database_initialization import initialize_on_app_startup

@app.on_event("startup")
async def startup():
    # This runs every time the app starts
    initialize_on_app_startup('data/evaluation.db')
    # But only creates tables if they don't exist!
```

### Why It's Safe

The schema uses `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS use_cases (...);
CREATE TABLE IF NOT EXISTS models (...);
```

**First startup**: Tables don't exist → Creates all tables
**Subsequent startups**: Tables exist → Does nothing

### Characteristics

- ✅ Zero manual setup required
- ✅ Works automatically in new environments
- ✅ Safe to call multiple times (idempotent)
- ✅ New developers just run the app
- ⚠️ No schema change tracking
- ⚠️ Harder to manage schema changes

### When Schema Runs

**Every startup** - But only creates missing tables

---

## Approach 3: Version-Controlled Migrations (RECOMMENDED for Production)

### When to Use

- Production environments
- Team projects
- When schema evolves over time
- Multi-server deployments
- Need audit trail of changes

### How It Works

**Schema is split into versioned migration files:**

```
database/
├── migrations/
│   ├── 001_initial_schema.sql        ← First version
│   ├── 002_add_model_evaluations.sql ← Added later
│   ├── 003_add_state_history.sql     ← Added even later
│   └── 004_add_indexes.sql           ← Latest
└── schema_sqlite.sql                  ← Still used for reference
```

Each migration runs **once and only once**:

```python
from database.database_initialization import DatabaseInitializer

# During deployment or startup
db_init = DatabaseInitializer('evaluation.db')
db_init.apply_migrations()  # Runs only new migrations
```

### Migration Tracking Table

```sql
-- Automatically created
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,    -- "001", "002", "003"
    name TEXT NOT NULL,               -- Migration description
    applied_at TEXT NOT NULL,         -- When it was run
    checksum TEXT NOT NULL,           -- Integrity check
    execution_time_ms INTEGER         -- How long it took
);
```

**Example**:

```sql
sqlite> SELECT * FROM schema_migrations;

version | name                    | applied_at          | execution_time_ms
--------|-------------------------|---------------------|------------------
001     | initial_schema          | 2024-01-15 10:00:00 | 45
002     | add_model_evaluations   | 2024-01-20 09:15:00 | 23
003     | add_state_history       | 2024-02-01 14:30:00 | 18
```

### How Migrations Work

#### Server 1 (First Deployment):

```
1. apply_migrations() called
2. Check schema_migrations table: empty
3. Run migration 001 ✓
4. Run migration 002 ✓
5. Run migration 003 ✓
6. Record all in schema_migrations
```

#### Server 1 (Second Deployment - New Migration Added):

```
1. apply_migrations() called
2. Check schema_migrations: has [001, 002, 003]
3. Skip migration 001 (already applied)
4. Skip migration 002 (already applied)
5. Skip migration 003 (already applied)
6. Run migration 004 ✓ (NEW!)
7. Record 004 in schema_migrations
```

#### Server 2 (Fresh Install):

```
1. apply_migrations() called
2. Check schema_migrations: empty (new database)
3. Run migration 001 ✓
4. Run migration 002 ✓
5. Run migration 003 ✓
6. Run migration 004 ✓
7. Record all in schema_migrations
```

### Characteristics

- ✅ Full audit trail of schema changes
- ✅ Safe for multiple servers
- ✅ Rollback capability
- ✅ Team-friendly (changes in version control)
- ✅ Prevents duplicate application
- ⚠️ Requires more setup
- ⚠️ Need to create migration files

### When Schema Runs

**Each migration runs once** - Tracked in schema_migrations table

---

## Comparison Table

| Feature                 | Manual Once | Auto-Initialize | Migrations |
| ----------------------- | ----------- | --------------- | ---------- |
| **Setup Complexity**    | Very Simple | Simple          | Medium     |
| **Suitable For**        | Development | Small Apps      | Production |
| **Schema Tracking**     | ❌ No       | ❌ No           | ✅ Yes     |
| **Audit Trail**         | ❌ No       | ❌ No           | ✅ Yes     |
| **Multi-Server Safe**   | ⚠️ Manual   | ⚠️ Mostly       | ✅ Yes     |
| **Schema Evolution**    | ❌ Hard     | ⚠️ Medium       | ✅ Easy    |
| **New Developer Setup** | Manual      | Automatic       | Automatic  |
| **Deployment Process**  | Manual      | Automatic       | Automatic  |

---

## Recommended Strategy by Environment

### Development

```python
# In main.py
from database.database_initialization import initialize_on_app_startup

@app.on_event("startup")
async def startup():
    initialize_on_app_startup('data/evaluation_dev.db')
```

**Why**: Auto-initialize = zero friction for developers

### Staging/Testing

```python
# In deployment script
from database.database_initialization import DatabaseInitializer

db_init = DatabaseInitializer('data/evaluation_staging.db')
db_init.apply_migrations()  # Runs pending migrations
```

**Why**: Test migrations before production

### Production

```python
# In deployment pipeline
from database.database_initialization import initialize_for_production

initialize_for_production()  # Full migration tracking
```

**Why**: Full audit trail, rollback capability, multi-server safe

---

## Creating New Migrations

### Step 1: Create Migration File

```bash
# Naming: {version}_{description}.sql
touch database/migrations/004_add_quality_check_cache.sql
```

### Step 2: Write Migration SQL

```sql
-- database/migrations/004_add_quality_check_cache.sql

-- Add new table
CREATE TABLE IF NOT EXISTS quality_check_cache (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    dataset_checksum TEXT NOT NULL,
    cached_issues TEXT,  -- JSON
    cached_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_evaluations(id)
);

-- Add index
CREATE INDEX IF NOT EXISTS idx_qc_cache_model
ON quality_check_cache(model_id);

-- Add new column to existing table
ALTER TABLE model_evaluations
ADD COLUMN last_qc_cache_hit TEXT;
```

### Step 3: Apply Migration

```bash
# Development
python database/database_initialization.py --migrate

# Or in code
from database.database_initialization import DatabaseInitializer
db_init = DatabaseInitializer('evaluation.db')
db_init.apply_migrations()
```

### Step 4: Verify

```python
db_init = DatabaseInitializer('evaluation.db')
history = db_init.get_migration_history()

for entry in history:
    print(f"{entry['version']}: {entry['name']} - {entry['applied_at']}")

# Output:
# 001: initial_schema - 2024-01-15 10:00:00
# 002: add_model_evaluations - 2024-01-20 09:15:00
# 003: add_state_history - 2024-02-01 14:30:00
# 004: add_quality_check_cache - 2024-02-10 11:45:00  ← NEW!
```

---

## Common Questions

### Q: What if I change schema_sqlite.sql after initial setup?

**Manual/Auto-Initialize**: Changes won't be applied automatically. You'd need to:

- Drop and recreate database (loses data!)
- Or manually run ALTER TABLE commands

**Migrations**: Create a new migration file with the changes. It will be applied automatically.

### Q: Can I use both schema_sqlite.sql and migrations?

**Yes!** Common pattern:

1. `001_initial_schema.sql` = copy of `schema_sqlite.sql`
2. Future changes go in `002_xxx.sql`, `003_xxx.sql`, etc.
3. Keep `schema_sqlite.sql` as reference documentation

### Q: What happens if migration fails halfway?

**With transactions**: Changes are rolled back

```python
try:
    conn.executescript(migration_sql)  # Atomic
    conn.commit()
except:
    conn.rollback()  # Undo everything
```

### Q: How do I rollback a migration?

**Option 1**: Create reverse migration

```sql
-- 005_rollback_cache_table.sql
DROP TABLE IF EXISTS quality_check_cache;

ALTER TABLE model_evaluations DROP COLUMN last_qc_cache_hit;
```

**Option 2**: Restore from backup

```bash
cp data/evaluation.db.backup data/evaluation.db
```

### Q: Multiple servers running at once?

**Migrations approach is safe:**

- SQLite uses file locking
- First server to run migration wins
- Other servers wait or skip (already applied)

**For high concurrency, consider PostgreSQL instead of SQLite.**

---

## Complete Setup Examples

### Example 1: Quick Start (Development)

```python
# main.py
from fastapi import FastAPI
from database.database_initialization import initialize_on_app_startup

app = FastAPI()

@app.on_event("startup")
async def startup():
    # This line does everything!
    initialize_on_app_startup('data/evaluation.db')
    print("✓ Database ready")

# Just run: python main.py
# Database auto-created on first run!
```

### Example 2: Production Deployment

```python
# deploy.py
from database.database_initialization import DatabaseInitializer

def deploy():
    print("1. Applying database migrations...")
    db_init = DatabaseInitializer('data/evaluation_prod.db')
    db_init.apply_migrations()

    print("2. Verifying schema...")
    if not db_init.verify_schema():
        raise RuntimeError("Schema verification failed!")

    print("3. Checking version...")
    version = db_init.get_schema_version()
    print(f"✓ Database ready (version: {version})")

    print("4. Starting application...")
    # Start FastAPI server

if __name__ == '__main__':
    deploy()
```

### Example 3: CLI Management

```bash
# Check current version
python database/database_initialization.py --version
# Output: Schema version: 003

# Apply new migrations
python database/database_initialization.py --migrate
# Output: ✓ Migration 004 applied successfully (23ms)

# Force recreate (development only!)
python database/database_initialization.py --force
# Output: ✓ Database recreated
```

---

## Best Practices

### ✅ DO:

- Use migrations for production
- Track all schema changes in version control
- Test migrations on staging first
- Keep migration files immutable (never edit after applying)
- Back up database before migrations
- Use descriptive migration names

### ❌ DON'T:

- Edit applied migration files
- Skip migration versions
- Run schema_sqlite.sql directly in production
- Modify schema manually in production
- Delete migration tracking table

---

## Summary

**Your Question**: "Is schema_sqlite.sql triggered just once?"

**Answer**:

1. **Manual approach**: Yes, you run it once manually
2. **Auto-initialize**: Runs on every startup, but `IF NOT EXISTS` makes it safe
3. **Migrations**: Split into versioned files, each runs once (tracked in DB)

**Recommendation**:

- **Development**: Auto-initialize (approach #2)
- **Production**: Migrations (approach #3)

The `schema_sqlite.sql` file serves as:

- Initial schema for approach #1 and #2
- Template for migration #001 in approach #3
- Reference documentation of current schema

Choose based on your needs! For most production systems, **migrations (#3) is the best choice**.
