"""Celery application configuration"""

from celery import Celery
import os

# Initialize Celery
celery_app = Celery('evaluation_system')

# Load configuration from celeryconfig.py or environment
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Task routing
    task_routes={
        'tasks.quality_check_tasks.*': {'queue': 'quality_checks'},
        'tasks.evaluation_tasks.*': {'queue': 'evaluations'},
        'tasks.notification_tasks.*': {'queue': 'notifications'},
    },

    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['tasks'])
