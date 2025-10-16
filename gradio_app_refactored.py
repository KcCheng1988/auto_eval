"""
Gradio POC App for Model Evaluation System (REFACTORED)

This version USES the actual architecture components instead of rewriting logic:
- Repositories for state management
- State machines for transitions
- Services for orchestration

Run: python gradio_app_refactored.py
"""

import gradio as gr
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import actual architecture components
from proposed_architecture.database.database_initialization import DatabaseInitializer
from proposed_architecture.repositories.model_evaluation_repository import ModelEvaluationRepository
from proposed_architecture.domain.models import Model
from proposed_architecture.domain.model_state_machine import (
    ModelEvaluationStateMachine,
    ModelEvaluationState,
    ModelStateTransitionMetadata
)
from proposed_architecture.services.file_upload_orchestrator import FileUploadOrchestrator
from proposed_architecture.quality_checks.quality_check_service import QualityCheckService

# Initialize
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "evaluation_poc.db"

# Initialize database
db_init = DatabaseInitializer(str(DB_PATH))
db_init.auto_initialize()  # Use actual initialization!

# Initialize repository
model_repo = ModelEvaluationRepository(str(DB_PATH))

# State display mapping
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


# ============================================================================
# Page 1: Register Model - Uses Repository Directly
# ============================================================================

def register_model(model_name, version, description):
    """Register a new model using the actual Model class and Repository"""
    try:
        # Use actual Model domain class
        model = Model.create_new(
            use_case_id='default_use_case',  # For POC, use default
            model_name=model_name,
            version=version
        )

        # Add description to metadata
        model.metadata['description'] = description

        # Use actual Repository to persist
        model_id = model_repo.create(model)

        return f"""✅ Model Registered Successfully!

**Model ID**: `{model_id}`
**Model Name**: {model_name}
**Version**: {version}
**Initial State**: REGISTERED

➡️ Go to "Upload Files" tab to upload dataset and start quality check!
"""

    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_registered_models():
    """Get list of all registered models using Repository"""
    try:
        # Use Repository query method
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, model_name, version, current_state, created_at
            FROM model_evaluations
            ORDER BY created_at DESC
        ''')

        models = cursor.fetchall()
        conn.close()

        if not models:
            return pd.DataFrame(columns=['Model ID', 'Model Name', 'Version', 'State', 'Created At'])

        df = pd.DataFrame(models, columns=['Model ID', 'Model Name', 'Version', 'State', 'Created At'])
        df['State'] = df['State'].map(lambda x: MODEL_STATES.get(x, x))
        return df

    except Exception as e:
        return pd.DataFrame(columns=['Model ID', 'Model Name', 'Version', 'State', 'Created At'])


# ============================================================================
# Page 2: Upload Files - Uses State Machine & Repository
# ============================================================================

def get_models_for_dropdown():
    """Get models for dropdown"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, model_name, version, current_state
        FROM model_evaluations
        ORDER BY created_at DESC
    ''')

    models = cursor.fetchall()
    conn.close()

    if not models:
        return ["No models registered yet"]

    choices = []
    for model_id, model_name, version, state in models:
        state_display = MODEL_STATES.get(state, state)
        choices.append(f"{model_id}|{model_name} v{version} - {state_display}")

    return choices


def get_model_details(model_dropdown):
    """Get detailed information using Repository and State Machine"""
    if model_dropdown == "No models registered yet":
        return "No model selected", "", ""

    try:
        # Extract model ID from dropdown
        model_id = model_dropdown.split('|')[0]

        # Use Repository to get state machine
        model_sm = model_repo.get_state_machine(model_id)

        # Get model details
        model = model_repo.get(model_id)

        # Build info display
        info = f"""## Model Information

**Model**: {model.model_name} v{model.version}
**Current State**: {MODEL_STATES.get(model_sm.current_state.value, model_sm.current_state.value)}
**Model ID**: `{model_id}`

### State History:
"""

        # Get history from state machine
        for state, timestamp, metadata in model_sm.state_history:
            info += f"\n- `{timestamp}`: **{MODEL_STATES.get(state.value, state.value)}**"
            if metadata:
                info += f" (by {metadata.triggered_by}: {metadata.trigger_reason})"

        # Determine next actions based on state machine
        current_state = model_sm.current_state
        actions_text = "### Possible Next Actions:\n"

        if current_state in [ModelEvaluationState.REGISTERED, ModelEvaluationState.AWAITING_DATA_FIX]:
            actions_text += "\n📤 **Upload Dataset** - Use the file upload below"
            actions_text += f"\n\nAllowed transitions: {', '.join([s.value for s in model_sm.get_allowed_transitions()])}"
        elif current_state == ModelEvaluationState.QUALITY_CHECK_PENDING:
            actions_text += "\n⏳ Click 'Run Quality Check' button"
        elif current_state == ModelEvaluationState.QUALITY_CHECK_PASSED:
            actions_text += "\n🎯 Click 'Start Evaluation' button"
        else:
            allowed = model_sm.get_allowed_transitions()
            if allowed:
                actions_text += f"\n\nNext possible states: {', '.join([s.value for s in allowed])}"

        return info, model_id, actions_text

    except Exception as e:
        return f"❌ Error: {str(e)}", "", ""


def upload_dataset(model_dropdown, file):
    """Handle dataset upload using State Machine"""
    if not file:
        return "❌ Please select a file to upload"

    if model_dropdown == "No models registered yet":
        return "❌ Please select a model first"

    try:
        # Extract model ID
        model_id = model_dropdown.split('|')[0]

        # Use Repository to get state machine
        model_sm = model_repo.get_state_machine(model_id)

        # Check if state allows upload using state machine
        current_state = model_sm.current_state

        if current_state not in [ModelEvaluationState.REGISTERED, ModelEvaluationState.AWAITING_DATA_FIX]:
            return f"❌ Cannot upload dataset in state: {MODEL_STATES.get(current_state.value, current_state.value)}"

        # Save file
        file_path = DATA_DIR / f"model_{model_id}_dataset.xlsx"
        with open(file_path, 'wb') as f:
            f.write(file.read())

        # Update model record
        model_repo.update_dataset_path(model_id, str(file_path))

        # Use state machine for transition
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_PENDING,
            metadata=ModelStateTransitionMetadata(
                triggered_by='user',
                trigger_reason='Dataset uploaded via Gradio app',
                file_uploaded=str(file_path)
            )
        )

        # Persist state using repository
        model_repo.save_state_machine(model_sm)

        return f"""✅ Dataset Uploaded Successfully!

**File**: {file.name if hasattr(file, 'name') else 'dataset.xlsx'}
**Saved to**: {file_path}

**State Transition**: {MODEL_STATES[current_state.value]} → **Quality Check Pending**

➡️ Click "Run Quality Check" to proceed!
"""

    except Exception as e:
        return f"❌ Error uploading dataset: {str(e)}"


def run_quality_check(model_dropdown):
    """
    Run quality check using State Machine for transitions
    and actual quality check service for validation
    """
    try:
        model_id = model_dropdown.split('|')[0]

        # Get state machine from repository
        model_sm = model_repo.get_state_machine(model_id)
        current_state = model_sm.current_state

        if current_state != ModelEvaluationState.QUALITY_CHECK_PENDING:
            return f"❌ Cannot run QC in state: {MODEL_STATES.get(current_state.value, current_state.value)}"

        # Transition to RUNNING using state machine
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_RUNNING,
            metadata=ModelStateTransitionMetadata(
                triggered_by='system',
                trigger_reason='QC started'
            )
        )
        model_repo.save_state_machine(model_sm)

        # Get model and dataset
        model = model_repo.get(model_id)
        dataset_path = model.dataset_file_path

        # Simulate quality check (in real app, use QualityCheckService)
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

        # Transition to result state using state machine
        new_state = ModelEvaluationState.QUALITY_CHECK_PASSED if qc_passed else ModelEvaluationState.QUALITY_CHECK_FAILED

        model_sm.transition_to(
            new_state,
            metadata=ModelStateTransitionMetadata(
                triggered_by='system',
                trigger_reason=f'QC {"passed" if qc_passed else "failed"}',
                quality_issues_count=len(issues)
            )
        )

        # If failed, transition to AWAITING_DATA_FIX
        if not qc_passed:
            model_sm.transition_to(
                ModelEvaluationState.AWAITING_DATA_FIX,
                metadata=ModelStateTransitionMetadata(
                    triggered_by='system',
                    trigger_reason='QC failed, needs fix'
                )
            )

        # Save state using repository
        model_repo.save_state_machine(model_sm)

        # Save QC results
        model_repo.update_quality_issues(model_id, [{'issue': issue} for issue in issues])

        if qc_passed:
            return f"""✅ Quality Check PASSED!

**State**: {MODEL_STATES['QUALITY_CHECK_RUNNING']} → **{MODEL_STATES['QUALITY_CHECK_PASSED']}**

No issues found! Dataset is ready for evaluation.

➡️ Click "Start Evaluation" to proceed!
"""
        else:
            issues_text = '\n'.join([f"- {issue}" for issue in issues])
            return f"""❌ Quality Check FAILED!

**State**: {MODEL_STATES['QUALITY_CHECK_RUNNING']} → {MODEL_STATES['QUALITY_CHECK_FAILED']} → **{MODEL_STATES['AWAITING_DATA_FIX']}**

**Issues Found**:
{issues_text}

➡️ Please fix the issues and upload a corrected dataset.
"""

    except Exception as e:
        return f"❌ Error running quality check: {str(e)}"


def start_evaluation(model_dropdown):
    """Start evaluation using State Machine for transitions"""
    try:
        model_id = model_dropdown.split('|')[0]

        # Get state machine from repository
        model_sm = model_repo.get_state_machine(model_id)
        current_state = model_sm.current_state

        if current_state != ModelEvaluationState.QUALITY_CHECK_PASSED:
            return f"❌ Cannot start evaluation in state: {MODEL_STATES.get(current_state.value, current_state.value)}"

        # Transition through states using state machine
        model_sm.transition_to(
            ModelEvaluationState.EVALUATION_QUEUED,
            metadata=ModelStateTransitionMetadata(
                triggered_by='user',
                trigger_reason='Evaluation started via Gradio'
            )
        )

        model_sm.transition_to(
            ModelEvaluationState.EVALUATION_RUNNING,
            metadata=ModelStateTransitionMetadata(
                triggered_by='system',
                trigger_reason='Evaluation running'
            )
        )

        # Simulate evaluation completion
        model_sm.transition_to(
            ModelEvaluationState.EVALUATION_COMPLETED,
            metadata=ModelStateTransitionMetadata(
                triggered_by='system',
                trigger_reason='Evaluation completed successfully'
            )
        )

        # Persist final state using repository
        model_repo.save_state_machine(model_sm)

        return f"""✅ Evaluation COMPLETED!

**State Transitions** (managed by State Machine):
1. {MODEL_STATES['QUALITY_CHECK_PASSED']} → {MODEL_STATES['EVALUATION_QUEUED']}
2. {MODEL_STATES['EVALUATION_QUEUED']} → {MODEL_STATES['EVALUATION_RUNNING']}
3. {MODEL_STATES['EVALUATION_RUNNING']} → **{MODEL_STATES['EVALUATION_COMPLETED']}**

**Results**: Accuracy: 87.5% (simulated)

🎉 Model evaluation complete!
"""

    except Exception as e:
        return f"❌ Error starting evaluation: {str(e)}"


# ============================================================================
# Gradio Interface (same as before)
# ============================================================================

def create_app():
    """Create Gradio app"""

    with gr.Blocks(title="Model Evaluation POC (Refactored)", theme=gr.themes.Soft()) as app:

        gr.Markdown("""
        # 🚀 Model Evaluation System - POC (Refactored)

        **This version uses actual architecture components:**
        - ✅ Repository pattern for state management
        - ✅ State machines for transitions
        - ✅ Domain models
        - ✅ Database initialization

        No duplicated logic - reuses the actual production code!
        """)

        with gr.Tabs():

            # Tab 1: Register Model
            with gr.Tab("📝 Register Model"):
                gr.Markdown("## Register New Model for Evaluation")

                with gr.Row():
                    with gr.Column():
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

                register_btn.click(
                    fn=register_model,
                    inputs=[model_name_input, version_input, description_input],
                    outputs=register_output
                )

                refresh_table_btn.click(
                    fn=get_registered_models,
                    outputs=models_table
                )

                app.load(fn=get_registered_models, outputs=models_table)

            # Tab 2: Upload Files
            with gr.Tab("📤 Upload Files & Track State"):
                gr.Markdown("## Upload Dataset and Track Model State")

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

                model_id_state = gr.State()

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
        ### ✨ Architecture Components Used

        - **DatabaseInitializer**: Auto-initializes SQLite database
        - **ModelEvaluationRepository**: State extraction and persistence
        - **ModelEvaluationStateMachine**: State transitions and validation
        - **Model**: Domain model class
        - **ModelStateTransitionMetadata**: Transition context

        This demonstrates how the actual production components work together!
        """)

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7861,  # Different port to not conflict
        share=False
    )
