# FastAPI Crash Course for Beginners

Welcome to your hands-on FastAPI course! Learn to build modern REST APIs quickly.

## 📚 Course Structure

### Module 1: FastAPI Basics (30 minutes)
- What is FastAPI?
- Installing FastAPI
- Your first API
- Running the server

### Module 2: Request & Response (45 minutes)
- Path parameters
- Query parameters
- Request bodies
- Response models

### Module 3: Data Validation (30 minutes)
- Pydantic models
- Validation rules
- Error handling

### Module 4: Advanced Topics (60 minutes)
- Dependency injection
- Database integration
- File uploads
- Authentication

---

## 🎯 Learning Path

1. **Start here**: `lesson_01_basics.md`
2. **Practice**: Run each example
3. **Test**: Use the interactive docs at `/docs`
4. **Build**: Create your own API

---

## 📂 Course Files

```
fastapi_course/
├── README.md                   # This file
├── lesson_01_basics.md         # Introduction to FastAPI
├── lesson_02_requests.md       # Handling requests
├── lesson_03_validation.md     # Data validation
├── lesson_04_advanced.md       # Advanced topics
├── examples/
│   ├── 01_hello_world.py       # Hello World API
│   ├── 02_path_params.py       # Path parameters
│   ├── 03_query_params.py      # Query parameters
│   ├── 04_request_body.py      # Request bodies
│   ├── 05_validation.py        # Data validation
│   ├── 06_dependencies.py      # Dependency injection
│   ├── 07_database.py          # Database integration
│   └── 08_file_upload.py       # File uploads
├── projects/
│   ├── todo_api.md             # Build a TODO API
│   ├── blog_api.md             # Build a blog API
│   └── evaluation_api.md       # Build evaluation API
└── cheatsheet.md               # Quick reference
```

---

## 🚀 Quick Start

### Install FastAPI

```bash
pip install fastapi uvicorn
```

### Your First API

Create `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, World!"}
```

### Run the Server

```bash
uvicorn main:app --reload
```

### Test It

Open your browser:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

---

## 🎓 Why FastAPI?

### ✅ Advantages:

1. **Fast** - High performance (NodeJS/Go level)
2. **Easy** - Simple, intuitive syntax
3. **Auto docs** - Swagger UI built-in
4. **Type hints** - Python type hints for validation
5. **Async** - Native async/await support
6. **Modern** - Based on latest Python features

### Comparison:

| Feature | FastAPI | Flask | Django REST |
|---------|---------|-------|-------------|
| Speed | ⚡⚡⚡ | ⚡ | ⚡⚡ |
| Auto docs | ✅ | ❌ | ❌ |
| Async | ✅ | Partial | Partial |
| Type validation | ✅ | ❌ | Partial |
| Learning curve | Easy | Easy | Medium |

---

## 📖 Prerequisites

- Basic Python knowledge
- Understanding of HTTP (GET, POST, etc.)
- Basic command line usage

**No web framework experience required!**

---

## 🛠️ Tools You'll Use

### 1. FastAPI
```bash
pip install fastapi
```

### 2. Uvicorn (ASGI server)
```bash
pip install uvicorn
```

### 3. Optional Tools
```bash
pip install python-multipart  # For file uploads
pip install python-dotenv      # For environment variables
pip install sqlalchemy        # For database
```

---

## 🎯 Course Objectives

By the end of this course, you will:

- ✅ Understand REST API concepts
- ✅ Create endpoints (GET, POST, PUT, DELETE)
- ✅ Handle path and query parameters
- ✅ Validate request data with Pydantic
- ✅ Use dependency injection
- ✅ Integrate with databases
- ✅ Handle file uploads
- ✅ Write API documentation
- ✅ Build a complete REST API

---

## 💡 Quick Test

Test your setup:

```python
# test_fastapi.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    return {"status": "working"}

# Run: uvicorn test_fastapi:app --reload
# Visit: http://localhost:8000/test
```

Expected output:
```json
{
  "status": "working"
}
```

---

## 📝 Course Progress Tracker

- [ ] Module 1: FastAPI Basics
- [ ] Module 2: Request & Response
- [ ] Module 3: Data Validation
- [ ] Module 4: Advanced Topics
- [ ] Final Project

---

## 🔗 Resources

- Official docs: https://fastapi.tiangolo.com/
- GitHub: https://github.com/tiangolo/fastapi
- Interactive tutorial: https://fastapi.tiangolo.com/tutorial/

---

## 🏁 Ready to Start?

**Open `lesson_01_basics.md` and begin your journey!**

```bash
# Start learning
cat lesson_01_basics.md

# Or jump straight to examples
python examples/01_hello_world.py
```

---

**Let's build some APIs! 🚀**
