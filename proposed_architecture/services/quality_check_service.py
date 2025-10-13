"""Quality check service for orchestrating data validation"""

from typing import List, Dict, Any
import pandas as pd

from ..quality_checks.base import QualityIssue, IssueSeverity
from ..quality_checks.factory import QualityCheckFactory
from ..repositories.use_case_repository import UseCaseRepository


class QualityCheckService:
    """Service for running quality checks on evaluation data"""

    def __init__(self, use_case_repo: UseCaseRepository):
        self.use_case_repo = use_case_repo

    def run_quality_checks(
        self,
        use_case_id: str,
        dataset_df: pd.DataFrame,
        field_config: Dict[str, Dict[str, Any]]
    ) -> List[QualityIssue]:
        """
        Run quality checks on dataset based on field configuration

        Args:
            use_case_id: Use case identifier
            dataset_df: Evaluation dataset
            field_config: Field configuration from use case team
                {
                    'field_name': {
                        'type': 'date',
                        'strategy': 'ExactDateTimeMatch',
                        'preprocessing': {...},
                        'validation_rules': {...}  # Quality check config
                    }
                }

        Returns:
            List of quality issues found
        """
        all_issues = []

        for field_name, config in field_config.items():
            if field_name not in dataset_df.columns:
                all_issues.append(QualityIssue(
                    row_number=0,
                    field_name=field_name,
                    value=None,
                    issue_type="missing_field",
                    message=f"Field '{field_name}' not found in dataset",
                    severity=IssueSeverity.ERROR
                ))
                continue

            field_type = config.get('type', 'string')
            validation_rules = config.get('validation_rules', {})

            try:
                checker = QualityCheckFactory.get_checker(field_type, **validation_rules)
                issues = checker.check(dataset_df, field_name)
                all_issues.extend(issues)
            except Exception as e:
                all_issues.append(QualityIssue(
                    row_number=0,
                    field_name=field_name,
                    value=None,
                    issue_type="check_error",
                    message=f"Error running quality check: {str(e)}",
                    severity=IssueSeverity.ERROR
                ))

        return all_issues

    def generate_quality_report(self, issues: List[QualityIssue]) -> pd.DataFrame:
        """
        Generate Excel report of quality issues

        Args:
            issues: List of quality issues

        Returns:
            DataFrame formatted for Excel export
        """
        if not issues:
            return pd.DataFrame()

        report_data = []
        for issue in issues:
            report_data.append({
                'Row Number': issue.row_number,
                'Field Name': issue.field_name,
                'Current Value': issue.value,
                'Issue Type': issue.issue_type,
                'Description': issue.message,
                'Severity': issue.severity.value,
                'Suggestion': issue.suggestion or ''
            })

        df = pd.DataFrame(report_data)
        df = df.sort_values(['Severity', 'Row Number'], ascending=[False, True])
        return df

    def has_blocking_issues(self, issues: List[QualityIssue]) -> bool:
        """
        Check if there are any ERROR severity issues that block evaluation

        Args:
            issues: List of quality issues

        Returns:
            True if there are blocking errors
        """
        return any(issue.severity == IssueSeverity.ERROR for issue in issues)

    def get_issue_summary(self, issues: List[QualityIssue]) -> Dict[str, int]:
        """
        Get summary statistics of issues

        Args:
            issues: List of quality issues

        Returns:
            Dictionary with counts by severity
        """
        summary = {
            'total': len(issues),
            'errors': 0,
            'warnings': 0,
            'info': 0
        }

        for issue in issues:
            if issue.severity == IssueSeverity.ERROR:
                summary['errors'] += 1
            elif issue.severity == IssueSeverity.WARNING:
                summary['warnings'] += 1
            elif issue.severity == IssueSeverity.INFO:
                summary['info'] += 1

        return summary
