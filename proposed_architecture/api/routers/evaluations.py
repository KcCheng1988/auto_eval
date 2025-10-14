"""
Evaluations Router
Endpoints for running and managing evaluations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
import json
import uuid
from datetime import datetime

from ..schemas import EvaluationRequest, EvaluationResponse
from ..dependencies import get_db_connection
from ...repositories.sqlite_repository import SQLiteConnection, UseCaseRepository

router = APIRouter()


@router.post("", response_model=EvaluationResponse, status_code=201)
async def start_evaluation(
    eval_request: EvaluationRequest,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Start a new evaluation

    - **use_case_id**: Use case to evaluate
    - **model_id**: Model to use (optional, uses default if not specified)
    """
    # Verify use case exists
    use_case_repo = UseCaseRepository(db)
    use_case = use_case_repo.get_by_id(eval_request.use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    # Check use case state
    if use_case.state.value not in ['evaluation_queued', 'evaluation_failed']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start evaluation: use case is in state '{use_case.state.value}'"
        )

    # Get model
    model_id = eval_request.model_id
    if not model_id:
        # Use default model
        row = db.execute_query(
            "SELECT id FROM models WHERE is_active = 1 LIMIT 1",
            fetch_one=True
        )
        if not row:
            raise HTTPException(status_code=400, detail="No active model found")
        model_id = row['id']

    # Create evaluation record
    eval_id = str(uuid.uuid4())

    query = """
        INSERT INTO evaluation_results (
            id, use_case_id, model_id, status, started_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """

    params = (
        eval_id,
        eval_request.use_case_id,
        model_id,
        'running',
        datetime.now().isoformat(),
        datetime.now().isoformat()
    )

    db.execute_query(query, params)

    # TODO: Trigger async evaluation task (Celery, background task, etc.)
    # For now, just return the created evaluation

    return EvaluationResponse(
        id=eval_id,
        use_case_id=eval_request.use_case_id,
        model_id=model_id,
        status='running',
        summary=None,
        result_file_path=None,
        error_message=None,
        started_at=datetime.now().isoformat(),
        completed_at=None,
        created_at=datetime.now().isoformat()
    )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Get evaluation status and results
    """
    query = "SELECT * FROM evaluation_results WHERE id = ?"
    row = db.execute_query(query, (evaluation_id,), fetch_one=True)

    if not row:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return EvaluationResponse(
        id=row['id'],
        use_case_id=row['use_case_id'],
        model_id=row['model_id'],
        status=row['status'],
        summary=json.loads(row['summary']) if row['summary'] else None,
        result_file_path=row['result_file_path'],
        error_message=row['error_message'],
        started_at=row['started_at'],
        completed_at=row['completed_at'],
        created_at=row['created_at']
    )


@router.get("/use-case/{use_case_id}", response_model=List[EvaluationResponse])
async def get_evaluations_by_use_case(
    use_case_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Get all evaluations for a use case
    """
    query = """
        SELECT * FROM evaluation_results
        WHERE use_case_id = ?
        ORDER BY created_at DESC
    """

    rows = db.execute_query(query, (use_case_id,), fetch_all=True)

    evaluations = []
    for row in rows:
        evaluations.append(EvaluationResponse(
            id=row['id'],
            use_case_id=row['use_case_id'],
            model_id=row['model_id'],
            status=row['status'],
            summary=json.loads(row['summary']) if row['summary'] else None,
            result_file_path=row['result_file_path'],
            error_message=row['error_message'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            created_at=row['created_at']
        ))

    return evaluations


@router.post("/{evaluation_id}/cancel", response_model=EvaluationResponse)
async def cancel_evaluation(
    evaluation_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Cancel a running evaluation
    """
    # Check if evaluation exists
    existing = db.execute_query(
        "SELECT * FROM evaluation_results WHERE id = ?",
        (evaluation_id,),
        fetch_one=True
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if existing['status'] != 'running':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel evaluation with status: {existing['status']}"
        )

    # Update status
    query = """
        UPDATE evaluation_results
        SET status = 'cancelled', completed_at = ?
        WHERE id = ?
    """

    db.execute_query(query, (datetime.now().isoformat(), evaluation_id))

    # TODO: Actually cancel the running task

    return await get_evaluation(evaluation_id, db)
