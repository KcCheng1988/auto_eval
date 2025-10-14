"""
SQLite Repository Implementation
Concrete implementation of repository interfaces using SQLite
"""

import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from ..domain.models import UseCase
from ..domain.state_machine import UseCaseState
from .base import Repository


class SQLiteConnection:
    """SQLite connection manager"""

    def __init__(self, db_path: str):
        """
        Initialize connection manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = False
    ):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.lastrowid

    def execute_many(self, query: str, params_list: List[tuple]):
        """Execute query with multiple parameter sets"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount


class UseCaseRepository(Repository[UseCase, str]):
    """SQLite repository for use cases"""

    def __init__(self, db_connection: SQLiteConnection):
        """
        Initialize repository

        Args:
            db_connection: SQLite connection manager
        """
        self.db = db_connection

    def create(self, entity: UseCase) -> UseCase:
        """Create new use case"""
        query = """
            INSERT INTO use_cases (
                id, name, team_email, state, config_file_path,
                dataset_file_path, quality_issues, evaluation_results,
                metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            entity.id,
            entity.name,
            entity.team_email,
            entity.state.value if isinstance(entity.state, UseCaseState) else entity.state,
            entity.config_file_path,
            entity.dataset_file_path,
            json.dumps(entity.quality_issues) if entity.quality_issues else None,
            json.dumps(entity.evaluation_results) if entity.evaluation_results else None,
            json.dumps(entity.metadata) if hasattr(entity, 'metadata') else '{}',
            entity.created_at.isoformat(),
            entity.updated_at.isoformat()
        )

        self.db.execute_query(query, params)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[UseCase]:
        """Get use case by ID"""
        query = "SELECT * FROM use_cases WHERE id = ?"
        row = self.db.execute_query(query, (entity_id,), fetch_one=True)

        if row:
            return self._row_to_entity(row)
        return None

    def update(self, entity: UseCase) -> UseCase:
        """Update use case"""
        query = """
            UPDATE use_cases
            SET name = ?, team_email = ?, state = ?, config_file_path = ?,
                dataset_file_path = ?, quality_issues = ?, evaluation_results = ?,
                metadata = ?, updated_at = ?
            WHERE id = ?
        """

        params = (
            entity.name,
            entity.team_email,
            entity.state.value if isinstance(entity.state, UseCaseState) else entity.state,
            entity.config_file_path,
            entity.dataset_file_path,
            json.dumps(entity.quality_issues) if entity.quality_issues else None,
            json.dumps(entity.evaluation_results) if entity.evaluation_results else None,
            json.dumps(entity.metadata) if hasattr(entity, 'metadata') else '{}',
            datetime.now().isoformat(),
            entity.id
        )

        self.db.execute_query(query, params)
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete use case"""
        query = "DELETE FROM use_cases WHERE id = ?"
        self.db.execute_query(query, (entity_id,))
        return True

    def get_all(self, limit: int = 100, offset: int = 0) -> List[UseCase]:
        """Get all use cases with pagination"""
        query = """
            SELECT * FROM use_cases
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        rows = self.db.execute_query(query, (limit, offset), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def find_by_state(self, state: UseCaseState) -> List[UseCase]:
        """Find use cases by state"""
        query = "SELECT * FROM use_cases WHERE state = ? ORDER BY created_at DESC"
        rows = self.db.execute_query(
            query,
            (state.value if isinstance(state, UseCaseState) else state,),
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def find_by_team_email(self, team_email: str) -> List[UseCase]:
        """Find use cases by team email"""
        query = "SELECT * FROM use_cases WHERE team_email = ? ORDER BY created_at DESC"
        rows = self.db.execute_query(query, (team_email,), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def search(self, search_term: str) -> List[UseCase]:
        """Search use cases by name"""
        query = """
            SELECT * FROM use_cases
            WHERE name LIKE ?
            ORDER BY created_at DESC
        """
        rows = self.db.execute_query(query, (f'%{search_term}%',), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def _row_to_entity(self, row: sqlite3.Row) -> UseCase:
        """Convert database row to UseCase entity"""
        return UseCase(
            id=row['id'],
            name=row['name'],
            team_email=row['team_email'],
            state=UseCaseState(row['state']),
            config_file_path=row['config_file_path'],
            dataset_file_path=row['dataset_file_path'],
            quality_issues=json.loads(row['quality_issues']) if row['quality_issues'] else None,
            evaluation_results=json.loads(row['evaluation_results']) if row['evaluation_results'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


class StateTransitionRepository:
    """Repository for state transitions"""

    def __init__(self, db_connection: SQLiteConnection):
        self.db = db_connection

    def create(self, transition: Dict[str, Any]) -> str:
        """Create state transition record"""
        transition_id = str(uuid.uuid4())

        query = """
            INSERT INTO state_transitions (
                id, use_case_id, from_state, to_state,
                triggered_by, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            transition_id,
            transition['use_case_id'],
            transition.get('from_state'),
            transition['to_state'],
            transition['triggered_by'],
            transition.get('notes'),
            datetime.now().isoformat()
        )

        self.db.execute_query(query, params)
        return transition_id

    def get_by_use_case(self, use_case_id: str) -> List[Dict[str, Any]]:
        """Get all transitions for a use case"""
        query = """
            SELECT * FROM state_transitions
            WHERE use_case_id = ?
            ORDER BY created_at ASC
        """
        rows = self.db.execute_query(query, (use_case_id,), fetch_all=True)

        transitions = []
        for row in rows:
            transitions.append({
                'id': row['id'],
                'use_case_id': row['use_case_id'],
                'from_state': row['from_state'],
                'to_state': row['to_state'],
                'triggered_by': row['triggered_by'],
                'notes': row['notes'],
                'created_at': row['created_at']
            })
        return transitions


class ActivityLogRepository:
    """Repository for activity logs"""

    def __init__(self, db_connection: SQLiteConnection):
        self.db = db_connection

    def log_activity(
        self,
        use_case_id: Optional[str],
        activity_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an activity"""
        activity_id = str(uuid.uuid4())

        query = """
            INSERT INTO activity_log (
                id, use_case_id, activity_type, description, details, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """

        params = (
            activity_id,
            use_case_id,
            activity_type,
            description,
            json.dumps(details) if details else None,
            datetime.now().isoformat()
        )

        self.db.execute_query(query, params)
        return activity_id

    def get_by_use_case(
        self,
        use_case_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get activity logs for a use case"""
        query = """
            SELECT * FROM activity_log
            WHERE use_case_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = self.db.execute_query(query, (use_case_id, limit), fetch_all=True)

        logs = []
        for row in rows:
            logs.append({
                'id': row['id'],
                'use_case_id': row['use_case_id'],
                'activity_type': row['activity_type'],
                'description': row['description'],
                'details': json.loads(row['details']) if row['details'] else None,
                'created_at': row['created_at']
            })
        return logs

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity logs across all use cases"""
        query = """
            SELECT * FROM activity_log
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = self.db.execute_query(query, (limit,), fetch_all=True)

        logs = []
        for row in rows:
            logs.append({
                'id': row['id'],
                'use_case_id': row['use_case_id'],
                'activity_type': row['activity_type'],
                'description': row['description'],
                'details': json.loads(row['details']) if row['details'] else None,
                'created_at': row['created_at']
            })
        return logs


class S3FileRepository:
    """Repository for tracking S3 files"""

    def __init__(self, db_connection: SQLiteConnection):
        self.db = db_connection

    def track_upload(
        self,
        use_case_id: str,
        file_type: str,
        s3_bucket: str,
        s3_key: str,
        local_path: Optional[str] = None,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track uploaded file"""
        file_id = str(uuid.uuid4())

        query = """
            INSERT INTO s3_files (
                id, use_case_id, file_type, s3_bucket, s3_key,
                local_path, file_size, checksum, metadata, uploaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            file_id,
            use_case_id,
            file_type,
            s3_bucket,
            s3_key,
            local_path,
            file_size,
            checksum,
            json.dumps(metadata) if metadata else None,
            datetime.now().isoformat()
        )

        self.db.execute_query(query, params)
        return file_id

    def get_by_use_case(
        self,
        use_case_id: str,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get files for a use case"""
        if file_type:
            query = """
                SELECT * FROM s3_files
                WHERE use_case_id = ? AND file_type = ?
                ORDER BY uploaded_at DESC
            """
            rows = self.db.execute_query(query, (use_case_id, file_type), fetch_all=True)
        else:
            query = """
                SELECT * FROM s3_files
                WHERE use_case_id = ?
                ORDER BY uploaded_at DESC
            """
            rows = self.db.execute_query(query, (use_case_id,), fetch_all=True)

        files = []
        for row in rows:
            files.append({
                'id': row['id'],
                'use_case_id': row['use_case_id'],
                'file_type': row['file_type'],
                's3_bucket': row['s3_bucket'],
                's3_key': row['s3_key'],
                'local_path': row['local_path'],
                'file_size': row['file_size'],
                'checksum': row['checksum'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                'uploaded_at': row['uploaded_at']
            })
        return files
