"""Dataset-level quality checks (non-field-specific validations)"""

from typing import List, Dict, Any
import pandas as pd

from .base import QualityCheckStrategy, QualityIssue, IssueSeverity


class DatasetLevelCheck(QualityCheckStrategy):
    """
    Base class for dataset-level checks that don't target specific fields

    These checks operate on the entire dataset and report issues at row 0
    to indicate they are dataset-level issues.
    """

    def check(self, df: pd.DataFrame, field_name: str = None) -> List[QualityIssue]:
        """
        Run dataset-level quality check

        Args:
            df: Pandas DataFrame containing the data
            field_name: Ignored for dataset-level checks (for interface compatibility)

        Returns:
            List of quality issues found (empty if no issues)
        """
        return self.check_dataset(df)

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        """
        Override this method to implement dataset-level checks

        Args:
            df: Pandas DataFrame containing the data

        Returns:
            List of quality issues found
        """
        raise NotImplementedError


class ScenarioSampleSizeCheck(DatasetLevelCheck):
    """
    Check if there are sufficient samples for each scenario/category

    Configuration options:
    - scenario_field: str - field name that defines scenarios (e.g., "gender", "document_type")
    - min_samples: int - minimum number of samples required per scenario (default: 30)
    - severity: str - "error", "warning", or "info" (default: "warning")
    - scenario_specific_minimums: Dict[str, int] - optional overrides for specific scenarios

    Example:
    {
        'scenario_field': 'gender',
        'min_samples': 50,
        'severity': 'warning',
        'scenario_specific_minimums': {
            'non-binary': 10  # Lower threshold for underrepresented groups
        }
    }
    """

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        issues = []

        scenario_field = self.config.get('scenario_field')
        if not scenario_field:
            return issues

        if scenario_field not in df.columns:
            issues.append(QualityIssue(
                row_number=0,
                field_name=scenario_field,
                value=None,
                issue_type="missing_scenario_field",
                message=f"Scenario field '{scenario_field}' not found in dataset",
                severity=IssueSeverity.ERROR
            ))
            return issues

        min_samples = self.config.get('min_samples', 30)
        severity_str = self.config.get('severity', 'warning').lower()
        severity_map = {
            'error': IssueSeverity.ERROR,
            'warning': IssueSeverity.WARNING,
            'info': IssueSeverity.INFO
        }
        severity = severity_map.get(severity_str, IssueSeverity.WARNING)
        scenario_minimums = self.config.get('scenario_specific_minimums', {})

        # Count samples per scenario
        scenario_counts = df[scenario_field].value_counts()

        for scenario, count in scenario_counts.items():
            # Check if scenario has specific minimum, otherwise use default
            required_min = scenario_minimums.get(scenario, min_samples)

            if count < required_min:
                issues.append(QualityIssue(
                    row_number=0,
                    field_name=scenario_field,
                    value=scenario,
                    issue_type="insufficient_scenario_samples",
                    message=f"Scenario '{scenario}' has only {count} samples (minimum required: {required_min})",
                    severity=severity,
                    suggestion=f"Add at least {required_min - count} more samples for scenario '{scenario}'"
                ))

        # Check for missing scenarios if configured
        expected_scenarios = self.config.get('expected_scenarios', [])
        if expected_scenarios:
            missing_scenarios = set(expected_scenarios) - set(scenario_counts.keys())
            for scenario in missing_scenarios:
                issues.append(QualityIssue(
                    row_number=0,
                    field_name=scenario_field,
                    value=None,
                    issue_type="missing_scenario",
                    message=f"Expected scenario '{scenario}' is not present in the dataset",
                    severity=IssueSeverity.ERROR,
                    suggestion=f"Add samples for scenario '{scenario}'"
                ))

        return issues

    def get_description(self) -> str:
        scenario_field = self.config.get('scenario_field', 'scenario')
        min_samples = self.config.get('min_samples', 30)
        return f"Validates sufficient samples per {scenario_field} (min: {min_samples})"


class DocumentSampleSizeCheck(DatasetLevelCheck):
    """
    Check if there are sufficient unique documents for tasks like entity extraction

    This is important for document-level tasks where having many fields from
    the same document doesn't provide true diversity in evaluation.

    Configuration options:
    - document_id_field: str - field that identifies unique documents
    - min_documents: int - minimum number of unique documents required (default: 20)
    - severity: str - "error", "warning", or "info" (default: "warning")
    - check_fields_per_document: bool - whether to warn if documents have uneven field counts (default: True)
    - max_fields_per_document: int - max fields from single document before warning (optional)

    Example:
    {
        'document_id_field': 'document_id',
        'min_documents': 25,
        'severity': 'error',
        'check_fields_per_document': True,
        'max_fields_per_document': 10
    }
    """

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        issues = []

        doc_id_field = self.config.get('document_id_field')
        if not doc_id_field:
            return issues

        if doc_id_field not in df.columns:
            issues.append(QualityIssue(
                row_number=0,
                field_name=doc_id_field,
                value=None,
                issue_type="missing_document_id_field",
                message=f"Document ID field '{doc_id_field}' not found in dataset",
                severity=IssueSeverity.ERROR
            ))
            return issues

        min_documents = self.config.get('min_documents', 20)
        severity_str = self.config.get('severity', 'warning').lower()
        severity_map = {
            'error': IssueSeverity.ERROR,
            'warning': IssueSeverity.WARNING,
            'info': IssueSeverity.INFO
        }
        severity = severity_map.get(severity_str, IssueSeverity.WARNING)

        # Count unique documents
        unique_docs = df[doc_id_field].nunique()
        total_fields = len(df)

        if unique_docs < min_documents:
            issues.append(QualityIssue(
                row_number=0,
                field_name=doc_id_field,
                value=unique_docs,
                issue_type="insufficient_document_samples",
                message=f"Only {unique_docs} unique documents found (minimum required: {min_documents})",
                severity=severity,
                suggestion=f"Add at least {min_documents - unique_docs} more unique documents"
            ))

        # Check fields per document distribution
        if self.config.get('check_fields_per_document', True):
            fields_per_doc = df[doc_id_field].value_counts()
            max_allowed = self.config.get('max_fields_per_document')

            if max_allowed:
                over_limit = fields_per_doc[fields_per_doc > max_allowed]
                if not over_limit.empty:
                    for doc_id, count in over_limit.items():
                        issues.append(QualityIssue(
                            row_number=0,
                            field_name=doc_id_field,
                            value=doc_id,
                            issue_type="too_many_fields_per_document",
                            message=f"Document '{doc_id}' has {count} fields (maximum recommended: {max_allowed})",
                            severity=IssueSeverity.WARNING,
                            suggestion=f"Consider distributing fields across more documents to avoid over-representation"
                        ))

            # Check for imbalanced distribution
            mean_fields = fields_per_doc.mean()
            std_fields = fields_per_doc.std()
            if std_fields > mean_fields * 0.5:  # High variance
                issues.append(QualityIssue(
                    row_number=0,
                    field_name=doc_id_field,
                    value=f"mean={mean_fields:.1f}, std={std_fields:.1f}",
                    issue_type="unbalanced_document_distribution",
                    message=f"Fields are unevenly distributed across documents (avg: {mean_fields:.1f} fields/doc, std: {std_fields:.1f})",
                    severity=IssueSeverity.INFO,
                    suggestion="Consider balancing the number of fields extracted from each document"
                ))

        return issues

    def get_description(self) -> str:
        doc_field = self.config.get('document_id_field', 'document_id')
        min_docs = self.config.get('min_documents', 20)
        return f"Validates sufficient unique documents via {doc_field} (min: {min_docs})"


class DatasetSizeCheck(DatasetLevelCheck):
    """
    Check overall dataset size

    Configuration options:
    - min_total_samples: int - minimum total number of rows (default: 100)
    - max_total_samples: int - maximum total number of rows (optional, for performance warnings)
    - severity: str - "error", "warning", or "info" (default: "error")

    Example:
    {
        'min_total_samples': 200,
        'max_total_samples': 10000,
        'severity': 'error'
    }
    """

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        issues = []

        min_samples = self.config.get('min_total_samples', 100)
        max_samples = self.config.get('max_total_samples')
        severity_str = self.config.get('severity', 'error').lower()
        severity_map = {
            'error': IssueSeverity.ERROR,
            'warning': IssueSeverity.WARNING,
            'info': IssueSeverity.INFO
        }
        severity = severity_map.get(severity_str, IssueSeverity.ERROR)

        total_rows = len(df)

        if total_rows < min_samples:
            issues.append(QualityIssue(
                row_number=0,
                field_name="dataset",
                value=total_rows,
                issue_type="insufficient_dataset_size",
                message=f"Dataset has only {total_rows} rows (minimum required: {min_samples})",
                severity=severity,
                suggestion=f"Add at least {min_samples - total_rows} more rows to the dataset"
            ))

        if max_samples and total_rows > max_samples:
            issues.append(QualityIssue(
                row_number=0,
                field_name="dataset",
                value=total_rows,
                issue_type="excessive_dataset_size",
                message=f"Dataset has {total_rows} rows (maximum recommended: {max_samples})",
                severity=IssueSeverity.WARNING,
                suggestion=f"Consider sampling or splitting the dataset for better performance"
            ))

        return issues

    def get_description(self) -> str:
        min_samples = self.config.get('min_total_samples', 100)
        return f"Validates overall dataset size (min: {min_samples} rows)"


class DataCompletenessCheck(DatasetLevelCheck):
    """
    Check data completeness across the dataset

    Configuration options:
    - max_missing_percentage: float - maximum allowed percentage of missing values (default: 10.0)
    - critical_fields: List[str] - fields that cannot have any missing values
    - severity: str - "error", "warning", or "info" (default: "warning")

    Example:
    {
        'max_missing_percentage': 5.0,
        'critical_fields': ['document_id', 'golden_answer'],
        'severity': 'warning'
    }
    """

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        issues = []

        max_missing_pct = self.config.get('max_missing_percentage', 10.0)
        critical_fields = self.config.get('critical_fields', [])
        severity_str = self.config.get('severity', 'warning').lower()
        severity_map = {
            'error': IssueSeverity.ERROR,
            'warning': IssueSeverity.WARNING,
            'info': IssueSeverity.INFO
        }
        severity = severity_map.get(severity_str, IssueSeverity.WARNING)

        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isna().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0

        if missing_pct > max_missing_pct:
            issues.append(QualityIssue(
                row_number=0,
                field_name="dataset",
                value=f"{missing_pct:.2f}%",
                issue_type="high_missing_data",
                message=f"Dataset has {missing_pct:.2f}% missing values (maximum allowed: {max_missing_pct}%)",
                severity=severity,
                suggestion="Review data collection process to reduce missing values"
            ))

        # Check critical fields
        for field in critical_fields:
            if field not in df.columns:
                issues.append(QualityIssue(
                    row_number=0,
                    field_name=field,
                    value=None,
                    issue_type="missing_critical_field",
                    message=f"Critical field '{field}' not found in dataset",
                    severity=IssueSeverity.ERROR
                ))
            else:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    issues.append(QualityIssue(
                        row_number=0,
                        field_name=field,
                        value=missing_count,
                        issue_type="missing_critical_values",
                        message=f"Critical field '{field}' has {missing_count} missing values (0 allowed)",
                        severity=IssueSeverity.ERROR,
                        suggestion=f"Fill in all missing values for critical field '{field}'"
                    ))

        return issues

    def get_description(self) -> str:
        max_pct = self.config.get('max_missing_percentage', 10.0)
        return f"Validates data completeness (max {max_pct}% missing values allowed)"


class BalancedDistributionCheck(DatasetLevelCheck):
    """
    Check if data is balanced across categories for classification tasks

    Configuration options:
    - category_field: str - field containing categories to balance
    - max_imbalance_ratio: float - maximum ratio between largest and smallest class (default: 3.0)
    - severity: str - "error", "warning", or "info" (default: "info")

    Example:
    {
        'category_field': 'golden_answer',
        'max_imbalance_ratio': 2.0,
        'severity': 'warning'
    }
    """

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        issues = []

        category_field = self.config.get('category_field')
        if not category_field:
            return issues

        if category_field not in df.columns:
            issues.append(QualityIssue(
                row_number=0,
                field_name=category_field,
                value=None,
                issue_type="missing_category_field",
                message=f"Category field '{category_field}' not found in dataset",
                severity=IssueSeverity.ERROR
            ))
            return issues

        max_ratio = self.config.get('max_imbalance_ratio', 3.0)
        severity_str = self.config.get('severity', 'info').lower()
        severity_map = {
            'error': IssueSeverity.ERROR,
            'warning': IssueSeverity.WARNING,
            'info': IssueSeverity.INFO
        }
        severity = severity_map.get(severity_str, IssueSeverity.INFO)

        category_counts = df[category_field].value_counts()

        if len(category_counts) < 2:
            issues.append(QualityIssue(
                row_number=0,
                field_name=category_field,
                value=len(category_counts),
                issue_type="insufficient_categories",
                message=f"Only {len(category_counts)} category found in '{category_field}' (classification requires at least 2)",
                severity=IssueSeverity.ERROR
            ))
            return issues

        max_count = category_counts.max()
        min_count = category_counts.min()
        imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')

        if imbalance_ratio > max_ratio:
            largest_class = category_counts.idxmax()
            smallest_class = category_counts.idxmin()

            issues.append(QualityIssue(
                row_number=0,
                field_name=category_field,
                value=f"{imbalance_ratio:.2f}",
                issue_type="imbalanced_distribution",
                message=f"Dataset is imbalanced (ratio: {imbalance_ratio:.2f}:1). "
                        f"Largest class '{largest_class}': {max_count}, Smallest class '{smallest_class}': {min_count}",
                severity=severity,
                suggestion=f"Consider balancing classes or using stratified sampling (target ratio <= {max_ratio}:1)"
            ))

        return issues

    def get_description(self) -> str:
        category_field = self.config.get('category_field', 'category')
        max_ratio = self.config.get('max_imbalance_ratio', 3.0)
        return f"Validates balanced distribution in {category_field} (max ratio: {max_ratio}:1)"
