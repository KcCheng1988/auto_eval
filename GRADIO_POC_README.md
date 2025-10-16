# Gradio POC App - Model Evaluation System

Simple proof-of-concept demonstrating the model evaluation workflow with an interactive web UI.

## Features

### Page 1: Register Model
- Register new models for evaluation
- View all registered models in a table
- Track model metadata (name, version, use case)

### Page 2: Upload Files & Track State
- Select registered model from dropdown
- Upload Excel dataset files
- View real-time state transitions
- Run quality checks
- Start evaluation
- See complete state history

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_gradio.txt
```

Or install individually:
```bash
pip install gradio pandas openpyxl
```

### 2. Run the App

```bash
python gradio_app.py
```

The app will start at: **http://127.0.0.1:7860**

### 3. Try the Demo Workflow

#### Step 1: Register a Model
1. Go to "📝 Register Model" tab
2. Fill in:
   - **Use Case**: "Invoice Extraction" (default)
   - **Model Name**: "GPT-4"
   - **Version**: "2024-01-15"
3. Click "Register Model"
4. See success message with model ID
5. View model in the table below

#### Step 2: Upload Dataset
1. Go to "📤 Upload Files & Track State" tab
2. Click "🔄 Refresh Models" to see your registered model
3. Select your model from dropdown
4. See current state: **REGISTERED**
5. Prepare an Excel file (or create a sample):
   ```python
   # Quick sample dataset creation
   import pandas as pd
   df = pd.DataFrame({
       'invoice_id': range(1, 21),
       'amount': [100.0 + i*10 for i in range(20)],
       'date': ['2024-01-' + str(i).zfill(2) for i in range(1, 21)]
   })
   df.to_excel('sample_dataset.xlsx', index=False)
   ```
6. Upload the Excel file
7. Watch state change: REGISTERED → **QUALITY_CHECK_PENDING**

#### Step 3: Run Quality Check
1. Click "▶️ Run Quality Check" button
2. Watch transitions:
   - QUALITY_CHECK_PENDING → QUALITY_CHECK_RUNNING
   - QUALITY_CHECK_RUNNING → **QUALITY_CHECK_PASSED** ✓
3. If QC fails, you'll see:
   - State: QUALITY_CHECK_FAILED → **AWAITING_DATA_FIX**
   - List of issues to fix
   - Upload corrected dataset to retry

#### Step 4: Start Evaluation
1. Click "🎯 Start Evaluation" button
2. Watch rapid transitions:
   - QUALITY_CHECK_PASSED → EVALUATION_QUEUED
   - EVALUATION_QUEUED → EVALUATION_RUNNING
   - EVALUATION_RUNNING → **EVALUATION_COMPLETED** ✓
3. See simulated results (87.5% accuracy)

#### Step 5: View State History
- All state transitions are logged in the "State History" section
- See timestamps, who triggered each transition, and reasons
- Complete audit trail maintained in SQLite database

## State Machine Flow

```
┌──────────────┐
│  REGISTERED  │ ← Model just created
└──────┬───────┘
       │ Upload Dataset
       ↓
┌──────────────────────┐
│ QUALITY_CHECK_PENDING│
└──────┬───────────────┘
       │ Run QC
       ↓
┌──────────────────────┐
│ QUALITY_CHECK_RUNNING│
└──────┬───────────────┘
       │
       ├─→ PASS ─→ ┌──────────────────────┐
       │           │ QUALITY_CHECK_PASSED │
       │           └──────┬───────────────┘
       │                  │ Start Evaluation
       │                  ↓
       │           ┌──────────────────┐
       │           │ EVALUATION_QUEUED│
       │           └──────┬───────────┘
       │                  │
       │                  ↓
       │           ┌───────────────────┐
       │           │ EVALUATION_RUNNING│
       │           └──────┬────────────┘
       │                  │
       │                  ↓
       │           ┌──────────────────────┐
       │           │ EVALUATION_COMPLETED │ ✓ Done!
       │           └──────────────────────┘
       │
       └─→ FAIL ─→ ┌──────────────────────┐
                   │ QUALITY_CHECK_FAILED │
                   └──────┬───────────────┘
                          │
                          ↓
                   ┌──────────────────┐
                   │ AWAITING_DATA_FIX│ ← Upload corrected dataset
                   └──────┬───────────┘
                          │
                          └─→ Back to QUALITY_CHECK_PENDING
```

## Database

The app creates a SQLite database at `data/evaluation_poc.db` with:

### Tables

1. **use_cases** - Evaluation use cases
2. **model_evaluations** - Registered models and current state
3. **model_state_history** - Complete state transition history
4. **quality_check_results** - QC results and issues

### Inspecting the Database

```bash
# View database contents
sqlite3 data/evaluation_poc.db

# Useful queries
SELECT * FROM model_evaluations;
SELECT * FROM model_state_history ORDER BY timestamp;
SELECT * FROM quality_check_results;
```

## Quality Check Logic

The POC implements basic quality checks:

✅ **Pass Criteria**:
- Dataset has ≥ 10 rows
- Dataset has ≥ 3 columns
- File is readable

❌ **Fail Criteria**:
- Too few rows (< 10)
- Too few columns (< 3)
- File cannot be read
- File doesn't exist

## Features Demonstrated

### 1. Model State Machine
- Independent state per model
- Strict state transition rules
- Cannot skip states
- Full history tracking

### 2. File Upload Handling
- Save uploaded files to disk
- Update model record with file path
- Automatic state transition on upload

### 3. State Transition Triggers
- User actions (upload, click button)
- System actions (QC completion, evaluation)
- All logged with timestamp and reason

### 4. Multiple Models
- Register multiple models
- Each has independent state
- View all models in table
- Select any model to work with

## Architecture Components Shown

| Component | In Full System | In POC |
|-----------|---------------|--------|
| **State Machine** | Complex with many states | Simplified 10 states |
| **Repository** | Abstraction layer | Direct SQLite queries |
| **Task Queue** | SimpleTaskQueue/Celery | Synchronous buttons |
| **File Storage** | S3 or local with tracking | Local `data/` folder |
| **Quality Checks** | 15+ check types | Basic validation |
| **Evaluation** | Full ML evaluation | Simulated results |

## Extending the POC

### Add Real Quality Checks

```python
def run_quality_check(model_dropdown):
    # ... existing code ...

    # Add your real quality check logic
    from proposed_architecture.quality_checks.factory import QualityCheckFactory
    from proposed_architecture.services.quality_check_service import QualityCheckService

    quality_service = QualityCheckService(use_case_repo)
    issues = quality_service.run_quality_checks(
        use_case_id=use_case_id,
        dataset_df=df,
        field_config=config['fields'],
        dataset_config=config
    )

    qc_passed = not quality_service.has_blocking_issues(issues)
    # ... continue ...
```

### Add Real Evaluation

```python
def start_evaluation(model_dropdown):
    # ... existing code ...

    # Add your real evaluation logic
    from src.evaluators.field_based_evaluator import FieldBasedEvaluator

    evaluator = FieldBasedEvaluator()
    results = evaluator.evaluate(dataset_df, field_config)

    # Use real results instead of simulated
```

### Add Background Processing

Replace synchronous buttons with actual task queue:

```python
from proposed_architecture.tasks.simple_task_queue import get_task_queue

task_queue = get_task_queue()

def upload_dataset(model_dropdown, file):
    # ... save file ...

    # Queue task instead of running synchronously
    task_id = task_queue.enqueue(
        'run_quality_check',
        args=[use_case_id, model_id]
    )

    return f"✅ Dataset uploaded! QC task queued: {task_id}"
```

## Troubleshooting

### "No models registered yet" in dropdown
- Go to "Register Model" tab first
- Register at least one model
- Click "🔄 Refresh Models" in Upload tab

### Quality Check always fails
- Ensure your Excel file has:
  - At least 10 rows
  - At least 3 columns
- Try the sample dataset creation code above

### Database locked error
- Close any SQLite browser connections
- Restart the Gradio app

### Port 7860 already in use
```python
# Change port in gradio_app.py
app.launch(server_port=7861)  # Use different port
```

## Next Steps

After trying the POC:

1. **Integrate Real Components**
   - Replace simulated QC with actual quality check service
   - Replace simulated evaluation with real evaluator
   - Add task queue for background processing

2. **Add More Features**
   - Multiple file uploads (config + dataset)
   - View quality check details
   - Download evaluation results
   - Compare multiple models

3. **Deploy**
   - Replace Gradio with FastAPI (production-ready)
   - Add authentication
   - Use PostgreSQL instead of SQLite
   - Deploy to cloud

## Screenshots

### Register Model Page
![Register Model](screenshots/register_model.png)
- Simple form to create new models
- Table showing all registered models

### Upload Files Page
![Upload Files](screenshots/upload_files.png)
- Dropdown to select model
- File upload widget
- Action buttons for QC and evaluation
- Real-time state display with history

## Summary

This POC demonstrates:
- ✅ Model registration
- ✅ File upload handling
- ✅ State machine transitions
- ✅ State history tracking
- ✅ Quality check workflow
- ✅ Evaluation workflow
- ✅ Interactive web UI

**Perfect for understanding the system flow before building the full production version!**

Enjoy exploring the evaluation workflow! 🚀
