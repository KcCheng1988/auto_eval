# SQLite Crash Course for Beginners

Welcome to your hands-on SQLite course! This course will teach you SQLite from zero to hero using practical examples.

## 📚 Course Structure

### Module 1: SQLite Basics (30 minutes)
- What is SQLite?
- Installing and accessing SQLite
- Your first database
- Basic SQL commands

### Module 2: Tables and Data Types (45 minutes)
- Creating tables
- Understanding data types
- Inserting data
- Querying data

### Module 3: Querying Data (60 minutes)
- SELECT statements
- WHERE conditions
- Sorting and filtering
- Aggregations

### Module 4: Advanced Topics (60 minutes)
- JOINs
- Indexes
- Triggers
- Transactions

### Module 5: Python + SQLite (45 minutes)
- Using sqlite3 module
- CRUD operations in Python
- Error handling
- Best practices

---

## 🎯 Learning Path

1. **Start here**: `lesson_01_basics.md`
2. **Practice**: Run each `.sql` file in order
3. **Test yourself**: Complete exercises
4. **Build**: Create your own database

---

## 📂 Course Files

```
sqlite_course/
├── README.md                          # This file
├── lesson_01_basics.md                # Introduction to SQLite
├── lesson_02_tables.md                # Tables and data types
├── lesson_03_queries.md               # Querying data
├── lesson_04_advanced.md              # Advanced SQL
├── lesson_05_python.md                # Python integration
├── exercises/
│   ├── exercise_01.sql                # Practice exercises
│   ├── exercise_02.sql
│   ├── exercise_03.sql
│   ├── exercise_04.sql
│   └── solutions/
│       ├── exercise_01_solution.sql
│       ├── exercise_02_solution.sql
│       ├── exercise_03_solution.sql
│       └── exercise_04_solution.sql
├── examples/
│   ├── 01_create_database.sql         # Example: Create database
│   ├── 02_insert_data.sql             # Example: Insert data
│   ├── 03_query_data.sql              # Example: Query data
│   ├── 04_update_delete.sql           # Example: Update/Delete
│   ├── 05_joins.sql                   # Example: JOINs
│   ├── 06_indexes.sql                 # Example: Indexes
│   └── 07_triggers.sql                # Example: Triggers
├── projects/
│   ├── project_01_todo_app.md         # Build a TODO app
│   ├── project_02_blog.md             # Build a blog database
│   └── project_03_evaluation.md       # Build evaluation system (like yours!)
└── cheatsheet.md                      # Quick reference
```

---

## 🚀 Quick Start

### Option 1: Using Command Line (if available)

```bash
# Navigate to course directory
cd sqlite_course

# Start SQLite with a new database
sqlite3 practice.db

# You'll see SQLite prompt:
sqlite>

# Run your first command
sqlite> SELECT 'Hello SQLite!';
```

### Option 2: Using Python (Recommended for CML)

```python
import sqlite3

# Connect to database (creates if doesn't exist)
conn = sqlite3.connect('practice.db')

# Create cursor
cursor = conn.cursor()

# Run your first query
cursor.execute("SELECT 'Hello SQLite!'")
result = cursor.fetchone()
print(result[0])  # Output: Hello SQLite!

# Close connection
conn.close()
```

### Option 3: Using Course Helper Script

```bash
python sqlite_helper.py
```

This opens an interactive SQLite shell where you can practice.

---

## 🎓 Learning Tips

1. **Type everything yourself** - Don't copy-paste. Muscle memory helps!
2. **Experiment** - Try modifying examples
3. **Make mistakes** - That's how you learn
4. **Use the cheatsheet** - Quick reference for syntax
5. **Complete exercises** - Practice makes perfect

---

## 📖 Prerequisites

- Basic understanding of data (tables, rows, columns)
- Python basics (for Module 5)
- Text editor

**No prior SQL experience required!**

---

## 🛠️ Tools You'll Use

### 1. SQLite Command Line (Optional)
Check if available:
```bash
sqlite3 --version
```

### 2. Python sqlite3 Module (Built-in)
```python
import sqlite3  # Always available!
```

### 3. DB Browser for SQLite (Optional GUI)
- Download: https://sqlitebrowser.org/
- Visual tool for exploring databases

---

## 🎯 Course Objectives

By the end of this course, you will:

- ✅ Understand what SQLite is and when to use it
- ✅ Create databases and tables
- ✅ Insert, update, and delete data
- ✅ Write complex queries with JOINs
- ✅ Use indexes for performance
- ✅ Create triggers for automation
- ✅ Use SQLite with Python
- ✅ Build a complete database application

---

## 📚 Additional Resources

- Official SQLite docs: https://www.sqlite.org/docs.html
- SQL Tutorial: https://www.w3schools.com/sql/
- SQLite Browser: https://sqlitebrowser.org/

---

## 🏁 Ready to Start?

**Open `lesson_01_basics.md` and begin your journey!**

```bash
# If you're reading this in terminal, open the lesson:
cat lesson_01_basics.md

# Or in Python/CML, open with your editor
```

---

## 💡 Quick Test

Before starting, test your setup:

```python
import sqlite3

# This should work without errors
conn = sqlite3.connect(':memory:')  # Creates temporary database
cursor = conn.cursor()
cursor.execute("SELECT 1+1")
print(cursor.fetchone()[0])  # Should print: 2
conn.close()

print("✅ You're ready to start!")
```

---

## 📝 Course Progress Tracker

- [ ] Module 1: SQLite Basics
- [ ] Module 2: Tables and Data Types
- [ ] Module 3: Querying Data
- [ ] Module 4: Advanced Topics
- [ ] Module 5: Python + SQLite
- [ ] Final Project

---

**Let's get started! 🚀**
