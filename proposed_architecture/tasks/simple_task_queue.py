"""
Simple task queue system using SQLite and background threads

This is a lightweight alternative to Celery/Redis for closed environments
where external dependencies cannot be installed.

Features:
- Persistent task queue using SQLite
- Background worker threads
- Task retries and error handling
- No external dependencies (Redis, RabbitMQ, etc.)
- Easy to deploy in restricted environments
"""

import sqlite3
import json
import threading
import time
import logging
import traceback
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Task:
    """Task representation"""
    id: str
    task_name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # Higher = more important

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task"""
        return {
            'id': self.id,
            'task_name': self.task_name,
            'args': json.dumps(self.args),
            'kwargs': json.dumps(self.kwargs),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'priority': self.priority
        }


class SimpleTaskQueue:
    """
    Simple task queue using SQLite for persistence

    Usage:
        # Initialize queue
        queue = SimpleTaskQueue('tasks.db')

        # Register task functions
        @queue.task(name='process_data')
        def process_data(data):
            # Your processing logic
            pass

        # Start worker
        queue.start_worker()

        # Queue a task
        queue.enqueue('process_data', args=[my_data])
    """

    def __init__(self, db_path: str = 'task_queue.db', num_workers: int = 2):
        """
        Initialize task queue

        Args:
            db_path: Path to SQLite database
            num_workers: Number of worker threads
        """
        self.db_path = db_path
        self.num_workers = num_workers
        self.task_registry: Dict[str, Callable] = {}
        self.workers: List[threading.Thread] = []
        self.running = False
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                args TEXT,
                kwargs TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                priority INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status_priority
            ON tasks (status, priority DESC, created_at)
        ''')

        conn.commit()
        conn.close()

    def task(self, name: Optional[str] = None, max_retries: int = 3):
        """
        Decorator to register task functions

        Usage:
            @queue.task(name='my_task', max_retries=5)
            def my_task(arg1, arg2):
                # Task logic
                pass
        """
        def decorator(func: Callable):
            task_name = name or func.__name__
            self.task_registry[task_name] = func
            func._task_name = task_name
            func._max_retries = max_retries
            return func
        return decorator

    def enqueue(
        self,
        task_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        max_retries: int = 3
    ) -> str:
        """
        Add task to queue

        Args:
            task_name: Name of registered task
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority (higher = more important)
            max_retries: Maximum retry attempts

        Returns:
            Task ID
        """
        if task_name not in self.task_registry:
            raise ValueError(f"Task '{task_name}' not registered")

        task = Task(
            id=str(uuid.uuid4()),
            task_name=task_name,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tasks
            (id, task_name, args, kwargs, status, created_at, retry_count, max_retries, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id,
            task.task_name,
            json.dumps(task.args),
            json.dumps(task.kwargs),
            task.status.value,
            task.created_at.isoformat(),
            task.retry_count,
            task.max_retries,
            task.priority
        ))

        conn.commit()
        conn.close()

        logger.info(f"Task enqueued: {task.task_name} (ID: {task.id})")
        return task.id

    def _get_next_task(self) -> Optional[Task]:
        """Get next pending task from queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get highest priority pending task
        cursor.execute('''
            SELECT id, task_name, args, kwargs, status, created_at,
                   started_at, completed_at, error_message, retry_count, max_retries, priority
            FROM tasks
            WHERE status IN ('pending', 'retrying')
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Task(
            id=row[0],
            task_name=row[1],
            args=json.loads(row[2]) if row[2] else [],
            kwargs=json.loads(row[3]) if row[3] else {},
            status=TaskStatus(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            started_at=datetime.fromisoformat(row[6]) if row[6] else None,
            completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
            error_message=row[8],
            retry_count=row[9],
            max_retries=row[10],
            priority=row[11]
        )

    def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None,
        increment_retry: bool = False
    ):
        """Update task status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        if status == TaskStatus.RUNNING:
            cursor.execute('''
                UPDATE tasks
                SET status = ?, started_at = ?
                WHERE id = ?
            ''', (status.value, now, task_id))

        elif status == TaskStatus.COMPLETED:
            cursor.execute('''
                UPDATE tasks
                SET status = ?, completed_at = ?
                WHERE id = ?
            ''', (status.value, now, task_id))

        elif status == TaskStatus.FAILED:
            cursor.execute('''
                UPDATE tasks
                SET status = ?, error_message = ?, completed_at = ?
                WHERE id = ?
            ''', (status.value, error_message, now, task_id))

        elif status == TaskStatus.RETRYING:
            retry_increment = 1 if increment_retry else 0
            cursor.execute('''
                UPDATE tasks
                SET status = ?, error_message = ?, retry_count = retry_count + ?
                WHERE id = ?
            ''', (status.value, error_message, retry_increment, task_id))

        conn.commit()
        conn.close()

    def _execute_task(self, task: Task):
        """Execute a task"""
        logger.info(f"Executing task: {task.task_name} (ID: {task.id})")

        try:
            # Mark as running
            self._update_task_status(task.id, TaskStatus.RUNNING)

            # Get task function
            task_func = self.task_registry[task.task_name]

            # Execute task
            task_func(*task.args, **task.kwargs)

            # Mark as completed
            self._update_task_status(task.id, TaskStatus.COMPLETED)
            logger.info(f"Task completed: {task.task_name} (ID: {task.id})")

        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Task failed: {task.task_name} (ID: {task.id}): {error_msg}")

            # Check if should retry
            if task.retry_count < task.max_retries:
                logger.info(
                    f"Retrying task {task.task_name} "
                    f"(attempt {task.retry_count + 1}/{task.max_retries})"
                )
                self._update_task_status(
                    task.id,
                    TaskStatus.RETRYING,
                    error_message=error_msg,
                    increment_retry=True
                )
            else:
                logger.error(
                    f"Task {task.task_name} failed after {task.max_retries} retries"
                )
                self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    error_message=error_msg
                )

    def _worker_loop(self, worker_id: int):
        """Worker thread main loop"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get next task
                task = self._get_next_task()

                if task:
                    self._execute_task(task)
                else:
                    # No tasks, sleep briefly
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    def start_worker(self):
        """Start worker threads"""
        if self.running:
            logger.warning("Workers already running")
            return

        self.running = True

        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started {self.num_workers} workers")

    def stop_worker(self):
        """Stop worker threads"""
        if not self.running:
            return

        logger.info("Stopping workers...")
        self.running = False

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=10)

        self.workers.clear()
        logger.info("All workers stopped")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, task_name, status, created_at, started_at, completed_at,
                   error_message, retry_count, max_retries
            FROM tasks
            WHERE id = ?
        ''', (task_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'id': row[0],
            'task_name': row[1],
            'status': row[2],
            'created_at': row[3],
            'started_at': row[4],
            'completed_at': row[5],
            'error_message': row[6],
            'retry_count': row[7],
            'max_retries': row[8]
        }

    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT status, COUNT(*)
            FROM tasks
            GROUP BY status
        ''')

        stats = {status.value: 0 for status in TaskStatus}
        for status, count in cursor.fetchall():
            stats[status] = count

        conn.close()
        return stats

    def cleanup_old_tasks(self, days: int = 30):
        """Remove old completed/failed tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            DELETE FROM tasks
            WHERE status IN ('completed', 'failed')
            AND completed_at < ?
        ''', (cutoff_date,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted} old tasks")
        return deleted


# Global task queue instance
_task_queue: Optional[SimpleTaskQueue] = None


def get_task_queue() -> SimpleTaskQueue:
    """Get global task queue instance"""
    global _task_queue
    if _task_queue is None:
        db_path = Path('data/task_queue.db')
        db_path.parent.mkdir(exist_ok=True)
        _task_queue = SimpleTaskQueue(str(db_path), num_workers=2)
    return _task_queue


def init_task_queue(db_path: str = 'data/task_queue.db', num_workers: int = 2):
    """Initialize global task queue"""
    global _task_queue
    Path(db_path).parent.mkdir(exist_ok=True)
    _task_queue = SimpleTaskQueue(db_path, num_workers)
    return _task_queue
