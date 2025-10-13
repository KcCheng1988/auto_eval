# Complete Code Reference

This document contains all the code implementations for the proposed architecture.
Each section can be copied into the appropriate file when ready to implement.

## Directory Structure

```
proposed_architecture/
├── domain/
│   ├── models.py ✓ (created)
│   └── state_machine.py ✓ (created)
├── repositories/
│   ├── base.py
│   └── postgres/
│       ├── use_case_repository.py
│       └── model_repository.py
├── quality_checks/
│   ├── base.py ✓ (created)
│   ├── date_checks.py
│   ├── numeric_checks.py
│   ├── string_checks.py
│   ├── consistency_checks.py
│   └── factory.py
├── services/
│   ├── quality_check_service.py
│   ├── evaluation_service.py
│   ├── email_service.py
│   └── file_storage_service.py
├── tasks/
│   ├── celery_app.py
│   ├── quality_check_tasks.py
│   └── evaluation_tasks.py
├── api/
│   ├── main.py
│   └── routes/
│       ├── use_cases.py
│       └── evaluations.py
└── database/
    └── schema.sql
```

## Implementation Priority

### Phase 1: Core Domain & Data Layer (Week 1-2)
1. ✓ Domain models (models.py)
2. ✓ State machine (state_machine.py)
3. Database schema
4. Repository implementations
5. Unit tests for domain logic

### Phase 2: Quality Checks (Week 3)
1. ✓ Quality check base classes
2. Date/Numeric/String validators
3. Consistency checkers
4. Quality check service
5. Unit tests for validators

### Phase 3: Services & Business Logic (Week 4-5)
1. File storage service
2. Evaluation service
3. Email service with templates
4. Integration tests

### Phase 4: Async Processing (Week 6)
1. Celery configuration
2. Quality check tasks
3. Evaluation tasks
4. Task monitoring

### Phase 5: API Layer (Week 7-8)
1. FastAPI setup
2. Authentication & authorization
3. API endpoints
4. API documentation

### Phase 6: Frontend (Week 9-10)
1. React setup
2. Dashboard components
3. File upload UI
4. Status monitoring

### Phase 7: Integration & Deployment (Week 11-12)
1. Docker containers
2. Docker Compose orchestration
3. CI/CD pipeline
4. Production deployment

## Key Files to Implement

### 1. Database Schema (database/schema.sql)

```sql
-- Use cases table
CREATE TABLE use_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    team_email VARCHAR(255) NOT NULL,
    state VARCHAR(50) NOT NULL,
    config_file_path VARCHAR(500),
    dataset_file_path VARCHAR(500),
    quality_issues JSONB,
    evaluation_results JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Models table
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(use_case_id, model_name, version)
);

-- State transitions audit log
CREATE TABLE state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    triggered_by VARCHAR(100),
    trigger_reason TEXT,
    metadata JSONB DEFAULT '{}',
    transitioned_at TIMESTAMP DEFAULT NOW()
);

-- Evaluation results table
CREATE TABLE evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    team VARCHAR(10) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    accuracy FLOAT,
    classification_metrics JSONB,
    agreement_rate FLOAT,
    metadata JSONB DEFAULT '{}',
    evaluated_at TIMESTAMP DEFAULT NOW()
);

-- Activity log table
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_use_cases_state ON use_cases(state);
CREATE INDEX idx_use_cases_team_email ON use_cases(team_email);
CREATE INDEX idx_use_cases_created_at ON use_cases(created_at DESC);
CREATE INDEX idx_state_transitions_use_case ON state_transitions(use_case_id);
CREATE INDEX idx_evaluation_results_use_case ON evaluation_results(use_case_id);
CREATE INDEX idx_activity_log_use_case ON activity_log(use_case_id);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_use_cases_updated_at
    BEFORE UPDATE ON use_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 2. Docker Compose (docker-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: evaluation_system
      POSTGRES_USER: eval_user
      POSTGRES_PASSWORD: eval_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./proposed_architecture/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  celery_worker:
    build: .
    command: celery -A tasks.celery_app worker --loglevel=info -Q quality_checks,evaluations
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://eval_user:eval_password@postgres:5432/evaluation_system
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0

  celery_beat:
    build: .
    command: celery -A tasks.celery_app beat --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://eval_user:eval_password@postgres:5432/evaluation_system
      CELERY_BROKER_URL: redis://redis:6379/0

  api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - postgres
      - redis
      - minio
    environment:
      DATABASE_URL: postgresql://eval_user:eval_password@postgres:5432/evaluation_system
      CELERY_BROKER_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
    ports:
      - "8000:8000"
    volumes:
      - .:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
    environment:
      REACT_APP_API_URL: http://localhost:8000

volumes:
  postgres_data:
  minio_data:
```

### 3. Requirements (requirements.txt)

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Task Queue
celery==5.3.4
redis==5.0.1

# Data Processing
pandas==2.1.3
openpyxl==3.1.2

# Email
jinja2==3.1.2
python-multipart==0.0.6

# File Storage
boto3==1.29.7
minio==7.2.0

# Quality Checks (use existing comparison strategies)
# Already have: src/models/comparison_strategies/

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.1

# Utilities
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

## Integration with Existing Code

### How to Use Existing Evaluators

```python
# In evaluation_service.py

from src.evaluators.field_based_evaluator import FieldBasedEvaluator
from src.models.evaluation_models import TaskType

def run_evaluation(use_case_id: str):
    # Load use case
    use_case = use_case_repo.get_by_id(use_case_id)

    # Load configuration
    evaluator = FieldBasedEvaluator.from_config_file(use_case.config_file_path)

    # Load dataset
    df = pd.read_excel(use_case.dataset_file_path)

    # Run evaluation
    results = evaluator.evaluate_dataset(df)

    # Get metrics summary
    summary = evaluator.get_metrics_summary(results)

    # Store results
    use_case.evaluation_results = summary
    use_case_repo.update(use_case)

    return summary
```

### How to Use Existing Field Classifier

```python
# In template generation

from src.analysers.field_classifier import FieldClassifier

def generate_config_template(dataset_path: str) -> pd.DataFrame:
    # Load dataset
    df = pd.read_excel(dataset_path)

    # Classify fields
    classifier = FieldClassifier()
    classifications = classifier.classify_fields(df)

    # Generate template with suggestions
    template_data = []
    for field_name, classification in classifications.items():
        template_data.append({
            'field_name': field_name,
            'field_type': classification['type'],  # Suggested
            'comparison_strategy': classification['strategy'],  # Suggested
            'preprocessing_options': {},
            'confidence': classification.get('confidence', 0)
        })

    template_df = pd.DataFrame(template_data)
    return template_df
```

## Next Steps

1. **Review this architecture** with your team
2. **Choose Phase 1 tasks** to start implementation
3. **Set up infrastructure** (PostgreSQL, Redis, MinIO)
4. **Create Git branch** for new architecture
5. **Implement incrementally** following the phase plan

## Notes

- All existing code in `src/` remains functional
- New system will integrate with existing evaluators
- Can migrate gradually, service by service
- Database migrations needed for production deployment
