# Dataset-Level Quality Checks - Implementation Summary

## Overview

This document summarizes the implementation of dataset-level quality checks (non-field-specific validations) in the proposed architecture.

## What Was Added

### 1. New File: `dataset_checks.py`

Contains 5 new dataset-level quality check classes:

#### `ScenarioSampleSizeCheck`
- **Purpose**: Validates sufficient samples for each scenario/category
- **Use Cases**: Gender distribution, document types, age groups
- **Key Features**:
  - Configurable minimum samples per scenario
  - Scenario-specific minimums (e.g., lower thresholds for underrepresented groups)
  - Checks for missing expected scenarios
  - Configurable severity levels

#### `DocumentSampleSizeCheck`
- **Purpose**: Validates sufficient unique documents for document-level tasks
- **Use Cases**: Entity extraction, OCR, document classification
- **Key Features**:
  - Minimum unique document count validation
  - Checks for uneven field distribution across documents
  - Maximum fields per document threshold
  - Warns about over-representation from single documents

#### `DatasetSizeCheck`
- **Purpose**: Validates overall dataset size
- **Key Features**:
  - Minimum total samples validation
  - Optional maximum for performance warnings
  - Ensures statistical validity

#### `DataCompletenessCheck`
- **Purpose**: Validates data completeness across the dataset
- **Key Features**:
  - Maximum missing value percentage threshold
  - Critical fields that cannot have missing values
  - Overall completeness metrics

#### `BalancedDistributionCheck`
- **Purpose**: Checks class balance for classification tasks
- **Key Features**:
  - Maximum imbalance ratio (largest:smallest class)
  - Detects imbalanced datasets
  - Ensures at least 2 categories exist

### 2. Updated Files

#### `factory.py`
- Added imports for all new dataset check classes
- Registered 5 new check types in `STRATEGY_MAP`:
  - `scenario_sample_size`
  - `document_sample_size`
  - `dataset_size`
  - `data_completeness`
  - `balanced_distribution`

#### `quality_check_service.py`
- Added `dataset_config` parameter to `run_quality_checks()` method
- Implemented dataset-level check execution logic
- Maintains backward compatibility (dataset checks are optional)

### 3. Documentation

#### `DATASET_CHECKS_GUIDE.md`
Comprehensive guide including:
- Detailed description of each check type
- Configuration options and parameters
- Usage examples and code snippets
- Best practices and recommendations
- Common use cases
- Troubleshooting guide

#### `example_config_with_dataset_checks.json`
Complete example configuration demonstrating:
- Both field-level and dataset-level checks
- Real-world use case (Invoice Entity Extraction)
- Multiple dataset checks working together
- Rationale for each check

## How to Use

### Basic Usage

```python
# Configuration
config = {
    "fields": {
        "document_id": {...},
        "invoice_date": {...},
        # ... field configs
    },
    "dataset_checks": [
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "gender",
                "min_samples": 50
            }
        },
        {
            "type": "document_sample_size",
            "config": {
                "document_id_field": "document_id",
                "min_documents": 30
            }
        }
    ]
}

# Run checks
issues = quality_service.run_quality_checks(
    use_case_id='my_use_case',
    dataset_df=dataset_df,
    field_config=config['fields'],
    dataset_config=config  # Pass full config with dataset_checks
)
```

### Configuration Structure

```json
{
    "fields": {
        // Field-level checks (existing functionality)
    },
    "dataset_checks": [
        // New dataset-level checks
        {
            "type": "check_type",
            "config": {
                // Check-specific configuration
            }
        }
    ]
}
```

## Key Design Decisions

### 1. Base Class Hierarchy

```
QualityCheckStrategy (base.py)
    └── DatasetLevelCheck (dataset_checks.py)
        ├── ScenarioSampleSizeCheck
        ├── DocumentSampleSizeCheck
        ├── DatasetSizeCheck
        ├── DataCompletenessCheck
        └── BalancedDistributionCheck
```

- `DatasetLevelCheck` extends `QualityCheckStrategy`
- Implements `check()` to call `check_dataset()` for consistency
- All dataset checks report issues at row_number=0 (dataset-level)

### 2. Row Number Convention

- **Row 0**: Dataset-level issues (non-field-specific)
- **Row 1+**: Field-level issues (specific rows with problems)

This convention makes it easy to distinguish between dataset-level and row-level issues in reports.

### 3. Backward Compatibility

The implementation maintains full backward compatibility:
- Existing code without `dataset_config` parameter continues to work
- Dataset checks are optional
- Field-level checks work exactly as before

### 4. Severity Levels

All dataset checks support configurable severity:
- **ERROR**: Blocks evaluation (e.g., dataset too small)
- **WARNING**: Should review but doesn't block (e.g., slight imbalance)
- **INFO**: Informational only (e.g., distribution statistics)

## Examples by Use Case

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
        }
    ]
}
```

### Classification with Demographics

```json
{
    "dataset_checks": [
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "gender",
                "min_samples": 50,
                "scenario_specific_minimums": {
                    "non-binary": 10
                }
            }
        },
        {
            "type": "balanced_distribution",
            "config": {
                "category_field": "golden_answer",
                "max_imbalance_ratio": 3.0
            }
        }
    ]
}
```

### Multi-Document Multi-Scenario

```json
{
    "dataset_checks": [
        {
            "type": "dataset_size",
            "config": {"min_total_samples": 200}
        },
        {
            "type": "document_sample_size",
            "config": {
                "document_id_field": "document_id",
                "min_documents": 30
            }
        },
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "document_type",
                "min_samples": 25
            }
        },
        {
            "type": "scenario_sample_size",
            "config": {
                "scenario_field": "region",
                "min_samples": 30
            }
        }
    ]
}
```

## Testing Recommendations

### Unit Tests

Test each check class independently:

```python
def test_scenario_sample_size_check():
    # Create test dataframe
    df = pd.DataFrame({
        'gender': ['male'] * 60 + ['female'] * 40 + ['non-binary'] * 5
    })

    # Configure check
    checker = ScenarioSampleSizeCheck(
        scenario_field='gender',
        min_samples=50,
        scenario_specific_minimums={'non-binary': 10}
    )

    # Run check
    issues = checker.check_dataset(df)

    # Assertions
    assert len(issues) == 2  # female and non-binary below threshold
    assert any('female' in issue.message for issue in issues)
    assert any('non-binary' in issue.message for issue in issues)
```

### Integration Tests

Test the complete flow:

```python
def test_quality_check_service_with_dataset_checks():
    config = {
        "fields": {...},
        "dataset_checks": [
            {
                "type": "dataset_size",
                "config": {"min_total_samples": 100}
            }
        ]
    }

    issues = quality_service.run_quality_checks(
        use_case_id='test',
        dataset_df=small_df,  # Only 50 rows
        field_config=config['fields'],
        dataset_config=config
    )

    assert any(issue.issue_type == 'insufficient_dataset_size' for issue in issues)
```

## Future Enhancements

### Potential Additional Checks

1. **Time-based Sampling Check**
   - Ensure data spans sufficient time periods
   - Check for temporal gaps

2. **Duplicate Detection**
   - Check for exact duplicate rows
   - Near-duplicate detection

3. **Outlier Detection**
   - Statistical outlier identification
   - Flag potential data quality issues

4. **Cross-Scenario Balance**
   - Check balance across multiple dimensions
   - E.g., gender × region combinations

5. **Data Freshness Check**
   - Validate data is not too old
   - Check last update timestamps

### Extension Pattern

To add new dataset checks:

```python
from quality_checks.dataset_checks import DatasetLevelCheck

class CustomDatasetCheck(DatasetLevelCheck):
    def check_dataset(self, df: pd.DataFrame) -> List[QualityIssue]:
        # Your logic here
        pass

    def get_description(self) -> str:
        return "Description of check"

# Register it
QualityCheckFactory.register_strategy('custom_check', CustomDatasetCheck)
```

## Performance Considerations

### Memory Usage

- Dataset checks operate on the full DataFrame
- For very large datasets (>1M rows), consider:
  - Sampling for distribution checks
  - Streaming for completeness checks
  - Caching computed statistics

### Execution Time

- Most checks are O(n) or O(n log n)
- For multiple scenario checks on same field, consider caching value_counts()
- Run checks in parallel when possible

### Optimization Tips

```python
# Cache scenario counts if checking multiple times
scenario_counts = df[scenario_field].value_counts()

# Use this cached result for multiple checks
# Instead of recomputing each time
```

## Related Documentation

- **Full Guide**: `DATASET_CHECKS_GUIDE.md`
- **Example Config**: `example_config_with_dataset_checks.json`
- **Base Classes**: `base.py`
- **Factory Pattern**: `factory.py`
- **Service Integration**: `../services/quality_check_service.py`

## Questions or Issues?

For questions about:
- **Configuration**: See `DATASET_CHECKS_GUIDE.md`
- **Implementation**: See `dataset_checks.py`
- **Integration**: See `quality_check_service.py`
- **Examples**: See `example_config_with_dataset_checks.json`
