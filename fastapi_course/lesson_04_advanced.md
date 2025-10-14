# Lesson 4: Advanced Topics

**Duration**: 60 minutes
**Difficulty**: Intermediate

---

## Dependency Injection

FastAPI's dependency injection system is powerful and flexible.

### Basic Dependency

```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_query_params(q: str = None, skip: int = 0, limit: int = 10):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items")
def list_items(params: dict = Depends(get_query_params)):
    return {
        "query": params["q"],
        "skip": params["skip"],
        "limit": params["limit"],
        "items": ["item1", "item2"]
    }
```

---

### Database Connection Dependency

```python
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect('app.db')
    try:
        yield conn
    finally:
        conn.close()

def get_db_connection():
    """Dependency for database connection"""
    with get_db() as conn:
        yield conn

@app.get("/users")
def list_users(db = Depends(get_db_connection)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return {"users": users}
```

---

### Class-Based Dependencies

```python
from fastapi import Depends

class Pagination:
    def __init__(self, skip: int = 0, limit: int = 10):
        self.skip = skip
        self.limit = limit

@app.get("/items")
def list_items(pagination: Pagination = Depends()):
    return {
        "skip": pagination.skip,
        "limit": pagination.limit
    }
```

---

### Dependency with Validation

```python
from fastapi import Depends, HTTPException

def verify_token(token: str):
    if token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.get("/protected")
def protected_route(token: str = Depends(verify_token)):
    return {"message": "Access granted", "token": token}
```

**Test:**
```bash
# Without token
curl http://localhost:8000/protected  # 401 error

# With valid token
curl "http://localhost:8000/protected?token=secret-token"
```

---

### Sub-Dependencies

```python
def get_token(token: str):
    return token

def verify_user(token: str = Depends(get_token)):
    if token != "valid-token":
        raise HTTPException(status_code=401, detail="Invalid")
    return {"user_id": 1, "username": "alice"}

@app.get("/me")
def get_current_user(user: dict = Depends(verify_user)):
    return user
```

---

## File Uploads

### Single File Upload

```python
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }
```

**Test:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

---

### Save Uploaded File

```python
import shutil
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "location": str(file_path),
        "size": file_path.stat().st_size
    }
```

---

### Multiple File Uploads

```python
from typing import List

@app.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        file_path = UPLOAD_DIR / file.filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        results.append({
            "filename": file.filename,
            "size": file_path.stat().st_size
        })

    return {"files": results, "total": len(results)}
```

**Test:**
```bash
curl -X POST http://localhost:8000/upload-multiple \
  -F "files=@file1.pdf" \
  -F "files=@file2.jpg"
```

---

### File Upload with Validation

```python
from fastapi import HTTPException

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed"
        )

    # Read and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {MAX_FILE_SIZE} bytes"
        )

    # Save file
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as f:
        f.write(contents)

    return {
        "filename": file.filename,
        "size": len(contents),
        "type": file.content_type
    }
```

---

## Background Tasks

Execute tasks after returning a response:

```python
from fastapi import BackgroundTasks
import time

def write_log(message: str):
    """Simulate slow logging operation"""
    time.sleep(5)
    with open("log.txt", "a") as f:
        f.write(f"{message}\n")

@app.post("/send-email")
def send_email(
    email: str,
    background_tasks: BackgroundTasks
):
    # Return response immediately
    background_tasks.add_task(write_log, f"Email sent to {email}")

    return {"message": "Email will be sent in background"}
```

---

### Background Task with Parameters

```python
def send_notification(email: str, message: str):
    # Simulate sending email
    time.sleep(3)
    print(f"Sent to {email}: {message}")

@app.post("/notify")
def notify_user(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_notification, email, message)
    return {"status": "notification queued"}
```

---

## Database Integration (SQLite)

```python
import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

DATABASE = "app.db"

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize on startup
init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (user.username, user.email)
            )
            conn.commit()
            user_id = cursor.lastrowid

            return UserResponse(
                id=user_id,
                username=user.username,
                email=user.email
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"]
        )
```

---

## Middleware

Add custom processing for all requests:

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    return response

@app.get("/")
def root():
    return {"message": "Hello"}
```

---

### CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
def get_data():
    return {"data": [1, 2, 3]}
```

---

## Error Handling

### Custom Exception Handler

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

class CustomException(Exception):
    def __init__(self, message: str):
        self.message = message

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=400,
        content={"error": exc.message}
    )

@app.get("/test")
def test():
    raise CustomException("Something went wrong!")
```

---

### Global Exception Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )
```

---

## Lifespan Events

Execute code on startup/shutdown:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up...")
    # Initialize resources (database, cache, etc.)

    yield  # Application runs

    # Shutdown
    print("👋 Shutting down...")
    # Cleanup resources

app = FastAPI(lifespan=lifespan)
```

---

## Request Context

Access request information:

```python
from fastapi import Request

@app.get("/info")
def get_request_info(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None
    }
```

---

## WebSockets

Real-time communication:

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

**Test with JavaScript:**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
    console.log(event.data);
};

ws.send("Hello!");
```

---

## Testing FastAPI

```python
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello"}

# Test
def test_root():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
```

---

## Complete Example: Blog API with All Features

```python
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
import sqlite3
from contextlib import contextmanager
from typing import List
import shutil
from pathlib import Path

app = FastAPI(title="Blog API")

# Database setup
DATABASE = "blog.db"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Models
class PostCreate(BaseModel):
    title: str
    content: str
    author: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str
    image_path: str = None

# Background task
def log_activity(activity: str):
    with open("activity.log", "a") as f:
        f.write(f"{activity}\n")

# Endpoints
@app.post("/posts", response_model=PostResponse)
def create_post(
    post: PostCreate,
    background_tasks: BackgroundTasks
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO posts (title, content, author) VALUES (?, ?, ?)",
            (post.title, post.content, post.author)
        )
        conn.commit()
        post_id = cursor.lastrowid

        background_tasks.add_task(
            log_activity,
            f"Post created: {post.title}"
        )

        return PostResponse(
            id=post_id,
            title=post.title,
            content=post.content,
            author=post.author
        )

@app.post("/posts/{post_id}/image")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...)
):
    # Verify post exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Post not found")

    # Save image
    file_path = UPLOAD_DIR / f"post_{post_id}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update post
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE posts SET image_path = ? WHERE id = ?",
            (str(file_path), post_id)
        )
        conn.commit()

    return {"filename": file.filename, "path": str(file_path)}

@app.get("/posts", response_model=List[PostResponse])
def list_posts(skip: int = 0, limit: int = 10):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM posts LIMIT ? OFFSET ?",
            (limit, skip)
        )
        rows = cursor.fetchall()

        return [
            PostResponse(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                author=row["author"],
                image_path=row["image_path"]
            )
            for row in rows
        ]
```

---

## 📝 Key Takeaways

1. ✅ Use dependency injection for reusable logic
2. ✅ Handle file uploads with `UploadFile`
3. ✅ Use background tasks for slow operations
4. ✅ Integrate with databases using context managers
5. ✅ Add middleware for cross-cutting concerns
6. ✅ Handle errors with custom exception handlers
7. ✅ Use lifespan events for initialization
8. ✅ Test APIs with `TestClient`

---

## Next Steps

You now know enough to build production-ready APIs!

**Continue learning:**
- ✅ Explore the [evaluation API](../proposed_architecture/api/) in this project
- ✅ Read [API_DOCUMENTATION.md](../proposed_architecture/API_DOCUMENTATION.md)
- ✅ Check official FastAPI docs: https://fastapi.tiangolo.com/

---

**✅ Course Complete! You're ready to build FastAPI applications! 🎉**
