"""Numeric validation strategies"""

from typing import List
import pandas as pd

from .base import QualityCheckStrategy, QualityIssue, IssueSeverity


class NumericFormatQualityCheck(QualityCheckStrategy):
    """
    Check if all values can be converted to valid numbers

    Configuration options:
    - min_value: float - minimum allowed value
    - max_value: float - maximum allowed value
    - allow_negative: bool (default True) - whether negative numbers are allowed
    - allow_zero: bool (default True) - whether zero is allowed
    - required: bool (default True) - whether nulls are allowed
    - integer_only: bool (default False) - require integer values
    """

    def check(self, df: pd.DataFrame, field_name: str) -> List[QualityIssue]:
        issues = []

        # Import here to avoid circular dependency
        from ...src.models.comparison_strategies.utils import NumericConverter

        min_value = self.config.get('min_value')
        max_value = self.config.get('max_value')
        allow_negative = self.config.get('allow_negative', True)
        allow_zero = self.config.get('allow_zero', True)
        required = self.config.get('required', True)
        integer_only = self.config.get('integer_only', False)

        for idx, value in df[field_name].items():
            # Check if null
            if pd.isna(value) or value == '' or value is None:
                if required:
                    issues.append(self._create_issue(
                        idx, field_name, value,
                        'missing_number',
                        f'Numeric field cannot be empty',
                        IssueSeverity.ERROR
                    ))
                continue

            # Try to convert to number
            num = NumericConverter.to_float(value)

            if num is None:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'invalid_numeric_format',
                    f'Cannot parse "{value}" as a valid number',
                    IssueSeverity.ERROR,
                    suggestion='Use numeric format: 123.45 or 1,234.56'
                ))
                continue

            # Check integer requirement
            if integer_only and not num.is_integer():
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'decimal_not_allowed',
                    f'Value {num} must be an integer (no decimals)',
                    IssueSeverity.ERROR
                ))

            # Check negative
            if not allow_negative and num < 0:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'negative_not_allowed',
                    f'Negative values are not allowed: {num}',
                    IssueSeverity.ERROR
                ))

            # Check zero
            if not allow_zero and num == 0:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'zero_not_allowed',
                    f'Zero value is not allowed',
                    IssueSeverity.ERROR
                ))

            # Check min value
            if min_value is not None and num < min_value:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'below_minimum',
                    f'Value {num} is below minimum {min_value}',
                    IssueSeverity.ERROR
                ))

            # Check max value
            if max_value is not None and num > max_value:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'above_maximum',
                    f'Value {num} is above maximum {max_value}',
                    IssueSeverity.ERROR
                ))

        return issues

    def get_description(self) -> str:
        return "Validates that all values are valid numbers within acceptable range"
