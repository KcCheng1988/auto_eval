# REST API Documentation

Complete API documentation for the Evaluation System.

## 📚 Table of Contents
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Use Cases](#use-cases)
  - [Models](#models)
  - [Evaluations](#evaluations)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn python-multipart
```

### 2. Set Environment Variables

Create `.env` file:

```bash
DATABASE_PATH=evaluation_system.db
S3_BUCKET_NAME=your-bucket
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

### 3. Run the API

```bash
# From project root
python -m proposed_architecture.api.main

# Or using uvicorn directly
uvicorn proposed_architecture.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Authentication

**Current**: No authentication (development mode)

**Production**: Add JWT authentication (TODO)

```python
# Future implementation
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify JWT token
    pass
```

---

## Endpoints

### Base URL

```
http://localhost:8000/api/v1
```

---

## Health Check

### GET /health

Check API health status

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "s3": "configured",
  "timestamp": "2025-01-14T12:00:00"
}
```

---

## Use Cases

### POST /api/v1/use-cases

Create a new use case

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/use-cases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Sentiment Analysis",
    "team_email": "ml-team@company.com"
  }'
```

**Response:** `201 Created`
```json
{
  "id": "uc-20250114120000",
  "name": "Customer Sentiment Analysis",
  "team_email": "ml-team@company.com",
  "state": "template_generation",
  "config_file_path": null,
  "dataset_file_path": null,
  "quality_issues": null,
  "evaluation_results": null,
  "created_at": "2025-01-14T12:00:00",
  "updated_at": "2025-01-14T12:00:00"
}
```

---

### GET /api/v1/use-cases

List use cases with pagination and filters

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 10, max: 100)
- `state` (string): Filter by state
- `team_email` (string): Filter by team email

**Request:**
```bash
# Get all use cases
curl http://localhost:8000/api/v1/use-cases

# Get page 2 with 20 items
curl "http://localhost:8000/api/v1/use-cases?page=2&page_size=20"

# Filter by state
curl "http://localhost:8000/api/v1/use-cases?state=awaiting_config"

# Filter by team
curl "http://localhost:8000/api/v1/use-cases?team_email=ml-team@company.com"
```

**Response:**
```json
{
  "total": 25,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": "uc-001",
      "name": "Sentiment Analysis",
      "team_email": "ml-team@company.com",
      "state": "evaluation_completed",
      "created_at": "2025-01-14T12:00:00",
      "updated_at": "2025-01-14T14:30:00"
    },
    // ... more items
  ]
}
```

---

### GET /api/v1/use-cases/{use_case_id}

Get specific use case

**Request:**
```bash
curl http://localhost:8000/api/v1/use-cases/uc-001
```

**Response:**
```json
{
  "id": "uc-001",
  "name": "Customer Sentiment Analysis",
  "team_email": "ml-team@company.com",
  "state": "evaluation_completed",
  "config_file_path": "evaluation_system/configs/uc-001/config.yaml",
  "dataset_file_path": "evaluation_system/datasets/uc-001/dataset.csv",
  "quality_issues": null,
  "evaluation_results": {
    "accuracy": 0.952,
    "precision": 0.948,
    "recall": 0.956
  },
  "created_at": "2025-01-14T12:00:00",
  "updated_at": "2025-01-14T14:30:00"
}
```

---

### PATCH /api/v1/use-cases/{use_case_id}

Update use case (partial update)

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/v1/use-cases/uc-001 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "team_email": "new-team@company.com"
  }'
```

**Response:**
```json
{
  "id": "uc-001",
  "name": "Updated Name",
  "team_email": "new-team@company.com",
  // ... other fields
}
```

---

### DELETE /api/v1/use-cases/{use_case_id}

Delete use case

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/use-cases/uc-001
```

**Response:** `204 No Content`

---

### GET /api/v1/use-cases/{use_case_id}/state

Get current state and available transitions

**Request:**
```bash
curl http://localhost:8000/api/v1/use-cases/uc-001/state
```

**Response:**
```json
{
  "current_state": "awaiting_config",
  "available_transitions": [
    "config_received",
    "cancelled",
    "on_hold"
  ]
}
```

---

### POST /api/v1/use-cases/{use_case_id}/transition

Transition use case to new state

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/use-cases/uc-001/transition \
  -H "Content-Type: application/json" \
  -d '{
    "to_state": "config_received",
    "triggered_by": "ml-team@company.com",
    "notes": "Team submitted config and dataset"
  }'
```

**Response:**
```json
{
  "id": "uc-001",
  "name": "Customer Sentiment Analysis",
  "state": "config_received",
  // ... other fields
}
```

**Error Response (invalid transition):**
```json
{
  "error": "Invalid transition from awaiting_config to evaluation_running. Valid transitions: ['config_received', 'cancelled', 'on_hold']",
  "status_code": 400
}
```

---

### GET /api/v1/use-cases/{use_case_id}/history

Get state transition history

**Request:**
```bash
curl http://localhost:8000/api/v1/use-cases/uc-001/history
```

**Response:**
```json
{
  "use_case_id": "uc-001",
  "current_state": "evaluation_completed",
  "history": [
    {
      "from_state": null,
      "to_state": "template_generation",
      "triggered_by": "system",
      "notes": "Use case created",
      "timestamp": "2025-01-14T12:00:00"
    },
    {
      "from_state": "template_generation",
      "to_state": "template_sent",
      "triggered_by": "dc_user@company.com",
      "notes": "Template sent to team",
      "timestamp": "2025-01-14T12:05:00"
    },
    // ... more transitions
  ]
}
```

---

### POST /api/v1/use-cases/{use_case_id}/upload-config

Upload configuration file

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/use-cases/uc-001/upload-config \
  -F "file=@config.yaml"
```

**Response:**
```json
{
  "file_id": "file-123",
  "file_type": "config",
  "s3_bucket": "eval-bucket",
  "s3_key": "evaluation_system/configs/uc-001/config.yaml",
  "file_size": 2048,
  "checksum": "a1b2c3d4e5f6...",
  "uploaded_at": "2025-01-14T12:10:00"
}
```

---

### POST /api/v1/use-cases/{use_case_id}/upload-dataset

Upload dataset file

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/use-cases/uc-001/upload-dataset \
  -F "file=@dataset.csv"
```

**Response:**
```json
{
  "file_id": "file-124",
  "file_type": "dataset",
  "s3_bucket": "eval-bucket",
  "s3_key": "evaluation_system/datasets/uc-001/dataset.csv",
  "file_size": 524288,
  "checksum": "f6e5d4c3b2a1...",
  "uploaded_at": "2025-01-14T12:15:00"
}
```

---

## Models

### POST /api/v1/models

Create AI model configuration

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-4",
    "model_type": "azure_openai",
    "config": {
      "endpoint": "https://your-endpoint.openai.azure.com",
      "deployment": "gpt-4",
      "api_version": "2023-05-15"
    },
    "is_active": true
  }'
```

**Response:** `201 Created`
```json
{
  "id": "model-123",
  "name": "GPT-4",
  "model_type": "azure_openai",
  "config": {
    "endpoint": "https://your-endpoint.openai.azure.com",
    "deployment": "gpt-4",
    "api_version": "2023-05-15"
  },
  "is_active": true,
  "created_at": "2025-01-14T12:00:00",
  "updated_at": "2025-01-14T12:00:00"
}
```

---

### GET /api/v1/models

List all models

**Query Parameters:**
- `active_only` (bool): Only return active models

**Request:**
```bash
# Get all models
curl http://localhost:8000/api/v1/models

# Get only active models
curl "http://localhost:8000/api/v1/models?active_only=true"
```

**Response:**
```json
[
  {
    "id": "model-123",
    "name": "GPT-4",
    "model_type": "azure_openai",
    "config": {...},
    "is_active": true,
    "created_at": "2025-01-14T12:00:00",
    "updated_at": "2025-01-14T12:00:00"
  },
  // ... more models
]
```

---

## Evaluations

### POST /api/v1/evaluations

Start new evaluation

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "use_case_id": "uc-001",
    "model_id": "model-123"
  }'
```

**Response:** `201 Created`
```json
{
  "id": "eval-456",
  "use_case_id": "uc-001",
  "model_id": "model-123",
  "status": "running",
  "summary": null,
  "result_file_path": null,
  "error_message": null,
  "started_at": "2025-01-14T12:20:00",
  "completed_at": null,
  "created_at": "2025-01-14T12:20:00"
}
```

---

### GET /api/v1/evaluations/{evaluation_id}

Get evaluation status

**Request:**
```bash
curl http://localhost:8000/api/v1/evaluations/eval-456
```

**Response:**
```json
{
  "id": "eval-456",
  "use_case_id": "uc-001",
  "model_id": "model-123",
  "status": "completed",
  "summary": {
    "accuracy": 0.952,
    "precision": 0.948,
    "recall": 0.956,
    "f1_score": 0.952
  },
  "result_file_path": "evaluation_system/results/uc-001/evaluation_20250114.csv",
  "error_message": null,
  "started_at": "2025-01-14T12:20:00",
  "completed_at": "2025-01-14T12:25:00",
  "created_at": "2025-01-14T12:20:00"
}
```

---

### GET /api/v1/evaluations/use-case/{use_case_id}

Get all evaluations for a use case

**Request:**
```bash
curl http://localhost:8000/api/v1/evaluations/use-case/uc-001
```

**Response:**
```json
[
  {
    "id": "eval-456",
    "use_case_id": "uc-001",
    "status": "completed",
    "started_at": "2025-01-14T12:20:00",
    "completed_at": "2025-01-14T12:25:00"
  },
  {
    "id": "eval-789",
    "use_case_id": "uc-001",
    "status": "running",
    "started_at": "2025-01-14T13:00:00",
    "completed_at": null
  }
]
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "Error description",
  "detail": "Detailed error message",
  "status_code": 400
}
```

### Common Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid data format |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid field value |
| 500 | Internal Server Error | Server error |

### Example Validation Error

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/use-cases \
  -H "Content-Type: application/json" \
  -d '{"name": ""}'  # Missing team_email
```

**Response:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "team_email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Complete Example: Full Workflow

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Create use case
response = requests.post(f"{BASE_URL}/use-cases", json={
    "name": "Sentiment Analysis",
    "team_email": "ml-team@company.com"
})
use_case = response.json()
use_case_id = use_case["id"]
print(f"Created use case: {use_case_id}")

# 2. Upload config file
with open("config.yaml", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/use-cases/{use_case_id}/upload-config",
        files={"file": f}
    )
print("Config uploaded")

# 3. Upload dataset
with open("dataset.csv", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/use-cases/{use_case_id}/upload-dataset",
        files={"file": f}
    )
print("Dataset uploaded")

# 4. Transition to next state
response = requests.post(
    f"{BASE_URL}/use-cases/{use_case_id}/transition",
    json={
        "to_state": "config_received",
        "triggered_by": "api_user",
        "notes": "Files uploaded via API"
    }
)
print(f"State: {response.json()['state']}")

# 5. Start evaluation
response = requests.post(f"{BASE_URL}/evaluations", json={
    "use_case_id": use_case_id
})
evaluation = response.json()
evaluation_id = evaluation["id"]
print(f"Started evaluation: {evaluation_id}")

# 6. Check evaluation status
response = requests.get(f"{BASE_URL}/evaluations/{evaluation_id}")
result = response.json()
print(f"Status: {result['status']}")
if result['status'] == 'completed':
    print(f"Summary: {result['summary']}")
```

---

## Next Steps

1. ✅ Review the [FastAPI Tutorial](../fastapi_course/README.md)
2. ✅ Check [HYBRID_GUIDE.md](HYBRID_GUIDE.md) for SQLite + S3 usage
3. ✅ See [STATE_MACHINE_TUTORIAL.md](STATE_MACHINE_TUTORIAL.md) for workflow
4. ✅ Run `python -m proposed_architecture.api.main` to start the API

---

**For questions or issues, refer to the interactive docs at `/docs`**
