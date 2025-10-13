# System Architecture Diagrams

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USERS                                     │
│  ┌──────────────┐              ┌──────────────┐                    │
│  │  DC Team     │              │ Use Case     │                    │
│  │  (Internal)  │              │ Team         │                    │
│  └──────┬───────┘              └──────┬───────┘                    │
└─────────┼──────────────────────────────┼──────────────────────────┘
          │                              │
          │ Web UI                       │ Email (Upload/Download)
          │                              │
┌─────────▼──────────────────────────────▼──────────────────────────┐
│                     FRONTEND LAYER                                 │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │              React Web Application                        │    │
│  │  • Dashboard  • Upload Files  • Monitor Status            │    │
│  │  • View Results  • Manage Queue  • Activity Log           │    │
│  └───────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬──────────────────────────────────────┘
                              │ REST API / WebSocket
┌─────────────────────────────▼──────────────────────────────────────┐
│                        API GATEWAY                                  │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                   FastAPI Backend                         │    │
│  │  • Authentication  • Authorization  • Rate Limiting        │    │
│  │  • Request Validation  • Response Formatting              │    │
│  └───────────────────────────────────────────────────────────┘    │
└───────┬─────────────────────────┬─────────────────────────┬────────┘
        │                         │                         │
┌───────▼─────────┐  ┌───────────▼─────────┐  ┌───────────▼─────────┐
│  Use Case       │  │  Quality Check      │  │  Evaluation         │
│  Service        │  │  Service            │  │  Service            │
│                 │  │                     │  │                     │
│ • Create UC     │  │ • Run validators    │  │ • Run evaluations   │
│ • Upload files  │  │ • Generate reports  │  │ • Store results     │
│ • Track state   │  │ • Update UC state   │  │ • Calculate metrics │
└───────┬─────────┘  └───────────┬─────────┘  └───────────┬─────────┘
        │                        │                         │
        │            ┌───────────▼─────────────────────────▼─────┐
        └───────────►│      Message Queue (Celery/Redis)         │
                     │  • Quality check tasks                     │
                     │  • Evaluation tasks                        │
                     │  • Notification tasks                      │
                     └───────────┬────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐  ┌───────────▼──────────┐  ┌─────────▼────────┐
│  Email         │  │  File Storage        │  │  Database        │
│  Service       │  │  (S3/MinIO)          │  │  (PostgreSQL)    │
│                │  │                      │  │                  │
│ • Templates    │  │ • Config files       │  │ • Use cases      │
│ • Attachments  │  │ • Datasets           │  │ • Models         │
│ • SMTP         │  │ • Reports            │  │ • Results        │
└────────────────┘  └──────────────────────┘  └──────────────────┘
```

## Workflow State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    Use Case Lifecycle                           │
└─────────────────────────────────────────────────────────────────┘

    [START]
       │
       ▼
┌──────────────────┐
│ TEMPLATE         │  DC generates field classification template
│ GENERATION       │  using existing FieldClassifier
└────────┬─────────┘
         │ Template ready
         ▼
┌──────────────────┐
│ TEMPLATE_SENT    │  Email sent to use case team with:
│                  │  • Config template (Excel)
└────────┬─────────┘  • Instructions
         │
         ▼
┌──────────────────┐
│ AWAITING_CONFIG  │  Waiting for team to:
│                  │  • Fill field types
└────────┬─────────┘  • Select strategies
         │ Files received via email
         ▼
┌──────────────────┐
│ CONFIG_RECEIVED  │  System receives:
│                  │  • Filled config template
└────────┬─────────┘  • MIIT evaluation dataset
         │
         ▼
┌──────────────────┐
│ CONFIG           │  Validate config file format
│ VALIDATION       │  • Check required columns
└────────┬─────────┘  • Validate field types
         │ Valid / Invalid
         ├────────────────┐
         │                ▼
         │         ┌──────────────┐
         │         │ CONFIG       │  Send email with issues
         │         │ INVALID      │  Team fixes and resubmits
         │         └──────┬───────┘
         │                │
         │◄───────────────┘
         │
         ▼
┌──────────────────┐
│ QUALITY_CHECK    │  Run quality validators:
│ RUNNING          │  • Date format checks
│                  │  • Numeric range checks
└────────┬─────────┘  • String validation
         │            • Consistency checks
         │ Pass / Fail
         ├────────────────┐
         │                ▼
         │         ┌──────────────┐
         │         │ QUALITY_     │  Generate Excel report
         │         │ CHECK_FAILED │  Send email with issues
         │         └──────┬───────┘
         │                │
         │                ▼
         │         ┌──────────────┐
         │         │ AWAITING_    │  Team reviews issues
         │         │ DATA_FIX     │  Fixes data and resubmits
         │         └──────┬───────┘
         │                │
         │◄───────────────┘ Resubmit
         │
         ▼
┌──────────────────┐
│ QUALITY_CHECK    │  All quality checks passed
│ PASSED           │  Ready for evaluation
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ EVALUATION       │  Queued for processing
│ QUEUED           │  Position in queue visible
└────────┬─────────┘  to users
         │ Worker available
         ▼
┌──────────────────┐
│ EVALUATION       │  Run FieldBasedEvaluator:
│ RUNNING          │  • Entity extraction accuracy
│                  │  • Classification metrics
└────────┬─────────┘  • Agreement rate
         │ Success / Failure
         ├────────────────┐
         │                ▼
         │         ┌──────────────┐
         │         │ EVALUATION_  │  Log error
         │         │ FAILED       │  Allow retry
         │         └──────┬───────┘
         │                │
         │◄───────────────┘ Retry
         │
         ▼
┌──────────────────┐
│ EVALUATION       │  Send success email with:
│ COMPLETED        │  • Accuracy metrics
│                  │  • Classification results
└────────┬─────────┘  • Agreement rate
         │
         ▼
┌──────────────────┐
│ ARCHIVED         │  Terminal state
│                  │  Can view historical results
└──────────────────┘

    [END]
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Template Generation                       │
└─────────────────────────────────────────────────────────────────┘

DC Team                System                      Use Case Team
   │                      │                              │
   │ Create use case      │                              │
   ├─────────────────────►│                              │
   │                      │ Generate template            │
   │                      │ (FieldClassifier)            │
   │                      │                              │
   │                      │ Send email with template     │
   │                      ├─────────────────────────────►│
   │                      │                              │
   │                      │                     Fill template
   │                      │                     Upload dataset
   │                      │                              │

┌─────────────────────────────────────────────────────────────────┐
│                  2. Quality Check Process                       │
└─────────────────────────────────────────────────────────────────┘

Use Case Team          System                    Quality Validators
   │                      │                              │
   │ Reply with files     │                              │
   ├─────────────────────►│                              │
   │                      │ Save files to storage        │
   │                      │                              │
   │                      │ Queue quality check task     │
   │                      ├─────────────────────────────►│
   │                      │                              │
   │                      │                      Run validators
   │                      │                      • Date checks
   │                      │                      • Numeric checks
   │                      │                      • String checks
   │                      │                              │
   │                      │ Quality check results        │
   │                      │◄─────────────────────────────┤
   │                      │                              │
   │ [IF FAILED]          │                              │
   │ Email with issues    │                              │
   │◄─────────────────────┤                              │
   │ (Excel report)       │                              │
   │                      │                              │
   │ Fix and resubmit     │                              │
   ├─────────────────────►│                              │
   │                      │                              │

┌─────────────────────────────────────────────────────────────────┐
│                   3. Evaluation Process                         │
└─────────────────────────────────────────────────────────────────┘

System                 Evaluator              Database
   │                      │                       │
   │ Quality checks pass  │                       │
   │                      │                       │
   │ Queue evaluation     │                       │
   ├─────────────────────►│                       │
   │                      │ Load config           │
   │                      │ Load dataset          │
   │                      │                       │
   │                      │ Run evaluation        │
   │                      │ (FieldBasedEvaluator) │
   │                      │                       │
   │                      │ Calculate metrics     │
   │                      │ • Accuracy            │
   │                      │ • Precision/Recall    │
   │                      │ • F-scores            │
   │                      │ • Agreement rate      │
   │                      │                       │
   │ Results              │                       │
   │◄─────────────────────┤                       │
   │                      │                       │
   │ Store results        │                       │
   ├──────────────────────────────────────────────►│
   │                      │                       │
   │ Send success email   │                       │
   │ to stakeholders      │                       │
   │                      │                       │
```

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                  API Request Flow                              │
└────────────────────────────────────────────────────────────────┘

Request arrives at API
        │
        ▼
┌────────────────┐
│ API Endpoint   │  FastAPI route handler
│ (main.py)      │  • Validate request
└───────┬────────┘  • Check authentication
        │
        ▼
┌────────────────┐
│ Service Layer  │  Business logic
│                │  • QualityCheckService
└───────┬────────┘  • EvaluationService
        │
        ▼
┌────────────────┐
│ Repository     │  Data access
│ Layer          │  • UseCaseRepository
└───────┬────────┘  • ModelRepository
        │
        ├────────────┬────────────┬────────────┐
        ▼            ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Database  │  │File      │  │Message   │  │Email     │
│          │  │Storage   │  │Queue     │  │Service   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## Database Entity Relationship Diagram

```
┌─────────────────────┐
│   use_cases         │
├─────────────────────┤
│ id (PK)             │
│ name                │
│ team_email          │
│ state               │◄──────┐
│ config_file_path    │       │
│ dataset_file_path   │       │
│ quality_issues      │       │
│ evaluation_results  │       │
│ created_at          │       │
│ updated_at          │       │
└─────────┬───────────┘       │
          │                   │
          │ 1:N               │ 1:N
          │                   │
          ▼                   │
┌─────────────────────┐       │
│   models            │       │
├─────────────────────┤       │
│ id (PK)             │       │
│ use_case_id (FK)    │───────┤
│ model_name          │       │
│ version             │       │
│ created_at          │       │
└─────────┬───────────┘       │
          │                   │
          │ 1:N               │
          │                   │
          ▼                   │
┌─────────────────────┐       │
│ evaluation_results  │       │
├─────────────────────┤       │
│ id (PK)             │       │
│ use_case_id (FK)    │───────┤
│ model_id (FK)       │       │
│ team                │       │
│ task_type           │       │
│ accuracy            │       │
│ classification_...  │       │
│ agreement_rate      │       │
│ evaluated_at        │       │
└─────────────────────┘       │
                              │
                              │
          ┌───────────────────┘
          │ 1:N
          │
          ▼
┌─────────────────────┐
│ state_transitions   │
├─────────────────────┤
│ id (PK)             │
│ use_case_id (FK)    │
│ from_state          │
│ to_state            │
│ triggered_by        │
│ trigger_reason      │
│ transitioned_at     │
└─────────────────────┘

          │ 1:N
          │
          ▼
┌─────────────────────┐
│ activity_log        │
├─────────────────────┤
│ id (PK)             │
│ use_case_id (FK)    │
│ activity_type       │
│ description         │
│ created_at          │
└─────────────────────┘
```

This architecture provides:
- Clear separation of concerns
- Scalable async processing
- Audit trail and monitoring
- Integration with existing code
- Email-based workflow automation
