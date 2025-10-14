"""
FastAPI Dependencies
Dependency injection for database, S3, services, etc.
"""

import os
from functools import lru_cache
from typing import Generator

from ..repositories.sqlite_repository import SQLiteConnection
from ..storage.s3_service import S3StorageService, S3FileManager


@lru_cache()
def get_database_path() -> str:
    """Get database path from environment"""
    db_path = os.getenv("DATABASE_PATH", "evaluation_system.db")
    return db_path


def get_db_connection() -> Generator[SQLiteConnection, None, None]:
    """
    Dependency for database connection

    Usage:
        @app.get("/items")
        def get_items(db: SQLiteConnection = Depends(get_db_connection)):
            ...
    """
    db_path = get_database_path()
    db = SQLiteConnection(db_path)
    try:
        yield db
    finally:
        # Cleanup if needed
        pass


@lru_cache()
def get_s3_config():
    """Get S3 configuration from environment"""
    return {
        "bucket_name": os.getenv("S3_BUCKET_NAME"),
        "region_name": os.getenv("S3_REGION", "us-east-1"),
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    }


def get_s3_service() -> Generator[S3StorageService, None, None]:
    """
    Dependency for S3 service

    Usage:
        @app.post("/upload")
        def upload_file(s3: S3StorageService = Depends(get_s3_service)):
            ...
    """
    config = get_s3_config()

    if not config["bucket_name"]:
        raise ValueError("S3_BUCKET_NAME not configured")

    s3_service = S3StorageService(
        bucket_name=config["bucket_name"],
        region_name=config["region_name"],
        aws_access_key_id=config["aws_access_key_id"],
        aws_secret_access_key=config["aws_secret_access_key"],
    )

    try:
        yield s3_service
    finally:
        # Cleanup if needed
        pass


def get_s3_file_manager() -> Generator[S3FileManager, None, None]:
    """
    Dependency for S3 file manager

    Usage:
        @app.post("/save-config")
        def save_config(file_mgr: S3FileManager = Depends(get_s3_file_manager)):
            ...
    """
    s3_service = next(get_s3_service())
    file_manager = S3FileManager(s3_service)

    try:
        yield file_manager
    finally:
        pass
