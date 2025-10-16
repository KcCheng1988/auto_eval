# Proposed System Architecture

This folder contains the proposed architecture for the full evaluation automation system.

## Overview

Event-driven microservices architecture with:
- State machine for workflow management
- Repository pattern for data access
- Strategy pattern for quality checks
- Task queue for async processing
- Email service for notifications
- REST API with React frontend

## Folder Structure

```
proposed_architecture/
├── domain/              # Domain models and business logic
│   ├── models.py       # UseCase, Model, etc.
│   └── state_machine.py # State machine implementation
├── repositories/        # Data access layer
│   ├── base.py         # Abstract repositories
│   └── postgres/       # PostgreSQL implementations
├── quality_checks/      # Quality check strategies
│   ├── base.py         # Abstract strategy
│   ├── date_checks.py  # Date validation
│   ├── numeric_checks.py # Numeric validation
│   ├── string_checks.py # String validation
│   ├── consistency_checks.py # Cross-field checks
│   ├── dataset_checks.py # Dataset-level checks (sample size, etc.)
│   ├── factory.py      # Strategy factory
│   ├── DATASET_CHECKS_GUIDE.md # Documentation for dataset checks
│   └── example_config_with_dataset_checks.json # Example configuration
├── services/           # Business logic services
│   ├── quality_check.py # Quality check orchestration
│   ├── evaluation.py   # Evaluation orchestration
│   ├── email.py        # Email service
│   └── file_storage.py # File storage service
├── tasks/              # Celery async tasks
│   ├── celery_app.py   # Celery configuration
│   ├── quality_checks.py # Quality check tasks
│   └── evaluations.py  # Evaluation tasks
├── api/                # FastAPI REST API
│   ├── main.py         # FastAPI app
│   └── routes/         # API endpoints
└── database/           # Database schemas
    └── schema.sql      # PostgreSQL schema
```

## Key Design Patterns

### 1. State Machine Pattern
- Manages use case lifecycle
- Validates state transitions
- Tracks history and audit trail

### 2. Repository Pattern
- Abstracts database operations
- Easy to test with mocks
- Supports multiple database backends

### 3. Strategy Pattern
- Extensible quality checks
- Configurable per field type
- Easy to add new validators

### 4. Service Layer Pattern
- Encapsulates business logic
- Coordinates between repositories
- Transaction management

### 5. Task Queue Pattern
- Async processing with Celery
- Background jobs for long-running tasks
- Retry and error handling

## Integration with Existing Code

The existing code in `src/` can be integrated as:
- `src/models/comparison_strategies/` → Used by evaluation service
- `src/evaluators/field_based_evaluator.py` → Called by evaluation tasks
- `src/analysers/field_classifier.py` → Used in template generation

## Next Steps

1. Review the proposed architecture
2. Decide which components to implement first
3. Create integration plan with existing code
4. Set up infrastructure (database, message queue, etc.)
5. Implement core components incrementally

## Technology Stack

- **Backend**: Python 3.9+ with FastAPI
- **Database**: PostgreSQL 13+
- **Message Queue**: RabbitMQ or Redis
- **Task Queue**: Celery
- **Email**: SMTP with Jinja2 templates
- **File Storage**: S3 or MinIO
- **Frontend**: React with Material-UI
- **Deployment**: Docker + Docker Compose
