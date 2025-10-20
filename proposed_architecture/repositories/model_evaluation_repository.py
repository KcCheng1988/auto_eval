"""
Repository for Model Evaluation state management

This is the CORE component for extracting and persisting model state.
All state reads/writes go through this repository.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import sqlite3
import logging

from ..domain import Model
from ..domain import (
    ModelEvaluationStateMachine,
    ModelEvaluationState,
    ModelStateTransitionMetadata
)

logger = logging.getLogger(__name__)


class ModelEvaluationRepository:
    """
    Repository for managing model evaluations and their state machines

    Key Responsibilities:
    1. Extract current state from database
    2. Reconstruct state machine with full history
    3. Persist state transitions back to database
    4. Maintain data integrity

    Note: Database schema is managed by DatabaseInitializer,
    not by this repository. See database/schema_sqlite.sql for schema definition.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Schema initialization is handled by DatabaseInitializer
        # NOT by individual repositories (single source of truth!)

    # ============================================================================
    # STATE EXTRACTION - Reading state from database
    # ============================================================================

    def get_state_machine(self, model_id: str) -> ModelEvaluationStateMachine:
        """
        CORE METHOD: Extract state from database and reconstruct state machine

        This method:
        1. Queries model_evaluations table for current state
        2. Queries model_state_history table for full transition history
        3. Reconstructs ModelEvaluationStateMachine object
        4. Returns ready-to-use state machine with all context

        Args:
            model_id: Model identifier

        Returns:
            ModelEvaluationStateMachine with current state and full history

        Example:
            model_sm = repo.get_state_machine("model_123")
            print(model_sm.current_state)  # AWAITING_DATA_FIX
            print(model_sm.get_allowed_transitions())  # [QUALITY_CHECK_PENDING]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Get current state from model_evaluations
        cursor.execute('''
            SELECT use_case_id, current_state, created_at
            FROM model_evaluations
            WHERE id = ?
        ''', (model_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Model {model_id} not found")

        use_case_id, current_state, created_at = row

        # 2. Get full state history
        cursor.execute('''
            SELECT from_state, to_state, triggered_by, trigger_reason,
                   file_uploaded, quality_issues_count, error_message,
                   additional_data, timestamp
            FROM model_state_history
            WHERE model_id = ?
            ORDER BY timestamp ASC
        ''', (model_id,))

        history_rows = cursor.fetchall()
        conn.close()

        # 3. Reconstruct state history
        state_history = []

        # Add initial state (from created_at)
        initial_state = ModelEvaluationState.REGISTERED
        state_history.append((
            initial_state,
            datetime.fromisoformat(created_at),
            None
        ))

        # Add all transitions from history table
        for row in history_rows:
            (from_state, to_state, triggered_by, trigger_reason,
             file_uploaded, quality_issues_count, error_message,
             additional_data_json, timestamp) = row

            metadata = ModelStateTransitionMetadata(
                triggered_by=triggered_by,
                trigger_reason=trigger_reason,
                file_uploaded=file_uploaded,
                quality_issues_count=quality_issues_count,
                error_message=error_message,
                additional_data=json.loads(additional_data_json) if additional_data_json else {},
                timestamp=datetime.fromisoformat(timestamp)
            )

            state_history.append((
                ModelEvaluationState(to_state),
                datetime.fromisoformat(timestamp),
                metadata
            ))

        # 4. Construct and return state machine
        state_machine = ModelEvaluationStateMachine(
            model_id=model_id,
            use_case_id=use_case_id,
            initial_state=ModelEvaluationState(current_state),
            state_history=state_history
        )

        logger.info(
            f"Loaded state machine for model {model_id}: "
            f"current_state={current_state}, history_entries={len(state_history)}"
        )

        return state_machine

    def get_current_state(self, model_id: str) -> ModelEvaluationState:
        """
        Quick method to get just the current state without full history

        Args:
            model_id: Model identifier

        Returns:
            Current ModelEvaluationState
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT current_state
            FROM model_evaluations
            WHERE id = ?
        ''', (model_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Model {model_id} not found")

        return ModelEvaluationState(row[0])

    # ============================================================================
    # STATE PERSISTENCE - Writing state to database
    # ============================================================================

    def save_state_machine(self, model_sm: ModelEvaluationStateMachine):
        """
        CORE METHOD: Persist state machine changes to database

        This method:
        1. Updates current_state in model_evaluations table
        2. Inserts new transition record in model_state_history table
        3. Maintains transaction integrity

        Args:
            model_sm: ModelEvaluationStateMachine with updated state

        Example:
            model_sm.transition_to(ModelEvaluationState.QUALITY_CHECK_PENDING)
            repo.save_state_machine(model_sm)  # Persists to database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 1. Update current_state in model_evaluations
            cursor.execute('''
                UPDATE model_evaluations
                SET current_state = ?, updated_at = ?
                WHERE id = ?
            ''', (
                model_sm.current_state.value,
                datetime.now().isoformat(),
                model_sm.model_id
            ))

            # 2. Get the latest transition from state_history
            if len(model_sm.state_history) > 1:
                # Get the last transition
                latest_state, timestamp, metadata = model_sm.state_history[-1]

                # Get the previous state
                previous_state = model_sm.state_history[-2][0] if len(model_sm.state_history) > 1 else None

                # 3. Insert into state history table
                import uuid
                cursor.execute('''
                    INSERT INTO model_state_history
                    (id, model_id, from_state, to_state, triggered_by, trigger_reason,
                     file_uploaded, quality_issues_count, error_message, additional_data, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    model_sm.model_id,
                    previous_state.value if previous_state else None,
                    latest_state.value,
                    metadata.triggered_by if metadata else "system",
                    metadata.trigger_reason if metadata else "Unknown",
                    metadata.file_uploaded if metadata else None,
                    metadata.quality_issues_count if metadata else None,
                    metadata.error_message if metadata else None,
                    json.dumps(metadata.additional_data) if metadata and metadata.additional_data else None,
                    timestamp.isoformat()
                ))

            conn.commit()
            logger.info(
                f"Saved state machine for model {model_sm.model_id}: "
                f"new_state={model_sm.current_state.value}"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save state machine for {model_sm.model_id}: {e}")
            raise

        finally:
            conn.close()

    # ============================================================================
    # QUERY METHODS - Finding models by state
    # ============================================================================

    def get_models_by_state(
        self,
        use_case_id: str,
        state: ModelEvaluationState
    ) -> List[str]:
        """
        Find all models in a specific state

        Useful for:
        - Finding all models awaiting data fix
        - Finding all models ready for evaluation
        - Dashboard queries

        Args:
            use_case_id: Use case identifier
            state: State to filter by

        Returns:
            List of model IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id
            FROM model_evaluations
            WHERE use_case_id = ? AND current_state = ?
        ''', (use_case_id, state.value))

        model_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return model_ids

    def get_models_needing_action(self, use_case_id: str) -> Dict[str, List[str]]:
        """
        Get models grouped by states that need action

        Returns:
            Dict mapping state to list of model IDs
            {
                'awaiting_data_fix': ['model_1', 'model_2'],
                'evaluation_failed': ['model_3']
            }
        """
        blocked_states = [
            ModelEvaluationState.AWAITING_DATA_FIX,
            ModelEvaluationState.QUALITY_CHECK_FAILED,
            ModelEvaluationState.EVALUATION_FAILED
        ]

        result = {}
        for state in blocked_states:
            model_ids = self.get_models_by_state(use_case_id, state)
            if model_ids:
                result[state.value] = model_ids

        return result

    def get_model_state_summary(self, use_case_id: str) -> Dict[str, int]:
        """
        Get count of models in each state for a use case

        Returns:
            {'quality_check_passed': 5, 'awaiting_data_fix': 2, ...}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT current_state, COUNT(*)
            FROM model_evaluations
            WHERE use_case_id = ?
            GROUP BY current_state
        ''', (use_case_id,))

        summary = {}
        for state_value, count in cursor.fetchall():
            summary[state_value] = count

        conn.close()
        return summary

    # ============================================================================
    # CRUD OPERATIONS - Basic model management
    # ============================================================================

    def create(self, model: Model) -> str:
        """Create new model evaluation record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO model_evaluations
            (id, use_case_id, model_name, version, current_state,
             created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model.id,
            model.use_case_id,
            model.model_name,
            model.version,
            ModelEvaluationState.REGISTERED.value,
            model.created_at.isoformat(),
            datetime.now().isoformat(),
            json.dumps(model.metadata) if model.metadata else '{}'
        ))

        conn.commit()
        conn.close()

        logger.info(f"Created model evaluation: {model.id}")
        return model.id

    def get(self, model_id: str) -> Model:
        """Get model by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, use_case_id, model_name, version, created_at, metadata
            FROM model_evaluations
            WHERE id = ?
        ''', (model_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Model {model_id} not found")

        return Model(
            id=row[0],
            use_case_id=row[1],
            model_name=row[2],
            version=row[3],
            created_at=datetime.fromisoformat(row[4]),
            metadata=json.loads(row[5]) if row[5] else {}
        )

    def update_dataset_path(self, model_id: str, file_path: str):
        """Update dataset file path for a model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE model_evaluations
            SET dataset_file_path = ?, updated_at = ?
            WHERE id = ?
        ''', (file_path, datetime.now().isoformat(), model_id))

        conn.commit()
        conn.close()

    def update_quality_issues(self, model_id: str, issues: List[Dict[str, Any]]):
        """Update quality issues for a model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE model_evaluations
            SET quality_issues = ?, updated_at = ?
            WHERE id = ?
        ''', (json.dumps(issues), datetime.now().isoformat(), model_id))

        conn.commit()
        conn.close()


# Example usage demonstrating the core pattern
if __name__ == "__main__":
    """
    This example shows how the repository acts as the state extraction bridge
    """

    # Initialize repository
    repo = ModelEvaluationRepository('evaluation.db')

    # Scenario: User uploads a fixed dataset after QC failure
    model_id = "model_123"

    # 1. EXTRACT STATE from database
    print("=== Extracting State from Database ===")
    model_sm = repo.get_state_machine(model_id)
    print(f"Current State: {model_sm.current_state}")
    print(f"History Entries: {len(model_sm.state_history)}")

    # 2. Business Logic (in memory)
    print("\n=== Performing Business Logic ===")
    if model_sm.current_state == ModelEvaluationState.AWAITING_DATA_FIX:
        print("Model is waiting for fix, transitioning to QC...")
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_PENDING,
            metadata=ModelStateTransitionMetadata(
                triggered_by="user@example.com",
                trigger_reason="Dataset file uploaded after fix",
                file_uploaded="/path/to/fixed_dataset.xlsx"
            )
        )

    # 3. PERSIST STATE back to database
    print("\n=== Persisting State to Database ===")
    repo.save_state_machine(model_sm)
    print(f"Saved new state: {model_sm.current_state}")

    # 4. Verify persistence
    print("\n=== Verifying Persistence ===")
    reloaded_sm = repo.get_state_machine(model_id)
    print(f"Reloaded State: {reloaded_sm.current_state}")
    print(f"Reloaded History Entries: {len(reloaded_sm.state_history)}")
