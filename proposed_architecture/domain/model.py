"""Model domain model"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
import uuid


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
