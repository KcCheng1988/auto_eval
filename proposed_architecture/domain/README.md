# Domain Layer

This directory contains the core business models and logic for the auto_eval system.

## Structure

```
domain/
├── __init__.py              # Exports all domain models for easy importing
├── enums.py                 # Business enums (TaskType, IssueSeverity)
├── use_case.py              # UseCase domain model
├── model.py                 # Model domain model
├── evaluation_result.py     # EvaluationResult domain model
├── quality_check.py         # QualityIssue domain model
├── activity_log.py          # ActivityLog domain model
├── state_machine.py         # UseCaseStateMachine (workflow management)
└── model_state_machine.py   # ModelEvaluationStateMachine (workflow management)
```

## Domain Models

### Core Entities

#### **UseCase** (`use_case.py`)
Represents an evaluation use case submitted by a team.
- Tracks workflow state via `UseCaseStateMachine`
- Can contain multiple models being evaluated
- Stores configuration, dataset paths, and quality issues

#### **Model** (`model.py`)
Represents a specific model version being evaluated within a use case.
- Identified by name and version
- Tracks its own state via `ModelEvaluationStateMachine`
- Contains model-specific metadata

#### **EvaluationResult** (`evaluation_result.py`)
Stores the results of evaluating a specific model.
- Contains accuracy, metrics, agreement rates
- Links to both use case and model
- Timestamped for historical tracking

#### **QualityIssue** (`quality_check.py`)
Represents a data quality problem found during validation.
- Contains row number, field name, and issue details
- Categorized by severity (ERROR, WARNING, INFO)
- Includes suggestions for fixing

#### **ActivityLog** (`activity_log.py`)
Audit trail entry for tracking system activities.
- Records who did what and when
- Contains structured metadata
- Used for debugging and compliance

### Enums

#### **TaskType** (`enums.py`)
Types of evaluation tasks:
- `ENTITY_EXTRACTION`
- `CLASSIFICATION`
- `CLASSIFICATION_AND_EXTRACTION`
- `SUMMARIZATION`
- `CONTEXT_REWRITING`

#### **IssueSeverity** (`enums.py`)
Quality issue severity levels:
- `ERROR` - Blocks evaluation, must be fixed
- `WARNING` - Should be reviewed, doesn't block
- `INFO` - Informational only

### State Machines

#### **UseCaseStateMachine** (`state_machine.py`)
Manages use case workflow lifecycle:
- Template generation → Configuration → Quality checks → Evaluation
- Validates state transitions
- Tracks state history
- Provides business logic methods (`is_terminal_state()`, `can_transition_to()`)

#### **ModelEvaluationStateMachine** (`model_state_machine.py`)
Manages individual model evaluation lifecycle:
- Registration → Quality checks → Evaluation → Completion
- Independent state per model (allows parallel evaluation)
- Provides methods like `is_blocked()`, `can_start_evaluation()`

## Usage

### Importing Domain Models

```python
# Import specific models
from proposed_architecture.domain import UseCase, Model, EvaluationResult
from proposed_architecture.domain import QualityIssue, ActivityLog

# Import enums
from proposed_architecture.domain import TaskType, IssueSeverity

# Import state machines
from proposed_architecture.domain import (
    UseCaseState,
    UseCaseStateMachine,
    ModelEvaluationState,
    ModelEvaluationStateMachine
)
```

### Creating New Objects

```python
# Create NEW use case (generates ID, timestamps)
use_case = UseCase.create_new(
    name="Customer Support Evaluation",
    team_email="team@example.com",
    initial_state=UseCaseState.TEMPLATE_GENERATION
)

# Create NEW model
model = Model.create_new(
    use_case_id=use_case.id,
    model_name="GPT-4",
    version="2024-01"
)

# Create NEW evaluation result
result = EvaluationResult.create_new(
    use_case_id=use_case.id,
    model_id=model.id,
    team="OPS",
    task_type=TaskType.CLASSIFICATION
)
```

### Loading Existing Objects (from Database)

```python
# Reconstruct from database row
use_case = UseCase.from_dict(dict(db_row))
model = Model.from_dict(dict(db_row))
result = EvaluationResult.from_dict(dict(db_row))
```

### Serializing Objects (for Database/API)

```python
# Serialize to dict
use_case_data = use_case.to_dict()
model_data = model.to_dict()

# Save to database
db.execute("INSERT INTO use_cases (...) VALUES (...)", use_case_data)

# Return from API
return jsonify(use_case.to_dict())
```

### Using State Machines

```python
# Create state machine
state_machine = ModelEvaluationStateMachine(
    model_id="model-123",
    use_case_id="uc-456",
    initial_state=ModelEvaluationState.REGISTERED
)

# Transition states
metadata = ModelStateTransitionMetadata(
    triggered_by="system",
    trigger_reason="Quality check completed"
)
state_machine.transition_to(ModelEvaluationState.QUALITY_CHECK_PASSED, metadata)

# Query state
if state_machine.is_blocked():
    print("Model needs attention!")

if state_machine.can_start_evaluation():
    run_evaluation(model_id)
```

## Design Principles

### 1. Factory Methods
Each domain model provides two factory methods:
- **`create_new()`** - For creating NEW objects (generates IDs, timestamps)
- **`from_dict()`** - For reconstructing EXISTING objects from database/API

### 2. Serialization
All models provide:
- **`to_dict()`** - Converts to dictionary for storage/API responses
- Handles enum → string, datetime → ISO format conversions

### 3. Business Logic
Domain models encapsulate business rules:
- `UseCase.is_ready_for_evaluation()` - Domain logic, not in repository
- `QualityIssue.is_blocking()` - Domain concept of what blocks evaluation
- `ModelEvaluationStateMachine.can_start_evaluation()` - Workflow rules

### 4. Single Responsibility
Each file contains exactly one domain concept:
- Easier to find and modify
- Clear dependencies
- Reduces merge conflicts

### 5. No Infrastructure Dependencies
Domain models do NOT depend on:
- ❌ Repositories
- ❌ Database connections
- ❌ External services (email, S3, etc.)
- ❌ Framework-specific code

They only depend on:
- ✅ Standard library (datetime, uuid, dataclasses)
- ✅ Other domain models
- ✅ Domain enums

## Testing Domain Models

```python
# Domain models are easy to test - no mocks needed!
def test_use_case_serialization():
    # Create
    original = UseCase.create_new(
        name="Test",
        team_email="test@example.com",
        initial_state=UseCaseState.TEMPLATE_GENERATION
    )

    # Serialize
    data = original.to_dict()

    # Deserialize
    restored = UseCase.from_dict(data)

    # Verify
    assert restored.id == original.id
    assert restored.name == original.name

def test_state_machine_transitions():
    # No database needed!
    sm = ModelEvaluationStateMachine(
        model_id="m1",
        use_case_id="uc1",
        initial_state=ModelEvaluationState.REGISTERED
    )

    # Test transitions
    sm.transition_to(ModelEvaluationState.QUALITY_CHECK_PENDING)
    assert sm.current_state == ModelEvaluationState.QUALITY_CHECK_PENDING

    # Test business logic
    assert not sm.is_blocked()
    assert not sm.can_start_evaluation()
```

## When to Add New Domain Models

Create a new domain model when:
- ✅ It represents a core business concept
- ✅ It has business logic/rules to encapsulate
- ✅ It needs to be passed between layers
- ✅ It has validation requirements

Don't create a domain model when:
- ❌ It's just a database table with no behavior
- ❌ It's an implementation detail (join tables, history tables)
- ❌ It's better represented as an enum or primitive type
- ❌ It's only used within one service/repository

## Related Documentation

- [Quality Checks](../quality_checks/README.md) - Quality check strategies
- [Repositories](../repositories/README.md) - Data access layer
- [Services](../services/README.md) - Business orchestration layer
