"""
FastAPI Main Application
Entry point for the REST API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from .routers import use_cases, models, evaluations, health
from .dependencies import get_db_connection, get_s3_service

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Evaluation System API",
    description="REST API for GenAI evaluation system with state machine workflow",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(use_cases.router, prefix="/api/v1/use-cases", tags=["Use Cases"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["Evaluations"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Starting Evaluation System API")
    print(f"📊 Database: {os.getenv('DATABASE_PATH', 'Not configured')}")
    print(f"☁️  S3 Bucket: {os.getenv('S3_BUCKET_NAME', 'Not configured')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 Shutting down Evaluation System API")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "proposed_architecture.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
