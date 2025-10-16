"""
Gradio POC App for Model Evaluation System

Simple proof-of-concept with two pages:
1. Register Model - Create new models for evaluation
2. Upload Files - Upload datasets and track state transitions

Run: python gradio_app.py
"""

import gradio as gr
import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import uuid

# Initialize database and directories
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "evaluation_poc.db"


# ============================================================================
# Database Setup
# ============================================================================

def init_database():
    """Initialize SQLite database with simplified schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Use cases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS use_cases (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            team_email TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Model evaluations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_evaluations (
            id TEXT PRIMARY KEY,
            use_case_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            version TEXT NOT NULL,
            current_state TEXT NOT NULL,
            dataset_file_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (use_case_id) REFERENCES use_cases(id)
        )
    ''')

    # State history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_state_history (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT NOT NULL,
            triggered_by TEXT NOT NULL,
            trigger_reason TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (model_id) REFERENCES model_evaluations(id)
        )
    ''')

    # Quality check results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quality_check_results (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            passed INTEGER NOT NULL,
            issues_count INTEGER DEFAULT 0,
            issues_detail TEXT,
            checked_at TEXT NOT NULL,
            FOREIGN KEY (model_id) REFERENCES model_evaluations(id)
        )
    ''')

    # Create default use case if none exists
    cursor.execute('SELECT COUNT(*) FROM use_cases')
    if cursor.fetchone()[0] == 0:
        default_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO use_cases (id, name, team_email, created_at)
            VALUES (?, ?, ?, ?)
        ''', (default_id, 'Demo Invoice Extraction', 'demo@example.com', datetime.now().isoformat()))

    conn.commit()
    conn.close()


# ============================================================================
# Model State Machine (Simplified)
# ============================================================================

MODEL_STATES = {
    'REGISTERED': 'Registered (waiting for dataset)',
    'QUALITY_CHECK_PENDING': 'Quality Check Pending',
    'QUALITY_CHECK_RUNNING': 'Quality Check Running',
    'QUALITY_CHECK_PASSED': 'Quality Check Passed ✓',
    'QUALITY_CHECK_FAILED': 'Quality Check Failed ✗',
    'AWAITING_DATA_FIX': 'Awaiting Data Fix',
    'EVALUATION_QUEUED': 'Evaluation Queued',
    'EVALUATION_RUNNING': 'Evaluation Running',
    'EVALUATION_COMPLETED': 'Evaluation Completed ✓',
    'EVALUATION_FAILED': 'Evaluation Failed ✗'
}

STATE_TRANSITIONS = {
    'REGISTERED': ['QUALITY_CHECK_PENDING'],
    'AWAITING_DATA_FIX': ['QUALITY_CHECK_PENDING'],
    'QUALITY_CHECK_PENDING': ['QUALITY_CHECK_RUNNING'],
    'QUALITY_CHECK_RUNNING': ['QUALITY_CHECK_PASSED', 'QUALITY_CHECK_FAILED'],
    'QUALITY_CHECK_FAILED': ['AWAITING_DATA_FIX'],
    'QUALITY_CHECK_PASSED': ['EVALUATION_QUEUED'],
    'EVALUATION_QUEUED': ['EVALUATION_RUNNING'],
    'EVALUATION_RUNNING': ['EVALUATION_COMPLETED', 'EVALUATION_FAILED'],
    'EVALUATION_FAILED': ['EVALUATION_QUEUED']
}


# ============================================================================
# Page 1: Register Model
# ============================================================================

def get_use_cases():
    """Get list of use cases"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM use_cases')
    use_cases = cursor.fetchall()
    conn.close()
    return use_cases


def register_model(use_case_name, model_name, version, description):
    """Register a new model for evaluation"""
    try:
        # Get or create use case
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM use_cases WHERE name = ?', (use_case_name,))
        result = cursor.fetchone()

        if result:
            use_case_id = result[0]
        else:
            use_case_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO use_cases (id, name, team_email, created_at)
                VALUES (?, ?, ?, ?)
            ''', (use_case_id, use_case_name, 'user@example.com', datetime.now().isoformat()))

        # Check if model already exists
        cursor.execute('''
            SELECT id FROM model_evaluations
            WHERE use_case_id = ? AND model_name = ? AND version = ?
        ''', (use_case_id, model_name, version))

        if cursor.fetchone():
            conn.close()
            return f"❌ Error: Model '{model_name}' version '{version}' already exists!"

        # Create model
        model_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO model_evaluations
            (id, use_case_id, model_name, version, current_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (model_id, use_case_id, model_name, version, 'REGISTERED', datetime.now().isoformat()))

        # Record initial state
        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            model_id,
            None,
            'REGISTERED',
            'user',
            'Model registered via Gradio app',
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return f"""✅ Model Registered Successfully!

**Model ID**: `{model_id}`
**Model Name**: {model_name}
**Version**: {version}
**Use Case**: {use_case_name}
**Current State**: REGISTERED

➡️ Go to "Upload Files" tab to upload dataset and start quality check!
"""

    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_registered_models():
    """Get list of all registered models"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            m.id,
            u.name as use_case,
            m.model_name,
            m.version,
            m.current_state,
            m.created_at
        FROM model_evaluations m
        JOIN use_cases u ON m.use_case_id = u.id
        ORDER BY m.created_at DESC
    ''')

    models = cursor.fetchall()
    conn.close()

    if not models:
        return pd.DataFrame(columns=['Model ID', 'Use Case', 'Model Name', 'Version', 'State', 'Created At'])

    df = pd.DataFrame(models, columns=['Model ID', 'Use Case', 'Model Name', 'Version', 'State', 'Created At'])
    df['State'] = df['State'].map(lambda x: MODEL_STATES.get(x, x))
    return df


# ============================================================================
# Page 2: Upload Files & State Transitions
# ============================================================================

def get_models_for_dropdown():
    """Get models for dropdown selection"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, u.name, m.model_name, m.version, m.current_state
        FROM model_evaluations m
        JOIN use_cases u ON m.use_case_id = u.id
        ORDER BY m.created_at DESC
    ''')

    models = cursor.fetchall()
    conn.close()

    if not models:
        return ["No models registered yet"]

    choices = []
    for model_id, use_case, model_name, version, state in models:
        state_display = MODEL_STATES.get(state, state)
        choices.append(f"{model_name} v{version} ({use_case}) - {state_display}")

    return choices


def get_model_id_from_dropdown(dropdown_value):
    """Extract model ID from dropdown selection"""
    if dropdown_value == "No models registered yet":
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Parse dropdown value
    parts = dropdown_value.split(' - ')
    if len(parts) < 2:
        return None

    model_info = parts[0]  # e.g., "GPT-4 v1.0 (Invoice Extraction)"

    cursor.execute('''
        SELECT m.id
        FROM model_evaluations m
        JOIN use_cases u ON m.use_case_id = u.id
    ''')

    models = cursor.fetchall()
    conn.close()

    # Return first model for POC (in production, parse properly)
    if models:
        return models[0][0]
    return None


def get_model_details(model_dropdown):
    """Get detailed information about selected model"""
    if model_dropdown == "No models registered yet":
        return "No model selected", "", ""

    # Extract model info (simplified for POC)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, u.name, m.model_name, m.version, m.current_state, m.dataset_file_path
        FROM model_evaluations m
        JOIN use_cases u ON m.use_case_id = u.id
        ORDER BY m.created_at DESC
        LIMIT 1
    ''')

    result = cursor.fetchone()

    if not result:
        conn.close()
        return "No model found", "", ""

    model_id, use_case, model_name, version, current_state, dataset_path = result

    # Get state history
    cursor.execute('''
        SELECT from_state, to_state, triggered_by, trigger_reason, timestamp
        FROM model_state_history
        WHERE model_id = ?
        ORDER BY timestamp ASC
    ''', (model_id,))

    history = cursor.fetchall()
    conn.close()

    # Build info display
    info = f"""## Model Information

**Model**: {model_name} v{version}
**Use Case**: {use_case}
**Current State**: {MODEL_STATES.get(current_state, current_state)}
**Dataset**: {dataset_path or 'Not uploaded'}

### State History:
"""

    for from_s, to_s, by, reason, ts in history:
        from_display = MODEL_STATES.get(from_s, from_s) if from_s else "Initial"
        to_display = MODEL_STATES.get(to_s, to_s)
        info += f"\n- `{ts}`: {from_display} → **{to_display}** (by {by})"

    # Determine next actions
    next_actions = STATE_TRANSITIONS.get(current_state, [])
    actions_text = "### Possible Next Actions:\n"

    if current_state in ['REGISTERED', 'AWAITING_DATA_FIX']:
        actions_text += "\n📤 **Upload Dataset** - Use the file upload below"
    elif current_state == 'QUALITY_CHECK_PENDING':
        actions_text += "\n⏳ Click 'Run Quality Check' button"
    elif current_state == 'QUALITY_CHECK_RUNNING':
        actions_text += "\n⏳ Check results after QC completes"
    elif current_state == 'QUALITY_CHECK_PASSED':
        actions_text += "\n🎯 Click 'Start Evaluation' button"
    elif current_state == 'EVALUATION_QUEUED':
        actions_text += "\n⏳ Click 'Run Evaluation' button"
    else:
        actions_text += f"\nNext possible states: {', '.join(next_actions)}"

    return info, model_id, actions_text


def upload_dataset(model_dropdown, file):
    """Handle dataset upload"""
    if not file:
        return "❌ Please select a file to upload"

    if model_dropdown == "No models registered yet":
        return "❌ Please select a model first"

    try:
        # Get model ID (simplified)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, current_state FROM model_evaluations ORDER BY created_at DESC LIMIT 1')
        result = cursor.fetchone()

        if not result:
            conn.close()
            return "❌ No model found"

        model_id, current_state = result

        # Check if state allows upload
        if current_state not in ['REGISTERED', 'AWAITING_DATA_FIX']:
            conn.close()
            return f"❌ Cannot upload dataset in state: {MODEL_STATES.get(current_state, current_state)}"

        # Save file
        file_path = DATA_DIR / f"model_{model_id}_dataset.xlsx"
        with open(file_path, 'wb') as f:
            f.write(file)

        # Update model
        cursor.execute('''
            UPDATE model_evaluations
            SET dataset_file_path = ?, current_state = ?
            WHERE id = ?
        ''', (str(file_path), 'QUALITY_CHECK_PENDING', model_id))

        # Record transition
        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            model_id,
            current_state,
            'QUALITY_CHECK_PENDING',
            'user',
            'Dataset uploaded via Gradio app',
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return f"""✅ Dataset Uploaded Successfully!

**File**: {file.name if hasattr(file, 'name') else 'dataset.xlsx'}
**Saved to**: {file_path}

**State Transition**: {MODEL_STATES[current_state]} → **Quality Check Pending**

➡️ Click "Run Quality Check" to proceed!
"""

    except Exception as e:
        return f"❌ Error uploading dataset: {str(e)}"


def run_quality_check(model_dropdown):
    """Simulate quality check execution"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, current_state, dataset_file_path
            FROM model_evaluations
            ORDER BY created_at DESC LIMIT 1
        ''')
        result = cursor.fetchone()

        if not result:
            conn.close()
            return "❌ No model found"

        model_id, current_state, dataset_path = result

        if current_state != 'QUALITY_CHECK_PENDING':
            conn.close()
            return f"❌ Cannot run QC in state: {MODEL_STATES.get(current_state, current_state)}"

        # Transition to RUNNING
        cursor.execute('''
            UPDATE model_evaluations SET current_state = ? WHERE id = ?
        ''', ('QUALITY_CHECK_RUNNING', model_id))

        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), model_id, current_state, 'QUALITY_CHECK_RUNNING',
              'system', 'QC started', datetime.now().isoformat()))

        # Simulate QC (check if file has data)
        qc_passed = True
        issues = []

        if dataset_path and Path(dataset_path).exists():
            try:
                df = pd.read_excel(dataset_path)
                if len(df) < 10:
                    qc_passed = False
                    issues.append(f"Dataset has only {len(df)} rows (minimum: 10)")
                if len(df.columns) < 3:
                    qc_passed = False
                    issues.append(f"Dataset has only {len(df.columns)} columns (minimum: 3)")
            except Exception as e:
                qc_passed = False
                issues.append(f"Cannot read dataset: {str(e)}")
        else:
            qc_passed = False
            issues.append("Dataset file not found")

        # Transition to result state
        new_state = 'QUALITY_CHECK_PASSED' if qc_passed else 'QUALITY_CHECK_FAILED'

        cursor.execute('''
            UPDATE model_evaluations SET current_state = ? WHERE id = ?
        ''', (new_state, model_id))

        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), model_id, 'QUALITY_CHECK_RUNNING', new_state,
              'system', f'QC {"passed" if qc_passed else "failed"}', datetime.now().isoformat()))

        # Save QC results
        cursor.execute('''
            INSERT INTO quality_check_results
            (id, model_id, passed, issues_count, issues_detail, checked_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), model_id, 1 if qc_passed else 0,
              len(issues), json.dumps(issues), datetime.now().isoformat()))

        if not qc_passed:
            cursor.execute('''
                UPDATE model_evaluations SET current_state = ? WHERE id = ?
            ''', ('AWAITING_DATA_FIX', model_id))

            cursor.execute('''
                INSERT INTO model_state_history
                (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), model_id, new_state, 'AWAITING_DATA_FIX',
                  'system', 'QC failed, needs fix', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        if qc_passed:
            return f"""✅ Quality Check PASSED!

**State**: QUALITY_CHECK_RUNNING → **QUALITY_CHECK_PASSED**

No issues found! Dataset is ready for evaluation.

➡️ Click "Start Evaluation" to proceed!
"""
        else:
            issues_text = '\n'.join([f"- {issue}" for issue in issues])
            return f"""❌ Quality Check FAILED!

**State**: QUALITY_CHECK_RUNNING → QUALITY_CHECK_FAILED → **AWAITING_DATA_FIX**

**Issues Found**:
{issues_text}

➡️ Please fix the issues and upload a corrected dataset.
"""

    except Exception as e:
        return f"❌ Error running quality check: {str(e)}"


def start_evaluation(model_dropdown):
    """Start model evaluation"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, current_state FROM model_evaluations ORDER BY created_at DESC LIMIT 1
        ''')
        result = cursor.fetchone()

        if not result:
            conn.close()
            return "❌ No model found"

        model_id, current_state = result

        if current_state != 'QUALITY_CHECK_PASSED':
            conn.close()
            return f"❌ Cannot start evaluation in state: {MODEL_STATES.get(current_state, current_state)}"

        # Transition to EVALUATION_QUEUED then RUNNING
        cursor.execute('''
            UPDATE model_evaluations SET current_state = ? WHERE id = ?
        ''', ('EVALUATION_QUEUED', model_id))

        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), model_id, current_state, 'EVALUATION_QUEUED',
              'user', 'Evaluation started via Gradio', datetime.now().isoformat()))

        # Simulate evaluation
        cursor.execute('''
            UPDATE model_evaluations SET current_state = ? WHERE id = ?
        ''', ('EVALUATION_RUNNING', model_id))

        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), model_id, 'EVALUATION_QUEUED', 'EVALUATION_RUNNING',
              'system', 'Evaluation running', datetime.now().isoformat()))

        # Complete evaluation
        cursor.execute('''
            UPDATE model_evaluations SET current_state = ? WHERE id = ?
        ''', ('EVALUATION_COMPLETED', model_id))

        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by, trigger_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), model_id, 'EVALUATION_RUNNING', 'EVALUATION_COMPLETED',
              'system', 'Evaluation completed successfully', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return f"""✅ Evaluation COMPLETED!

**State Transitions**:
1. QUALITY_CHECK_PASSED → EVALUATION_QUEUED
2. EVALUATION_QUEUED → EVALUATION_RUNNING
3. EVALUATION_RUNNING → **EVALUATION_COMPLETED**

**Results**: Accuracy: 87.5% (simulated)

🎉 Model evaluation complete!
"""

    except Exception as e:
        return f"❌ Error starting evaluation: {str(e)}"


# ============================================================================
# Gradio Interface
# ============================================================================

def create_app():
    """Create Gradio app with two pages"""

    # Initialize database
    init_database()

    with gr.Blocks(title="Model Evaluation POC", theme=gr.themes.Soft()) as app:

        gr.Markdown("""
        # 🚀 Model Evaluation System - POC

        Simple proof-of-concept demonstrating model registration, dataset upload, and state transitions.
        """)

        with gr.Tabs():

            # ================================================================
            # Tab 1: Register Model
            # ================================================================
            with gr.Tab("📝 Register Model"):
                gr.Markdown("""
                ## Register New Model for Evaluation

                Create a new model entry to start the evaluation workflow.
                """)

                with gr.Row():
                    with gr.Column():
                        use_case_input = gr.Textbox(
                            label="Use Case Name",
                            placeholder="e.g., Invoice Extraction",
                            value="Demo Invoice Extraction"
                        )
                        model_name_input = gr.Textbox(
                            label="Model Name",
                            placeholder="e.g., GPT-4, Claude-3, etc."
                        )
                        version_input = gr.Textbox(
                            label="Version",
                            placeholder="e.g., 1.0, 2024-01-15"
                        )
                        description_input = gr.Textbox(
                            label="Description (Optional)",
                            placeholder="Any notes about this model",
                            lines=2
                        )

                        register_btn = gr.Button("Register Model", variant="primary", size="lg")

                    with gr.Column():
                        register_output = gr.Markdown(label="Result")

                gr.Markdown("### Registered Models")
                models_table = gr.Dataframe(label="All Models")

                refresh_table_btn = gr.Button("🔄 Refresh Table")

                # Event handlers
                register_btn.click(
                    fn=register_model,
                    inputs=[use_case_input, model_name_input, version_input, description_input],
                    outputs=register_output
                )

                refresh_table_btn.click(
                    fn=get_registered_models,
                    outputs=models_table
                )

                # Auto-refresh table on load
                app.load(fn=get_registered_models, outputs=models_table)

            # ================================================================
            # Tab 2: Upload Files & State Transitions
            # ================================================================
            with gr.Tab("📤 Upload Files & Track State"):
                gr.Markdown("""
                ## Upload Dataset and Track Model State

                Upload dataset files and watch state transitions happen automatically.
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        model_dropdown = gr.Dropdown(
                            label="Select Model",
                            choices=get_models_for_dropdown(),
                            interactive=True
                        )

                        refresh_dropdown_btn = gr.Button("🔄 Refresh Models")

                        gr.Markdown("---")

                        file_upload = gr.File(
                            label="Upload Dataset (Excel)",
                            file_types=[".xlsx", ".xls"]
                        )

                        upload_btn = gr.Button("📤 Upload Dataset", variant="primary")

                        gr.Markdown("---")

                        qc_btn = gr.Button("▶️ Run Quality Check", variant="secondary")
                        eval_btn = gr.Button("🎯 Start Evaluation", variant="secondary")

                    with gr.Column(scale=2):
                        model_info = gr.Markdown("Select a model to see details")
                        next_actions = gr.Markdown("")
                        operation_result = gr.Markdown("")

                # Hidden state for model ID
                model_id_state = gr.State()

                # Event handlers
                refresh_dropdown_btn.click(
                    fn=get_models_for_dropdown,
                    outputs=model_dropdown
                )

                model_dropdown.change(
                    fn=get_model_details,
                    inputs=model_dropdown,
                    outputs=[model_info, model_id_state, next_actions]
                )

                upload_btn.click(
                    fn=upload_dataset,
                    inputs=[model_dropdown, file_upload],
                    outputs=operation_result
                ).then(
                    fn=get_model_details,
                    inputs=model_dropdown,
                    outputs=[model_info, model_id_state, next_actions]
                )

                qc_btn.click(
                    fn=run_quality_check,
                    inputs=model_dropdown,
                    outputs=operation_result
                ).then(
                    fn=get_model_details,
                    inputs=model_dropdown,
                    outputs=[model_info, model_id_state, next_actions]
                )

                eval_btn.click(
                    fn=start_evaluation,
                    inputs=model_dropdown,
                    outputs=operation_result
                ).then(
                    fn=get_model_details,
                    inputs=model_dropdown,
                    outputs=[model_info, model_id_state, next_actions]
                )

        gr.Markdown("""
        ---
        ### 📖 How to Use

        **Step 1**: Go to "Register Model" tab and create a new model
        **Step 2**: Go to "Upload Files & Track State" tab
        **Step 3**: Select your model from dropdown
        **Step 4**: Upload an Excel dataset file
        **Step 5**: Click "Run Quality Check"
        **Step 6**: If QC passes, click "Start Evaluation"
        **Step 7**: Watch the state transitions happen!

        ### 🔄 State Flow

        ```
        REGISTERED
            ↓ (upload dataset)
        QUALITY_CHECK_PENDING
            ↓ (run QC)
        QUALITY_CHECK_RUNNING
            ↓
        QUALITY_CHECK_PASSED ✓  or  QUALITY_CHECK_FAILED ✗
            ↓                           ↓
        EVALUATION_QUEUED          AWAITING_DATA_FIX
            ↓                           ↓ (upload fixed)
        EVALUATION_RUNNING         QUALITY_CHECK_PENDING
            ↓
        EVALUATION_COMPLETED ✓
        ```
        """)

    return app


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )
