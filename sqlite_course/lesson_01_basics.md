# Lesson 1: SQLite Basics

**Duration**: 30 minutes
**Difficulty**: Beginner

---

## What is SQLite?

SQLite is a **lightweight, serverless database** that stores data in a single file.

### Key Features:

- 🚀 **No setup required** - Just a file!
- 📦 **Self-contained** - No server needed
- 💾 **Small footprint** - Perfect for embedded systems
- 🔒 **Reliable** - ACID compliant (transactions are safe)
- 🐍 **Built into Python** - Always available

### When to Use SQLite:

✅ **Good for:**
- Desktop applications
- Mobile apps (iOS, Android)
- Development and testing
- Small to medium websites
- Embedded systems
- Data analysis

❌ **Not ideal for:**
- High-concurrency write operations
- Very large databases (>1TB)
- Network file systems
- Applications requiring user permissions

---

## SQLite vs Other Databases

| Feature | SQLite | PostgreSQL | MySQL |
|---------|--------|------------|-------|
| Setup | None | Server | Server |
| File-based | ✅ Yes | ❌ No | ❌ No |
| Concurrent writes | Limited | Excellent | Good |
| Size limit | 281 TB | Unlimited | 64 TB |
| Built into Python | ✅ Yes | ❌ No | ❌ No |

---

## Your First SQLite Database

### Using Python (Recommended)

Create a file called `first_database.py`:

```python
import sqlite3

# Connect to database (creates file if doesn't exist)
conn = sqlite3.connect('my_first_database.db')

print("✅ Database created successfully!")
print(f"📁 Database file: my_first_database.db")

# Always close when done
conn.close()
```

Run it:
```bash
python first_database.py
```

You'll see a new file: `my_first_database.db` 🎉

---

## Understanding Database Files

```python
import sqlite3
import os

# Create database
conn = sqlite3.connect('test.db')
conn.close()

# Check if file exists
if os.path.exists('test.db'):
    print("✅ Database file exists")

    # Get file size
    size = os.path.getsize('test.db')
    print(f"📊 File size: {size} bytes")
```

**Output:**
```
✅ Database file exists
📊 File size: 8192 bytes
```

Even an empty SQLite database has a small file (header information).

---

## In-Memory Databases

For testing or temporary data, use **in-memory** databases:

```python
import sqlite3

# Create database in RAM (no file)
conn = sqlite3.connect(':memory:')

print("✅ In-memory database created")
print("⚠️  Data will be lost when connection closes")

conn.close()
# Database is now gone!
```

**Use cases:**
- Unit tests
- Temporary calculations
- Caching

---

## Basic SQL Syntax

SQL has 4 main categories:

### 1. DDL (Data Definition Language)
Define structure:
- `CREATE` - Create tables
- `ALTER` - Modify tables
- `DROP` - Delete tables

### 2. DML (Data Manipulation Language)
Manipulate data:
- `INSERT` - Add data
- `UPDATE` - Modify data
- `DELETE` - Remove data

### 3. DQL (Data Query Language)
Query data:
- `SELECT` - Retrieve data

### 4. DCL (Data Control Language)
Control access (less common in SQLite):
- `GRANT` - Give permissions
- `REVOKE` - Remove permissions

---

## Your First SQL Command

```python
import sqlite3

conn = sqlite3.connect('my_first_database.db')

# Create a cursor (executes commands)
cursor = conn.cursor()

# Execute SQL command
cursor.execute("SELECT 'Hello, SQLite!'")

# Fetch result
result = cursor.fetchone()
print(result[0])  # Output: Hello, SQLite!

conn.close()
```

**Explanation:**
1. `cursor` - Tool to execute SQL commands
2. `execute()` - Run SQL command
3. `fetchone()` - Get one result row
4. `result[0]` - First column of result

---

## SQL Comments

```sql
-- This is a single-line comment

/*
   This is a
   multi-line comment
*/

SELECT 'Hello';  -- Comment after code
```

---

## SQLite Command Line (Optional)

If you have `sqlite3` command:

```bash
# Open database
sqlite3 my_database.db

# SQLite prompt appears
sqlite>

# Run commands
sqlite> SELECT 'Hello SQLite!';

# Exit
sqlite> .quit
```

### Useful SQLite Commands:

```bash
.help          # Show all commands
.databases     # List databases
.tables        # List tables
.schema        # Show table structures
.quit          # Exit
```

---

## Practical Example: Simple Calculator

```python
import sqlite3

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# SQLite can do math!
queries = [
    "SELECT 5 + 3",           # Addition
    "SELECT 10 - 4",          # Subtraction
    "SELECT 6 * 7",           # Multiplication
    "SELECT 20 / 4",          # Division
    "SELECT 2 * (3 + 4)",     # Parentheses
    "SELECT 10 % 3",          # Modulo (remainder)
]

print("SQLite Calculator:")
print("-" * 30)

for query in queries:
    cursor.execute(query)
    result = cursor.fetchone()[0]
    print(f"{query:25} = {result}")

conn.close()
```

**Output:**
```
SQLite Calculator:
------------------------------
SELECT 5 + 3              = 8
SELECT 10 - 4             = 6
SELECT 6 * 7              = 42
SELECT 20 / 4             = 5.0
SELECT 2 * (3 + 4)        = 14
SELECT 10 % 3             = 1
```

---

## Built-in Functions

SQLite has many built-in functions:

```python
import sqlite3

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

functions = [
    "SELECT upper('hello')",           # HELLO
    "SELECT lower('WORLD')",           # world
    "SELECT length('SQLite')",         # 6
    "SELECT abs(-42)",                 # 42
    "SELECT round(3.14159, 2)",        # 3.14
    "SELECT date('now')",              # Current date
    "SELECT time('now')",              # Current time
    "SELECT datetime('now')",          # Current datetime
]

print("Built-in Functions:")
print("-" * 50)

for func in functions:
    cursor.execute(func)
    result = cursor.fetchone()[0]
    print(f"{func:35} = {result}")

conn.close()
```

---

## Error Handling

Always handle errors:

```python
import sqlite3

try:
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    # This will cause an error (invalid SQL)
    cursor.execute("INVALID SQL COMMAND")

except sqlite3.Error as e:
    print(f"❌ Database error: {e}")

finally:
    if conn:
        conn.close()
        print("✅ Connection closed")
```

---

## Context Manager (Best Practice)

Use `with` statement for automatic cleanup:

```python
import sqlite3

# Connection closes automatically
with sqlite3.connect('test.db') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello!'")
    result = cursor.fetchone()
    print(result[0])

# No need to call conn.close()!
```

---

## 🎯 Practice Exercise 1

**Task**: Create a program that:
1. Creates a database called `calculator.db`
2. Asks user for two numbers
3. Performs addition using SQL
4. Displays the result

**Solution**:

```python
import sqlite3

# Get user input
num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))

# Create database and calculate
with sqlite3.connect('calculator.db') as conn:
    cursor = conn.cursor()

    # Use SQL to calculate
    query = f"SELECT {num1} + {num2}"
    cursor.execute(query)
    result = cursor.fetchone()[0]

    print(f"\nResult: {num1} + {num2} = {result}")
```

---

## 🎯 Practice Exercise 2

**Task**: Write a program that:
1. Creates an in-memory database
2. Tests all comparison operators
3. Prints True/False results

**Hint**: Use these operators:
- `=` (equal)
- `!=` (not equal)
- `>` (greater than)
- `<` (less than)
- `>=` (greater or equal)
- `<=` (less or equal)

**Solution**:

```python
import sqlite3

with sqlite3.connect(':memory:') as conn:
    cursor = conn.cursor()

    tests = [
        "SELECT 5 = 5",      # True (1)
        "SELECT 5 != 3",     # True (1)
        "SELECT 10 > 5",     # True (1)
        "SELECT 3 < 10",     # True (1)
        "SELECT 5 >= 5",     # True (1)
        "SELECT 3 <= 2",     # False (0)
    ]

    print("Comparison Tests:")
    print("-" * 40)

    for test in tests:
        cursor.execute(test)
        result = cursor.fetchone()[0]
        status = "✅ True" if result else "❌ False"
        print(f"{test:20} = {status}")
```

---

## 📝 Key Takeaways

1. ✅ SQLite is a **file-based database** (no server needed)
2. ✅ Use `sqlite3.connect()` to create/open database
3. ✅ Use `cursor.execute()` to run SQL commands
4. ✅ Use `fetchone()` or `fetchall()` to get results
5. ✅ Always close connections (or use `with` statement)
6. ✅ Use `:memory:` for temporary databases
7. ✅ SQLite can do calculations, string operations, dates, etc.

---

## 🎓 Quiz

1. What is the main difference between SQLite and PostgreSQL?
2. How do you create an in-memory database?
3. What method executes SQL commands?
4. What does `fetchone()` return?
5. How do you automatically close database connections?

**Answers at end of file** ⬇️

---

## Next Lesson

**Lesson 2: Tables and Data Types** 🎯

You'll learn:
- Creating tables
- Understanding data types
- Inserting data
- Primary keys and constraints

---

## Quiz Answers

1. SQLite is file-based (no server), PostgreSQL requires a server
2. `sqlite3.connect(':memory:')`
3. `cursor.execute()`
4. A tuple containing one row of results
5. Use `with` statement: `with sqlite3.connect(...) as conn:`

---

**✅ Lesson 1 Complete! Ready for Lesson 2?**
