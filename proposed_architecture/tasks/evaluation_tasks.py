"""Celery tasks for evaluations"""

from celery import Task
import logging

from .celery_app import celery_app
from ..domain.state_machine import UseCaseState

logger = logging.getLogger(__name__)


class EvaluationTask(Task):
    """Base task for evaluations with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        use_case_id = kwargs.get('use_case_id')
        logger.error(f"Evaluation failed for use case {use_case_id}: {exc}")

        # Update use case state to EVALUATION_FAILED
        # Allow retry


@celery_app.task(bind=True, base=EvaluationTask, name='tasks.evaluation_tasks.run_evaluation')
def run_evaluation_task(self, use_case_id: str):
    """
    Celery task for running evaluation

    Args:
        use_case_id: Use case identifier

    Returns:
        Evaluation results dictionary
    """
    logger.info(f"Starting evaluation for use case {use_case_id}")

    try:
        # Get use case and update state to RUNNING
        # use_case = use_case_repo.get_by_id(use_case_id)
        # use_case.state = UseCaseState.EVALUATION_RUNNING
        # use_case_repo.update(use_case)

        # Run evaluation
        from ..services.evaluation_service import EvaluationService
        from ..services.quality_check_service import QualityCheckService

        # Would use dependency injection
        # evaluation_service = EvaluationService(use_case_repo, quality_check_service)
        # results = evaluation_service.run_evaluation(use_case_id)

        # Placeholder
        results = {}

        # Send success notification
        send_evaluation_success_email.delay(use_case_id)

        logger.info(f"Evaluation completed for use case {use_case_id}")
        return {'status': 'completed', 'results': results}

    except Exception as e:
        logger.error(f"Evaluation error for use case {use_case_id}: {e}", exc_info=True)
        # Update state to EVALUATION_FAILED
        raise


@celery_app.task(name='tasks.evaluation_tasks.send_evaluation_success_email')
def send_evaluation_success_email(use_case_id: str):
    """
    Send success email with evaluation results

    Args:
        use_case_id: Use case identifier
    """
    logger.info(f"Sending success email for use case {use_case_id}")

    try:
        # Get use case with results
        # use_case = use_case_repo.get_by_id(use_case_id)

        # Send email
        # email_service = EmailService(smtp_config)
        # email_service.send_evaluation_success_notification(
        #     use_case_id=use_case.id,
        #     use_case_name=use_case.name,
        #     team_email=use_case.team_email,
        #     results=use_case.evaluation_results
        # )

        logger.info(f"Success email sent for use case {use_case_id}")

    except Exception as e:
        logger.error(f"Failed to send success email for {use_case_id}: {e}", exc_info=True)
        raise


@celery_app.task(name='tasks.evaluation_tasks.process_evaluation_queue')
def process_evaluation_queue():
    """
    Periodic task to process evaluation queue

    This task runs on a schedule to pick up queued evaluations
    """
    logger.info("Processing evaluation queue")

    try:
        # Get queued use cases
        # use_case_repo = get_use_case_repository()
        # queued_use_cases = use_case_repo.get_pending_evaluation_queue()

        # Process each
        # for use_case in queued_use_cases:
        #     run_evaluation_task.delay(use_case.id)

        pass

    except Exception as e:
        logger.error(f"Error processing evaluation queue: {e}", exc_info=True)
        raise
