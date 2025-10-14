"""
Pydantic Schemas for Request/Response Models
Data validation and serialization
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# Use Case Schemas
# ============================================================================

class UseCaseCreate(BaseModel):
    """Request model for creating a use case"""
    name: str = Field(..., min_length=1, max_length=255, description="Use case name")
    team_email: EmailStr = Field(..., description="Team email address")


class UseCaseUpdate(BaseModel):
    """Request model for updating a use case"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    team_email: Optional[EmailStr] = None
    state: Optional[str] = None


class StateTransition(BaseModel):
    """Request model for state transition"""
    to_state: str = Field(..., description="Target state")
    triggered_by: str = Field(..., description="User or system triggering transition")
    notes: Optional[str] = Field(None, description="Optional notes")


class UseCaseResponse(BaseModel):
    """Response model for use case"""
    id: str
    name: str
    team_email: str
    state: str
    config_file_path: Optional[str] = None
    dataset_file_path: Optional[str] = None
    quality_issues: Optional[List[Dict[str, Any]]] = None
    evaluation_results: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UseCaseListResponse(BaseModel):
    """Response model for list of use cases"""
    total: int
    page: int
    page_size: int
    items: List[UseCaseResponse]


# ============================================================================
# Model Schemas
# ============================================================================

class ModelCreate(BaseModel):
    """Request model for creating a model"""
    name: str = Field(..., min_length=1, max_length=255)
    model_type: str = Field(..., description="e.g., 'azure_openai', 'bedrock'")
    config: Dict[str, Any] = Field(..., description="Model configuration (JSON)")
    is_active: bool = Field(default=True)


class ModelUpdate(BaseModel):
    """Request model for updating a model"""
    name: Optional[str] = None
    model_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ModelResponse(BaseModel):
    """Response model for model"""
    id: str
    name: str
    model_type: str
    config: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


# ============================================================================
# Evaluation Schemas
# ============================================================================

class EvaluationRequest(BaseModel):
    """Request model for starting evaluation"""
    use_case_id: str = Field(..., description="Use case ID to evaluate")
    model_id: Optional[str] = Field(None, description="Model to use (optional)")


class EvaluationResponse(BaseModel):
    """Response model for evaluation"""
    id: str
    use_case_id: str
    model_id: str
    status: str
    summary: Optional[Dict[str, Any]] = None
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str


# ============================================================================
# Quality Check Schemas
# ============================================================================

class QualityCheckRequest(BaseModel):
    """Request model for quality check"""
    use_case_id: str = Field(..., description="Use case ID")


class QualityIssue(BaseModel):
    """Quality issue model"""
    field_name: str
    issue_type: str
    severity: str
    message: str
    affected_rows: Optional[List[int]] = None


class QualityCheckResponse(BaseModel):
    """Response model for quality check"""
    use_case_id: str
    passed: bool
    issues: List[QualityIssue]
    total_issues: int
    checked_at: str


# ============================================================================
# File Upload Schemas
# ============================================================================

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    file_id: str
    file_type: str
    s3_bucket: str
    s3_key: str
    file_size: int
    checksum: str
    uploaded_at: str


# ============================================================================
# Activity Log Schemas
# ============================================================================

class ActivityLogResponse(BaseModel):
    """Response model for activity log"""
    id: str
    use_case_id: Optional[str]
    activity_type: str
    description: str
    details: Optional[Dict[str, Any]] = None
    created_at: str


# ============================================================================
# State Machine Schemas
# ============================================================================

class StateInfo(BaseModel):
    """State information"""
    current_state: str
    available_transitions: List[str]


class StateHistoryItem(BaseModel):
    """State history item"""
    from_state: Optional[str]
    to_state: str
    triggered_by: str
    notes: Optional[str]
    timestamp: str


class StateHistoryResponse(BaseModel):
    """Response model for state history"""
    use_case_id: str
    current_state: str
    history: List[StateHistoryItem]


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    s3: str
    timestamp: str


# ============================================================================
# Statistics Schemas
# ============================================================================

class UseCaseStatistics(BaseModel):
    """Use case statistics"""
    total_use_cases: int
    by_state: Dict[str, int]
    completed_count: int
    failed_count: int
    in_progress_count: int
