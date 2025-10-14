# Cloudera Machine Learning (CML) Deployment Guide

## Overview

This guide covers deploying the evaluation system in a **Cloudera Machine Learning environment with no internet access**, using internal repositories (JFrog/Artifactory) for dependencies.

## Architecture for Air-Gapped CML

```
┌─────────────────────────────────────────────────────────┐
│         Cloudera Machine Learning (CML)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │ CML Project  │    │ CML Session  │                 │
│  │ (API/Worker) │    │ (Interactive)│                 │
│  └──────┬───────┘    └──────┬───────┘                 │
│         │                   │                          │
│         └───────────┬───────┘                          │
│                     │                                  │
│         ┌───────────▼───────────┐                      │
│         │  PostgreSQL Database  │                      │
│         │  (CML Internal DB)    │                      │
│         └───────────────────────┘                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │                          │
         │ SMTP                     │ File Storage
         ▼                          ▼
┌─────────────────┐        ┌─────────────────┐
│ Email Server    │        │ HDFS / NFS      │
│ (Internal)      │        │ (CML Storage)   │
└─────────────────┘        └─────────────────┘
```

## Step-by-Step Setup

### 1. PostgreSQL Setup in CML

#### Option A: Use CML's Built-in PostgreSQL

CML often has PostgreSQL available. Check with your admin:

```bash
# Check if PostgreSQL is available
which psql

# If available, connect
psql -h <cml-postgres-host> -U <username> -d <database>
```

#### Option B: Install PostgreSQL in CML Project

If you have permissions to install PostgreSQL:

```bash
# In CML session terminal
# Download PostgreSQL client from internal repo
pip install --index-url https://<your-jfrog-url>/artifactory/api/pypi/pypi/simple psycopg2-binary

# Or if you have .whl files pre-downloaded
pip install /path/to/psycopg2_binary-2.9.9-cp39-cp39-linux_x86_64.whl
```

#### Option C: Request PostgreSQL Service from Admin

Most common approach for air-gapped environments:
1. Request PostgreSQL database from CML/IT admin
2. They provide: `host`, `port`, `database`, `username`, `password`
3. You create schema using provided credentials

### 2. Dependencies for Air-Gapped Environment

#### Required Python Packages

Create `requirements_airgapped.txt`:

```txt
# Core (must have)
psycopg2-binary==2.9.9
pandas==2.1.3
openpyxl==3.1.2
python-dotenv==1.0.0
Jinja2==3.1.2

# For API (if building API layer)
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# For async tasks (if using Celery)
celery==5.3.4
redis==5.0.1

# Existing dependencies (already in your src/)
# (should already be available)
```

#### Download from JFrog/Artifactory

```bash
# Method 1: Configure pip to use internal repo
pip config set global.index-url https://<your-jfrog-url>/artifactory/api/pypi/pypi/simple
pip install -r requirements_airgapped.txt

# Method 2: Download .whl files beforehand
# On machine with internet (outside CML):
pip download -r requirements_airgapped.txt -d ./wheels/

# Transfer ./wheels/ to CML, then:
pip install --no-index --find-links ./wheels/ -r requirements_airgapped.txt

# Method 3: Use internal Artifactory directly
pip install psycopg2-binary --index-url https://<jfrog-url>/artifactory/api/pypi/pypi/simple
```

### 3. Create PostgreSQL Database

#### Step 3.1: Connect to PostgreSQL

```bash
# In CML session terminal
psql -h <postgres-host> -U <username> -d postgres

# Or using Python
python3 << EOF
import psycopg2
conn = psycopg2.connect(
    host='<postgres-host>',
    port=5432,
    database='postgres',
    user='<username>',
    password='<password>'
)
print("Connected successfully!")
conn.close()
EOF
```

#### Step 3.2: Create Database

```sql
-- In psql terminal
CREATE DATABASE evaluation_system;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE evaluation_system TO <your_username>;

-- Connect to new database
\c evaluation_system
```

#### Step 3.3: Run Schema

```bash
# From CML terminal
psql -h <postgres-host> -U <username> -d evaluation_system -f proposed_architecture/database/schema.sql

# Or using Python script
python3 << EOF
import psycopg2

conn = psycopg2.connect(
    host='<postgres-host>',
    database='evaluation_system',
    user='<username>',
    password='<password>'
)

with open('proposed_architecture/database/schema.sql', 'r') as f:
    schema_sql = f.read()

with conn.cursor() as cur:
    cur.execute(schema_sql)
    conn.commit()

print("Schema created successfully!")
conn.close()
EOF
```

### 4. Configuration for CML

#### Create `.env` file (for secrets)

```bash
# .env file in project root
DATABASE_HOST=<cml-postgres-host>
DATABASE_PORT=5432
DATABASE_NAME=evaluation_system
DATABASE_USER=<username>
DATABASE_PASSWORD=<password>

# Email configuration (internal SMTP)
SMTP_HOST=<internal-smtp-host>
SMTP_PORT=587
SMTP_USERNAME=<email-username>
SMTP_PASSWORD=<email-password>
SMTP_FROM_EMAIL=auto-eval@yourcompany.com

# File storage (use CML's storage)
FILE_STORAGE_PATH=/home/cdsw/evaluation_files
```

#### Create `config.py`

```python
# proposed_architecture/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration for CML environment"""

    # Database
    DATABASE_URL = (
        f"postgresql://{os.getenv('DATABASE_USER')}:"
        f"{os.getenv('DATABASE_PASSWORD')}@"
        f"{os.getenv('DATABASE_HOST')}:"
        f"{os.getenv('DATABASE_PORT')}/"
        f"{os.getenv('DATABASE_NAME')}"
    )

    # Email
    SMTP_CONFIG = {
        'host': os.getenv('SMTP_HOST'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD'),
        'from_email': os.getenv('SMTP_FROM_EMAIL'),
        'template_dir': './email_templates'
    }

    # File Storage (use CML's local storage or HDFS)
    FILE_STORAGE_PATH = os.getenv('FILE_STORAGE_PATH', '/home/cdsw/evaluation_files')

    # CML specific
    CML_PROJECT_NAME = os.getenv('CDSW_PROJECT', 'auto_eval')
    CML_USERNAME = os.getenv('CDSW_PROJECT_OWNER', 'unknown')

config = Config()
```

### 5. PostgreSQL Repository Implementation for CML

```python
# proposed_architecture/repositories/postgres/connection.py

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import os

class DatabaseConnection:
    """PostgreSQL connection manager for CML environment"""

    _pool = None

    @classmethod
    def initialize_pool(cls, minconn=1, maxconn=10):
        """Initialize connection pool"""
        if cls._pool is None:
            cls._pool = SimpleConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                host=os.getenv('DATABASE_HOST'),
                port=int(os.getenv('DATABASE_PORT', 5432)),
                database=os.getenv('DATABASE_NAME'),
                user=os.getenv('DATABASE_USER'),
                password=os.getenv('DATABASE_PASSWORD')
            )

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get connection from pool"""
        if cls._pool is None:
            cls.initialize_pool()

        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        """Close all connections"""
        if cls._pool is not None:
            cls._pool.closeall()

# Usage example
def test_connection():
    """Test PostgreSQL connection in CML"""
    from proposed_architecture.repositories.postgres.connection import DatabaseConnection

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print(f"PostgreSQL version: {version[0]}")

                cur.execute("SELECT COUNT(*) FROM use_cases;")
                count = cur.fetchone()
                print(f"Use cases count: {count[0]}")

        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
```

### 6. Simplified Architecture for CML (No Celery)

Since CML may not have Redis/Celery, here's a simplified synchronous version:

```python
# proposed_architecture/cml_simple_runner.py

"""
Simplified runner for CML environment without Celery
Runs tasks synchronously within CML sessions
"""

from typing import Dict, Any
import logging

from .services.quality_check_service import QualityCheckService
from .services.evaluation_service import EvaluationService
from .services.email_service import EmailService
from .repositories.postgres.connection import DatabaseConnection
from .repositories.postgres.use_case_repository import PostgresUseCaseRepository

logger = logging.getLogger(__name__)

class CMLEvaluationRunner:
    """Synchronous runner for CML environment"""

    def __init__(self):
        """Initialize services"""
        # Initialize database connection
        DatabaseConnection.initialize_pool()

        # Initialize repositories
        self.use_case_repo = PostgresUseCaseRepository(DatabaseConnection)

        # Initialize services
        self.quality_check_service = QualityCheckService(self.use_case_repo)
        self.evaluation_service = EvaluationService(
            self.use_case_repo,
            self.quality_check_service
        )

        # Email service (if configured)
        from .config import config
        self.email_service = EmailService(config.SMTP_CONFIG)

    def process_use_case(
        self,
        use_case_id: str,
        config_file_path: str,
        dataset_file_path: str
    ) -> Dict[str, Any]:
        """
        Process use case synchronously in CML

        Args:
            use_case_id: Use case identifier
            config_file_path: Path to config file
            dataset_file_path: Path to dataset file

        Returns:
            Result dictionary
        """
        logger.info(f"Processing use case {use_case_id} in CML")

        try:
            # Step 1: Run quality checks
            logger.info("Running quality checks...")
            result = self.evaluation_service.process_submitted_files(
                use_case_id,
                config_file_path,
                dataset_file_path
            )

            if result['status'] == 'quality_check_failed':
                logger.warning(f"Quality checks failed: {result['issues_count']} issues")

                # Generate report
                report_df = self.quality_check_service.generate_quality_report(
                    result['issues']
                )
                report_path = f"/tmp/quality_issues_{use_case_id}.xlsx"
                report_df.to_excel(report_path, index=False)

                # Send email
                use_case = self.use_case_repo.get_by_id(use_case_id)
                self.email_service.send_quality_issues_notification(
                    use_case_id=use_case.id,
                    use_case_name=use_case.name,
                    team_email=use_case.team_email,
                    issues=[i.to_dict() for i in result['issues']],
                    report_file_path=report_path
                )

                return result

            # Step 2: Run evaluation
            logger.info("Quality checks passed. Running evaluation...")
            eval_results = self.evaluation_service.run_evaluation(use_case_id)

            # Step 3: Send success email
            use_case = self.use_case_repo.get_by_id(use_case_id)
            self.email_service.send_evaluation_success_notification(
                use_case_id=use_case.id,
                use_case_name=use_case.name,
                team_email=use_case.team_email,
                results=eval_results
            )

            logger.info("Evaluation completed successfully!")
            return {
                'status': 'completed',
                'results': eval_results
            }

        except Exception as e:
            logger.error(f"Error processing use case: {e}", exc_info=True)
            raise

# Usage in CML
if __name__ == "__main__":
    runner = CMLEvaluationRunner()

    result = runner.process_use_case(
        use_case_id="uc-001",
        config_file_path="/home/cdsw/data/config.xlsx",
        dataset_file_path="/home/cdsw/data/dataset.xlsx"
    )

    print(f"Result: {result}")
```

### 7. CML Project Structure

```
/home/cdsw/auto_eval/
├── .env                          # Secrets (don't commit!)
├── src/                          # Your existing code
│   ├── evaluators/
│   ├── analysers/
│   └── models/
├── proposed_architecture/        # New architecture
│   ├── config.py                # CML configuration
│   ├── cml_simple_runner.py     # Synchronous runner
│   ├── domain/
│   ├── quality_checks/
│   ├── repositories/
│   │   └── postgres/
│   │       ├── connection.py    # PostgreSQL connection
│   │       └── use_case_repository.py
│   ├── services/
│   └── database/
│       └── schema.sql
├── email_templates/              # Jinja2 templates
│   ├── quality_issues.html
│   └── evaluation_success.html
├── evaluation_files/             # File storage
│   ├── configs/
│   └── datasets/
└── logs/                         # Application logs
```

### 8. Testing PostgreSQL Connection in CML

```python
# test_cml_setup.py

"""Test script for CML environment setup"""

def test_postgresql_connection():
    """Test 1: PostgreSQL connection"""
    print("=" * 50)
    print("Test 1: PostgreSQL Connection")
    print("=" * 50)

    import psycopg2
    import os

    try:
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST'),
            port=int(os.getenv('DATABASE_PORT', 5432)),
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD')
        )

        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0][:50]}...")

            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = cur.fetchall()
            print(f"✅ Found {len(tables)} tables: {[t[0] for t in tables]}")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_file_storage():
    """Test 2: File storage access"""
    print("\n" + "=" * 50)
    print("Test 2: File Storage")
    print("=" * 50)

    import os

    storage_path = os.getenv('FILE_STORAGE_PATH', '/home/cdsw/evaluation_files')

    try:
        os.makedirs(storage_path, exist_ok=True)
        test_file = os.path.join(storage_path, 'test.txt')

        with open(test_file, 'w') as f:
            f.write('test')

        os.remove(test_file)
        print(f"✅ File storage accessible at: {storage_path}")
        return True
    except Exception as e:
        print(f"❌ File storage test failed: {e}")
        return False

def test_dependencies():
    """Test 3: Python dependencies"""
    print("\n" + "=" * 50)
    print("Test 3: Python Dependencies")
    print("=" * 50)

    required = ['psycopg2', 'pandas', 'openpyxl', 'jinja2']

    all_ok = True
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅ {pkg} installed")
        except ImportError:
            print(f"❌ {pkg} NOT installed")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    print("\n🔍 CML Environment Test Suite\n")

    results = {
        'PostgreSQL': test_postgresql_connection(),
        'File Storage': test_file_storage(),
        'Dependencies': test_dependencies()
    }

    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test}: {status}")

    if all(results.values()):
        print("\n🎉 All tests passed! Ready to deploy.")
    else:
        print("\n⚠️  Some tests failed. Fix issues before deploying.")
```

### 9. Deployment Checklist for CML

- [ ] Request PostgreSQL database from admin (or confirm access)
- [ ] Get database credentials: host, port, database, user, password
- [ ] Download required Python packages from JFrog/Artifactory
- [ ] Create `.env` file with credentials (don't commit!)
- [ ] Install dependencies: `pip install -r requirements_airgapped.txt`
- [ ] Run `database/schema.sql` to create tables
- [ ] Run `test_cml_setup.py` to verify everything works
- [ ] Configure email SMTP settings
- [ ] Set up file storage directory
- [ ] Test with a sample use case

### 10. Running in CML

```python
# In CML Session/Job

from proposed_architecture.cml_simple_runner import CMLEvaluationRunner

# Initialize runner
runner = CMLEvaluationRunner()

# Process a use case
result = runner.process_use_case(
    use_case_id="test-001",
    config_file_path="/home/cdsw/data/config.xlsx",
    dataset_file_path="/home/cdsw/data/dataset.xlsx"
)

print(result)
```

## Summary for CML Environment

✅ **PostgreSQL** - Primary database (already designed for it!)
✅ **Air-gapped** - All dependencies via JFrog/Artifactory
✅ **Simplified** - No Redis/Celery needed (synchronous processing)
✅ **CML-native** - Uses CML's file storage and sessions
✅ **Tested** - Includes comprehensive test script

**You're all set for CML deployment!** 🚀
