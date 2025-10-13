"""Date and datetime validation strategies"""

from datetime import datetime
from typing import List
import pandas as pd

from .base import QualityCheckStrategy, QualityIssue, IssueSeverity


class DateFormatQualityCheck(QualityCheckStrategy):
    """
    Check if all values can be converted to valid dates

    Configuration options:
    - allow_future: bool (default False) - whether to allow future dates
    - min_date: str - minimum allowed date (ISO format)
    - max_date: str - maximum allowed date (ISO format)
    - required: bool (default True) - whether nulls are allowed
    """

    def check(self, df: pd.DataFrame, field_name: str) -> List[QualityIssue]:
        issues = []

        # Import here to avoid circular dependency
        from ...src.models.comparison_strategies.utils import DateTimeConverter

        allow_future = self.config.get('allow_future', False)
        min_date = self.config.get('min_date')
        max_date = self.config.get('max_date')
        required = self.config.get('required', True)

        # Parse min/max dates if provided
        min_dt = datetime.fromisoformat(min_date) if min_date else None
        max_dt = datetime.fromisoformat(max_date) if max_date else None

        for idx, value in df[field_name].items():
            # Check if null
            if pd.isna(value) or value == '' or value is None:
                if required:
                    issues.append(self._create_issue(
                        idx, field_name, value,
                        'missing_date',
                        f'Date field cannot be empty',
                        IssueSeverity.ERROR
                    ))
                continue

            # Try to convert to date
            dt = DateTimeConverter.to_datetime(value)

            if dt is None:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'invalid_date_format',
                    f'Cannot parse "{value}" as a valid date',
                    IssueSeverity.ERROR,
                    suggestion='Use format: YYYY-MM-DD or MM/DD/YYYY'
                ))
                continue

            # Check if future date
            if not allow_future and dt > datetime.now():
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'future_date_not_allowed',
                    f'Future dates are not allowed: {dt.date()}',
                    IssueSeverity.ERROR
                ))

            # Check min date
            if min_dt and dt < min_dt:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'date_before_minimum',
                    f'Date {dt.date()} is before minimum allowed date {min_dt.date()}',
                    IssueSeverity.ERROR
                ))

            # Check max date
            if max_dt and dt > max_dt:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'date_after_maximum',
                    f'Date {dt.date()} is after maximum allowed date {max_dt.date()}',
                    IssueSeverity.ERROR
                ))

        return issues

    def get_description(self) -> str:
        return "Validates that all values are valid dates in acceptable format"
