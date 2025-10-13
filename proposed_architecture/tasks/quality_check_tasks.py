"""Celery tasks for quality checks"""

from celery import Task
from typing import Dict, Any
import logging

from .celery_app import celery_app
from ..domain.state_machine import UseCaseState, StateTransitionMetadata
from ..services.quality_check_service import QualityCheckService
from ..services.evaluation_service import EvaluationService
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


class QualityCheckTask(Task):
    """Base task for quality checks with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        use_case_id = kwargs.get('use_case_id')
        logger.error(f"Quality check failed for use case {use_case_id}: {exc}")

        # Update use case state to failed
        # Send notification email about failure
        # (Implementation would use actual repositories and services)


@celery_app.task(bind=True, base=QualityCheckTask, name='tasks.quality_check_tasks.run_quality_check')
def run_quality_check_task(self, use_case_id: str, config_file_path: str, dataset_file_path: str):
    """
    Celery task for running quality checks

    Args:
        use_case_id: Use case identifier
        config_file_path: Path to configuration file
        dataset_file_path: Path to dataset file

    Returns:
        Result dictionary with status and issues
    """
    logger.info(f"Starting quality check for use case {use_case_id}")

    try:
        # Initialize services (would use dependency injection in real implementation)
        # use_case_repo = get_use_case_repository()
        # quality_check_service = QualityCheckService(use_case_repo)
        # evaluation_service = EvaluationService(use_case_repo, quality_check_service)

        # For now, placeholder implementation
        from ..services.evaluation_service import EvaluationService
        from ..services.quality_check_service import QualityCheckService

        # This would be injected
        evaluation_service = None  # EvaluationService(use_case_repo, quality_check_service)

        # Process files
        result = evaluation_service.process_submitted_files(
            use_case_id,
            config_file_path,
            dataset_file_path
        )

        if result['status'] == 'quality_check_failed':
            # Generate report and send email
            send_quality_issues_email.delay(use_case_id, result['issues'])
        else:
            # Queue evaluation
            from .evaluation_tasks import run_evaluation_task
            run_evaluation_task.delay(use_case_id)

        return result

    except Exception as e:
        logger.error(f"Quality check error for use case {use_case_id}: {e}", exc_info=True)
        raise


@celery_app.task(name='tasks.quality_check_tasks.send_quality_issues_email')
def send_quality_issues_email(use_case_id: str, issues: list):
    """
    Send email with quality issues report

    Args:
        use_case_id: Use case identifier
        issues: List of quality issues (serialized)
    """
    logger.info(f"Sending quality issues email for use case {use_case_id}")

    try:
        # Get use case details
        # use_case = use_case_repo.get_by_id(use_case_id)

        # Generate quality report Excel
        from ..services.quality_check_service import QualityCheckService
        from ..quality_checks.base import QualityIssue, IssueSeverity

        # Reconstruct QualityIssue objects from dicts
        issue_objects = [
            QualityIssue(
                row_number=i['row_number'],
                field_name=i['field_name'],
                value=i['value'],
                issue_type=i['issue_type'],
                message=i['message'],
                severity=IssueSeverity(i['severity']),
                suggestion=i.get('suggestion')
            )
            for i in issues
        ]

        # quality_check_service = QualityCheckService(use_case_repo)
        # report_df = quality_check_service.generate_quality_report(issue_objects)

        # report_path = f'/tmp/quality_issues_{use_case_id}.xlsx'
        # report_df.to_excel(report_path, index=False)

        # Send email
        # email_service = EmailService(smtp_config)
        # email_service.send_quality_issues_notification(
        #     use_case_id=use_case.id,
        #     use_case_name=use_case.name,
        #     team_email=use_case.team_email,
        #     issues=issues,
        #     report_file_path=report_path
        # )

        logger.info(f"Quality issues email sent for use case {use_case_id}")

    except Exception as e:
        logger.error(f"Failed to send quality issues email for {use_case_id}: {e}", exc_info=True)
        raise
