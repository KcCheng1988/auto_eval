"""Base classes for quality check strategies"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class IssueSeverity(Enum):
    """Severity levels for quality issues"""
    ERROR = "error"        # Blocks evaluation
    WARNING = "warning"    # Doesn't block, but should be reviewed
    INFO = "info"          # Informational only


@dataclass
class QualityIssue:
    """Represents a single quality check failure"""
    row_number: int              # Excel row number (1-indexed with header)
    field_name: str              # Field that failed
    value: Any                   # Actual value that failed
    issue_type: str              # Type of issue (e.g., "invalid_date")
    message: str                 # Human-readable description
    severity: IssueSeverity      # ERROR, WARNING, or INFO
    suggestion: Optional[str] = None  # Suggested fix

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'row_number': self.row_number,
            'field_name': self.field_name,
            'value': str(self.value),
            'issue_type': self.issue_type,
            'message': self.message,
            'severity': self.severity.value,
            'suggestion': self.suggestion
        }


class QualityCheckStrategy(ABC):
    """
    Abstract base class for quality check strategies

    Each strategy implements checks for a specific data type or constraint
    """

    def __init__(self, **config):
        """
        Initialize strategy with configuration

        Args:
            **config: Strategy-specific configuration parameters
        """
        self.config = config

    @abstractmethod
    def check(
        self,
        df: pd.DataFrame,
        field_name: str
    ) -> List[QualityIssue]:
        """
        Run quality check on specific field in dataframe

        Args:
            df: Pandas DataFrame containing the data
            field_name: Name of the column to check

        Returns:
            List of quality issues found (empty if no issues)
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of what this check does"""
        pass

    def _create_issue(
        self,
        row_idx: int,
        field_name: str,
        value: Any,
        issue_type: str,
        message: str,
        severity: IssueSeverity = IssueSeverity.ERROR,
        suggestion: Optional[str] = None
    ) -> QualityIssue:
        """Helper to create quality issue with consistent formatting"""
        return QualityIssue(
            row_number=row_idx + 2,  # +1 for 0-index, +1 for header row
            field_name=field_name,
            value=value,
            issue_type=issue_type,
            message=message,
            severity=severity,
            suggestion=suggestion
        )
