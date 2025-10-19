"""EvaluationResult domain model"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from .enums import TaskType


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
