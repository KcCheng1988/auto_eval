"""
Health Check Router
Endpoints for API health and status
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import os

from ..schemas import HealthResponse
from ..dependencies import get_db_connection, get_s3_service
from ...repositories.sqlite_repository import SQLiteConnection
from ...storage.s3_service import S3StorageService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: SQLiteConnection = Depends(get_db_connection),
):
    """
    Check API health status

    Returns status of database and S3 connections
    """
    # Check database
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check S3
    try:
        s3_bucket = os.getenv("S3_BUCKET_NAME")
        if s3_bucket:
            s3_status = "configured"
        else:
            s3_status = "not configured"
    except Exception as e:
        s3_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        s3=s3_status,
        timestamp=datetime.now().isoformat()
    )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Evaluation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
