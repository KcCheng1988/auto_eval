"""String validation strategies"""

from typing import List, Set
import pandas as pd
import re

from .base import QualityCheckStrategy, QualityIssue, IssueSeverity


class StringQualityCheck(QualityCheckStrategy):
    """
    Check string field constraints

    Configuration options:
    - min_length: int - minimum string length
    - max_length: int - maximum string length
    - pattern: str - regex pattern that value must match
    - allowed_values: List[str] - whitelist of allowed values
    - disallowed_values: List[str] - blacklist of forbidden values
    - required: bool (default True) - whether nulls are allowed
    - trim_whitespace: bool (default True) - whether to trim before validation
    """

    def check(self, df: pd.DataFrame, field_name: str) -> List[QualityIssue]:
        issues = []

        min_length = self.config.get('min_length')
        max_length = self.config.get('max_length')
        pattern = self.config.get('pattern')
        allowed_values = set(self.config.get('allowed_values', []))
        disallowed_values = set(self.config.get('disallowed_values', []))
        required = self.config.get('required', True)
        trim_whitespace = self.config.get('trim_whitespace', True)

        # Compile regex if provided
        regex = re.compile(pattern) if pattern else None

        for idx, value in df[field_name].items():
            # Check if null
            if pd.isna(value) or value == '' or value is None:
                if required:
                    issues.append(self._create_issue(
                        idx, field_name, value,
                        'missing_string',
                        f'String field cannot be empty',
                        IssueSeverity.ERROR
                    ))
                continue

            # Convert to string and trim if needed
            str_value = str(value)
            if trim_whitespace:
                str_value = str_value.strip()

            # Check length
            if min_length is not None and len(str_value) < min_length:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'string_too_short',
                    f'String length {len(str_value)} is below minimum {min_length}',
                    IssueSeverity.ERROR
                ))

            if max_length is not None and len(str_value) > max_length:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'string_too_long',
                    f'String length {len(str_value)} exceeds maximum {max_length}',
                    IssueSeverity.WARNING
                ))

            # Check pattern
            if regex and not regex.match(str_value):
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'pattern_mismatch',
                    f'Value does not match required pattern: {pattern}',
                    IssueSeverity.ERROR
                ))

            # Check allowed values
            if allowed_values and str_value not in allowed_values:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'value_not_allowed',
                    f'Value "{str_value}" is not in allowed list',
                    IssueSeverity.ERROR,
                    suggestion=f'Allowed values: {", ".join(sorted(allowed_values))}'
                ))

            # Check disallowed values
            if disallowed_values and str_value in disallowed_values:
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'value_forbidden',
                    f'Value "{str_value}" is not allowed',
                    IssueSeverity.ERROR
                ))

        return issues

    def get_description(self) -> str:
        return "Validates string length, format, and allowed values"


class EmailQualityCheck(QualityCheckStrategy):
    """Check if values are valid email addresses"""

    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    def check(self, df: pd.DataFrame, field_name: str) -> List[QualityIssue]:
        issues = []
        regex = re.compile(self.EMAIL_PATTERN)

        for idx, value in df[field_name].items():
            if pd.isna(value) or value == '':
                continue

            str_value = str(value).strip()

            if not regex.match(str_value):
                issues.append(self._create_issue(
                    idx, field_name, value,
                    'invalid_email',
                    f'"{str_value}" is not a valid email address',
                    IssueSeverity.ERROR,
                    suggestion='Use format: user@example.com'
                ))

        return issues

    def get_description(self) -> str:
        return "Validates that values are properly formatted email addresses"
