-- Example 1: Creating a Database and Basic Tables
-- This file demonstrates creating tables with various constraints

-- ============================================================================
-- EXAMPLE 1: Simple Table
-- ============================================================================

CREATE TABLE users (
    id INTEGER,
    username TEXT,
    email TEXT
);

-- ============================================================================
-- EXAMPLE 2: Table with Primary Key
-- ============================================================================

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL DEFAULT 0.0
);

-- ============================================================================
-- EXAMPLE 3: Table with Multiple Constraints
-- ============================================================================

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    age INTEGER CHECK(age >= 18),
    created_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);

-- ============================================================================
-- EXAMPLE 4: Table with Foreign Key
-- ============================================================================

-- Parent table
CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT
);

-- Child table with foreign key
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author_id INTEGER,
    isbn TEXT UNIQUE,
    published_year INTEGER,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- ============================================================================
-- EXAMPLE 5: Complete E-commerce Schema
-- ============================================================================

-- Categories table
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- Products table
CREATE TABLE store_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price >= 0),
    stock_quantity INTEGER DEFAULT 0,
    category_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Orders table
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'pending',
    total_amount REAL DEFAULT 0.0,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Order items table
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price_at_time REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES store_products(id)
);

-- ============================================================================
-- EXAMPLE 6: Drop Tables (Cleanup)
-- ============================================================================

-- Drop tables if they exist (useful for practice)
-- Note: Uncomment these lines if you want to recreate tables

-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS products;
-- DROP TABLE IF EXISTS customers;
-- DROP TABLE IF EXISTS books;
-- DROP TABLE IF EXISTS authors;
-- DROP TABLE IF EXISTS order_items;
-- DROP TABLE IF EXISTS orders;
-- DROP TABLE IF EXISTS store_products;
-- DROP TABLE IF EXISTS categories;

-- ============================================================================
-- HOW TO USE THIS FILE
-- ============================================================================

-- Option 1: Using Python
-- import sqlite3
-- conn = sqlite3.connect('example.db')
-- with open('01_create_database.sql', 'r') as f:
--     conn.executescript(f.read())
-- conn.close()

-- Option 2: Using sqlite3 command line
-- sqlite3 example.db < 01_create_database.sql

-- Option 3: Copy-paste into Python
-- cursor.execute("CREATE TABLE ...")
