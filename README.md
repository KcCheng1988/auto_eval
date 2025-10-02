# Auto-Evaluation Tool for GenAI Use Cases

**Operation Team Data Chapter** - Automated evaluation system for GenAI model governance

## Overview

This tool automates the evaluation process for GenAI use cases, ensuring compliance with governance requirements. It validates Excel templates, evaluates model performance, and generates comprehensive reports.

## Features

### Task 1: Template Validation
- ✅ Validates Excel structure against standard template
- ✅ Flexible field detection (handles forms, images, various layouts)
- ✅ Data type and format validation
- ✅ Mandatory vs optional field checks
- ✅ Easy configuration updates for template changes

### Task 2: Model Evaluation
- ✅ Supports simple tasks (classification, entity extraction)
- ✅ Supports complex tasks (summarization, QA, rewriting)
- ✅ Human annotation-based evaluation for soft metrics
- ✅ MIIT dataset evaluation (sandbox vs UAT consistency)
- ✅ Configurable thresholds per use case stage

### Task 3: Report Generation
- ✅ HTML email report with visual formatting
- ✅ Auto-populated evaluation details
- ✅ Threshold compliance checks
- ✅ Discrepancy highlighting

## Project Structure

```
auto_eval/
├── src/
│   ├── validators/
│   │   └── template_validator.py      # Task 1: Template validation
│   ├── evaluators/
│   │   ├── inhouse_evaluator.py       # In-house evaluation library interface
│   │   └── evaluation_orchestrator.py # Task 2: Evaluation orchestration
│   ├── reporters/
│   │   └── report_generator.py        # Task 3: Report generation
│   ├── analysers/
│   │   ├── structure_analyser.py      # Sheet & structure analysis
│   │   ├── data_quality_analyser.py   # Data quality checks
│   │   ├── statistical_analyser.py    # Statistical summaries
│   │   ├── tabular_detector.py        # Tabular structure detection
│   │   └── excel_analyser.py          # Main analyser orchestrator
│   ├── utils/
│   │   ├── config_loader.py           # Configuration management
│   │   └── logger.py                  # Logging setup
│   └── pipeline.py                    # Main pipeline orchestrator
├── config/
│   ├── template_config.json           # Template validation rules
│   ├── evaluation_config.json         # Evaluation thresholds
│   └── report_config.json             # Report settings
├── logs/                              # Log files
├── output/                            # Generated reports
├── main.py                            # Evaluation CLI entry point
├── analyse_excel.py                   # Excel analysis CLI entry point
└── requirements.txt                   # Python dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- Cloudera environment access

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Verify directory structure exists:
```bash
python -c "from pathlib import Path; [Path(d).mkdir(exist_ok=True) for d in ['config', 'logs', 'output']]"
```

## Configuration

### Template Configuration (`config/template_config.json`)

Define expected sheets, fields, and validation rules:

```json
{
  "sheets": [
    {"name": "Use Case Information", "required": true},
    {"name": "Model Information", "required": true},
    {"name": "Evaluation Samples", "required": true},
    {"name": "MIIT", "required": false}
  ],
  "fields": {
    "Use Case Information": {
      "Use Case Name": {"mandatory": true},
      "Stage": {"mandatory": true}
    }
  },
  "validation_rules": {
    "Use Case Information": {
      "Stage": {
        "type": "string",
        "allowed_values": ["Autonomous", "Human-in-Loop"]
      }
    }
  }
}
```

### Evaluation Configuration (`config/evaluation_config.json`)

Define thresholds and metrics:

```json
{
  "thresholds": {
    "autonomous": {
      "accuracy": 0.95,
      "consistency_rate": 0.98
    },
    "human_in_loop": {
      "accuracy": 0.85,
      "consistency_rate": 0.90
    }
  }
}
```

### Updating Configurations

The tool is designed for easy configuration updates:

1. **Adding new fields**: Update `template_config.json` → `fields` section
2. **Changing thresholds**: Update `evaluation_config.json` → `thresholds` section
3. **New validation rules**: Update `template_config.json` → `validation_rules` section

Configuration changes take effect immediately on next run.

## Usage

### Basic Usage

Run the complete pipeline:
```bash
python main.py path/to/template.xlsx
```

### Advanced Options

**Validation only:**
```bash
python main.py path/to/template.xlsx --validation-only
```

**Evaluation only:**
```bash
python main.py path/to/template.xlsx --evaluation-only
```

**Custom output directory:**
```bash
python main.py path/to/template.xlsx --output-dir reports/
```

**Skip report generation:**
```bash
python main.py path/to/template.xlsx --no-report
```

**Verbose logging:**
```bash
python main.py path/to/template.xlsx --verbose
```

### Programmatic Usage

```python
from src.pipeline import AutoEvaluationPipeline

# Initialize pipeline
pipeline = AutoEvaluationPipeline(config_dir="config")

# Run full pipeline
results = pipeline.run(
    excel_path="path/to/template.xlsx",
    output_dir="output",
    generate_report=True
)

# Check results
if results['overall_status'] == 'success':
    print("Evaluation passed!")
    print(f"Report: {results['report_path']}")
else:
    print(f"Evaluation failed: {results['overall_status']}")
```

## Implementing In-House Evaluation Library

The tool provides a clean interface for your in-house evaluation library at `src/evaluators/inhouse_evaluator.py`.

### Steps to Integrate:

1. Open `src/evaluators/inhouse_evaluator.py`
2. Replace placeholder methods with your actual evaluation logic
3. Available methods:
   - `evaluate_classification()` - For classification tasks
   - `evaluate_entity_extraction()` - For entity extraction
   - `evaluate_with_human_annotation()` - For complex tasks with human annotations
   - `evaluate_miit()` - For MIIT consistency checks
   - `calculate_custom_metrics()` - For custom metrics

### Example Integration:

```python
def evaluate_classification(self, predictions: List[str], ground_truth: List[str], **kwargs):
    # Replace with your in-house library
    from your_inhouse_lib import ClassificationEvaluator

    evaluator = ClassificationEvaluator()
    results = evaluator.compute_metrics(predictions, ground_truth)

    return {
        "accuracy": results.accuracy,
        "precision": results.precision,
        "recall": results.recall
    }
```

## Excel Template Structure

### Expected Sheets

1. **Use Case Information** - Basic use case details
2. **Model Information** - Model and prompt details
3. **Evaluation Samples** - Test dataset with predictions
4. **MIIT** (optional) - Sandbox vs UAT comparison

### Field Detection

The tool uses flexible field detection:
- Handles "Field: Value" patterns
- Detects labels and values at any location
- Works with form-like structures
- Supports images and complex layouts

### Required Columns (Evaluation Samples)

- **Prediction** / Model Output / Output
- **Ground Truth** / Label / Expected
- For complex tasks: Human annotation columns

### Required Columns (MIIT)

- **Query** / Input / Question
- **Sandbox Response** / Sandbox Output
- **UAT Response** / UAT Output

## Outputs

### Log Files

Located in `logs/`:
- Format: `auto_eval_YYYYMMDD_HHMMSS.log`
- Contains detailed execution logs

### HTML Reports

Located in `output/`:
- Format: `evaluation_report_{filename}_{timestamp}.html`
- Includes:
  - Overall status badges
  - Use case and model information
  - Validation results with errors/warnings
  - Evaluation metrics
  - MIIT consistency results
  - Threshold compliance checks

### Report Sections

1. **Overall Status** - Pass/Fail badges
2. **Use Case Information** - Extracted details
3. **Model Information** - Model configuration
4. **Template Validation** - Errors and warnings
5. **Evaluation Results** - All metrics
6. **MIIT Results** - Consistency checks and discrepancies
7. **Threshold Compliance** - Pass/Fail per metric

## Workflow

1. **Receive Excel** from use case team
2. **Run validation** to check template structure
3. **Extract data** from validated template
4. **Run evaluation** using in-house library
5. **Check thresholds** based on use case stage
6. **Generate report** for approval
7. **Send to head** of department

## Error Handling

The tool provides clear error messages for:
- Missing sheets or fields
- Invalid data types
- Threshold failures
- MIIT discrepancies
- Template structure deviations

All errors are logged and included in the report.

## Extending the Tool

### Adding New Validation Rules

Edit `config/template_config.json`:
```json
"validation_rules": {
  "Your Sheet Name": {
    "Your Field": {
      "type": "integer",
      "min": 10,
      "max": 100,
      "pattern": "^[A-Z]+$"
    }
  }
}
```

### Adding New Metrics

1. Implement in `src/evaluators/inhouse_evaluator.py`
2. Add to `config/evaluation_config.json`:
```json
"metrics": [
  {
    "name": "your_metric",
    "description": "Description of metric"
  }
]
```

### Adding New Thresholds

Edit `config/evaluation_config.json`:
```json
"thresholds": {
  "autonomous": {
    "your_metric": 0.95
  }
}
```

## Troubleshooting

### Common Issues

**Issue**: Template validation fails
- Check that sheet names match configuration
- Verify mandatory fields are present
- Check data types and formats

**Issue**: Evaluation fails
- Ensure dataset has required columns
- Check that predictions and ground truth are aligned
- Verify in-house library is properly implemented

**Issue**: MIIT evaluation skipped
- Check if MIIT sheet exists
- Verify column names match expected patterns

### Debug Mode

Run with verbose logging:
```bash
python main.py template.xlsx --verbose
```

Check logs in `logs/` directory for detailed execution trace.

## Best Practices

1. **Keep configurations up to date** - Update configs when template structure changes
2. **Test with sample data** - Validate new configurations with test files
3. **Review reports** - Check generated reports before sending to stakeholders
4. **Version control configs** - Track configuration changes
5. **Document custom metrics** - Add descriptions for team understanding

## Excel Analyser

A comprehensive Excel file analysis tool that provides:

### Features

1. **Structure Analysis**
   - Active vs hidden sheets count
   - Images and charts detection
   - Merged cells analysis
   - Formulas, data validation, conditional formatting detection

2. **Data Quality Analysis**
   - Missing values detection
   - Duplicate rows identification
   - Data type consistency checks
   - Whitespace issues detection
   - Quality scoring (0-100)

3. **Statistical Analysis**
   - Descriptive statistics for numeric columns (mean, median, std, quartiles)
   - Text statistics (length analysis, pattern detection)
   - DateTime range analysis
   - Top values frequency

4. **Tabular Structure Detection**
   - Identifies if sheets contain tabular data
   - Confidence scoring
   - Header row detection
   - Column consistency analysis
   - Rectangular structure validation

### Usage

**Quick summary:**
```bash
python analyse_excel.py file.xlsx --quick
```

**Full comprehensive analysis:**
```bash
python analyse_excel.py file.xlsx
```

**Specific analysis types:**
```bash
python analyse_excel.py file.xlsx --structure
python analyse_excel.py file.xlsx --quality
python analyse_excel.py file.xlsx --statistics
python analyse_excel.py file.xlsx --tabular
```

**Analyze specific sheet:**
```bash
python analyse_excel.py file.xlsx --sheet "Sheet1" --quality
```

**Save report to file:**
```bash
python analyse_excel.py file.xlsx --output report.txt
python analyse_excel.py file.xlsx --output report.json --format json
```

**Programmatic usage:**
```python
from src.analysers.excel_analyser import ExcelAnalyser

analyser = ExcelAnalyser()

# Quick summary
summary = analyser.get_quick_summary("file.xlsx")
print(summary)

# Comprehensive analysis
results = analyser.analyse_all("file.xlsx", output_format="dict")

# Specific analyses
structure = analyser.analyse_structure("file.xlsx")
quality = analyser.analyse_quality("file.xlsx", sheet_name="Sheet1")
stats = analyser.analyse_statistics("file.xlsx")
tabular = analyser.detect_tabular("file.xlsx")

# Save report
analyser.save_report("file.xlsx", "output/report.txt", format="text")
```

### Output Examples

**Quick Summary:**
```
📊 STRUCTURE:
  • Total Sheets: 3
  • Active: 3, Hidden: 0
  • Images: 2
  • Charts: 1

✅ QUALITY:
  • Overall Score: 85.5/100
  • Issues: 5 (Critical: 1)

📋 TABULAR STRUCTURE:
  • Tabular Sheets: 2/3
  • Tabular: Sheet1, Sheet2
  • Non-Tabular: Dashboard
```

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review configuration files in `config/`
- Contact Operation Team Data Chapter

## License

Internal tool for Operation Team Data Chapter
