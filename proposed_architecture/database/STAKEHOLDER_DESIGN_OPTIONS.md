# Multiple Stakeholders Design Options

## The Question
"There may be multiple stakeholders in a use case. How can I include their emails in the use_cases table?"

## Three Approaches

### Option 1: JSON Array in use_cases Table (Simplest)

**Store multiple emails as JSON in existing column**

```sql
-- Modify use_cases table
ALTER TABLE use_cases
RENAME COLUMN team_email TO stakeholder_emails;

-- Now store as JSON array
INSERT INTO use_cases (id, name, stakeholder_emails, ...) VALUES
    ('uc_123', 'Invoice Extraction',
     '["alice@company.com", "bob@company.com", "carol@company.com"]', ...);
```

**Pros:**
- ✅ Simple - no schema changes needed
- ✅ Quick to implement
- ✅ Works for most use cases

**Cons:**
- ❌ Hard to query "all use cases for alice@company.com"
- ❌ No referential integrity
- ❌ Can't easily add stakeholder metadata (role, name, etc.)

**When to use:**
- Simple notifications only
- Small number of stakeholders (< 5)
- Don't need to query by stakeholder

---

### Option 2: Separate Stakeholders Table (RECOMMENDED)

**Create dedicated table with many-to-many relationship**

```sql
-- Stakeholders table
CREATE TABLE IF NOT EXISTS stakeholders (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT,  -- 'team_lead', 'data_scientist', 'reviewer', etc.
    created_at TEXT DEFAULT (datetime('now'))
);

-- Junction table (many-to-many)
CREATE TABLE IF NOT EXISTS use_case_stakeholders (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    role_in_use_case TEXT,  -- Role specific to this use case
    is_primary_contact INTEGER DEFAULT 0,  -- Flag primary contact
    added_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
    UNIQUE(use_case_id, stakeholder_id)  -- No duplicates
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_use_case
    ON use_case_stakeholders(use_case_id);
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_stakeholder
    ON use_case_stakeholders(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_stakeholders_email
    ON stakeholders(email);
```

**Example Usage:**

```sql
-- Insert stakeholders
INSERT INTO stakeholders (id, email, name, role) VALUES
    ('s1', 'alice@company.com', 'Alice Smith', 'team_lead'),
    ('s2', 'bob@company.com', 'Bob Jones', 'data_scientist'),
    ('s3', 'carol@company.com', 'Carol Davis', 'reviewer');

-- Link stakeholders to use case
INSERT INTO use_case_stakeholders (id, use_case_id, stakeholder_id, role_in_use_case, is_primary_contact) VALUES
    ('us1', 'uc_123', 's1', 'Project Owner', 1),  -- Primary
    ('us2', 'uc_123', 's2', 'ML Engineer', 0),
    ('us3', 'uc_123', 's3', 'QA Reviewer', 0);

-- Query: Get all stakeholders for a use case
SELECT s.email, s.name, ucs.role_in_use_case, ucs.is_primary_contact
FROM use_case_stakeholders ucs
JOIN stakeholders s ON ucs.stakeholder_id = s.id
WHERE ucs.use_case_id = 'uc_123';

-- Query: Get all use cases for a stakeholder
SELECT u.id, u.name, ucs.role_in_use_case
FROM use_case_stakeholders ucs
JOIN use_cases u ON ucs.use_case_id = u.id
WHERE ucs.stakeholder_id = 's1';

-- Query: Get primary contact for use case
SELECT s.email, s.name
FROM use_case_stakeholders ucs
JOIN stakeholders s ON ucs.stakeholder_id = s.id
WHERE ucs.use_case_id = 'uc_123' AND ucs.is_primary_contact = 1;
```

**Pros:**
- ✅ Proper normalization
- ✅ Easy to query by stakeholder
- ✅ Can store stakeholder metadata
- ✅ Referential integrity
- ✅ Can track role changes over time
- ✅ Reuse stakeholders across use cases

**Cons:**
- ⚠️ More complex schema
- ⚠️ More tables to join

**When to use:**
- Need to query by stakeholder
- Want stakeholder profiles
- Multiple use cases share stakeholders
- Need audit trail of who's involved

---

### Option 3: Hybrid Approach

**Keep primary contact in use_cases, add stakeholders table for others**

```sql
-- use_cases keeps primary contact
CREATE TABLE use_cases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    primary_contact_email TEXT NOT NULL,  -- Main person
    primary_contact_name TEXT,
    ...
);

-- Additional stakeholders in separate table
CREATE TABLE additional_stakeholders (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    email TEXT NOT NULL,
    name TEXT,
    role TEXT,
    notification_preference TEXT,  -- 'all', 'summary', 'failures_only'
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE
);
```

**Pros:**
- ✅ Fast access to primary contact
- ✅ Flexible for additional stakeholders
- ✅ Simpler than full many-to-many

**Cons:**
- ⚠️ Duplication if primary contact changes
- ⚠️ Stakeholder data not reusable

**When to use:**
- Always have one main contact
- Additional stakeholders vary widely
- Want simple primary contact access

---

## Recommendation: Option 2 (Stakeholders Table)

Here's why:

### Use Case Scenarios

**Scenario 1: Send notification email**
```python
def send_quality_check_notification(use_case_id, issues):
    # Get all stakeholders
    stakeholders = get_stakeholders_for_use_case(use_case_id)

    for stakeholder in stakeholders:
        if stakeholder.role_in_use_case == 'QA Reviewer':
            # Send detailed report
            send_email(stakeholder.email, detailed_report)
        else:
            # Send summary
            send_email(stakeholder.email, summary)
```

**Scenario 2: User dashboard**
```python
def get_my_use_cases(user_email):
    # Show all use cases where I'm a stakeholder
    return db.query("""
        SELECT u.*, ucs.role_in_use_case
        FROM use_cases u
        JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id
        JOIN stakeholders s ON ucs.stakeholder_id = s.id
        WHERE s.email = ?
    """, user_email)
```

**Scenario 3: Access control**
```python
def can_upload_dataset(user_email, use_case_id):
    stakeholder = get_stakeholder_for_use_case(user_email, use_case_id)
    return stakeholder and stakeholder.role_in_use_case in ['Project Owner', 'ML Engineer']
```

---

## Updated Schema (Option 2)

```sql
-- ============================================================================
-- Stakeholder Management Tables
-- ============================================================================

-- Stakeholders table - Reusable across use cases
CREATE TABLE IF NOT EXISTS stakeholders (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT,  -- General role: 'data_scientist', 'ml_engineer', 'reviewer'
    department TEXT,
    notification_enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Use case stakeholders junction table
CREATE TABLE IF NOT EXISTS use_case_stakeholders (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    role_in_use_case TEXT NOT NULL,  -- Specific role: 'Project Owner', 'Contributor'
    is_primary_contact INTEGER DEFAULT 0,
    permissions TEXT DEFAULT '{}',  -- JSON: {'can_upload': true, 'can_approve': false}
    added_at TEXT DEFAULT (datetime('now')),
    added_by TEXT,  -- Who added this stakeholder
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
    UNIQUE(use_case_id, stakeholder_id)
);

-- Notification history (track what was sent to whom)
CREATE TABLE IF NOT EXISTS stakeholder_notifications (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    notification_type TEXT NOT NULL,  -- 'qc_failed', 'eval_complete', etc.
    sent_at TEXT DEFAULT (datetime('now')),
    status TEXT,  -- 'sent', 'failed', 'bounced'
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stakeholders_email ON stakeholders(email);
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_use_case
    ON use_case_stakeholders(use_case_id);
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_stakeholder
    ON use_case_stakeholders(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_primary
    ON use_case_stakeholders(use_case_id, is_primary_contact);

-- Trigger to update timestamp
CREATE TRIGGER IF NOT EXISTS update_stakeholders_timestamp
AFTER UPDATE ON stakeholders
BEGIN
    UPDATE stakeholders SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- Convenient Views
-- ============================================================================

-- View: Use cases with primary contact
CREATE VIEW IF NOT EXISTS v_use_cases_with_contact AS
SELECT
    u.*,
    s.email as primary_contact_email,
    s.name as primary_contact_name,
    s.role as primary_contact_role
FROM use_cases u
LEFT JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id AND ucs.is_primary_contact = 1
LEFT JOIN stakeholders s ON ucs.stakeholder_id = s.id;

-- View: All stakeholders per use case
CREATE VIEW IF NOT EXISTS v_use_case_team AS
SELECT
    u.id as use_case_id,
    u.name as use_case_name,
    s.id as stakeholder_id,
    s.email,
    s.name as stakeholder_name,
    ucs.role_in_use_case,
    ucs.is_primary_contact,
    ucs.added_at
FROM use_cases u
JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id
JOIN stakeholders s ON ucs.stakeholder_id = s.id
ORDER BY u.name, ucs.is_primary_contact DESC, s.name;
```

---

## Migration Path

If you already have data with single `team_email`:

```sql
-- Step 1: Migrate existing emails to stakeholders table
INSERT INTO stakeholders (id, email, name, role)
SELECT
    lower(hex(randomblob(16))) as id,
    team_email as email,
    team_email as name,  -- Use email as name initially
    'team_lead' as role
FROM use_cases
WHERE team_email IS NOT NULL
ON CONFLICT(email) DO NOTHING;

-- Step 2: Create use_case_stakeholders entries
INSERT INTO use_case_stakeholders (id, use_case_id, stakeholder_id, role_in_use_case, is_primary_contact)
SELECT
    lower(hex(randomblob(16))) as id,
    u.id as use_case_id,
    s.id as stakeholder_id,
    'Project Owner' as role_in_use_case,
    1 as is_primary_contact
FROM use_cases u
JOIN stakeholders s ON u.team_email = s.email;

-- Step 3: (Optional) Drop old column after verification
-- ALTER TABLE use_cases DROP COLUMN team_email;
```

---

## Code Examples

### Repository Methods

```python
class UseCaseRepository:

    def add_stakeholder(
        self,
        use_case_id: str,
        email: str,
        name: str,
        role_in_use_case: str,
        is_primary: bool = False
    ):
        """Add stakeholder to use case"""
        # Create or get stakeholder
        stakeholder = self._get_or_create_stakeholder(email, name)

        # Link to use case
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO use_case_stakeholders
            (id, use_case_id, stakeholder_id, role_in_use_case, is_primary_contact)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), use_case_id, stakeholder.id, role_in_use_case, 1 if is_primary else 0))

        conn.commit()
        conn.close()

    def get_stakeholders(self, use_case_id: str) -> List[Dict]:
        """Get all stakeholders for a use case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.id, s.email, s.name, ucs.role_in_use_case, ucs.is_primary_contact
            FROM use_case_stakeholders ucs
            JOIN stakeholders s ON ucs.stakeholder_id = s.id
            WHERE ucs.use_case_id = ?
            ORDER BY ucs.is_primary_contact DESC
        ''', (use_case_id,))

        stakeholders = []
        for row in cursor.fetchall():
            stakeholders.append({
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'role': row[3],
                'is_primary': bool(row[4])
            })

        conn.close()
        return stakeholders

    def get_primary_contact(self, use_case_id: str) -> Optional[Dict]:
        """Get primary contact for use case"""
        stakeholders = self.get_stakeholders(use_case_id)
        for s in stakeholders:
            if s['is_primary']:
                return s
        return stakeholders[0] if stakeholders else None
```

### Email Service

```python
class EmailService:

    def send_quality_check_notification(self, use_case_id: str, issues: List):
        """Send notification to all stakeholders"""
        stakeholders = self.use_case_repo.get_stakeholders(use_case_id)

        for stakeholder in stakeholders:
            # Customize email based on role
            if stakeholder['is_primary']:
                subject = f"[Action Required] Quality Check Failed"
                body = self._render_detailed_report(issues)
            else:
                subject = f"[FYI] Quality Check Failed"
                body = self._render_summary(issues)

            self.send_email(
                to=stakeholder['email'],
                subject=subject,
                body=body
            )

            # Log notification
            self._log_notification(use_case_id, stakeholder['id'], 'qc_failed')
```

---

## Summary

**Recommended: Option 2 (Stakeholders Table)**

**Benefits:**
- ✅ Properly normalized
- ✅ Reusable stakeholder profiles
- ✅ Easy to query in both directions
- ✅ Supports roles and permissions
- ✅ Scalable to many stakeholders
- ✅ Audit trail of team changes

**Implementation:**
1. Add `stakeholders` table
2. Add `use_case_stakeholders` junction table
3. Add convenience views
4. Update repository methods
5. Migrate existing `team_email` data

This gives you maximum flexibility for future requirements!
