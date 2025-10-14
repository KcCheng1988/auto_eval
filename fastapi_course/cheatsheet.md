# FastAPI Quick Reference Cheatsheet

## 📚 Installation

```bash
pip install fastapi uvicorn
pip install "fastapi[all]"  # With all optional dependencies
```

---

## 🚀 Basic App

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

# Run: uvicorn main:app --reload
```

---

## 📍 HTTP Methods

```python
@app.get("/items")          # Read
def get_items(): ...

@app.post("/items")         # Create
def create_item(): ...

@app.put("/items/{id}")     # Update (full)
def update_item(id: int): ...

@app.patch("/items/{id}")   # Update (partial)
def patch_item(id: int): ...

@app.delete("/items/{id}")  # Delete
def delete_item(id: int): ...
```

---

## 🔗 Path Parameters

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

# URL: /users/123
```

---

## ❓ Query Parameters

```python
@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# URL: /items?skip=0&limit=10
```

---

## 📦 Request Body (Pydantic)

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str = None

@app.post("/items")
def create_item(item: Item):
    return item
```

---

## ✅ Validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1, le=1000)
```

---

## 📤 Response Model

```python
class UserResponse(BaseModel):
    id: int
    username: str
    # password excluded

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    return user  # password filtered out
```

---

## 🔢 Status Codes

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(): ...

@app.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(id: int): ...
```

---

## ❗ Exceptions

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

---

## 🎯 Dependency Injection

```python
from fastapi import Depends

def get_current_user(token: str):
    # Verify token
    return {"user_id": 1}

@app.get("/me")
def read_users_me(user: dict = Depends(get_current_user)):
    return user
```

---

## 📁 File Upload

```python
from fastapi import File, UploadFile

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

---

## 🔐 Headers & Cookies

```python
from fastapi import Header, Cookie

@app.get("/items")
def read_items(
    user_agent: str = Header(None),
    session_id: str = Cookie(None)
):
    return {"user_agent": user_agent}
```

---

## 🎨 Email Validation

```python
from pydantic import EmailStr

class User(BaseModel):
    email: EmailStr  # pip install pydantic[email]
```

---

## 🔢 Enum Validation

```python
from enum import Enum

class Role(str, Enum):
    admin = "admin"
    user = "user"

class User(BaseModel):
    role: Role
```

---

## ✏️ Custom Validators

```python
from pydantic import validator

class User(BaseModel):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password too short')
        return v
```

---

## 📋 List & Dict Types

```python
from typing import List, Dict

class Cart(BaseModel):
    items: List[str]
    metadata: Dict[str, Any]
```

---

## 📅 Date & Time

```python
from datetime import date, datetime

class Event(BaseModel):
    event_date: date        # YYYY-MM-DD
    start_time: datetime    # ISO 8601
```

---

## 🔗 URL Validation

```python
from pydantic import HttpUrl

class Website(BaseModel):
    url: HttpUrl
```

---

## 🆔 UUID Validation

```python
from uuid import UUID

class Resource(BaseModel):
    id: UUID
```

---

## 🔄 Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str):
    # Send email
    pass

@app.post("/notify")
def notify(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email)
    return {"message": "Email will be sent"}
```

---

## 🗄️ Database (SQLite Example)

```python
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect('app.db')
    try:
        yield conn
    finally:
        conn.close()

@app.get("/users")
def list_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()
```

---

## 🔧 Middleware

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response
```

---

## 🌐 CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🎬 Lifespan Events

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

---

## 🔍 Request Context

```python
from fastapi import Request

@app.get("/info")
def get_info(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host
    }
```

---

## 🧪 Testing

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
```

---

## 📚 Documentation URLs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🎨 App Metadata

```python
app = FastAPI(
    title="My API",
    description="API description",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

---

## 🚀 Run Commands

```bash
# Development (auto-reload)
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000

# With workers
uvicorn main:app --workers 4

# With HTTPS
uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

---

## 📦 Common Imports

```python
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Header,
    Cookie,
    Request,
    Response,
    BackgroundTasks,
    Query,
    Path,
    Body
)

from pydantic import (
    BaseModel,
    Field,
    validator,
    EmailStr,
    HttpUrl,
    UUID
)

from typing import List, Dict, Optional
```

---

## 🔗 Useful Links

- **Official Docs**: https://fastapi.tiangolo.com/
- **GitHub**: https://github.com/tiangolo/fastapi
- **Pydantic**: https://docs.pydantic.dev/

---

**📖 For complete examples, see the lessons in this course!**
