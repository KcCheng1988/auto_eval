# SQLite + S3 Hybrid Architecture Guide

## Overview

This hybrid architecture combines the best of local and cloud storage:

- **SQLite** for fast local database operations (metadata, state tracking, activity logs)
- **S3** for durable cloud storage (files, datasets, results, backups)

Perfect for air-gapped CML environments with S3 access!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Evaluation System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │  SQLite (Local)  │              │   S3 (Cloud)     │     │
│  ├──────────────────┤              ├──────────────────┤     │
│  │ • Use cases      │              │ • Config files   │     │
│  │ • State machine  │◄────sync────►│ • Datasets       │     │
│  │ • Activity logs  │              │ • Results        │     │
│  │ • File metadata  │              │ • DB backups     │     │
│  └──────────────────┘              └──────────────────┘     │
│         ▲                                    ▲                │
│         │                                    │                │
│         └────────────── App Logic ──────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## What Goes Where?

### SQLite Stores:
- ✅ Use case metadata (ID, name, team, state, timestamps)
- ✅ State transitions history
- ✅ Activity logs
- ✅ Model configurations
- ✅ Evaluation status and summaries
- ✅ S3 file tracking (bucket, key, checksum)

### S3 Stores:
- ✅ Configuration files (YAML/JSON templates)
- ✅ Dataset files (CSV, Excel, etc.)
- ✅ Evaluation result files (detailed CSV/JSON)
- ✅ Database backups (scheduled backups)
- ✅ Email attachments

## Quick Start

### 1. Run Setup

```bash
python setup_hybrid_system.py
```

This will:
- Check dependencies (boto3, sqlite3)
- Create SQLite database with schema
- Test S3 connection
- Create local directories
- Save configuration to `.env` file

### 2. Configuration

The setup creates a `.env` file:

```bash
# SQLite Database
DATABASE_PATH=/path/to/evaluation_system.db

# S3 Storage
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key  # Or use IAM role
AWS_SECRET_ACCESS_KEY=your-secret

# Local directories
LOCAL_CACHE_DIR=/home/cdsw/evaluation_cache
FILE_STORAGE_PATH=/home/cdsw/evaluation_files
```

## Usage Examples

### Basic Setup

```python
import os
from proposed_architecture.repositories.sqlite_repository import (
    SQLiteConnection,
    UseCaseRepository,
    ActivityLogRepository
)
from proposed_architecture.storage.s3_service import (
    S3StorageService,
    S3FileManager
)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Initialize SQLite
db_conn = SQLiteConnection(os.getenv('DATABASE_PATH'))
use_case_repo = UseCaseRepository(db_conn)
activity_repo = ActivityLogRepository(db_conn)

# Initialize S3
s3_service = S3StorageService(
    bucket_name=os.getenv('S3_BUCKET_NAME'),
    region_name=os.getenv('S3_REGION')
)
file_manager = S3FileManager(s3_service)
```

### Creating a Use Case

```python
from proposed_architecture.domain.models import UseCase
from proposed_architecture.domain.state_machine import UseCaseState

# Create new use case
use_case = UseCase.create_new(
    name="Customer Sentiment Analysis",
    team_email="ml-team@company.com",
    initial_state=UseCaseState.TEMPLATE_GENERATION
)

# Save to SQLite
use_case_repo.create(use_case)

# Log activity
activity_repo.log_activity(
    use_case_id=use_case.id,
    activity_type='use_case_created',
    description='New use case created',
    details={'created_by': 'system'}
)

print(f"Created use case: {use_case.id}")
```

### Uploading Files to S3

```python
# Upload configuration file
config_result = file_manager.save_config_file(
    use_case_id=use_case.id,
    local_file_path='/path/to/config.yaml'
)

# Upload dataset
dataset_result = file_manager.save_dataset_file(
    use_case_id=use_case.id,
    local_file_path='/path/to/dataset.csv'
)

# Update use case with S3 paths
use_case.config_file_path = config_result['s3_key']
use_case.dataset_file_path = dataset_result['s3_key']
use_case_repo.update(use_case)

print(f"Config uploaded to: s3://{config_result['s3_bucket']}/{config_result['s3_key']}")
print(f"Dataset uploaded to: s3://{dataset_result['s3_bucket']}/{dataset_result['s3_key']}")
```

### Downloading Files from S3

```python
# Download config file
local_config_path = file_manager.get_config_file(use_case.id)
print(f"Config downloaded to: {local_config_path}")

# Download dataset
local_dataset_path = file_manager.get_dataset_file(use_case.id, file_extension='.csv')
print(f"Dataset downloaded to: {local_dataset_path}")

# Now you can use the files
import pandas as pd
df = pd.read_csv(local_dataset_path)
print(f"Dataset has {len(df)} rows")
```

### Backing Up Database

```python
# Manual backup
backup_result = s3_service.backup_database(
    db_file_path=os.getenv('DATABASE_PATH'),
    backup_prefix='backups/database/'
)

print(f"Database backed up to: s3://{backup_result['s3_bucket']}/{backup_result['s3_key']}")

# List all backups
backups = s3_service.list_backups()
for backup in backups:
    print(f"  - {backup['key']} ({backup['size']} bytes, {backup['last_modified']})")

# Get latest backup
latest = s3_service.get_latest_backup()
print(f"Latest backup: {latest['key']}")
```

### Restoring Database

```python
# Restore from backup
restored_path = s3_service.restore_database(
    backup_s3_key='backups/database/evaluation_system_20250114_120000.db',
    restore_path='/path/to/restored_database.db'
)

print(f"Database restored to: {restored_path}")
```

### State Transitions

```python
from proposed_architecture.repositories.sqlite_repository import StateTransitionRepository

transition_repo = StateTransitionRepository(db_conn)

# Record state transition
transition_repo.create({
    'use_case_id': use_case.id,
    'from_state': 'template_generation',
    'to_state': 'awaiting_config',
    'triggered_by': 'system',
    'notes': 'Template sent to team via email'
})

# Get transition history
transitions = transition_repo.get_by_use_case(use_case.id)
for t in transitions:
    print(f"{t['from_state']} → {t['to_state']} ({t['created_at']})")
```

### Querying Use Cases

```python
# Get all use cases
all_cases = use_case_repo.get_all(limit=50)
print(f"Total use cases: {len(all_cases)}")

# Find by state
awaiting = use_case_repo.find_by_state(UseCaseState.AWAITING_CONFIG)
print(f"Awaiting config: {len(awaiting)}")

# Find by team
team_cases = use_case_repo.find_by_team_email('ml-team@company.com')
print(f"ML team cases: {len(team_cases)}")

# Search by name
results = use_case_repo.search('sentiment')
print(f"Found {len(results)} cases matching 'sentiment'")
```

## Integration with Existing Code

### Using with FieldBasedEvaluator

```python
from src.evaluators.field_based_evaluator import FieldBasedEvaluator
import pandas as pd
import yaml

# Get use case from database
use_case = use_case_repo.get_by_id(use_case_id)

# Download files from S3
config_path = file_manager.get_config_file(use_case.id)
dataset_path = file_manager.get_dataset_file(use_case.id)

# Load configuration
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Load dataset
df_input = pd.read_csv(dataset_path)

# Run evaluation
evaluator = FieldBasedEvaluator(config)
results = evaluator.evaluate(df_input)

# Save results to S3
results_path = '/tmp/results.csv'
results.to_csv(results_path, index=False)

results_s3 = file_manager.save_results_file(
    use_case_id=use_case.id,
    local_file_path=results_path,
    result_type='field_evaluation'
)

# Update use case
use_case.evaluation_results = {
    's3_key': results_s3['s3_key'],
    'summary': {
        'total_rows': len(results),
        'accuracy': results['match'].mean()
    }
}
use_case.state = UseCaseState.EVALUATION_COMPLETED
use_case_repo.update(use_case)

# Log activity
activity_repo.log_activity(
    use_case_id=use_case.id,
    activity_type='evaluation_completed',
    description='Field-based evaluation completed',
    details={'results_s3_key': results_s3['s3_key']}
)
```

## Scheduled Tasks

### Daily Database Backup (Cron Job)

Create `backup_database.py`:

```python
#!/usr/bin/env python
"""Daily database backup to S3"""

import os
from datetime import datetime
from dotenv import load_dotenv
from proposed_architecture.storage.s3_service import S3StorageService

load_dotenv()

# Initialize S3
s3_service = S3StorageService(
    bucket_name=os.getenv('S3_BUCKET_NAME'),
    region_name=os.getenv('S3_REGION')
)

# Backup database
db_path = os.getenv('DATABASE_PATH')
result = s3_service.backup_database(db_path)

print(f"✅ Backup completed: {result['s3_key']}")
print(f"   Size: {result['file_size']} bytes")
print(f"   Time: {datetime.now().isoformat()}")
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/project && python backup_database.py >> /path/to/logs/backup.log 2>&1
```

### Clean Old Cache Files

Create `cleanup_cache.py`:

```python
#!/usr/bin/env python
"""Clean old cache files"""

import os
from dotenv import load_dotenv
from proposed_architecture.storage.s3_service import S3StorageService

load_dotenv()

s3_service = S3StorageService(
    bucket_name=os.getenv('S3_BUCKET_NAME'),
    region_name=os.getenv('S3_REGION'),
    local_cache_dir=os.getenv('LOCAL_CACHE_DIR')
)

# Delete files older than 7 days
s3_service.clear_cache(older_than_days=7)
print("✅ Cache cleaned")
```

## Best Practices

### 1. **Always Upload Important Files to S3**
```python
# ✅ Good: Upload to S3 for durability
s3_result = file_manager.save_dataset_file(use_case_id, local_path)
use_case.dataset_file_path = s3_result['s3_key']

# ❌ Bad: Only store locally
use_case.dataset_file_path = local_path  # Lost if CML session restarts!
```

### 2. **Use Local Cache for Performance**
```python
# ✅ Good: Download once, cache locally
local_path = s3_service.download_file(s3_key, use_cache=True)

# Process file multiple times - uses cache
for i in range(10):
    df = pd.read_csv(local_path)  # Fast!
```

### 3. **Regular Database Backups**
```python
# ✅ Good: Scheduled daily backups
# See cron job example above

# ⚠️ Also backup before major operations
s3_service.backup_database(db_path)
# ... perform risky operation ...
```

### 4. **Track Files in Database**
```python
from proposed_architecture.repositories.sqlite_repository import S3FileRepository

s3_file_repo = S3FileRepository(db_conn)

# Track uploaded file
s3_file_repo.track_upload(
    use_case_id=use_case.id,
    file_type='dataset',
    s3_bucket=s3_result['s3_bucket'],
    s3_key=s3_result['s3_key'],
    file_size=s3_result['file_size'],
    checksum=s3_result['checksum']
)

# Later: Find all files for use case
files = s3_file_repo.get_by_use_case(use_case.id)
```

### 5. **Handle Errors Gracefully**
```python
try:
    # Try S3 first
    local_path = file_manager.get_dataset_file(use_case_id)
except Exception as e:
    # Fallback to local copy if exists
    print(f"S3 download failed: {e}")
    local_path = use_case.dataset_file_path
    if not os.path.exists(local_path):
        raise FileNotFoundError("Dataset not available")
```

## Troubleshooting

### S3 Connection Issues

```python
# Test S3 connection
import boto3

s3_client = boto3.client('s3', region_name='us-east-1')
try:
    s3_client.head_bucket(Bucket='your-bucket')
    print("✅ S3 connection successful")
except Exception as e:
    print(f"❌ S3 connection failed: {e}")
```

### SQLite Database Locked

```python
# Increase timeout
conn = sqlite3.connect(db_path, timeout=30.0)

# Or use WAL mode for better concurrency
conn.execute('PRAGMA journal_mode=WAL')
```

### Large File Uploads

```python
# For files > 5GB, use multipart upload
s3_client.upload_file(
    local_path,
    bucket,
    s3_key,
    Config=boto3.s3.transfer.TransferConfig(
        multipart_threshold=1024 * 1024 * 100,  # 100MB
        max_concurrency=10
    )
)
```

## Migration from PostgreSQL

If you started with the PostgreSQL architecture:

```python
# Export from PostgreSQL
pg_conn = psycopg2.connect(...)
df_use_cases = pd.read_sql("SELECT * FROM use_cases", pg_conn)

# Import to SQLite
sqlite_conn = sqlite3.connect('evaluation_system.db')
df_use_cases.to_sql('use_cases', sqlite_conn, if_exists='append', index=False)
```

## Next Steps

1. ✅ Run `python setup_hybrid_system.py`
2. ✅ Test S3 upload/download with sample files
3. ✅ Set up daily backup cron job
4. ✅ Integrate with your existing evaluators
5. ✅ Build email service for notifications
6. ✅ Create frontend dashboard (optional)

## Support

For issues or questions:
- Check `proposed_architecture/README.md` for architecture overview
- Review `proposed_architecture/ARCHITECTURE_DIAGRAM.md` for workflows
- See `proposed_architecture/COMPLETE_CODE_REFERENCE.md` for full implementation
