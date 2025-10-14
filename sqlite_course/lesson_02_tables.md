# Lesson 2: Tables and Data Types

**Duration**: 45 minutes
**Difficulty**: Beginner

---

## What is a Table?

A **table** is like a spreadsheet:
- **Rows** = Records (individual entries)
- **Columns** = Fields (attributes)

Example: `students` table

| id | name  | age | email |
|----|-------|-----|-------|
| 1  | Alice | 20  | alice@example.com |
| 2  | Bob   | 22  | bob@example.com |

---

## SQLite Data Types

SQLite has 5 storage classes:

### 1. NULL
Empty value (nothing)
```sql
NULL
```

### 2. INTEGER
Whole numbers
```sql
1, 42, -100, 0
```

### 3. REAL
Floating-point numbers
```sql
3.14, -0.5, 2.0
```

### 4. TEXT
Strings (any length)
```sql
'Hello', "SQLite", 'user@example.com'
```

### 5. BLOB
Binary data (images, files)
```sql
-- Rarely used directly
```

---

## Common Type Affinity

SQLite is flexible with types:

```python
import sqlite3

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create table with specific types
cursor.execute("""
    CREATE TABLE demo (
        id INTEGER,
        name TEXT,
        price REAL,
        active INTEGER,  -- Used for boolean (0=False, 1=True)
        data BLOB
    )
""")

print("✅ Table created with type hints")
conn.close()
```

---

## Creating Your First Table

### Syntax:

```sql
CREATE TABLE table_name (
    column1 datatype constraints,
    column2 datatype constraints,
    ...
);
```

### Example: Simple Students Table

```python
import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE students (
        id INTEGER,
        name TEXT,
        age INTEGER,
        email TEXT
    )
""")

print("✅ Table 'students' created!")
conn.commit()  # Save changes
conn.close()
```

---

## Viewing Table Structure

### Using Python:

```python
import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(students)")
columns = cursor.fetchall()

print("Table Structure:")
print("-" * 60)
for col in columns:
    print(f"Column: {col[1]:15} Type: {col[2]:10}")

conn.close()
```

**Output:**
```
Table Structure:
------------------------------------------------------------
Column: id              Type: INTEGER
Column: name            Type: TEXT
Column: age             Type: INTEGER
Column: email           Type: TEXT
```

### Using SQLite Command (if available):

```bash
sqlite3 school.db
sqlite> .schema students
```

---

## Constraints

Constraints enforce rules on data:

### 1. PRIMARY KEY
Unique identifier for each row (auto-increments)

```python
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY,  -- Auto-increments!
        name TEXT,
        age INTEGER
    )
""")
```

### 2. NOT NULL
Column must have a value

```python
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,      -- Name is required
        age INTEGER
    )
""")
```

### 3. UNIQUE
No duplicate values allowed

```python
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE        -- Email must be unique
    )
""")
```

### 4. DEFAULT
Default value if none provided

```python
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER DEFAULT 18,  -- Default age is 18
        active INTEGER DEFAULT 1 -- Active by default
    )
""")
```

### 5. CHECK
Custom validation rule

```python
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER CHECK(age >= 0 AND age <= 150)  -- Valid age range
    )
""")
```

---

## Complete Table Example

```python
import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Drop table if exists (for practice)
cursor.execute("DROP TABLE IF EXISTS students")

# Create comprehensive table
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER CHECK(age >= 16 AND age <= 100),
        gpa REAL DEFAULT 0.0,
        enrolled_date TEXT DEFAULT (date('now')),
        is_active INTEGER DEFAULT 1
    )
""")

print("✅ Students table created with constraints!")
conn.commit()
conn.close()
```

---

## Inserting Data

### Basic INSERT:

```python
import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Insert one student
cursor.execute("""
    INSERT INTO students (first_name, last_name, email, age, gpa)
    VALUES ('Alice', 'Smith', 'alice@school.com', 20, 3.8)
""")

print("✅ Student inserted!")
conn.commit()
conn.close()
```

### Multiple INSERTs:

```python
import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Insert multiple students
students_data = [
    ('Bob', 'Johnson', 'bob@school.com', 22, 3.5),
    ('Charlie', 'Brown', 'charlie@school.com', 19, 3.9),
    ('Diana', 'Prince', 'diana@school.com', 21, 4.0),
]

cursor.executemany("""
    INSERT INTO students (first_name, last_name, email, age, gpa)
    VALUES (?, ?, ?, ?, ?)
""", students_data)

print(f"✅ Inserted {cursor.rowcount} students!")
conn.commit()
conn.close()
```

**Note**: `?` are placeholders (safe from SQL injection)

---

## Querying Data

### SELECT All:

```python
import sqlite3

conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Get all students
cursor.execute("SELECT * FROM students")
students = cursor.fetchall()

print(f"Total students: {len(students)}\n")

for student in students:
    print(f"ID: {student[0]}, Name: {student[1]} {student[2]}, GPA: {student[5]}")

conn.close()
```

### SELECT Specific Columns:

```python
cursor.execute("SELECT first_name, last_name, gpa FROM students")
students = cursor.fetchall()

for name, last, gpa in students:
    print(f"{name} {last}: GPA {gpa}")
```

---

## Using Row Factory (Better Output)

```python
import sqlite3

conn = sqlite3.connect('school.db')
conn.row_factory = sqlite3.Row  # Enable column names

cursor = conn.cursor()
cursor.execute("SELECT * FROM students")
students = cursor.fetchall()

for student in students:
    # Access by column name!
    print(f"{student['first_name']} {student['last_name']}")
    print(f"  Email: {student['email']}")
    print(f"  GPA: {student['gpa']}")
    print()

conn.close()
```

**Output:**
```
Alice Smith
  Email: alice@school.com
  GPA: 3.8

Bob Johnson
  Email: bob@school.com
  GPA: 3.5
```

---

## Practical Example: Complete CRUD

```python
import sqlite3

def create_connection():
    """Create database connection"""
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Create students table"""
    with create_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER CHECK(age >= 16 AND age <= 100),
                gpa REAL DEFAULT 0.0
            )
        """)
        print("✅ Table ready")

def add_student(first_name, last_name, email, age, gpa):
    """Add new student"""
    with create_connection() as conn:
        conn.execute("""
            INSERT INTO students (first_name, last_name, email, age, gpa)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, email, age, gpa))
        print(f"✅ Added {first_name} {last_name}")

def get_all_students():
    """Get all students"""
    with create_connection() as conn:
        cursor = conn.execute("SELECT * FROM students")
        return cursor.fetchall()

def display_students():
    """Display all students"""
    students = get_all_students()
    print(f"\nTotal Students: {len(students)}")
    print("-" * 60)
    for s in students:
        print(f"{s['id']:3} | {s['first_name']} {s['last_name']:12} | GPA: {s['gpa']}")

# Main program
if __name__ == "__main__":
    create_table()

    # Add some students
    add_student('Alice', 'Smith', 'alice@school.com', 20, 3.8)
    add_student('Bob', 'Johnson', 'bob@school.com', 22, 3.5)
    add_student('Charlie', 'Brown', 'charlie@school.com', 19, 3.9)

    # Display all
    display_students()
```

---

## Date and Time in SQLite

SQLite stores dates as TEXT in ISO8601 format: `YYYY-MM-DD HH:MM:SS`

```python
import sqlite3

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create table with timestamps
cursor.execute("""
    CREATE TABLE events (
        id INTEGER PRIMARY KEY,
        name TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        event_date TEXT
    )
""")

# Insert with automatic timestamp
cursor.execute("""
    INSERT INTO events (name, event_date)
    VALUES ('Meeting', '2025-01-15 14:00:00')
""")

# Query
cursor.execute("SELECT * FROM events")
event = cursor.fetchone()
print(f"Event: {event[1]}")
print(f"Created: {event[2]}")
print(f"Scheduled: {event[3]}")

conn.close()
```

---

## Boolean Values

SQLite doesn't have native boolean. Use INTEGER:
- `0` = False
- `1` = True

```python
cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        is_active INTEGER DEFAULT 1,    -- Boolean
        is_admin INTEGER DEFAULT 0      -- Boolean
    )
""")

# Insert
cursor.execute("""
    INSERT INTO users (username, is_active, is_admin)
    VALUES ('alice', 1, 0)
""")

# Query active users
cursor.execute("SELECT * FROM users WHERE is_active = 1")
```

---

## JSON in SQLite

SQLite can store JSON as TEXT:

```python
import sqlite3
import json

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        metadata TEXT  -- JSON stored as TEXT
    )
""")

# Insert with JSON
metadata = {
    'color': 'blue',
    'size': 'large',
    'tags': ['electronic', 'gadget']
}

cursor.execute("""
    INSERT INTO products (name, metadata)
    VALUES (?, ?)
""", ('Widget', json.dumps(metadata)))

# Query and parse JSON
cursor.execute("SELECT * FROM products")
product = cursor.fetchone()
product_metadata = json.loads(product[2])

print(f"Product: {product[1]}")
print(f"Color: {product_metadata['color']}")
print(f"Tags: {', '.join(product_metadata['tags'])}")

conn.close()
```

---

## 🎯 Practice Exercise 1

**Task**: Create a `books` table with:
- `id` (primary key, auto-increment)
- `title` (required)
- `author` (required)
- `isbn` (unique, required)
- `year_published` (integer, between 1000 and 2100)
- `price` (real, default 0.0)
- `in_stock` (boolean, default 1)

Then insert 3 books.

**Solution**:

```python
import sqlite3

conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL,
        year_published INTEGER CHECK(year_published >= 1000 AND year_published <= 2100),
        price REAL DEFAULT 0.0,
        in_stock INTEGER DEFAULT 1
    )
""")

# Insert books
books_data = [
    ('Python Crash Course', 'Eric Matthes', '978-1593279288', 2019, 39.99, 1),
    ('Clean Code', 'Robert Martin', '978-0132350884', 2008, 44.99, 1),
    ('The Pragmatic Programmer', 'Hunt & Thomas', '978-0135957059', 2019, 49.99, 0),
]

cursor.executemany("""
    INSERT INTO books (title, author, isbn, year_published, price, in_stock)
    VALUES (?, ?, ?, ?, ?, ?)
""", books_data)

print(f"✅ Inserted {cursor.rowcount} books!")

# Display
cursor.execute("SELECT title, author, price FROM books")
for book in cursor.fetchall():
    print(f"  - {book[0]} by {book[1]} (${book[2]})")

conn.commit()
conn.close()
```

---

## 🎯 Practice Exercise 2

**Task**: Create a `tasks` table for a TODO app:
- `id`, `title`, `description`, `completed`, `created_at`

Add functions to:
1. Create new task
2. Mark task as completed
3. List all incomplete tasks

**Solution**: See `examples/02_insert_data.sql` for reference.

---

## 📝 Key Takeaways

1. ✅ Tables are like spreadsheets (rows = records, columns = fields)
2. ✅ SQLite has 5 types: NULL, INTEGER, REAL, TEXT, BLOB
3. ✅ Use constraints: PRIMARY KEY, NOT NULL, UNIQUE, DEFAULT, CHECK
4. ✅ `INSERT` adds data, `SELECT` retrieves data
5. ✅ Use `?` placeholders for safe queries (prevents SQL injection)
6. ✅ Use `conn.row_factory = sqlite3.Row` to access columns by name
7. ✅ Store dates as TEXT in ISO8601 format
8. ✅ Store booleans as INTEGER (0/1)

---

## Next Lesson

**Lesson 3: Querying Data** 🎯

You'll learn:
- WHERE conditions
- Sorting (ORDER BY)
- Limiting results
- Aggregations (COUNT, SUM, AVG, etc.)

---

**✅ Lesson 2 Complete! Ready for Lesson 3?**
