"""
Example 2: Path Parameters
Extract values from URL path

Run with:
    uvicorn examples.02_path_params:app --reload

Test with:
    http://localhost:8000/users/123
    http://localhost:8000/items/laptop
    http://localhost:8000/products/999/reviews/5
"""

from fastapi import FastAPI
from enum import Enum

app = FastAPI(title="Path Parameters Example")


# Simple path parameter
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID (integer)"""
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }


# String path parameter
@app.get("/items/{item_name}")
def get_item(item_name: str):
    """Get item by name (string)"""
    return {
        "item_name": item_name,
        "price": 99.99,
        "in_stock": True
    }


# Multiple path parameters
@app.get("/products/{product_id}/reviews/{review_id}")
def get_review(product_id: int, review_id: int):
    """Get specific review for a product"""
    return {
        "product_id": product_id,
        "review_id": review_id,
        "rating": 5,
        "comment": "Great product!"
    }


# Enum path parameter (predefined values)
class Category(str, Enum):
    electronics = "electronics"
    books = "books"
    clothing = "clothing"


@app.get("/categories/{category}")
def get_category(category: Category):
    """
    Get items by category

    Only accepts: electronics, books, or clothing
    """
    return {
        "category": category.value,
        "items": [f"item1 in {category.value}", f"item2 in {category.value}"]
    }


# Path parameter with validation
@app.get("/age/{age}")
def check_age(age: int):
    """Check if age is valid"""
    if age < 0:
        return {"error": "Age cannot be negative"}
    elif age < 18:
        return {"age": age, "status": "minor"}
    else:
        return {"age": age, "status": "adult"}
