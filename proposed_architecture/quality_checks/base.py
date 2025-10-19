"""Base classes for quality check strategies"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

# Import domain models
from ..domain import QualityIssue, IssueSeverity


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
