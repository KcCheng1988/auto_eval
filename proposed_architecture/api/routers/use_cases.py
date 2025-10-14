"""
Use Cases Router
CRUD operations and state management for use cases
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional
import json
from datetime import datetime

from ..schemas import (
    UseCaseCreate,
    UseCaseUpdate,
    UseCaseResponse,
    UseCaseListResponse,
    StateTransition,
    StateInfo,
    StateHistoryResponse,
    FileUploadResponse
)
from ..dependencies import get_db_connection, get_s3_file_manager
from ...repositories.sqlite_repository import (
    SQLiteConnection,
    UseCaseRepository,
    StateTransitionRepository,
    ActivityLogRepository,
    S3FileRepository
)
from ...domain.models import UseCase
from ...domain.state_machine import UseCaseState, UseCaseStateMachine
from ...storage.s3_service import S3FileManager

router = APIRouter()


@router.post("", response_model=UseCaseResponse, status_code=201)
async def create_use_case(
    use_case_data: UseCaseCreate,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Create a new use case

    - **name**: Use case name
    - **team_email**: Team email address
    """
    repo = UseCaseRepository(db)
    activity_repo = ActivityLogRepository(db)

    # Create new use case
    use_case = UseCase.create_new(
        name=use_case_data.name,
        team_email=use_case_data.team_email,
        initial_state=UseCaseState.TEMPLATE_GENERATION
    )

    # Save to database
    repo.create(use_case)

    # Log activity
    activity_repo.log_activity(
        use_case_id=use_case.id,
        activity_type="use_case_created",
        description=f"Use case '{use_case.name}' created",
        details={"created_by": "api"}
    )

    return UseCaseResponse(
        id=use_case.id,
        name=use_case.name,
        team_email=use_case.team_email,
        state=use_case.state.value,
        config_file_path=use_case.config_file_path,
        dataset_file_path=use_case.dataset_file_path,
        quality_issues=use_case.quality_issues,
        evaluation_results=use_case.evaluation_results,
        created_at=use_case.created_at.isoformat(),
        updated_at=use_case.updated_at.isoformat()
    )


@router.get("", response_model=UseCaseListResponse)
async def list_use_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    state: Optional[str] = Query(None, description="Filter by state"),
    team_email: Optional[str] = Query(None, description="Filter by team email"),
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    List use cases with pagination and filters

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **state**: Filter by state (optional)
    - **team_email**: Filter by team email (optional)
    """
    repo = UseCaseRepository(db)

    # Apply filters
    if state:
        try:
            state_enum = UseCaseState(state)
            use_cases = repo.find_by_state(state_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid state: {state}")
    elif team_email:
        use_cases = repo.find_by_team_email(team_email)
    else:
        offset = (page - 1) * page_size
        use_cases = repo.get_all(limit=page_size, offset=offset)

    # Convert to response models
    items = [
        UseCaseResponse(
            id=uc.id,
            name=uc.name,
            team_email=uc.team_email,
            state=uc.state.value,
            config_file_path=uc.config_file_path,
            dataset_file_path=uc.dataset_file_path,
            quality_issues=uc.quality_issues,
            evaluation_results=uc.evaluation_results,
            created_at=uc.created_at.isoformat(),
            updated_at=uc.updated_at.isoformat()
        )
        for uc in use_cases
    ]

    return UseCaseListResponse(
        total=len(items),
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{use_case_id}", response_model=UseCaseResponse)
async def get_use_case(
    use_case_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Get a specific use case by ID
    """
    repo = UseCaseRepository(db)
    use_case = repo.get_by_id(use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    return UseCaseResponse(
        id=use_case.id,
        name=use_case.name,
        team_email=use_case.team_email,
        state=use_case.state.value,
        config_file_path=use_case.config_file_path,
        dataset_file_path=use_case.dataset_file_path,
        quality_issues=use_case.quality_issues,
        evaluation_results=use_case.evaluation_results,
        created_at=use_case.created_at.isoformat(),
        updated_at=use_case.updated_at.isoformat()
    )


@router.patch("/{use_case_id}", response_model=UseCaseResponse)
async def update_use_case(
    use_case_id: str,
    update_data: UseCaseUpdate,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Update a use case

    Only updates fields that are provided (partial update)
    """
    repo = UseCaseRepository(db)
    use_case = repo.get_by_id(use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    # Update fields
    if update_data.name:
        use_case.name = update_data.name
    if update_data.team_email:
        use_case.team_email = update_data.team_email

    # Save changes
    repo.update(use_case)

    return UseCaseResponse(
        id=use_case.id,
        name=use_case.name,
        team_email=use_case.team_email,
        state=use_case.state.value,
        config_file_path=use_case.config_file_path,
        dataset_file_path=use_case.dataset_file_path,
        quality_issues=use_case.quality_issues,
        evaluation_results=use_case.evaluation_results,
        created_at=use_case.created_at.isoformat(),
        updated_at=use_case.updated_at.isoformat()
    )


@router.delete("/{use_case_id}", status_code=204)
async def delete_use_case(
    use_case_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Delete a use case
    """
    repo = UseCaseRepository(db)
    use_case = repo.get_by_id(use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    repo.delete(use_case_id)
    return None


# ============================================================================
# State Management Endpoints
# ============================================================================

@router.get("/{use_case_id}/state", response_model=StateInfo)
async def get_use_case_state(
    use_case_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Get current state and available transitions for a use case
    """
    repo = UseCaseRepository(db)
    use_case = repo.get_by_id(use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    available_transitions = UseCaseStateMachine.get_next_states(use_case.state.value)

    return StateInfo(
        current_state=use_case.state.value,
        available_transitions=available_transitions
    )


@router.post("/{use_case_id}/transition", response_model=UseCaseResponse)
async def transition_use_case_state(
    use_case_id: str,
    transition: StateTransition,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Transition use case to a new state

    - **to_state**: Target state
    - **triggered_by**: User or system triggering transition
    - **notes**: Optional notes about the transition
    """
    repo = UseCaseRepository(db)
    transition_repo = StateTransitionRepository(db)
    activity_repo = ActivityLogRepository(db)

    use_case = repo.get_by_id(use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    # Validate transition
    current_state = use_case.state.value
    if not UseCaseStateMachine.is_valid_transition(current_state, transition.to_state):
        valid_transitions = UseCaseStateMachine.get_next_states(current_state)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current_state} to {transition.to_state}. "
                   f"Valid transitions: {valid_transitions}"
        )

    # Perform transition
    old_state = use_case.state
    use_case.state = UseCaseState(transition.to_state)
    use_case.updated_at = datetime.now()

    # Save use case
    repo.update(use_case)

    # Record transition
    transition_repo.create({
        'use_case_id': use_case_id,
        'from_state': old_state.value,
        'to_state': transition.to_state,
        'triggered_by': transition.triggered_by,
        'notes': transition.notes or ""
    })

    # Log activity
    activity_repo.log_activity(
        use_case_id=use_case_id,
        activity_type="state_transition",
        description=f"State changed: {old_state.value} → {transition.to_state}",
        details={
            'from_state': old_state.value,
            'to_state': transition.to_state,
            'triggered_by': transition.triggered_by
        }
    )

    return UseCaseResponse(
        id=use_case.id,
        name=use_case.name,
        team_email=use_case.team_email,
        state=use_case.state.value,
        config_file_path=use_case.config_file_path,
        dataset_file_path=use_case.dataset_file_path,
        quality_issues=use_case.quality_issues,
        evaluation_results=use_case.evaluation_results,
        created_at=use_case.created_at.isoformat(),
        updated_at=use_case.updated_at.isoformat()
    )


@router.get("/{use_case_id}/history", response_model=StateHistoryResponse)
async def get_state_history(
    use_case_id: str,
    db: SQLiteConnection = Depends(get_db_connection)
):
    """
    Get state transition history for a use case
    """
    repo = UseCaseRepository(db)
    transition_repo = StateTransitionRepository(db)

    use_case = repo.get_by_id(use_case_id)

    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    # Get transition history
    transitions = transition_repo.get_by_use_case(use_case_id)

    return StateHistoryResponse(
        use_case_id=use_case_id,
        current_state=use_case.state.value,
        history=transitions
    )


# ============================================================================
# File Upload Endpoints
# ============================================================================

@router.post("/{use_case_id}/upload-config", response_model=FileUploadResponse)
async def upload_config_file(
    use_case_id: str,
    file: UploadFile = File(...),
    db: SQLiteConnection = Depends(get_db_connection),
    file_mgr: S3FileManager = Depends(get_s3_file_manager)
):
    """
    Upload configuration file for a use case
    """
    repo = UseCaseRepository(db)
    s3_file_repo = S3FileRepository(db)

    use_case = repo.get_by_id(use_case_id)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    # Save file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Upload to S3
        result = file_mgr.save_config_file(use_case_id, tmp_path)

        # Update use case
        use_case.config_file_path = result['s3_key']
        repo.update(use_case)

        # Track in database
        file_id = s3_file_repo.track_upload(
            use_case_id=use_case_id,
            file_type='config',
            s3_bucket=result['s3_bucket'],
            s3_key=result['s3_key'],
            local_path=tmp_path,
            file_size=result['file_size'],
            checksum=result['checksum']
        )

        return FileUploadResponse(
            file_id=file_id,
            file_type='config',
            s3_bucket=result['s3_bucket'],
            s3_key=result['s3_key'],
            file_size=result['file_size'],
            checksum=result['checksum'],
            uploaded_at=result['uploaded_at']
        )

    finally:
        # Cleanup temp file
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/{use_case_id}/upload-dataset", response_model=FileUploadResponse)
async def upload_dataset_file(
    use_case_id: str,
    file: UploadFile = File(...),
    db: SQLiteConnection = Depends(get_db_connection),
    file_mgr: S3FileManager = Depends(get_s3_file_manager)
):
    """
    Upload dataset file for a use case
    """
    repo = UseCaseRepository(db)
    s3_file_repo = S3FileRepository(db)

    use_case = repo.get_by_id(use_case_id)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    # Save file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Upload to S3
        result = file_mgr.save_dataset_file(use_case_id, tmp_path)

        # Update use case
        use_case.dataset_file_path = result['s3_key']
        repo.update(use_case)

        # Track in database
        file_id = s3_file_repo.track_upload(
            use_case_id=use_case_id,
            file_type='dataset',
            s3_bucket=result['s3_bucket'],
            s3_key=result['s3_key'],
            local_path=tmp_path,
            file_size=result['file_size'],
            checksum=result['checksum']
        )

        return FileUploadResponse(
            file_id=file_id,
            file_type='dataset',
            s3_bucket=result['s3_bucket'],
            s3_key=result['s3_key'],
            file_size=result['file_size'],
            checksum=result['checksum'],
            uploaded_at=result['uploaded_at']
        )

    finally:
        # Cleanup temp file
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
