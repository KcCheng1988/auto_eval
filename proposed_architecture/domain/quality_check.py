"""QualityCheck domain models"""

from dataclasses import dataclass
from typing import Any, Optional, Dict

from .enums import IssueSeverity


@dataclass
class QualityIssue:
    """
    Represents a single quality check failure

    This is a domain model representing quality issues found during
    data validation. Each issue captures:
    - Where the issue occurred (row_number, field_name)
    - What the problem is (issue_type, message)
    - How severe it is (severity)
    - How to fix it (suggestion)
    """
    row_number: int              # Excel row number (1-indexed with header)
    field_name: str              # Field that failed
    value: Any                   # Actual value that failed
    issue_type: str              # Type of issue (e.g., "invalid_date")
    message: str                 # Human-readable description
    severity: IssueSeverity      # ERROR, WARNING, or INFO
    suggestion: Optional[str] = None  # Suggested fix

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityIssue':
        """
        Factory method for reconstructing EXISTING quality issues (from database/API).

        Use this when loading from database or deserializing from JSON.
        Handles type conversions (strings → enums).
        """
        return cls(
            row_number=data['row_number'],
            field_name=data['field_name'],
            value=data['value'],
            issue_type=data['issue_type'],
            message=data['message'],
            severity=IssueSeverity(data['severity']) if isinstance(data['severity'], str) else data['severity'],
            suggestion=data.get('suggestion')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Use this when saving to database or returning from API.
        """
        return {
            'row_number': self.row_number,
            'field_name': self.field_name,
            'value': str(self.value),
            'issue_type': self.issue_type,
            'message': self.message,
            'severity': self.severity.value,
            'suggestion': self.suggestion
        }

    def is_blocking(self) -> bool:
        """Check if this issue blocks evaluation"""
        return self.severity == IssueSeverity.ERROR
