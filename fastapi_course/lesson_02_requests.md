# Lesson 2: Requests & Responses

**Duration**: 45 minutes
**Difficulty**: Beginner

---

## Request Bodies with Pydantic

FastAPI uses **Pydantic** models to define and validate request bodies.

### What is Pydantic?

Pydantic is a data validation library that uses Python type hints.

**Benefits:**
- ✅ Automatic validation
- ✅ Clear error messages
- ✅ Auto-generated documentation
- ✅ Type safety

---

## Basic Request Body

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Define request model
class Item(BaseModel):
    name: str
    price: float
    description: str = None  # Optional field
    tax: float = None

@app.post("/items")
def create_item(item: Item):
    return {
        "message": "Item created",
        "item": item,
        "price_with_tax": item.price + (item.tax or 0)
    }
```

**Test it:**

```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "price": 999.99,
    "description": "Gaming laptop",
    "tax": 50.00
  }'
```

**Response:**
```json
{
  "message": "Item created",
  "item": {
    "name": "Laptop",
    "price": 999.99,
    "description": "Gaming laptop",
    "tax": 50.00
  },
  "price_with_tax": 1049.99
}
```

---

## Pydantic Field Validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    quantity: int = Field(default=1, ge=1, le=1000)
    description: str = Field(None, max_length=500)

@app.post("/items")
def create_item(item: Item):
    return {"item": item}
```

**Field parameters:**
- `...` - Required field
- `default=value` - Default value
- `min_length` / `max_length` - String length
- `gt` / `ge` - Greater than / greater or equal
- `lt` / `le` - Less than / less or equal
- `description` - Documentation

**Test with invalid data:**

```bash
# Invalid: price is 0
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "price": 0}'
```

**Error response:**
```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## Nested Models

```python
from typing import List
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str
    zipcode: str

class User(BaseModel):
    name: str
    email: str
    age: int
    address: Address  # Nested model
    tags: List[str] = []  # List of strings

@app.post("/users")
def create_user(user: User):
    return {"user": user}
```

**Request:**
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "age": 25,
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "country": "USA",
    "zipcode": "10001"
  },
  "tags": ["developer", "python"]
}
```

---

## Response Models

Define what your API returns:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # Notice: password is NOT included

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    # Simulate saving user and getting ID
    fake_user_dict = user.dict()
    fake_user_dict["id"] = 1

    # Even if we return password, FastAPI filters it out
    return fake_user_dict
```

**Benefits:**
- ✅ Filters response data (removes password)
- ✅ Validates response structure
- ✅ Generates accurate documentation

---

## Multiple Request/Response Models

```python
from typing import Optional
from pydantic import BaseModel

# Request models
class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

# Response model
class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    created_at: str

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate):
    return {
        "id": 1,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "created_at": "2025-01-14T12:00:00"
    }

@app.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate):
    return {
        "id": product_id,
        "name": product.name or "Old Name",
        "price": product.price or 99.99,
        "stock": product.stock or 10,
        "created_at": "2025-01-14T12:00:00"
    }
```

---

## Query Parameters with Validation

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/items")
def list_items(
    q: str = Query(None, min_length=3, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return {
        "query": q,
        "skip": skip,
        "limit": limit,
        "items": ["item1", "item2"]
    }
```

**Test:**
```bash
# Valid
curl "http://localhost:8000/items?q=laptop&skip=0&limit=10"

# Invalid: q too short
curl "http://localhost:8000/items?q=ab"
```

---

## Path Parameters with Validation

```python
from fastapi import Path

@app.get("/items/{item_id}")
def get_item(
    item_id: int = Path(..., title="Item ID", ge=1),
    q: str = Query(None, max_length=50)
):
    return {"item_id": item_id, "q": q}
```

---

## Combining Path, Query, and Body

```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.put("/items/{item_id}")
def update_item(
    item_id: int = Path(..., ge=1),
    item: Item = None,
    q: str = Query(None)
):
    result = {"item_id": item_id}
    if item:
        result["item"] = item
    if q:
        result["q"] = q
    return result
```

**Request:**
```bash
curl -X PUT "http://localhost:8000/items/5?q=test" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Item", "price": 29.99}'
```

---

## Status Codes

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(name: str):
    return {"name": name}

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    return None  # No content returned

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        return {"error": "Not found"}, 404
    return {"item_id": item_id}
```

**Common status codes:**
- `200` - OK (default for GET)
- `201` - Created (for POST)
- `204` - No Content (for DELETE)
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error (automatic)
- `500` - Internal Server Error

---

## Response Status Code Override

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.post("/items")
def create_item(name: str, response: Response):
    if not name:
        response.status_code = 400
        return {"error": "Name is required"}

    response.status_code = 201
    return {"name": name}
```

---

## Headers and Cookies

```python
from fastapi import FastAPI, Header, Cookie

app = FastAPI()

@app.get("/headers")
def read_headers(
    user_agent: str = Header(None),
    accept_language: str = Header(None)
):
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }

@app.get("/cookies")
def read_cookies(session_id: str = Cookie(None)):
    return {"session_id": session_id}
```

---

## Response Headers

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int, response: Response):
    response.headers["X-Custom-Header"] = "Custom Value"
    response.headers["X-Item-ID"] = str(item_id)
    return {"item_id": item_id}
```

---

## JSONResponse with Custom Status

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        return JSONResponse(
            status_code=404,
            content={"error": "Item not found"}
        )
    return {"item_id": item_id}
```

---

## Practical Example: User Registration API

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List

app = FastAPI(title="User Registration API")

# In-memory database
users_db = []

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=13, le=120)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    age: int

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    # Check if username exists
    if any(u["username"] == user.username for u in users_db):
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Check if email exists
    if any(u["email"] == user.email for u in users_db):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create user
    user_dict = user.dict()
    user_dict["id"] = len(users_db) + 1
    users_db.append(user_dict)

    return user_dict

@app.get("/users", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 10):
    return users_db[skip:skip + limit]

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user
```

**Test it:**

```bash
# Register user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "secure123",
    "age": 25
  }'

# List users
curl http://localhost:8000/users

# Get specific user
curl http://localhost:8000/users/1
```

---

## 🎯 Practice Exercise 1

**Task**: Create a blog post API with:

1. `POST /posts` - Create post (title, content, author)
2. `GET /posts` - List posts with pagination
3. `GET /posts/{post_id}` - Get specific post
4. `PUT /posts/{post_id}` - Update post

**Validation:**
- Title: 5-100 characters
- Content: required
- Author: 3-50 characters

**Solution:**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Blog API")

posts_db = []

class PostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    content: str
    author: str = Field(..., min_length=3, max_length=50)

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=100)
    content: Optional[str] = None
    author: Optional[str] = Field(None, min_length=3, max_length=50)

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str

@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    post_dict = post.dict()
    post_dict["id"] = len(posts_db) + 1
    posts_db.append(post_dict)
    return post_dict

@app.get("/posts", response_model=List[PostResponse])
def list_posts(skip: int = 0, limit: int = 10):
    return posts_db[skip:skip + limit]

@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostUpdate):
    db_post = next((p for p in posts_db if p["id"] == post_id), None)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.title:
        db_post["title"] = post.title
    if post.content:
        db_post["content"] = post.content
    if post.author:
        db_post["author"] = post.author

    return db_post
```

---

## 📝 Key Takeaways

1. ✅ Use **Pydantic models** for request/response validation
2. ✅ `response_model` filters and validates responses
3. ✅ Use `Field()` for advanced validation
4. ✅ Nest models for complex data structures
5. ✅ Set appropriate status codes
6. ✅ Use `HTTPException` for errors
7. ✅ Combine path, query, and body parameters
8. ✅ Access headers and cookies with dependencies

---

## Next Lesson

**Lesson 3: Data Validation** 🎯

You'll learn:
- Custom validators
- Email validation
- Enum validation
- Complex validation rules

---

**✅ Lesson 2 Complete! Ready for Lesson 3?**
