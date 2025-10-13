"""Evaluation service for orchestrating the evaluation workflow"""

from typing import Dict, Any
import pandas as pd

from ..domain.state_machine import UseCaseState
from ..repositories.use_case_repository import UseCaseRepository
from .quality_check_service import QualityCheckService


class EvaluationService:
    """Service for running evaluations"""

    def __init__(
        self,
        use_case_repo: UseCaseRepository,
        quality_check_service: QualityCheckService
    ):
        self.use_case_repo = use_case_repo
        self.quality_check_service = quality_check_service

    def process_submitted_files(
        self,
        use_case_id: str,
        config_file_path: str,
        dataset_file_path: str
    ) -> Dict[str, Any]:
        """
        Process submitted configuration and dataset files

        Args:
            use_case_id: Use case identifier
            config_file_path: Path to configuration Excel file
            dataset_file_path: Path to dataset Excel file

        Returns:
            Result dict with status and issues if any
        """
        use_case = self.use_case_repo.get_by_id(use_case_id)
        if not use_case:
            raise ValueError(f"Use case {use_case_id} not found")

        # Load files
        config_df = pd.read_excel(config_file_path)
        dataset_df = pd.read_excel(dataset_file_path)

        # Parse field configuration
        field_config = self._parse_field_config(config_df)

        # Run quality checks
        issues = self.quality_check_service.run_quality_checks(
            use_case_id, dataset_df, field_config
        )

        # Update use case state
        if self.quality_check_service.has_blocking_issues(issues):
            # Has blocking issues - send for fixing
            use_case.state = UseCaseState.QUALITY_CHECK_FAILED
            use_case.quality_issues = [issue.to_dict() for issue in issues]
            use_case.config_file_path = config_file_path
            use_case.dataset_file_path = dataset_file_path
            self.use_case_repo.update(use_case)

            return {
                'status': 'quality_check_failed',
                'issues_count': len(issues),
                'issues': issues,
                'summary': self.quality_check_service.get_issue_summary(issues)
            }
        else:
            # No blocking issues - queue for evaluation
            use_case.state = UseCaseState.EVALUATION_QUEUED
            use_case.quality_issues = None
            use_case.config_file_path = config_file_path
            use_case.dataset_file_path = dataset_file_path
            self.use_case_repo.update(use_case)

            return {
                'status': 'quality_check_passed',
                'queued_for_evaluation': True,
                'warnings': [issue for issue in issues]  # May have warnings
            }

    def run_evaluation(self, use_case_id: str) -> Dict[str, Any]:
        """
        Run field-based evaluation for a use case

        Args:
            use_case_id: Use case identifier

        Returns:
            Evaluation results
        """
        use_case = self.use_case_repo.get_by_id(use_case_id)
        if not use_case:
            raise ValueError(f"Use case {use_case_id} not found")

        # Import existing evaluator
        from ...src.evaluators.field_based_evaluator import FieldBasedEvaluator

        # Load evaluator with config
        evaluator = FieldBasedEvaluator.from_config_file(use_case.config_file_path)

        # Load dataset
        df = pd.read_excel(use_case.dataset_file_path)

        # Run evaluation
        results = evaluator.evaluate_dataset(df)

        # Get metrics summary
        summary = evaluator.get_metrics_summary(results)

        # Store results
        use_case.evaluation_results = summary
        use_case.state = UseCaseState.EVALUATION_COMPLETED
        self.use_case_repo.update(use_case)

        return summary

    def _parse_field_config(self, config_df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Parse field configuration from Excel

        Expected columns:
        - field_name
        - field_type
        - comparison_strategy
        - preprocessing_options (optional)
        - validation_rules (optional)

        Args:
            config_df: Configuration DataFrame

        Returns:
            Dictionary of field configurations
        """
        field_config = {}

        for _, row in config_df.iterrows():
            field_name = row['field_name']
            field_config[field_name] = {
                'type': row['field_type'],
                'strategy': row['comparison_strategy'],
                'preprocessing': self._parse_json_column(row.get('preprocessing_options', '{}')),
                'validation_rules': self._parse_json_column(row.get('validation_rules', '{}'))
            }

        return field_config

    def _parse_json_column(self, value: Any) -> Dict:
        """Parse JSON string column to dict"""
        import json
        if pd.isna(value) or value == '':
            return {}
        if isinstance(value, dict):
            return value
        try:
            return json.loads(str(value))
        except:
            return {}
