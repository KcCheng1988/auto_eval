# Installing SQLite on Windows

## ✅ Good News: SQLite is Already Available!

Python includes the `sqlite3` module by default. You can use SQLite **right now** without installing anything!

**Test it:**
```python
import sqlite3
print("✅ SQLite is ready!")
print(f"SQLite version: {sqlite3.sqlite_version}")
```

---

## 📦 Installing sqlite3 Command-Line Tool (Optional)

The command-line tool is useful but **NOT required** for the course. You can do everything with Python!

### Method 1: Download Pre-compiled Binaries (Easiest)

1. **Visit**: https://www.sqlite.org/download.html

2. **Download** (for Windows):
   - Look for "Precompiled Binaries for Windows"
   - Download: `sqlite-tools-win32-x86-xxxxxxx.zip`

3. **Extract** the ZIP file:
   - Extract to: `C:\sqlite\`
   - You'll get: `sqlite3.exe`, `sqldiff.exe`, `sqlite3_analyzer.exe`

4. **Add to PATH** (optional):
   - Right-click "This PC" → Properties → Advanced System Settings
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Click "Edit" → "New"
   - Add: `C:\sqlite\`
   - Click OK

5. **Test**:
   ```bash
   sqlite3 --version
   ```

### Method 2: Using Chocolatey (Windows Package Manager)

If you have Chocolatey installed:

```bash
choco install sqlite
```

### Method 3: Using Conda (If in Conda Environment)

```bash
conda install -c conda-forge sqlite
```

---

## 🐧 Installing on Linux

### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install sqlite3
```

### CentOS/RHEL:
```bash
sudo yum install sqlite
```

### Fedora:
```bash
sudo dnf install sqlite
```

---

## 🍎 Installing on macOS

SQLite is pre-installed on macOS!

**Test it:**
```bash
sqlite3 --version
```

If needed, install via Homebrew:
```bash
brew install sqlite3
```

---

## 🎓 Do You Need the Command-Line Tool?

**NO!** For this course, you can do everything with Python.

### With Python Only:
```python
import sqlite3

# Create database
conn = sqlite3.connect('mydata.db')
cursor = conn.cursor()

# Run SQL
cursor.execute("CREATE TABLE users (id INTEGER, name TEXT)")
cursor.execute("INSERT INTO users VALUES (1, 'Alice')")
cursor.execute("SELECT * FROM users")

print(cursor.fetchall())  # [(1, 'Alice')]
conn.close()
```

### With Command-Line Tool:
```bash
sqlite3 mydata.db
sqlite> CREATE TABLE users (id INTEGER, name TEXT);
sqlite> INSERT INTO users VALUES (1, 'Alice');
sqlite> SELECT * FROM users;
sqlite> .quit
```

**Same result, different interface!**

---

## 🔧 Using the Interactive Helper (Recommended)

Instead of installing command-line SQLite, use our course helper:

```bash
cd sqlite_course
python sqlite_helper.py
```

This gives you an **interactive SQLite shell** using Python!

```
sql> CREATE TABLE users (id INTEGER, name TEXT);
✅ Query executed. Rows affected: 0

sql> INSERT INTO users VALUES (1, 'Alice');
✅ Query executed. Rows affected: 1

sql> SELECT * FROM users;
id              | name
---------------------------------
1               | Alice

Total rows: 1
```

---

## ✅ What You Have Right Now

| Feature | Status | Notes |
|---------|--------|-------|
| Python `sqlite3` module | ✅ Installed | Built into Python |
| Create databases | ✅ Works | Use Python code |
| Run SQL queries | ✅ Works | Use Python code |
| Interactive shell | ✅ Works | Use `sqlite_helper.py` |
| Command-line tool | ❓ Optional | Nice to have, not required |

---

## 🎯 Quick Start (No Installation Needed!)

**Right now, you can:**

1. **Create a database:**
```python
import sqlite3
conn = sqlite3.connect('test.db')
print("✅ Database created!")
conn.close()
```

2. **Run the course:**
```bash
cd sqlite_course
python sqlite_helper.py
```

3. **Follow lessons:**
- Open `lesson_01_basics.md`
- Try all examples in Python
- No command-line tool needed!

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'sqlite3'"

This is **extremely rare** (SQLite is built into Python). If you see this:

1. Check Python version:
   ```bash
   python --version
   ```
   Should be Python 3.6+

2. Reinstall Python from https://www.python.org/

3. Or use system Python (not a minimal Python build)

### "sqlite3: command not found"

This means the **command-line tool** isn't in your PATH. But **you don't need it!**

Just use Python:
```python
import sqlite3  # This works!
```

---

## 📚 Summary

**For this course:**
- ✅ Use Python `sqlite3` module (already installed)
- ✅ Use `sqlite_helper.py` for interactive practice
- ❌ Don't worry about command-line tool (optional)

**You're ready to start learning SQLite right now!** 🚀

---

## Next Steps

1. ✅ Verify SQLite works:
   ```python
   import sqlite3
   print("✅ SQLite ready!")
   ```

2. ✅ Start the course:
   ```bash
   cd sqlite_course
   cat lesson_01_basics.md
   ```

3. ✅ Practice interactively:
   ```bash
   python sqlite_helper.py
   ```

**No installation required! Let's go!** 🎓
