# Lesson 3: Data Validation

**Duration**: 30 minutes
**Difficulty**: Intermediate

---

## Advanced Pydantic Validation

Pydantic provides powerful validation beyond basic type hints.

---

## Email Validation

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class User(BaseModel):
    username: str
    email: EmailStr  # Validates email format

@app.post("/users")
def create_user(user: User):
    return user
```

**Install email validator:**
```bash
pip install pydantic[email]
```

**Test:**
```bash
# Valid email
curl -X POST http://localhost:8000/users \
  -d '{"username": "alice", "email": "alice@example.com"}'

# Invalid email
curl -X POST http://localhost:8000/users \
  -d '{"username": "alice", "email": "not-an-email"}'
```

---

## Enum Validation

```python
from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum

app = FastAPI()

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    guest = "guest"

class User(BaseModel):
    username: str
    role: UserRole  # Must be one of the enum values

@app.post("/users")
def create_user(user: User):
    return {
        "username": user.username,
        "role": user.role,
        "is_admin": user.role == UserRole.admin
    }
```

**Only accepts:** `"admin"`, `"user"`, or `"guest"`

---

## Custom Validators

```python
from fastapi import FastAPI
from pydantic import BaseModel, validator

app = FastAPI()

class User(BaseModel):
    username: str
    password: str
    password_confirm: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

@app.post("/register")
def register(user: User):
    return {"username": user.username, "message": "User registered"}
```

**Test:**
```bash
# Valid
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice123",
    "password": "SecurePass1",
    "password_confirm": "SecurePass1"
  }'

# Invalid: password too weak
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice123",
    "password": "weak",
    "password_confirm": "weak"
  }'
```

---

## Field Validators

```python
from pydantic import BaseModel, Field, validator

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, le=1000000)
    discount: float = Field(0, ge=0, le=100)

    @validator('discount')
    def check_discount(cls, v, values):
        if v > 0 and 'price' in values:
            discounted_price = values['price'] * (1 - v / 100)
            if discounted_price < 0:
                raise ValueError('Discount too large')
        return v
```

---

## Root Validators

Validate the entire model:

```python
from pydantic import BaseModel, root_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @root_validator
    def check_dates(cls, values):
        start = values.get('start_date')
        end = values.get('end_date')

        if start and end and start > end:
            raise ValueError('start_date must be before end_date')

        return values

@app.post("/bookings")
def create_booking(booking: DateRange):
    return booking
```

---

## Pre and Post Validators

```python
from pydantic import BaseModel, validator

class User(BaseModel):
    username: str
    email: str

    @validator('username', pre=True)
    def username_to_lower(cls, v):
        """Convert to lowercase before validation"""
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('email')
    def validate_email_domain(cls, v):
        """Validate after type checking"""
        if '@company.com' not in v:
            raise ValueError('Email must be from company.com domain')
        return v
```

---

## Constrained Types

```python
from pydantic import BaseModel, constr, conint, confloat

class Product(BaseModel):
    name: constr(min_length=1, max_length=100, regex=r'^[a-zA-Z0-9 ]+$')
    quantity: conint(ge=0, le=1000)
    price: confloat(gt=0.0, le=1000000.0)
    sku: constr(regex=r'^[A-Z]{3}-\d{4}$')  # Format: ABC-1234

@app.post("/products")
def create_product(product: Product):
    return product
```

**Test:**
```bash
# Valid
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "quantity": 10,
    "price": 999.99,
    "sku": "LAP-1234"
  }'
```

---

## Optional and Required Fields

```python
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    # Required fields
    username: str
    email: str

    # Optional fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None

    # Optional with default
    is_active: bool = True
    role: str = "user"
```

---

## List Validation

```python
from typing import List
from pydantic import BaseModel, Field

class ShoppingCart(BaseModel):
    items: List[str] = Field(..., min_items=1, max_items=100)
    quantities: List[int] = Field(..., min_items=1)

    @validator('quantities')
    def validate_quantities(cls, v):
        if any(q <= 0 for q in v):
            raise ValueError('All quantities must be positive')
        return v

@app.post("/cart")
def add_to_cart(cart: ShoppingCart):
    return cart
```

---

## Dict Validation

```python
from typing import Dict
from pydantic import BaseModel

class Settings(BaseModel):
    features: Dict[str, bool]
    limits: Dict[str, int]

    @validator('limits')
    def validate_limits(cls, v):
        for key, value in v.items():
            if value < 0:
                raise ValueError(f'{key} limit must be non-negative')
        return v

@app.post("/settings")
def update_settings(settings: Settings):
    return settings
```

**Test:**
```json
{
  "features": {
    "email_notifications": true,
    "sms_alerts": false
  },
  "limits": {
    "max_users": 100,
    "max_storage_gb": 50
  }
}
```

---

## Date and Time Validation

```python
from datetime import date, datetime
from pydantic import BaseModel, Field

class Event(BaseModel):
    name: str
    event_date: date  # Format: YYYY-MM-DD
    start_time: datetime  # ISO 8601 format
    duration_minutes: int = Field(..., ge=1, le=1440)

@app.post("/events")
def create_event(event: Event):
    return {
        "name": event.name,
        "date": event.event_date.isoformat(),
        "start": event.start_time.isoformat()
    }
```

**Test:**
```json
{
  "name": "Conference",
  "event_date": "2025-06-15",
  "start_time": "2025-06-15T09:00:00",
  "duration_minutes": 120
}
```

---

## URL Validation

```python
from pydantic import BaseModel, HttpUrl

class Website(BaseModel):
    name: str
    url: HttpUrl  # Validates URL format

@app.post("/websites")
def add_website(website: Website):
    return website
```

---

## UUID Validation

```python
from uuid import UUID
from pydantic import BaseModel

class Resource(BaseModel):
    id: UUID
    name: str

@app.post("/resources")
def create_resource(resource: Resource):
    return resource
```

**Test:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Resource 1"
}
```

---

## File Size Validation

```python
from pydantic import BaseModel, validator

class FileUpload(BaseModel):
    filename: str
    size_bytes: int

    @validator('size_bytes')
    def validate_size(cls, v):
        max_size = 10 * 1024 * 1024  # 10 MB
        if v > max_size:
            raise ValueError(f'File size must not exceed {max_size} bytes')
        return v

    @validator('filename')
    def validate_extension(cls, v):
        allowed = ['.jpg', '.png', '.pdf', '.docx']
        if not any(v.lower().endswith(ext) for ext in allowed):
            raise ValueError(f'File must be one of: {", ".join(allowed)}')
        return v
```

---

## Practical Example: Order Validation System

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List
from enum import Enum
from datetime import datetime

app = FastAPI(title="Order Validation System")

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=100)
    price: float = Field(..., gt=0)

    @validator('price')
    def validate_price(cls, v):
        if v > 100000:
            raise ValueError('Price seems unusually high')
        return round(v, 2)

class ShippingAddress(BaseModel):
    street: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zipcode: str = Field(..., regex=r'^\d{5}(-\d{4})?$')

class Order(BaseModel):
    customer_email: EmailStr
    items: List[OrderItem] = Field(..., min_items=1, max_items=50)
    shipping_address: ShippingAddress
    status: OrderStatus = OrderStatus.pending
    notes: str = Field("", max_length=500)

    @validator('items')
    def validate_items(cls, v):
        total = sum(item.quantity for item in v)
        if total > 100:
            raise ValueError('Total quantity cannot exceed 100 items')
        return v

    @property
    def total_amount(self):
        return sum(item.quantity * item.price for item in self.items)

@app.post("/orders")
def create_order(order: Order):
    if order.total_amount > 10000:
        raise HTTPException(
            status_code=400,
            detail="Order total exceeds maximum allowed amount"
        )

    return {
        "message": "Order created successfully",
        "order": order,
        "total": order.total_amount,
        "created_at": datetime.now().isoformat()
    }
```

**Test:**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "items": [
      {"product_id": 1, "quantity": 2, "price": 29.99},
      {"product_id": 2, "quantity": 1, "price": 49.99}
    ],
    "shipping_address": {
      "street": "123 Main Street",
      "city": "New York",
      "state": "NY",
      "zipcode": "10001"
    },
    "notes": "Please deliver after 5 PM"
  }'
```

---

## 🎯 Practice Exercise

**Task**: Create a user profile API with strict validation:

1. Username: 3-20 chars, alphanumeric + underscore only
2. Email: valid email format
3. Age: 13-120
4. Phone: US format (XXX-XXX-XXXX)
5. Bio: max 500 chars
6. Website: valid URL (optional)
7. Social handles: list of strings, each 3-30 chars

**Solution:**

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl
from typing import Optional, List

app = FastAPI()

class UserProfile(BaseModel):
    username: str = Field(..., regex=r'^[a-zA-Z0-9_]{3,20}$')
    email: EmailStr
    age: int = Field(..., ge=13, le=120)
    phone: str = Field(..., regex=r'^\d{3}-\d{3}-\d{4}$')
    bio: str = Field("", max_length=500)
    website: Optional[HttpUrl] = None
    social_handles: List[str] = Field(default_factory=list)

    @validator('social_handles')
    def validate_handles(cls, v):
        for handle in v:
            if not (3 <= len(handle) <= 30):
                raise ValueError('Each handle must be 3-30 characters')
        return v

    @validator('bio')
    def clean_bio(cls, v):
        return v.strip()

@app.post("/profiles")
def create_profile(profile: UserProfile):
    return {
        "message": "Profile created",
        "profile": profile
    }
```

---

## 📝 Key Takeaways

1. ✅ Use `EmailStr` for email validation
2. ✅ Use `Enum` for predefined choices
3. ✅ Write custom validators with `@validator`
4. ✅ Use `@root_validator` for cross-field validation
5. ✅ Use constrained types (`constr`, `conint`, etc.)
6. ✅ Validate lists, dicts, dates, URLs, UUIDs
7. ✅ Chain validators (pre/post validation)
8. ✅ Provide clear error messages

---

## Next Lesson

**Lesson 4: Advanced Topics** 🎯

You'll learn:
- Dependency injection
- Database integration
- File uploads
- Background tasks
- Middleware

---

**✅ Lesson 3 Complete! Ready for Lesson 4?**
