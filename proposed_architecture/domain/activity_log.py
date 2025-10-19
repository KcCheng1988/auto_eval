"""ActivityLog domain model"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


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
