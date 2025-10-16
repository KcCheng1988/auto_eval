"""
File Upload Orchestrator Service

Handles file uploads and automatically triggers appropriate state transitions
and background tasks for quality checks and evaluations.
"""

from typing import Optional, Dict, Any
import pandas as pd
import logging
from pathlib import Path

from ..domain.model_state_machine import (
    ModelEvaluationStateMachine,
    ModelEvaluationState,
    ModelStateTransitionMetadata
)
from ..domain.state_machine import UseCaseState, StateTransitionMetadata
from ..tasks.simple_task_queue import get_task_queue
from ..repositories.use_case_repository import UseCaseRepository
from ..repositories.model_evaluation_repository import ModelEvaluationRepository
from .file_storage_service import FileStorageService
from .activity_log_service import ActivityLogService

logger = logging.getLogger(__name__)


class FileUploadOrchestrator:
    """
    Orchestrates file uploads and triggers appropriate workflows

    Responsibilities:
    - Handle file uploads (config, dataset)
    - Detect file type and purpose
    - Transition state machines appropriately
    - Queue background tasks
    - Log activities
    - Send notifications
    """

    def __init__(
        self,
        use_case_repo: UseCaseRepository,
        model_repo: ModelEvaluationRepository,
        file_storage: FileStorageService,
        activity_log: ActivityLogService
    ):
        self.use_case_repo = use_case_repo
        self.model_repo = model_repo
        self.file_storage = file_storage
        self.activity_log = activity_log
        self.task_queue = get_task_queue()

    async def handle_config_upload(
        self,
        use_case_id: str,
        file_content: bytes,
        filename: str,
        uploaded_by: str
    ) -> Dict[str, Any]:
        """
        Handle configuration file upload

        Flow:
        1. Save file to storage
        2. Validate JSON structure (quick check)
        3. Update use case record
        4. Transition use case state
        5. Queue config validation task

        Args:
            use_case_id: Use case identifier
            file_content: File content bytes
            filename: Original filename
            uploaded_by: User who uploaded

        Returns:
            Upload result with status and next steps
        """
        logger.info(f"Handling config upload for use case {use_case_id}")

        try:
            # 1. Save file
            file_path = await self.file_storage.save_file(
                content=file_content,
                filename=filename,
                path=f"use_cases/{use_case_id}/config.json"
            )

            # 2. Quick validation (valid JSON?)
            try:
                import json
                config = json.loads(file_content)
                if 'fields' not in config:
                    return {
                        'status': 'error',
                        'message': "Invalid config: 'fields' key missing"
                    }
            except json.JSONDecodeError as e:
                return {
                    'status': 'error',
                    'message': f"Invalid JSON: {str(e)}"
                }

            # 3. Update use case
            use_case = self.use_case_repo.get(use_case_id)
            use_case.config_file_path = file_path
            use_case.updated_at = pd.Timestamp.now()
            self.use_case_repo.update(use_case)

            # 4. Transition use case state
            use_case_sm = self.use_case_repo.get_state_machine(use_case_id)

            if use_case_sm.current_state == UseCaseState.AWAITING_CONFIG:
                use_case_sm.transition_to(
                    UseCaseState.CONFIG_RECEIVED,
                    metadata=StateTransitionMetadata(
                        triggered_by=uploaded_by,
                        trigger_reason="Configuration file uploaded",
                        additional_data={'file_path': file_path}
                    )
                )

                # Auto-transition to validation
                use_case_sm.transition_to(
                    UseCaseState.CONFIG_VALIDATION_RUNNING,
                    metadata=StateTransitionMetadata(
                        triggered_by="system",
                        trigger_reason="Auto-started validation"
                    )
                )

                self.use_case_repo.save_state_machine(use_case_sm)

            # 5. Queue validation task
            task_id = self.task_queue.enqueue(
                'validate_config',
                args=[use_case_id],
                priority=10
            )

            # 6. Log activity
            self.activity_log.log(
                use_case_id=use_case_id,
                activity_type='config_upload',
                description=f"Configuration file uploaded by {uploaded_by}",
                metadata={'file_path': file_path, 'task_id': task_id}
            )

            return {
                'status': 'success',
                'message': 'Configuration uploaded successfully, validation queued',
                'task_id': task_id,
                'file_path': file_path
            }

        except Exception as e:
            logger.error(f"Config upload failed for {use_case_id}: {e}")
            return {
                'status': 'error',
                'message': f"Upload failed: {str(e)}"
            }

    async def handle_dataset_upload(
        self,
        use_case_id: str,
        model_id: str,
        file_content: bytes,
        filename: str,
        uploaded_by: str
    ) -> Dict[str, Any]:
        """
        Handle dataset file upload for a specific model

        Flow:
        1. Save file to storage
        2. Validate basic structure (Excel readable?)
        3. Update model record
        4. Get model state machine
        5. Check if model is in AWAITING_DATA_FIX
        6. If yes, transition to QUALITY_CHECK_PENDING
        7. Queue quality check task

        Args:
            use_case_id: Use case identifier
            model_id: Model identifier
            file_content: File content bytes
            filename: Original filename
            uploaded_by: User who uploaded

        Returns:
            Upload result with status and next steps
        """
        logger.info(f"Handling dataset upload for model {model_id}")

        try:
            # 1. Save file
            file_path = await self.file_storage.save_file(
                content=file_content,
                filename=filename,
                path=f"use_cases/{use_case_id}/models/{model_id}/dataset.xlsx"
            )

            # 2. Quick validation (Excel readable?)
            try:
                df = pd.read_excel(file_path)
                if len(df) == 0:
                    return {
                        'status': 'error',
                        'message': 'Dataset is empty'
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Cannot read Excel file: {str(e)}'
                }

            # 3. Update model record
            model = self.model_repo.get(model_id)
            model.dataset_file_path = file_path
            model.updated_at = pd.Timestamp.now()
            self.model_repo.update(model)

            # 4. Get model state machine
            model_sm = self.model_repo.get_state_machine(model_id)

            # 5. Check current state and determine action
            current_state = model_sm.current_state
            transition_made = False
            task_id = None

            if current_state == ModelEvaluationState.AWAITING_DATA_FIX:
                # User uploaded fix after QC failure
                model_sm.transition_to(
                    ModelEvaluationState.QUALITY_CHECK_PENDING,
                    metadata=ModelStateTransitionMetadata(
                        triggered_by=uploaded_by,
                        trigger_reason="Dataset file uploaded after fix",
                        file_uploaded=file_path
                    )
                )
                transition_made = True

                # Queue quality check
                task_id = self.task_queue.enqueue(
                    'run_quality_check',
                    args=[use_case_id, model_id],
                    priority=10
                )

            elif current_state == ModelEvaluationState.REGISTERED:
                # Initial dataset upload
                model_sm.transition_to(
                    ModelEvaluationState.QUALITY_CHECK_PENDING,
                    metadata=ModelStateTransitionMetadata(
                        triggered_by=uploaded_by,
                        trigger_reason="Initial dataset file uploaded",
                        file_uploaded=file_path
                    )
                )
                transition_made = True

                # Queue quality check
                task_id = self.task_queue.enqueue(
                    'run_quality_check',
                    args=[use_case_id, model_id],
                    priority=10
                )

            elif current_state == ModelEvaluationState.QUALITY_CHECK_PENDING:
                # Re-upload before QC started
                logger.info(f"Dataset re-uploaded for model {model_id} in QUALITY_CHECK_PENDING")
                # Just update the file, task already queued

            else:
                # Unexpected state
                logger.warning(
                    f"Dataset uploaded for model {model_id} in unexpected state: {current_state}"
                )

            # 6. Save state machine
            if transition_made:
                self.model_repo.save_state_machine(model_sm)

            # 7. Log activity
            self.activity_log.log(
                use_case_id=use_case_id,
                activity_type='dataset_upload',
                description=f"Dataset uploaded for model {model_id} by {uploaded_by}",
                metadata={
                    'model_id': model_id,
                    'file_path': file_path,
                    'task_id': task_id,
                    'previous_state': current_state.value if current_state else None,
                    'rows_count': len(df)
                }
            )

            message = 'Dataset uploaded successfully'
            if task_id:
                message += ', quality check queued'

            return {
                'status': 'success',
                'message': message,
                'task_id': task_id,
                'file_path': file_path,
                'rows_count': len(df),
                'current_state': model_sm.current_state.value
            }

        except Exception as e:
            logger.error(f"Dataset upload failed for model {model_id}: {e}")

            # Log failed attempt
            self.activity_log.log(
                use_case_id=use_case_id,
                activity_type='dataset_upload_failed',
                description=f"Dataset upload failed for model {model_id}",
                metadata={'model_id': model_id, 'error': str(e)}
            )

            return {
                'status': 'error',
                'message': f"Upload failed: {str(e)}"
            }

    async def handle_model_prediction_upload(
        self,
        use_case_id: str,
        model_id: str,
        file_content: bytes,
        filename: str,
        uploaded_by: str
    ) -> Dict[str, Any]:
        """
        Handle model prediction results upload

        This is used when the model generates predictions that need to be
        evaluated against golden answers.

        Flow:
        1. Save file
        2. Validate structure
        3. Merge with dataset (predictions + golden answers)
        4. Trigger evaluation
        """
        logger.info(f"Handling prediction upload for model {model_id}")

        try:
            # 1. Save file
            file_path = await self.file_storage.save_file(
                content=file_content,
                filename=filename,
                path=f"use_cases/{use_case_id}/models/{model_id}/predictions.xlsx"
            )

            # 2. Validate
            try:
                predictions_df = pd.read_excel(file_path)
                if 'model_output' not in predictions_df.columns:
                    return {
                        'status': 'error',
                        'message': "Missing 'model_output' column in predictions"
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Cannot read predictions file: {str(e)}'
                }

            # 3. Update model record
            model = self.model_repo.get(model_id)
            model.predictions_file_path = file_path
            model.updated_at = pd.Timestamp.now()
            self.model_repo.update(model)

            # 4. Check if ready for evaluation
            model_sm = self.model_repo.get_state_machine(model_id)

            if model_sm.current_state == ModelEvaluationState.QUALITY_CHECK_PASSED:
                # Ready to evaluate
                model_sm.transition_to(
                    ModelEvaluationState.EVALUATION_QUEUED,
                    metadata=ModelStateTransitionMetadata(
                        triggered_by=uploaded_by,
                        trigger_reason="Model predictions uploaded",
                        file_uploaded=file_path
                    )
                )

                # Queue evaluation
                task_id = self.task_queue.enqueue(
                    'run_evaluation',
                    args=[use_case_id, model_id],
                    priority=5
                )

                self.model_repo.save_state_machine(model_sm)

                # Log activity
                self.activity_log.log(
                    use_case_id=use_case_id,
                    activity_type='predictions_upload',
                    description=f"Predictions uploaded for model {model_id}",
                    metadata={
                        'model_id': model_id,
                        'file_path': file_path,
                        'task_id': task_id
                    }
                )

                return {
                    'status': 'success',
                    'message': 'Predictions uploaded, evaluation queued',
                    'task_id': task_id,
                    'file_path': file_path
                }

            else:
                return {
                    'status': 'error',
                    'message': f"Cannot evaluate in current state: {model_sm.current_state.value}"
                }

        except Exception as e:
            logger.error(f"Prediction upload failed for model {model_id}: {e}")
            return {
                'status': 'error',
                'message': f"Upload failed: {str(e)}"
            }

    def get_upload_requirements(
        self,
        use_case_id: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get what files are needed for a use case or model

        Returns instructions on what to upload next based on current state

        Args:
            use_case_id: Use case identifier
            model_id: Optional model identifier

        Returns:
            Required uploads and instructions
        """
        use_case = self.use_case_repo.get(use_case_id)
        use_case_sm = self.use_case_repo.get_state_machine(use_case_id)

        requirements = {
            'use_case_id': use_case_id,
            'use_case_state': use_case_sm.current_state.value,
            'required_files': [],
            'optional_files': [],
            'next_steps': []
        }

        # Check use case level
        if use_case_sm.current_state == UseCaseState.AWAITING_CONFIG:
            requirements['required_files'].append({
                'type': 'config',
                'description': 'Configuration JSON file',
                'endpoint': f'/api/use-cases/{use_case_id}/upload-config'
            })
            requirements['next_steps'].append(
                'Upload configuration file to proceed'
            )

        # Check model level
        if model_id:
            model = self.model_repo.get(model_id)
            model_sm = self.model_repo.get_state_machine(model_id)

            requirements['model_id'] = model_id
            requirements['model_state'] = model_sm.current_state.value

            if model_sm.current_state in [
                ModelEvaluationState.REGISTERED,
                ModelEvaluationState.AWAITING_DATA_FIX
            ]:
                requirements['required_files'].append({
                    'type': 'dataset',
                    'description': 'Evaluation dataset Excel file',
                    'endpoint': f'/api/use-cases/{use_case_id}/models/{model_id}/upload-dataset'
                })
                requirements['next_steps'].append(
                    'Upload dataset to start quality check'
                )

            if model_sm.current_state == ModelEvaluationState.QUALITY_CHECK_PASSED:
                requirements['optional_files'].append({
                    'type': 'predictions',
                    'description': 'Model prediction results (if not auto-generated)',
                    'endpoint': f'/api/use-cases/{use_case_id}/models/{model_id}/upload-predictions'
                })

        return requirements
