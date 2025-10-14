"""
Example 1: Hello World API
The simplest FastAPI application

Run with:
    uvicorn examples.01_hello_world:app --reload

Then visit:
    http://localhost:8000
    http://localhost:8000/docs
"""

from fastapi import FastAPI

# Create FastAPI application
app = FastAPI(
    title="Hello World API",
    description="The simplest FastAPI example",
    version="1.0.0"
)


@app.get("/")
def root():
    """Root endpoint - returns welcome message"""
    return {"message": "Hello, World!"}


@app.get("/hello")
def hello():
    """Hello endpoint"""
    return {"message": "Hello from FastAPI!"}


@app.get("/info")
def info():
    """API information"""
    return {
        "name": "Hello World API",
        "version": "1.0.0",
        "framework": "FastAPI",
        "status": "running"
    }
