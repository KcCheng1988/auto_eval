"""
Models Router
CRUD operations for AI models
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
import json
import uuid
from datetime import datetime

from ..schemas import ModelCreate, ModelUpdate, ModelResponse
from ..dependencies import get_db_connection
from ...repositories.sqlite_repository import SQLiteConnection

router = APIRouter()


@router.post("", response_model=ModelResponse, status_code=201)
async def create_model(
    model_data: ModelCreate,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Create a new AI model configuration

    - **name**: Model name (e.g., "GPT-4")
    - **model_type**: Type (e.g., "azure_openai", "bedrock")
    - **config**: Model configuration as JSON
    - **is_active**: Whether model is active
    """
    model_id = str(uuid.uuid4())

    query = """
        INSERT INTO models (id, name, model_type, config, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        model_id,
        model_data.name,
        model_data.model_type,
        json.dumps(model_data.config),
        1 if model_data.is_active else 0,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    )

    db.execute_query(query, params)

    return ModelResponse(
        id=model_id,
        name=model_data.name,
        model_type=model_data.model_type,
        config=model_data.config,
        is_active=model_data.is_active,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )


@router.get("", response_model=List[ModelResponse])
async def list_models(
    active_only: bool = False,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    List all AI models

    - **active_only**: Only return active models (default: false)
    """
    if active_only:
        query = "SELECT * FROM models WHERE is_active = 1 ORDER BY name"
    else:
        query = "SELECT * FROM models ORDER BY name"

    rows = db.execute_query(query, fetch_all=True)

    models = []
    for row in rows:
        models.append(ModelResponse(
            id=row['id'],
            name=row['name'],
            model_type=row['model_type'],
            config=json.loads(row['config']),
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ))

    return models


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Get a specific AI model by ID
    """
    query = "SELECT * FROM models WHERE id = ?"
    row = db.execute_query(query, (model_id,), fetch_one=True)

    if not row:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelResponse(
        id=row['id'],
        name=row['name'],
        model_type=row['model_type'],
        config=json.loads(row['config']),
        is_active=bool(row['is_active']),
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    update_data: ModelUpdate,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Update an AI model

    Only updates fields that are provided (partial update)
    """
    # Check if model exists
    existing = db.execute_query("SELECT * FROM models WHERE id = ?", (model_id,), fetch_one=True)
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")

    # Build update query
    updates = []
    params = []

    if update_data.name is not None:
        updates.append("name = ?")
        params.append(update_data.name)

    if update_data.model_type is not None:
        updates.append("model_type = ?")
        params.append(update_data.model_type)

    if update_data.config is not None:
        updates.append("config = ?")
        params.append(json.dumps(update_data.config))

    if update_data.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if update_data.is_active else 0)

    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())

    params.append(model_id)

    query = f"UPDATE models SET {', '.join(updates)} WHERE id = ?"
    db.execute_query(query, tuple(params))

    # Fetch updated model
    return await get_model(model_id, db)


@router.delete("/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Delete an AI model
    """
    existing = db.execute_query("SELECT * FROM models WHERE id = ?", (model_id,), fetch_one=True)
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")

    query = "DELETE FROM models WHERE id = ?"
    db.execute_query(query, (model_id,))

    return None
