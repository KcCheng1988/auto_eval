# SQLite Quick Reference Cheatsheet

## 📚 Table of Contents
- [Data Types](#data-types)
- [Creating Tables](#creating-tables)
- [Inserting Data](#inserting-data)
- [Querying Data](#querying-data)
- [Updating Data](#updating-data)
- [Deleting Data](#deleting-data)
- [Constraints](#constraints)
- [Indexes](#indexes)
- [JOINs](#joins)
- [Aggregations](#aggregations)
- [Common Functions](#common-functions)
- [Python sqlite3](#python-sqlite3)

---

## Data Types

```sql
INTEGER         -- Whole numbers: 1, 42, -100
REAL            -- Floating point: 3.14, -0.5
TEXT            -- Strings: 'hello', "world"
BLOB            -- Binary data
NULL            -- Empty value
```

---

## Creating Tables

### Basic Table
```sql
CREATE TABLE users (
    id INTEGER,
    name TEXT,
    email TEXT
);
```

### With Constraints
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER CHECK(age >= 18),
    created_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);
```

### Drop Table
```sql
DROP TABLE IF EXISTS users;
```

### Check if Table Exists
```sql
SELECT name FROM sqlite_master
WHERE type='table' AND name='users';
```

---

## Inserting Data

### Single Row
```sql
INSERT INTO users (name, email, age)
VALUES ('Alice', 'alice@example.com', 25);
```

### Multiple Rows
```sql
INSERT INTO users (name, email, age) VALUES
    ('Bob', 'bob@example.com', 30),
    ('Charlie', 'charlie@example.com', 28);
```

### Insert or Ignore (skip duplicates)
```sql
INSERT OR IGNORE INTO users (name, email)
VALUES ('Alice', 'alice@example.com');
```

### Insert or Replace
```sql
INSERT OR REPLACE INTO users (id, name, email)
VALUES (1, 'Alice', 'newemail@example.com');
```

---

## Querying Data

### Select All
```sql
SELECT * FROM users;
```

### Select Specific Columns
```sql
SELECT name, email FROM users;
```

### WHERE Conditions
```sql
SELECT * FROM users WHERE age > 25;
SELECT * FROM users WHERE name = 'Alice';
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT * FROM users WHERE age BETWEEN 20 AND 30;
SELECT * FROM users WHERE name IN ('Alice', 'Bob');
```

### Sorting
```sql
SELECT * FROM users ORDER BY age ASC;
SELECT * FROM users ORDER BY name DESC;
SELECT * FROM users ORDER BY age DESC, name ASC;
```

### Limiting Results
```sql
SELECT * FROM users LIMIT 10;
SELECT * FROM users LIMIT 10 OFFSET 20;  -- Skip first 20
```

### DISTINCT (unique values)
```sql
SELECT DISTINCT department FROM employees;
```

---

## Updating Data

### Update Single Row
```sql
UPDATE users
SET email = 'newemail@example.com'
WHERE id = 1;
```

### Update Multiple Columns
```sql
UPDATE users
SET name = 'Alice Smith', age = 26
WHERE id = 1;
```

### Update All Rows (dangerous!)
```sql
UPDATE users SET is_active = 1;
```

---

## Deleting Data

### Delete Specific Rows
```sql
DELETE FROM users WHERE id = 1;
DELETE FROM users WHERE age < 18;
```

### Delete All Rows (dangerous!)
```sql
DELETE FROM users;
```

---

## Constraints

```sql
PRIMARY KEY              -- Unique identifier
AUTOINCREMENT           -- Auto-increment for PRIMARY KEY
NOT NULL                -- Column cannot be NULL
UNIQUE                  -- No duplicate values
DEFAULT value           -- Default value if not provided
CHECK(condition)        -- Custom validation
FOREIGN KEY             -- Reference another table
```

### Example:
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL CHECK(amount > 0),
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Indexes

### Create Index
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_name_age ON users(name, age);
```

### Drop Index
```sql
DROP INDEX IF EXISTS idx_users_email;
```

### List All Indexes
```sql
SELECT name FROM sqlite_master
WHERE type='index';
```

---

## JOINs

### INNER JOIN
```sql
SELECT users.name, orders.amount
FROM users
INNER JOIN orders ON users.id = orders.user_id;
```

### LEFT JOIN
```sql
SELECT users.name, orders.amount
FROM users
LEFT JOIN orders ON users.id = orders.user_id;
```

### Multiple JOINs
```sql
SELECT u.name, o.amount, p.name AS product
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN products p ON o.product_id = p.id;
```

---

## Aggregations

### COUNT
```sql
SELECT COUNT(*) FROM users;
SELECT COUNT(DISTINCT department) FROM employees;
```

### SUM, AVG, MIN, MAX
```sql
SELECT SUM(salary) FROM employees;
SELECT AVG(age) FROM users;
SELECT MIN(price) FROM products;
SELECT MAX(created_at) FROM orders;
```

### GROUP BY
```sql
SELECT department, COUNT(*) as count
FROM employees
GROUP BY department;

SELECT department, AVG(salary) as avg_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 50000;
```

---

## Common Functions

### String Functions
```sql
SELECT upper('hello');              -- HELLO
SELECT lower('WORLD');              -- world
SELECT length('SQLite');            -- 6
SELECT substr('SQLite', 1, 3);      -- SQL
SELECT trim('  hello  ');           -- hello
SELECT replace('hello', 'l', 'L');  -- heLLo
SELECT 'Hello' || ' ' || 'World';   -- Hello World (concatenation)
```

### Math Functions
```sql
SELECT abs(-42);                    -- 42
SELECT round(3.14159, 2);           -- 3.14
SELECT random();                    -- Random integer
SELECT min(10, 20);                 -- 10
SELECT max(10, 20);                 -- 20
```

### Date/Time Functions
```sql
SELECT date('now');                 -- 2025-01-14
SELECT time('now');                 -- 12:30:45
SELECT datetime('now');             -- 2025-01-14 12:30:45
SELECT date('now', '+7 days');      -- Date 7 days from now
SELECT date('now', '-1 month');     -- Date 1 month ago
SELECT strftime('%Y', 'now');       -- 2025 (year only)
SELECT strftime('%m', 'now');       -- 01 (month only)
```

### Conditional (CASE)
```sql
SELECT name,
    CASE
        WHEN age < 18 THEN 'Minor'
        WHEN age < 65 THEN 'Adult'
        ELSE 'Senior'
    END AS category
FROM users;
```

---

## Python sqlite3

### Connect to Database
```python
import sqlite3

# File-based database
conn = sqlite3.connect('database.db')

# In-memory database
conn = sqlite3.connect(':memory:')

# Enable column names
conn.row_factory = sqlite3.Row
```

### Execute Query
```python
cursor = conn.cursor()

# Single query
cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
result = cursor.fetchone()

# Multiple queries
cursor.execute("SELECT * FROM users")
results = cursor.fetchall()

# Insert/Update/Delete
cursor.execute("INSERT INTO users (name) VALUES (?)", ('Alice',))
conn.commit()
```

### Execute Many (Batch Insert)
```python
data = [
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com'),
]

cursor.executemany(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    data
)
conn.commit()
```

### Context Manager
```python
with sqlite3.connect('database.db') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    # Auto-commits and closes
```

### Error Handling
```python
try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
except sqlite3.Error as e:
    print(f"Database error: {e}")
finally:
    if conn:
        conn.close()
```

### Fetch Results
```python
# Fetch one row
row = cursor.fetchone()

# Fetch all rows
rows = cursor.fetchall()

# Fetch N rows
rows = cursor.fetchmany(10)

# Access by index
print(row[0], row[1])

# Access by column name (with row_factory)
conn.row_factory = sqlite3.Row
print(row['name'], row['email'])
```

---

## Useful Queries

### Copy Table Structure
```sql
CREATE TABLE users_backup AS SELECT * FROM users WHERE 1=0;
```

### Copy Table with Data
```sql
CREATE TABLE users_backup AS SELECT * FROM users;
```

### Get Table Info
```sql
PRAGMA table_info(users);
```

### Get Database List
```sql
PRAGMA database_list;
```

### Vacuum (optimize database)
```sql
VACUUM;
```

### Enable Foreign Keys
```sql
PRAGMA foreign_keys = ON;
```

---

## Common Patterns

### Pagination
```python
page = 1
page_size = 10
offset = (page - 1) * page_size

cursor.execute(
    "SELECT * FROM users LIMIT ? OFFSET ?",
    (page_size, offset)
)
```

### Search
```python
search_term = 'alice'
cursor.execute(
    "SELECT * FROM users WHERE name LIKE ?",
    (f'%{search_term}%',)
)
```

### Upsert (Insert or Update)
```python
cursor.execute("""
    INSERT INTO users (id, name, email)
    VALUES (?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        email = excluded.email
""", (1, 'Alice', 'alice@example.com'))
```

---

## Quick Tips

✅ **Always use placeholders** (`?`) to prevent SQL injection
✅ **Use transactions** for multiple writes
✅ **Add indexes** on frequently queried columns
✅ **Use EXPLAIN QUERY PLAN** to optimize slow queries
✅ **Vacuum regularly** to reclaim space
✅ **Enable WAL mode** for better concurrency: `PRAGMA journal_mode=WAL;`

---

**📖 For more details, see the full lessons in the course folder!**
