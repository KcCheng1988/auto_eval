"""UseCase domain model"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


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
