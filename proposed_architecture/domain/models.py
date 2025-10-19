"""Domain models for the evaluation system"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class TaskType(Enum):
    """Types of evaluation tasks"""
    ENTITY_EXTRACTION = "entity_extraction"
    CLASSIFICATION = "classification"
    CLASSIFICATION_AND_EXTRACTION = "classification_and_extraction"
    SUMMARIZATION = "summarization"
    CONTEXT_REWRITING = "context_rewriting"


@dataclass
class UseCase:
    """
    Use case domain model

    Represents a single evaluation use case submitted by a team.
    A use case can have multiple models being evaluated.
    """
    id: str
    name: str
    team_email: str
    state: 'UseCaseState'  # From state_machine.py
    created_at: datetime
    updated_at: datetime
    config_file_path: Optional[str] = None
    dataset_file_path: Optional[str] = None
    quality_issues: Optional[List[Dict[str, Any]]] = None
    evaluation_results: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_new(
        cls,
        name: str,
        team_email: str,
        initial_state: 'UseCaseState'
    ) -> 'UseCase':
        """
        Factory method for creating NEW use cases (from user input).

        Use this when a user submits a new use case.
        Generates ID and timestamps automatically.
        """
        now = datetime.now()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            team_email=team_email,
            state=initial_state,
            created_at=now,
            updated_at=now
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UseCase':
        """
        Factory method for reconstructing EXISTING use cases (from database/API).

        Use this when loading from database or deserializing from JSON.
        Handles type conversions (strings → datetime, enums, etc.)
        """
        from .state_machine import UseCaseState

        return cls(
            id=data['id'],
            name=data['name'],
            team_email=data['team_email'],
            state=UseCaseState(data['state']) if isinstance(data['state'], str) else data['state'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
            config_file_path=data.get('config_file_path'),
            dataset_file_path=data.get('dataset_file_path'),
            quality_issues=data.get('quality_issues'),
            evaluation_results=data.get('evaluation_results'),
            metadata=data.get('metadata', {})
        )

    def has_quality_issues(self) -> bool:
        """Check if use case has quality issues"""
        return bool(self.quality_issues)

    def is_ready_for_evaluation(self) -> bool:
        """Check if use case is ready for evaluation"""
        from .state_machine import UseCaseState
        return (
            self.state == UseCaseState.EVALUATION_QUEUED and
            self.config_file_path is not None and
            self.dataset_file_path is not None and
            not self.has_quality_issues()
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Use this when saving to database or returning from API.
        """
        return {
            'id': self.id,
            'name': self.name,
            'team_email': self.team_email,
            'state': self.state.value,
            'config_file_path': self.config_file_path,
            'dataset_file_path': self.dataset_file_path,
            'quality_issues': self.quality_issues,
            'evaluation_results': self.evaluation_results,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Model:
    """
    Model being evaluated

    A use case can evaluate multiple models (different versions, etc.)
    """
    id: str
    use_case_id: str
    model_name: str
    version: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_new(
        cls,
        use_case_id: str,
        model_name: str,
        version: str
    ) -> 'Model':
        """
        Factory method for creating NEW models.

        Use this when a user registers a new model.
        Generates ID and timestamp automatically.
        """
        return cls(
            id=str(uuid.uuid4()),
            use_case_id=use_case_id,
            model_name=model_name,
            version=version,
            created_at=datetime.now()
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Model':
        """
        Factory method for reconstructing EXISTING models (from database/API).

        Use this when loading from database or deserializing from JSON.
        Handles type conversions (strings → datetime).
        """
        return cls(
            id=data['id'],
            use_case_id=data['use_case_id'],
            model_name=data['model_name'],
            version=data['version'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Use this when saving to database or returning from API.
        """
        return {
            'id': self.id,
            'use_case_id': self.use_case_id,
            'model_name': self.model_name,
            'version': self.version,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class EvaluationResult:
    """
    Evaluation result for a specific model
    """
    id: str
    use_case_id: str
    model_id: str
    team: str  # 'OPS' or 'DC'
    task_type: TaskType
    accuracy: Optional[float] = None
    classification_metrics: Optional[Dict[str, Any]] = None
    agreement_rate: Optional[float] = None
    evaluated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_new(
        cls,
        use_case_id: str,
        model_id: str,
        team: str,
        task_type: TaskType
    ) -> 'EvaluationResult':
        """
        Factory method for creating NEW evaluation results.

        Use this when starting a new evaluation.
        Generates ID and timestamp automatically.
        """
        return cls(
            id=str(uuid.uuid4()),
            use_case_id=use_case_id,
            model_id=model_id,
            team=team,
            task_type=task_type
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """
        Factory method for reconstructing EXISTING evaluation results (from database/API).

        Use this when loading from database or deserializing from JSON.
        Handles type conversions (strings → datetime, enums).
        """
        return cls(
            id=data['id'],
            use_case_id=data['use_case_id'],
            model_id=data['model_id'],
            team=data['team'],
            task_type=TaskType(data['task_type']) if isinstance(data['task_type'], str) else data['task_type'],
            accuracy=data.get('accuracy'),
            classification_metrics=data.get('classification_metrics'),
            agreement_rate=data.get('agreement_rate'),
            evaluated_at=datetime.fromisoformat(data['evaluated_at']) if isinstance(data['evaluated_at'], str) else data['evaluated_at'],
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Use this when saving to database or returning from API.
        """
        return {
            'id': self.id,
            'use_case_id': self.use_case_id,
            'model_id': self.model_id,
            'team': self.team,
            'task_type': self.task_type.value,
            'accuracy': self.accuracy,
            'classification_metrics': self.classification_metrics,
            'agreement_rate': self.agreement_rate,
            'evaluated_at': self.evaluated_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ActivityLog:
    """
    Activity log entry for audit trail
    """
    id: str
    use_case_id: str
    activity_type: str
    description: str
    metadata: Dict[str, Any]
    created_at: datetime

    @classmethod
    def create_new(
        cls,
        use_case_id: str,
        activity_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ActivityLog':
        """
        Factory method for creating NEW activity logs.

        Use this when logging a new activity.
        Generates ID and timestamp automatically.
        """
        return cls(
            id=str(uuid.uuid4()),
            use_case_id=use_case_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {},
            created_at=datetime.now()
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityLog':
        """
        Factory method for reconstructing EXISTING activity logs (from database/API).

        Use this when loading from database or deserializing from JSON.
        Handles type conversions (strings → datetime).
        """
        return cls(
            id=data['id'],
            use_case_id=data['use_case_id'],
            activity_type=data['activity_type'],
            description=data['description'],
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at']
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Use this when saving to database or returning from API.
        """
        return {
            'id': self.id,
            'use_case_id': self.use_case_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
