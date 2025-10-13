"""Cross-field consistency validation strategies"""

from typing import List, Dict, Any
import pandas as pd

from .base import QualityCheckStrategy, QualityIssue, IssueSeverity


class CrossFieldConsistencyCheck(QualityCheckStrategy):
    """
    Check consistency across multiple fields

    Configuration options:
    - rules: List[Dict] - list of consistency rules
        Each rule: {
            'condition_field': str,
            'condition_value': Any,
            'required_field': str,
            'required_value': Any (optional),
            'message': str
        }

    Example: If task_type is "Classification", then golden_answer cannot be empty
    """

    def check(self, df: pd.DataFrame, field_name: str) -> List[QualityIssue]:
        issues = []
        rules = self.config.get('rules', [])

        for rule in rules:
            condition_field = rule['condition_field']
            condition_value = rule['condition_value']
            required_field = rule['required_field']
            required_value = rule.get('required_value')
            message = rule['message']

            for idx, row in df.iterrows():
                # Check if condition is met
                if row[condition_field] == condition_value:
                    # Check required field
                    actual_value = row[required_field]

                    if required_value is not None:
                        # Specific value required
                        if actual_value != required_value:
                            issues.append(self._create_issue(
                                idx, required_field, actual_value,
                                'consistency_violation',
                                message,
                                IssueSeverity.ERROR
                            ))
                    else:
                        # Just check not empty
                        if pd.isna(actual_value) or actual_value == '':
                            issues.append(self._create_issue(
                                idx, required_field, actual_value,
                                'consistency_violation',
                                message,
                                IssueSeverity.ERROR
                            ))

        return issues

    def get_description(self) -> str:
        return "Validates consistency rules across multiple fields"


class DuplicateCheck(QualityCheckStrategy):
    """
    Check for duplicate values in fields that should be unique

    Configuration options:
    - check_across_fields: List[str] - check uniqueness across multiple fields
    """

    def check(self, df: pd.DataFrame, field_name: str) -> List[QualityIssue]:
        issues = []
        check_across = self.config.get('check_across_fields', [])

        if check_across:
            # Check combinations
            fields = [field_name] + check_across
            duplicates = df[df.duplicated(subset=fields, keep=False)]

            for idx, row in duplicates.iterrows():
                values = [row[f] for f in fields]
                issues.append(self._create_issue(
                    idx, field_name, row[field_name],
                    'duplicate_combination',
                    f'Duplicate combination found: {dict(zip(fields, values))}',
                    IssueSeverity.WARNING
                ))
        else:
            # Check single field
            duplicates = df[df[field_name].duplicated(keep=False)]

            for idx, value in duplicates[field_name].items():
                if not pd.isna(value):
                    issues.append(self._create_issue(
                        idx, field_name, value,
                        'duplicate_value',
                        f'Duplicate value found: "{value}"',
                        IssueSeverity.WARNING
                    ))

        return issues

    def get_description(self) -> str:
        return "Checks for duplicate values that should be unique"
