# Lesson 1: FastAPI Basics

**Duration**: 30 minutes
**Difficulty**: Beginner

---

## What is FastAPI?

FastAPI is a **modern, fast web framework** for building APIs with Python 3.7+.

### Key Features:

- 🚀 **Fast**: One of the fastest Python frameworks
- 📝 **Auto documentation**: Swagger UI and ReDoc built-in
- ✅ **Type validation**: Automatic data validation
- 🔄 **Async support**: Native async/await
- 🎯 **Easy to learn**: Simple, intuitive syntax

---

## Installation

```bash
# Install FastAPI and Uvicorn
pip install fastapi uvicorn

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

---

## Your First API

Create `main.py`:

```python
from fastapi import FastAPI

# Create FastAPI instance
app = FastAPI()

# Define a route
@app.get("/")
def root():
    return {"message": "Hello, World!"}
```

**Run it:**

```bash
uvicorn main:app --reload
```

**Test it:**

Open http://localhost:8000

**Output:**
```json
{
  "message": "Hello, World!"
}
```

---

## Understanding the Code

```python
from fastapi import FastAPI  # Import FastAPI class

app = FastAPI()  # Create application instance

@app.get("/")  # Decorator: HTTP GET method at "/" path
def root():    # Function name can be anything
    return {"message": "Hello, World!"}  # Returns JSON automatically
```

**Key Points:**
- `@app.get("/")` - Route decorator (path + HTTP method)
- Function returns a dict - FastAPI converts to JSON automatically
- `--reload` - Auto-restart on code changes (dev only)

---

## Interactive Documentation

FastAPI generates **interactive API docs** automatically!

### Swagger UI
Visit: http://localhost:8000/docs

- Test endpoints directly in browser
- See request/response formats
- Try different parameters

### ReDoc
Visit: http://localhost:8000/redoc

- Alternative documentation style
- Better for reading/sharing

---

## Multiple Endpoints

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to my API"}

@app.get("/hello")
def hello():
    return {"message": "Hello!"}

@app.get("/bye")
def goodbye():
    return {"message": "Goodbye!"}

@app.get("/info")
def info():
    return {
        "name": "My API",
        "version": "1.0.0",
        "status": "running"
    }
```

**Test each endpoint:**
- http://localhost:8000/
- http://localhost:8000/hello
- http://localhost:8000/bye
- http://localhost:8000/info

---

## HTTP Methods

### GET - Retrieve data

```python
@app.get("/items")
def get_items():
    return {"items": ["item1", "item2", "item3"]}
```

### POST - Create data

```python
@app.post("/items")
def create_item():
    return {"message": "Item created"}
```

### PUT - Update data

```python
@app.put("/items/{item_id}")
def update_item(item_id: int):
    return {"message": f"Item {item_id} updated"}
```

### DELETE - Delete data

```python
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"message": f"Item {item_id} deleted"}
```

---

## Path Parameters

Extract values from URL path:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "John Doe"}

@app.get("/items/{item_name}")
def get_item(item_name: str):
    return {"item": item_name, "price": 9.99}
```

**Try it:**
- http://localhost:8000/users/123
- http://localhost:8000/items/laptop

**Output:**
```json
// /users/123
{
  "user_id": 123,
  "name": "John Doe"
}

// /items/laptop
{
  "item": "laptop",
  "price": 9.99
}
```

---

## Type Hints & Validation

FastAPI uses Python type hints for automatic validation:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):  # Must be integer
    return {"user_id": user_id}
```

**Valid request:**
- http://localhost:8000/users/123 ✅

**Invalid request:**
- http://localhost:8000/users/abc ❌

**Error response:**
```json
{
  "detail": [
    {
      "loc": ["path", "user_id"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

---

## Query Parameters

Parameters after `?` in URL:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/search")
def search(q: str):
    return {"query": q, "results": ["result1", "result2"]}

@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    return {
        "skip": skip,
        "limit": limit,
        "items": ["item1", "item2", "item3"]
    }
```

**Try it:**
- http://localhost:8000/search?q=fastapi
- http://localhost:8000/items?skip=0&limit=5
- http://localhost:8000/items (uses defaults)

---

## Practical Example: Calculator API

```python
from fastapi import FastAPI

app = FastAPI(title="Calculator API")

@app.get("/")
def root():
    return {"message": "Calculator API - Use /docs for documentation"}

@app.get("/add")
def add(a: float, b: float):
    return {"operation": "add", "a": a, "b": b, "result": a + b}

@app.get("/subtract")
def subtract(a: float, b: float):
    return {"operation": "subtract", "a": a, "b": b, "result": a - b}

@app.get("/multiply")
def multiply(a: float, b: float):
    return {"operation": "multiply", "a": a, "b": b, "result": a * b}

@app.get("/divide")
def divide(a: float, b: float):
    if b == 0:
        return {"error": "Cannot divide by zero"}
    return {"operation": "divide", "a": a, "b": b, "result": a / b}

@app.get("/power")
def power(base: float, exponent: float):
    return {
        "operation": "power",
        "base": base,
        "exponent": exponent,
        "result": base ** exponent
    }
```

**Test it:**
```bash
# Addition
curl "http://localhost:8000/add?a=5&b=3"

# Division
curl "http://localhost:8000/divide?a=10&b=2"

# Power
curl "http://localhost:8000/power?base=2&exponent=8"
```

---

## Customizing API Metadata

```python
from fastapi import FastAPI

app = FastAPI(
    title="My Awesome API",
    description="This API does awesome things",
    version="1.0.0",
    contact={
        "name": "Your Name",
        "email": "your.email@example.com",
    },
    license_info={
        "name": "MIT",
    }
)

@app.get("/")
def root():
    return {"message": "Welcome!"}
```

This information appears in `/docs` and `/redoc`!

---

## Async Endpoints

FastAPI supports async/await for better performance:

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/sync")
def sync_endpoint():
    return {"type": "synchronous"}

@app.get("/async")
async def async_endpoint():
    await asyncio.sleep(1)  # Simulate async operation
    return {"type": "asynchronous"}
```

**When to use async:**
- Database queries
- API calls
- File I/O
- Long-running operations

**When to use sync:**
- Simple calculations
- Return static data
- CPU-bound tasks

---

## Response Status Codes

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "OK"}

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item():
    return {"message": "Item created"}

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    return None
```

**Common status codes:**
- `200` - OK
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

---

## 🎯 Practice Exercise 1

**Task**: Create a simple user API with these endpoints:

1. `GET /` - Welcome message
2. `GET /users/{user_id}` - Get user by ID
3. `GET /users` - List users with pagination (skip, limit)

**Solution:**

```python
from fastapi import FastAPI

app = FastAPI(title="User API")

# Fake user database
users = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    3: {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
}

@app.get("/")
def root():
    return {"message": "Welcome to User API"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = users.get(user_id)
    if not user:
        return {"error": "User not found"}
    return user

@app.get("/users")
def list_users(skip: int = 0, limit: int = 10):
    user_list = list(users.values())[skip:skip + limit]
    return {"total": len(users), "skip": skip, "limit": limit, "users": user_list}
```

---

## 🎯 Practice Exercise 2

**Task**: Create a temperature conversion API:

1. `GET /celsius-to-fahrenheit?celsius=X`
2. `GET /fahrenheit-to-celsius?fahrenheit=X`

**Solution:**

```python
from fastapi import FastAPI

app = FastAPI(title="Temperature Converter")

@app.get("/celsius-to-fahrenheit")
def celsius_to_fahrenheit(celsius: float):
    fahrenheit = (celsius * 9/5) + 32
    return {
        "celsius": celsius,
        "fahrenheit": round(fahrenheit, 2),
        "formula": "F = (C × 9/5) + 32"
    }

@app.get("/fahrenheit-to-celsius")
def fahrenheit_to_celsius(fahrenheit: float):
    celsius = (fahrenheit - 32) * 5/9
    return {
        "fahrenheit": fahrenheit,
        "celsius": round(celsius, 2),
        "formula": "C = (F - 32) × 5/9"
    }
```

---

## 📝 Key Takeaways

1. ✅ FastAPI is fast, easy, and has auto documentation
2. ✅ `@app.get("/path")` defines an endpoint
3. ✅ Functions return dicts → FastAPI converts to JSON
4. ✅ Type hints provide automatic validation
5. ✅ `/docs` gives interactive API documentation
6. ✅ Path parameters: `/users/{user_id}`
7. ✅ Query parameters: `/search?q=value`
8. ✅ Use `async def` for async endpoints

---

## 🎓 Quiz

1. What command runs a FastAPI application?
2. What URL shows interactive docs?
3. How do you define a path parameter?
4. What's the difference between path and query parameters?
5. What does `@app.post()` do?

**Answers:**
1. `uvicorn main:app --reload`
2. http://localhost:8000/docs
3. `/users/{user_id}` with function parameter `user_id: int`
4. Path: part of URL (`/users/123`), Query: after `?` (`?skip=0&limit=10`)
5. Defines a POST endpoint (for creating data)

---

## Next Lesson

**Lesson 2: Requests & Responses** 🎯

You'll learn:
- Request bodies with Pydantic
- Response models
- File uploads
- Error handling

---

**✅ Lesson 1 Complete! Ready for Lesson 2?**
