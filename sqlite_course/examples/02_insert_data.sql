-- Example 2: Inserting Data
-- This file demonstrates various ways to insert data into tables

-- ============================================================================
-- SETUP: Create sample table
-- ============================================================================

DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT,
    salary REAL CHECK(salary >= 0),
    hire_date TEXT DEFAULT (date('now')),
    is_active INTEGER DEFAULT 1
);

-- ============================================================================
-- EXAMPLE 1: Basic INSERT
-- ============================================================================

INSERT INTO employees (first_name, last_name, email, department, salary)
VALUES ('John', 'Doe', 'john.doe@company.com', 'Engineering', 75000);

-- ============================================================================
-- EXAMPLE 2: INSERT with Default Values
-- ============================================================================

-- hire_date and is_active will use default values
INSERT INTO employees (first_name, last_name, email, department, salary)
VALUES ('Jane', 'Smith', 'jane.smith@company.com', 'Marketing', 68000);

-- ============================================================================
-- EXAMPLE 3: INSERT Multiple Rows
-- ============================================================================

INSERT INTO employees (first_name, last_name, email, department, salary) VALUES
    ('Alice', 'Johnson', 'alice.j@company.com', 'Engineering', 82000),
    ('Bob', 'Williams', 'bob.w@company.com', 'Sales', 65000),
    ('Charlie', 'Brown', 'charlie.b@company.com', 'Engineering', 77000),
    ('Diana', 'Miller', 'diana.m@company.com', 'HR', 70000);

-- ============================================================================
-- EXAMPLE 4: INSERT with Specific Date
-- ============================================================================

INSERT INTO employees (first_name, last_name, email, department, salary, hire_date)
VALUES ('Eve', 'Davis', 'eve.d@company.com', 'Marketing', 72000, '2024-01-15');

-- ============================================================================
-- EXAMPLE 5: INSERT from SELECT (copy data)
-- ============================================================================

-- Create backup table
CREATE TABLE employees_backup AS SELECT * FROM employees WHERE 1=0;

-- Copy all engineers to backup
INSERT INTO employees_backup
SELECT * FROM employees WHERE department = 'Engineering';

-- ============================================================================
-- EXAMPLE 6: INSERT OR IGNORE (skip if duplicate)
-- ============================================================================

-- This will be skipped if email already exists
INSERT OR IGNORE INTO employees (first_name, last_name, email, department, salary)
VALUES ('John', 'Doe', 'john.doe@company.com', 'Sales', 80000);

-- ============================================================================
-- EXAMPLE 7: INSERT OR REPLACE (update if exists)
-- ============================================================================

-- This will replace if id already exists
INSERT OR REPLACE INTO employees (id, first_name, last_name, email, department, salary)
VALUES (1, 'John', 'Doe', 'john.updated@company.com', 'Engineering', 80000);

-- ============================================================================
-- VERIFY: Display all inserted data
-- ============================================================================

SELECT
    id,
    first_name || ' ' || last_name AS full_name,
    email,
    department,
    salary,
    hire_date
FROM employees
ORDER BY department, last_name;

-- ============================================================================
-- EXAMPLE 8: TODO App Table
-- ============================================================================

DROP TABLE IF EXISTS tasks;

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    completed INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 1 CHECK(priority BETWEEN 1 AND 5),
    due_date TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);

-- Insert sample tasks
INSERT INTO tasks (title, description, priority, due_date) VALUES
    ('Buy groceries', 'Milk, eggs, bread', 2, '2025-01-15'),
    ('Finish project', 'Complete SQLite course', 5, '2025-01-20'),
    ('Call dentist', 'Schedule checkup appointment', 3, '2025-01-18'),
    ('Read book', 'Finish chapter 5', 1, NULL),
    ('Exercise', 'Go to gym', 2, '2025-01-14');

-- Display all tasks
SELECT
    id,
    title,
    priority,
    CASE
        WHEN completed = 1 THEN '✅ Done'
        ELSE '⏳ Pending'
    END AS status,
    due_date
FROM tasks
ORDER BY priority DESC, due_date;

-- ============================================================================
-- HOW TO RUN THIS FILE
-- ============================================================================

-- Using Python:
-- import sqlite3
-- conn = sqlite3.connect('example.db')
-- with open('02_insert_data.sql', 'r') as f:
--     conn.executescript(f.read())
-- conn.close()

-- Using sqlite3 command:
-- sqlite3 example.db < 02_insert_data.sql
