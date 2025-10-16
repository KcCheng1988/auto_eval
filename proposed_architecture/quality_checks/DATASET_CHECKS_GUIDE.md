# Dataset-Level Quality Checks Guide

This guide explains how to configure and use dataset-level quality checks (non-field-specific validations) in the evaluation system.

## Overview

Dataset-level checks validate overall dataset characteristics rather than individual field values. These checks are essential for ensuring:
- Sufficient sample sizes for statistical validity
- Balanced distributions for fair evaluation
- Adequate data completeness
- Proper document diversity (for document-level tasks)

## Available Dataset-Level Checks

### 1. Scenario Sample Size Check

**Type:** `scenario_sample_size`

Validates that each scenario/category has sufficient samples for meaningful evaluation.

**Use Cases:**
- Gender distribution (male, female, non-binary)
- Document types (invoice, receipt, contract)
- Age groups (18-25, 26-35, etc.)
- Any categorical variable that affects model performance

**Configuration:**
```json
{
    "type": "scenario_sample_size",
    "config": {
        "scenario_field": "gender",
        "min_samples": 50,
        "severity": "warning",
        "scenario_specific_minimums": {
            "non-binary": 10
        },
        "expected_scenarios": ["male", "female", "non-binary"]
    }
}
```

**Parameters:**
- `scenario_field` (required): Field name defining scenarios
- `min_samples` (default: 30): Minimum samples required per scenario
- `severity` (default: "warning"): "error", "warning", or "info"
- `scenario_specific_minimums` (optional): Override minimum for specific scenarios
- `expected_scenarios` (optional): List of scenarios that must be present

**Example Issues Detected:**
- "Scenario 'female' has only 15 samples (minimum required: 50)"
- "Expected scenario 'non-binary' is not present in the dataset"

---

### 2. Document Sample Size Check

**Type:** `document_sample_size`

Validates sufficient unique documents for document-level tasks like entity extraction.

**Use Cases:**
- Entity extraction (ensuring diversity across different documents)
- Document classification
- OCR evaluation
- Any task where multiple fields come from the same document

**Configuration:**
```json
{
    "type": "document_sample_size",
    "config": {
        "document_id_field": "document_id",
        "min_documents": 25,
        "severity": "error",
        "check_fields_per_document": true,
        "max_fields_per_document": 10
    }
}
```

**Parameters:**
- `document_id_field` (required): Field identifying unique documents
- `min_documents` (default: 20): Minimum unique documents required
- `severity` (default: "warning"): "error", "warning", or "info"
- `check_fields_per_document` (default: true): Check for uneven distribution
- `max_fields_per_document` (optional): Warn if document has too many fields

**Example Issues Detected:**
- "Only 12 unique documents found (minimum required: 25)"
- "Document 'invoice_001' has 25 fields (maximum recommended: 10)"
- "Fields are unevenly distributed across documents (avg: 5.2 fields/doc, std: 8.3)"

---

### 3. Dataset Size Check

**Type:** `dataset_size`

Validates overall dataset size for statistical validity.

**Configuration:**
```json
{
    "type": "dataset_size",
    "config": {
        "min_total_samples": 200,
        "max_total_samples": 10000,
        "severity": "error"
    }
}
```

**Parameters:**
- `min_total_samples` (default: 100): Minimum total rows required
- `max_total_samples` (optional): Maximum rows before performance warning
- `severity` (default: "error"): "error", "warning", or "info"

**Example Issues Detected:**
- "Dataset has only 75 rows (minimum required: 200)"
- "Dataset has 15000 rows (maximum recommended: 10000)"

---

### 4. Data Completeness Check

**Type:** `data_completeness`

Validates data completeness and checks critical fields have no missing values.

**Configuration:**
```json
{
    "type": "data_completeness",
    "config": {
        "max_missing_percentage": 5.0,
        "critical_fields": ["document_id", "golden_answer"],
        "severity": "warning"
    }
}
```

**Parameters:**
- `max_missing_percentage` (default: 10.0): Maximum allowed percentage of missing values
- `critical_fields` (optional): Fields that cannot have any missing values
- `severity` (default: "warning"): "error", "warning", or "info"

**Example Issues Detected:**
- "Dataset has 12.5% missing values (maximum allowed: 5.0%)"
- "Critical field 'golden_answer' has 3 missing values (0 allowed)"

---

### 5. Balanced Distribution Check

**Type:** `balanced_distribution`

Checks if data is balanced across categories for classification tasks.

**Configuration:**
```json
{
    "type": "balanced_distribution",
    "config": {
        "category_field": "golden_answer",
        "max_imbalance_ratio": 2.0,
        "severity": "info"
    }
}
```

**Parameters:**
- `category_field` (required): Field containing categories to balance
- `max_imbalance_ratio` (default: 3.0): Maximum ratio between largest and smallest class
- `severity` (default: "info"): "error", "warning", or "info"

**Example Issues Detected:**
- "Dataset is imbalanced (ratio: 5.2:1). Largest class 'yes': 520, Smallest class 'no': 100"
- "Only 1 category found in 'golden_answer' (classification requires at least 2)"

---

## Complete Configuration Example

Here's a complete example configuration combining field-level and dataset-level checks:

```json
{
    "fields": {
        "document_id": {
            "type": "string",
            "strategy": "ExactStringMatch",
            "validation_rules": {
                "max_length": 50,
                "pattern": "^DOC_[0-9]+$"
            }
        },
        "invoice_date": {
            "type": "date",
            "strategy": "ExactDateTimeMatch",
            "validation_rules": {
                "date_format": "%Y-%m-%d",
                "min_date": "2020-01-01",
                "max_date": "2024-12-31"
            }
        },
        "total_amount": {
            "type": "numeric",
            "strategy": "NumericMatch",
            "validation_rules": {
                "min_value": 0,
                "max_value": 1000000,
                "decimal_places": 2
            }
        },
        "golden_answer": {
            "type": "string",
            "strategy": "ExactStringMatch"
        }
    },
    "dataset_checks": [
        {
            "type": "dataset_size",
            "config": {
                "min_total_samples": 200,
                "max_total_samples": 10000,
                "severity": "error"
            }
        },
        {
            "type": "document_sample_size",
            "config": {
                "document_id_field": "document_id",
                "min_documents": 30,
                "severity": "error",
                "check_fields_per_document": true,
                "max_fields_per_document": 15
            }
        },
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "document_type",
                "min_samples": 25,
                "severity": "warning",
                "expected_scenarios": ["invoice", "receipt", "purchase_order"]
            }
        },
        {
            "type": "balanced_distribution",
            "config": {
                "category_field": "golden_answer",
                "max_imbalance_ratio": 3.0,
                "severity": "info"
            }
        },
        {
            "type": "data_completeness",
            "config": {
                "max_missing_percentage": 5.0,
                "critical_fields": ["document_id", "golden_answer"],
                "severity": "warning"
            }
        }
    ]
}
```

## How to Use in Code

### Running Quality Checks with Dataset Checks

```python
from services.quality_check_service import QualityCheckService
from repositories.use_case_repository import UseCaseRepository
import pandas as pd
import json

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Initialize service
use_case_repo = UseCaseRepository(session)
quality_service = QualityCheckService(use_case_repo)

# Load dataset
dataset_df = pd.read_excel('evaluation_dataset.xlsx')

# Run checks
field_config = config['fields']
dataset_config = config  # Contains 'dataset_checks' key

issues = quality_service.run_quality_checks(
    use_case_id='my_use_case',
    dataset_df=dataset_df,
    field_config=field_config,
    dataset_config=dataset_config
)

# Check for blocking issues
if quality_service.has_blocking_issues(issues):
    print("Dataset has blocking errors!")
    for issue in issues:
        if issue.severity == IssueSeverity.ERROR:
            print(f"ERROR: {issue.message}")
else:
    print("Dataset passed all quality checks!")

# Generate report
report_df = quality_service.generate_quality_report(issues)
report_df.to_excel('quality_report.xlsx', index=False)
```

### Creating Custom Dataset-Level Checks

You can create custom dataset-level checks by extending `DatasetLevelCheck`:

```python
from quality_checks.dataset_checks import DatasetLevelCheck
from quality_checks.base import QualityIssue, IssueSeverity
import pandas as pd

class CustomDatasetCheck(DatasetLevelCheck):
    """Your custom check description"""

    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        issues = []

        # Your validation logic here
        # Use self.config to access configuration parameters

        if something_is_wrong:
            issues.append(QualityIssue(
                row_number=0,  # 0 for dataset-level issues
                field_name="dataset",
                value=some_value,
                issue_type="custom_issue",
                message="Description of the issue",
                severity=IssueSeverity.WARNING,
                suggestion="How to fix it"
            ))

        return issues

    def get_description(self) -> str:
        return "Description of what this check does"

# Register it
from quality_checks.factory import QualityCheckFactory
QualityCheckFactory.register_strategy('custom_check', CustomDatasetCheck)
```

## Best Practices

### 1. Choose Appropriate Severity Levels

- **ERROR**: Blocks evaluation, must be fixed
  - Missing critical fields
  - Dataset too small for statistical validity
  - Zero samples in required scenarios

- **WARNING**: Should be reviewed, but doesn't block
  - Slightly imbalanced distributions
  - Fewer samples than recommended
  - Missing optional fields

- **INFO**: Informational, good to know
  - Minor imbalances
  - Distribution statistics
  - Optimization suggestions

### 2. Set Realistic Thresholds

```json
{
    "scenario_sample_size": {
        "min_samples": 30  // Statistical minimum for t-tests
    },
    "balanced_distribution": {
        "max_imbalance_ratio": 3.0  // Up to 3:1 is generally acceptable
    },
    "data_completeness": {
        "max_missing_percentage": 10.0  // More than 10% missing is concerning
    }
}
```

### 3. Use Scenario-Specific Minimums

For underrepresented groups or rare scenarios, use lower thresholds:

```json
{
    "scenario_field": "ethnicity",
    "min_samples": 50,
    "scenario_specific_minimums": {
        "indigenous": 15,  // Lower for rare groups
        "pacific_islander": 15
    }
}
```

### 4. Combine Multiple Checks

Use multiple checks together for comprehensive validation:

```json
{
    "dataset_checks": [
        {"type": "dataset_size", ...},           // Overall size
        {"type": "document_sample_size", ...},   // Document diversity
        {"type": "scenario_sample_size", ...},   // Scenario coverage
        {"type": "balanced_distribution", ...},  // Class balance
        {"type": "data_completeness", ...}       // Completeness
    ]
}
```

### 5. Document Your Requirements

Always document why you chose specific thresholds:

```json
{
    "type": "scenario_sample_size",
    "config": {
        "scenario_field": "gender",
        "min_samples": 50,
        "_comment": "Minimum 50 samples per gender based on power analysis for detecting 10% performance difference with 80% power"
    }
}
```

## Common Use Cases

### Entity Extraction from Documents

```json
{
    "dataset_checks": [
        {
            "type": "document_sample_size",
            "config": {
                "document_id_field": "document_id",
                "min_documents": 30,
                "max_fields_per_document": 20
            }
        },
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "document_type",
                "min_samples": 20
            }
        }
    ]
}
```

### Classification Task

```json
{
    "dataset_checks": [
        {
            "type": "dataset_size",
            "config": {
                "min_total_samples": 200
            }
        },
        {
            "type": "balanced_distribution",
            "config": {
                "category_field": "golden_answer",
                "max_imbalance_ratio": 2.0
            }
        },
        {
            "type": "data_completeness",
            "config": {
                "critical_fields": ["golden_answer"]
            }
        }
    ]
}
```

### Multi-Scenario Evaluation

```json
{
    "dataset_checks": [
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "age_group",
                "min_samples": 40,
                "expected_scenarios": ["18-25", "26-35", "36-50", "51+"]
            }
        },
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "region",
                "min_samples": 30,
                "expected_scenarios": ["north", "south", "east", "west"]
            }
        }
    ]
}
```

## Troubleshooting

### "Document ID field not found"
- Ensure `document_id_field` matches the exact column name in your dataset
- Check for typos or case sensitivity

### "Scenario field not found"
- Verify the `scenario_field` exists in your dataset
- Make sure the column name is spelled correctly

### "Too many dataset checks"
- Limit to 5-7 dataset-level checks for performance
- Focus on the most critical checks for your use case

### "Check failing unexpectedly"
- Review the actual data in your dataset
- Check if thresholds are too strict
- Consider using "warning" instead of "error" during initial testing

## Related Files

- `proposed_architecture/quality_checks/dataset_checks.py` - Implementation
- `proposed_architecture/quality_checks/factory.py` - Factory registration
- `proposed_architecture/services/quality_check_service.py` - Service integration
- `proposed_architecture/quality_checks/base.py` - Base classes
