# Complete System Flow Guide

This document explains the complete flow of the evaluation system, including state machines, file uploads, and automatic triggers.

## Architecture Overview

### Two-Level State Management

The system uses **two independent state machines**:

1. **Use Case State Machine** (`UseCaseState`)
   - Manages overall use case lifecycle
   - Tracks configuration submission and validation
   - One per use case

2. **Model State Machine** (`ModelEvaluationState`)
   - Manages individual model evaluation lifecycle
   - Each model has its own independent state
   - Multiple models can be registered under one use case
   - Each model goes through: registration → quality check → evaluation

### Task Queue System

Instead of Celery/Redis (not available in closed environments), we use:
- **SimpleTaskQueue**: SQLite-based task queue
- Background worker threads
- No external dependencies
- Persistent across restarts

---

## Complete Flow: File Upload to Evaluation

### Scenario: Team Uploads Fixed Dataset

Let's trace what happens when a team uploads a corrected dataset after quality check failure.

```
Initial State:
- Use Case: "invoice_extraction_v1"
- Model 1: "gpt-4" - State: AWAITING_DATA_FIX (QC failed)
- Model 2: "claude-3" - State: AWAITING_DATA_FIX (QC failed)

User Action: Upload corrected dataset file
```

### Step-by-Step Flow

#### 1. File Upload (API Endpoint)

```python
POST /api/use-cases/{use_case_id}/models/{model_id}/upload-dataset

# Request: multipart/form-data with file
# Handler: api/routes/use_case_routes.py
```

**What Happens:**
```python
async def upload_dataset(use_case_id: str, model_id: str, file: UploadFile):
    # 1. Save file to storage (S3 or local)
    file_path = await file_storage_service.save_file(
        file,
        path=f"use_cases/{use_case_id}/models/{model_id}/dataset.xlsx"
    )

    # 2. Update model record with new file path
    model_repo.update_dataset_path(model_id, file_path)

    # 3. Get model state machine
    model_sm = model_state_repo.get_state_machine(model_id)

    # 4. Check current state
    if model_sm.current_state == ModelEvaluationState.AWAITING_DATA_FIX:
        # 5. Transition to QUALITY_CHECK_PENDING
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_PENDING,
            metadata=ModelStateTransitionMetadata(
                triggered_by=current_user_id,
                trigger_reason="Dataset file uploaded",
                file_uploaded=file_path
            )
        )

        # 6. Save updated state
        model_state_repo.save_state_machine(model_sm)

        # 7. TRIGGER: Queue quality check task
        task_queue.enqueue(
            'run_quality_check',
            args=[use_case_id, model_id],
            priority=10  # High priority
        )

        # 8. Log activity
        activity_log.create(
            use_case_id=use_case_id,
            activity_type='file_upload',
            description=f'Dataset uploaded for model {model_id}',
            metadata={'file_path': file_path, 'model_id': model_id}
        )

    return {"status": "success", "message": "File uploaded, quality check queued"}
```

#### 2. Background Worker Picks Up Task

**Worker Thread** (runs continuously):
```python
# Worker loop in SimpleTaskQueue
while running:
    task = get_next_task()  # Gets 'run_quality_check' task

    if task:
        execute_task(task)  # Calls run_quality_check(use_case_id, model_id)
```

#### 3. Quality Check Task Execution

```python
@task_queue.task(name='run_quality_check', max_retries=2)
def run_quality_check(use_case_id: str, model_id: str):
    """
    Background task to run quality checks on a model's dataset
    """
    # 1. Get model state machine
    model_sm = model_state_repo.get_state_machine(model_id)

    # 2. Verify state (should be QUALITY_CHECK_PENDING)
    if model_sm.current_state != ModelEvaluationState.QUALITY_CHECK_PENDING:
        logger.warning(f"Model {model_id} not in QUALITY_CHECK_PENDING state")
        return

    # 3. Transition to QUALITY_CHECK_RUNNING
    model_sm.transition_to(
        ModelEvaluationState.QUALITY_CHECK_RUNNING,
        metadata=ModelStateTransitionMetadata(
            triggered_by="system",
            trigger_reason="Quality check task started"
        )
    )
    model_state_repo.save_state_machine(model_sm)

    # 4. Load dataset
    model = model_repo.get(model_id)
    dataset_df = pd.read_excel(model.dataset_file_path)

    # 5. Load configuration
    use_case = use_case_repo.get(use_case_id)
    config = load_config(use_case.config_file_path)

    # 6. Run quality checks
    quality_check_service = QualityCheckService(use_case_repo)
    issues = quality_check_service.run_quality_checks(
        use_case_id=use_case_id,
        dataset_df=dataset_df,
        field_config=config['fields'],
        dataset_config=config  # Includes dataset_checks
    )

    # 7. Save quality check results
    model_repo.update_quality_issues(model_id, [i.to_dict() for i in issues])

    # 8. Transition based on results
    if quality_check_service.has_blocking_issues(issues):
        # FAILED - Transition to QUALITY_CHECK_FAILED
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_FAILED,
            metadata=ModelStateTransitionMetadata(
                triggered_by="system",
                trigger_reason="Quality check found blocking issues",
                quality_issues_count=len(issues)
            )
        )

        # Send notification to team
        email_service.send_quality_check_failure_email(
            use_case=use_case,
            model=model,
            issues=issues
        )

    else:
        # PASSED - Transition to QUALITY_CHECK_PASSED
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_PASSED,
            metadata=ModelStateTransitionMetadata(
                triggered_by="system",
                trigger_reason="Quality check passed"
            )
        )

        # Auto-transition to EVALUATION_QUEUED
        model_sm.transition_to(
            ModelEvaluationState.EVALUATION_QUEUED,
            metadata=ModelStateTransitionMetadata(
                triggered_by="system",
                trigger_reason="Auto-queued after QC pass"
            )
        )

        # TRIGGER: Queue evaluation task
        task_queue.enqueue(
            'run_evaluation',
            args=[use_case_id, model_id],
            priority=5
        )

    # 9. Save final state
    model_state_repo.save_state_machine(model_sm)

    # 10. Log activity
    activity_log.create(
        use_case_id=use_case_id,
        activity_type='quality_check_completed',
        description=f'Quality check for model {model_id}: {"PASSED" if not has_blocking_issues else "FAILED"}',
        metadata={'model_id': model_id, 'issues_count': len(issues)}
    )
```

#### 4. Evaluation Task Execution (If QC Passed)

```python
@task_queue.task(name='run_evaluation', max_retries=2)
def run_evaluation(use_case_id: str, model_id: str):
    """
    Background task to run model evaluation
    """
    # 1. Get model state
    model_sm = model_state_repo.get_state_machine(model_id)

    # 2. Verify state
    if model_sm.current_state != ModelEvaluationState.EVALUATION_QUEUED:
        logger.warning(f"Model {model_id} not in EVALUATION_QUEUED state")
        return

    # 3. Transition to EVALUATION_RUNNING
    model_sm.transition_to(
        ModelEvaluationState.EVALUATION_RUNNING,
        metadata=ModelStateTransitionMetadata(
            triggered_by="system",
            trigger_reason="Evaluation task started"
        )
    )
    model_state_repo.save_state_machine(model_sm)

    try:
        # 4. Load data
        model = model_repo.get(model_id)
        use_case = use_case_repo.get(use_case_id)
        dataset_df = pd.read_excel(model.dataset_file_path)
        config = load_config(use_case.config_file_path)

        # 5. Run evaluation using existing code
        from src.evaluators.field_based_evaluator import FieldBasedEvaluator

        evaluator = FieldBasedEvaluator()
        results = evaluator.evaluate(
            dataset_df=dataset_df,
            field_config=config['fields']
        )

        # 6. Save results
        evaluation_result = EvaluationResult.create_new(
            use_case_id=use_case_id,
            model_id=model_id,
            team=use_case.metadata.get('team', 'Unknown'),
            task_type=TaskType(config.get('task_type', 'entity_extraction'))
        )
        evaluation_result.accuracy = results.get('overall_accuracy')
        evaluation_result.classification_metrics = results.get('metrics')

        evaluation_result_repo.save(evaluation_result)

        # 7. Transition to EVALUATION_COMPLETED
        model_sm.transition_to(
            ModelEvaluationState.EVALUATION_COMPLETED,
            metadata=ModelStateTransitionMetadata(
                triggered_by="system",
                trigger_reason="Evaluation completed successfully"
            )
        )

        # 8. Send success email
        email_service.send_evaluation_complete_email(
            use_case=use_case,
            model=model,
            results=results
        )

    except Exception as e:
        # Evaluation failed
        logger.error(f"Evaluation failed for model {model_id}: {e}")

        model_sm.transition_to(
            ModelEvaluationState.EVALUATION_FAILED,
            metadata=ModelStateTransitionMetadata(
                triggered_by="system",
                trigger_reason="Evaluation failed",
                error_message=str(e)
            )
        )

        # Send failure email
        email_service.send_evaluation_failure_email(
            use_case=use_case,
            model=model,
            error=str(e)
        )

    finally:
        # Save final state
        model_state_repo.save_state_machine(model_sm)
```

---

## State Transition Diagram

### Model State Flow

```
                                [File Upload]
                                      ↓
[REGISTERED] → [QUALITY_CHECK_PENDING] → [QUALITY_CHECK_RUNNING]
                                                ↓           ↓
                                              PASS       FAIL
                                                ↓           ↓
                                 [QUALITY_CHECK_PASSED]  [QUALITY_CHECK_FAILED]
                                      ↓ (auto)                ↓
                              [EVALUATION_QUEUED]      [AWAITING_DATA_FIX]
                                      ↓                        ↓
                              [EVALUATION_RUNNING]     [File Upload Again]
                                  ↓         ↓                 ↓
                              SUCCESS   FAILURE    Back to QUALITY_CHECK_PENDING
                                  ↓         ↓
                        [EVALUATION_COMPLETED]  [EVALUATION_FAILED]
                                  ↓                     ↓
                              [ARCHIVED]            [Retry]
```

### Multiple Models Under One Use Case

```
Use Case: "invoice_extraction_v1"
    │
    ├─ Model 1: "gpt-4-v1"
    │   └─ State: EVALUATION_COMPLETED ✓
    │
    ├─ Model 2: "gpt-4-v2"
    │   └─ State: QUALITY_CHECK_RUNNING ⏳
    │
    └─ Model 3: "claude-3"
        └─ State: AWAITING_DATA_FIX ❌
```

**Each model progresses independently!**

---

## API Endpoints for Complete Flow

### 1. Create Use Case

```http
POST /api/use-cases
{
    "name": "Invoice Extraction v1",
    "team_email": "ml-team@company.com"
}

Response:
{
    "id": "uc_123",
    "state": "template_generation"
}
```

### 2. Upload Configuration

```http
POST /api/use-cases/{use_case_id}/upload-config
Content-Type: multipart/form-data

file: config.json

Response:
{
    "status": "success",
    "message": "Config uploaded, validation queued"
}
```

### 3. Register Model

```http
POST /api/use-cases/{use_case_id}/models
{
    "model_name": "gpt-4",
    "version": "2024-01-15",
    "metadata": {}
}

Response:
{
    "id": "model_456",
    "state": "registered"
}
```

### 4. Upload Dataset for Model

```http
POST /api/use-cases/{use_case_id}/models/{model_id}/upload-dataset
Content-Type: multipart/form-data

file: dataset.xlsx

Response:
{
    "status": "success",
    "message": "Dataset uploaded, quality check queued",
    "task_id": "task_789"
}

# This triggers the quality check automatically!
```

### 5. Check Model Status

```http
GET /api/use-cases/{use_case_id}/models/{model_id}/status

Response:
{
    "model_id": "model_456",
    "current_state": "quality_check_running",
    "state_history": [
        {
            "state": "registered",
            "timestamp": "2024-01-15T10:00:00"
        },
        {
            "state": "quality_check_pending",
            "timestamp": "2024-01-15T10:05:00",
            "triggered_by": "user@company.com"
        },
        {
            "state": "quality_check_running",
            "timestamp": "2024-01-15T10:05:30",
            "triggered_by": "system"
        }
    ],
    "is_blocked": false,
    "current_state_duration_seconds": 125
}
```

### 6. Get Quality Check Results

```http
GET /api/use-cases/{use_case_id}/models/{model_id}/quality-issues

Response:
{
    "model_id": "model_456",
    "passed": false,
    "issues": [
        {
            "row_number": 0,
            "field_name": "document_id",
            "issue_type": "insufficient_document_samples",
            "severity": "error",
            "message": "Only 12 unique documents found (minimum required: 30)"
        },
        {
            "row_number": 45,
            "field_name": "invoice_date",
            "issue_type": "invalid_date_format",
            "severity": "error",
            "message": "Invalid date format: '2024/13/01'"
        }
    ],
    "total_issues": 2,
    "checked_at": "2024-01-15T10:06:00"
}
```

### 7. Get All Models Under Use Case

```http
GET /api/use-cases/{use_case_id}/models

Response:
{
    "use_case_id": "uc_123",
    "models": [
        {
            "id": "model_456",
            "model_name": "gpt-4",
            "version": "2024-01-15",
            "state": "evaluation_completed",
            "created_at": "2024-01-15T10:00:00"
        },
        {
            "id": "model_789",
            "model_name": "claude-3",
            "version": "2024-01-10",
            "state": "awaiting_data_fix",
            "created_at": "2024-01-14T15:30:00"
        }
    ]
}
```

### 8. Get Evaluation Results

```http
GET /api/use-cases/{use_case_id}/models/{model_id}/results

Response:
{
    "model_id": "model_456",
    "model_name": "gpt-4",
    "accuracy": 0.87,
    "classification_metrics": {
        "precision": 0.89,
        "recall": 0.85,
        "f1_score": 0.87
    },
    "evaluated_at": "2024-01-15T10:15:00",
    "result_file_url": "/api/files/download/results_model_456.xlsx"
}
```

---

## Database Schema for State Management

### model_evaluations Table

```sql
CREATE TABLE model_evaluations (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL REFERENCES use_cases(id),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    current_state TEXT NOT NULL,  -- ModelEvaluationState enum
    dataset_file_path TEXT,
    quality_issues JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    metadata JSON,
    UNIQUE(use_case_id, model_name, version)
);

CREATE INDEX idx_model_use_case ON model_evaluations(use_case_id);
CREATE INDEX idx_model_state ON model_evaluations(current_state);
```

### model_state_history Table

```sql
CREATE TABLE model_state_history (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES model_evaluations(id),
    from_state TEXT,
    to_state TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    trigger_reason TEXT,
    file_uploaded TEXT,
    quality_issues_count INTEGER,
    error_message TEXT,
    additional_data JSON,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx_model_history ON model_state_history(model_id, timestamp);
```

---

## Automatic Triggers Summary

| Event | Trigger | Action |
|-------|---------|--------|
| **File Upload** (dataset) | User uploads file | → Queue quality check task |
| **Quality Check Pass** | QC completes successfully | → Auto-transition to EVALUATION_QUEUED<br>→ Queue evaluation task |
| **Quality Check Fail** | QC finds blocking issues | → Transition to AWAITING_DATA_FIX<br>→ Send email notification |
| **Evaluation Complete** | Evaluation succeeds | → Transition to EVALUATION_COMPLETED<br>→ Send success email |
| **Evaluation Fail** | Evaluation fails | → Transition to EVALUATION_FAILED<br>→ Send failure email |
| **Config Upload** | User uploads config | → Validate config<br>→ If valid, create default model |

---

## How the System Tracks State

### Repository Pattern

```python
class ModelEvaluationRepository:
    """Repository for model evaluations and state"""

    def save_state_machine(self, model_sm: ModelEvaluationStateMachine):
        """Save current state and history"""
        # Update current_state in model_evaluations table
        # Insert transition record in model_state_history table

    def get_state_machine(self, model_id: str) -> ModelEvaluationStateMachine:
        """Reconstruct state machine from database"""
        # Load current state and history
        # Return ModelEvaluationStateMachine instance

    def get_models_by_state(
        self,
        use_case_id: str,
        state: ModelEvaluationState
    ) -> List[ModelEvaluation]:
        """Get all models in specific state"""
```

### Example: Getting Latest State

```python
# When file is uploaded
model_sm = model_state_repo.get_state_machine(model_id)

# State machine automatically has:
# - Current state
# - Full history of transitions
# - Allowed next transitions
# - Duration in current state

if model_sm.current_state == ModelEvaluationState.AWAITING_DATA_FIX:
    # Can transition to QUALITY_CHECK_PENDING
    if model_sm.can_transition_to(ModelEvaluationState.QUALITY_CHECK_PENDING):
        model_sm.transition_to(...)
```

---

## Error Handling & Retries

### Task Queue Retries

```python
@task_queue.task(name='run_quality_check', max_retries=3)
def run_quality_check(use_case_id, model_id):
    # If this fails with exception:
    # 1. Task status → RETRYING
    # 2. Retry after delay
    # 3. If fails 3 times → FAILED
    # 4. Email notification sent
```

### State Machine Rollback

```python
# If something goes wrong, can rollback
model_sm.rollback(steps=1)  # Go back one state

# Or force a transition (use with caution)
model_sm.transition_to(
    ModelEvaluationState.QUALITY_CHECK_PENDING,
    force=True
)
```

---

## Monitoring & Debugging

### Get Task Queue Statistics

```python
GET /api/tasks/stats

Response:
{
    "pending": 5,
    "running": 2,
    "completed": 127,
    "failed": 3,
    "retrying": 1
}
```

### Get Model State Duration

```python
GET /api/models/{model_id}/state-duration

Response:
{
    "model_id": "model_456",
    "current_state": "quality_check_running",
    "duration_seconds": 45,
    "duration_human": "45 seconds"
}
```

### Activity Log

```sql
SELECT * FROM activity_log
WHERE use_case_id = 'uc_123'
ORDER BY created_at DESC;
```

Shows complete audit trail of all actions.

---

## Summary

The system automatically handles the entire flow:

1. **User uploads file** → System detects and queues QC
2. **Worker picks up task** → Runs QC in background
3. **QC completes** → System auto-transitions state
4. **If QC passes** → System auto-queues evaluation
5. **Worker picks up eval** → Runs evaluation in background
6. **Eval completes** → System updates state and sends email

**All automatic, no manual intervention needed!**

The state machines track everything, and you can query the current state of any model at any time.
