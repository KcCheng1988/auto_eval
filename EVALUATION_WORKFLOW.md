```markdown
# Evaluation Workflow Architecture

## Overview

This document describes the complete workflow for evaluating LLM outputs across different task types.

## Input Data Structure

**Source Excel file with columns:**

| Column | Description | Example |
|--------|-------------|---------|
| category | Scenario grouping (age group, gender, etc.) | "Age 18-25" |
| task categorization | Task type | "Entity Extraction" |
| file name or unique identifier | Sample ID | "sample_001.txt" |
| prompt or prompt id | Production prompt used | "prompt_v2.1" |
| input text | Input to the prompt | "Patient is 45 years old..." |
| base field | Field hierarchy base | "name" |
| field name | Specific field | "mother" |
| model output | LLM output | "Jane Smith" |
| golden answer | Ground truth | "Jane Smith" |
| ops evaluation (accuracy) | Ops Pass/Fail (manual) | "Pass" |
| DC evaluation (accuracy) | DC Pass/Fail (automated) | "Pass" |
| ... | (quality metrics for Summarization tasks) | ... |

## Workflow by Task Type

### 1. Entity Extraction & Classification Tasks

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Field Classification                                    │
│ - Extract (base_field, field_name, model_output, golden_answer)│
│ - Use FieldClassifier to auto-detect field types and strategies│
│ - Save to Excel with dropdowns for manual review               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: User Review & Edit                                      │
│ - User opens Excel                                              │
│ - Adjusts field_type (dropdown)                               │
│ - Adjusts recommended_strategy (dropdown)                       │
│ - Adjusts settings (TRUE/FALSE dropdowns)                       │
│ - Saves edited configuration                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Field-Based Evaluation                                  │
│ - Load edited configuration with FieldConfigLoader              │
│ - For each row in source data:                                  │
│   • Apply strategy to compare model_output vs golden_answer     │
│   • Get MatchResult and similarity_score                        │
│   • DC evaluation = Pass if EXACT_MATCH, else Fail (automated)  │
│   • Ops evaluation = read from Excel (manual)                   │
│   • Calculate agreement: Ops == DC?                             │
│   • Create FieldEvaluationResult object                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Metrics Calculation                                     │
│ • Accuracy Metrics:                                             │
│   - Per category (Ops manual & DC automated)                    │
│   - Overall (Ops manual & DC automated)                         │
│   - Agreement rate (Ops vs DC consistency)                      │
│ • Classification Metrics (if task is Classification):           │
│   - Per class: Precision, Recall, F1, F-beta                   │
│   - Per category (Ops & DC)                                     │
│   - Overall (Ops & DC)                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Summary Tables & Visualization                          │
│ - Generate summary tables                                        │
│ - Create charts (accuracy by category, confusion matrix, etc.) │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Summarization & Context Rewriting Tasks

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Extract Quality Metrics                                 │
│ - Read columns 13-24 for non-empty values                      │
│ - Parse Ops evaluations (reference alignment, hallucination,    │
│   comprehensiveness, relevance)                                 │
│ - Parse DC evaluations (same metrics)                           │
│ - Create QualityMetricsResult objects                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Metrics Aggregation                                     │
│ • Count quality levels (Good/Average/Poor) for each metric      │
│ • Calculate average scores (Good=3, Average=2, Poor=1)          │
│ • Calculate agreement rates (Ops vs DC)                         │
│ • Generate per category and overall summaries                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Summary Tables & Visualization                          │
│ - Generate summary tables                                        │
│ - Create charts (quality distribution, agreement rates, etc.)   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### FieldEvaluationResult
For Entity Extraction/Classification tasks - stores comparison results for each field.

### QualityMetricsResult
For Summarization/Context Rewriting tasks - stores quality metric evaluations.

### AccuracyMetrics
Stores accuracy calculations (correct/total).

### ClassificationMetrics
Stores per-class metrics (TP, FP, FN, TN, precision, recall, F-scores).

### QualityMetricsSummary
Aggregated quality metrics with counts and averages.

### CategoryEvaluationSummary
Summary for a specific category (contains appropriate metrics based on task type).

### OverallEvaluationSummary
Overall summary across all categories.

## Key Classes to Implement

### 1. FieldBasedEvaluator
```python
class FieldBasedEvaluator:
    def __init__(self, field_config: Dict[str, ComparisonStrategy])
    def evaluate_sample(self, field_name, model_output, golden_answer) -> FieldEvaluationResult
    def evaluate_dataset(self, df: pd.DataFrame) -> List[FieldEvaluationResult]
    def calculate_accuracy(self, results: List[FieldEvaluationResult]) -> AccuracyMetrics
    def calculate_classification_metrics(self, results: List[FieldEvaluationResult]) -> Dict[str, ClassificationMetrics]
```

### 2. QualityMetricsEvaluator
```python
class QualityMetricsEvaluator:
    def extract_quality_metrics(self, df: pd.DataFrame) -> List[QualityMetricsResult]
    def calculate_quality_summary(self, results: List[QualityMetricsResult]) -> QualityMetricsSummary
```

### 3. EvaluationAggregator
```python
class EvaluationAggregator:
    def aggregate_by_category(self, results: List, team: EvaluationTeam) -> Dict[str, CategoryEvaluationSummary]
    def aggregate_overall(self, category_summaries: Dict) -> OverallEvaluationSummary
    def generate_summary_table(self, summary: OverallEvaluationSummary) -> pd.DataFrame
```

### 4. EvaluationVisualizer
```python
class EvaluationVisualizer:
    def plot_accuracy_by_category(self, summary: OverallEvaluationSummary)
    def plot_confusion_matrix(self, metrics: ClassificationMetrics)
    def plot_quality_distribution(self, summary: QualityMetricsSummary)
    def plot_agreement_rates(self, summary: OverallEvaluationSummary)
    def generate_report(self, summary: OverallEvaluationSummary, output_path: str)
```

## Usage Example

```python
from src.analysers.field_classifier import FieldClassifier
from src.analysers.field_config_loader import FieldConfigLoader
from src.evaluators.field_based_evaluator import FieldBasedEvaluator
from src.evaluators.quality_metrics_evaluator import QualityMetricsEvaluator
from src.evaluators.evaluation_aggregator import EvaluationAggregator
from src.reporters.evaluation_visualizer import EvaluationVisualizer

# Load source data
df = pd.read_excel('evaluation_data.xlsx')

# Separate by task type
entity_extraction_df = df[df['task categorization'].isin(['Entity Extraction', 'Classification'])]
summarization_df = df[df['task categorization'].isin(['Summarization', 'Context Rewriting'])]

## Entity Extraction / Classification Workflow
# 1. Classify fields
classifier = FieldClassifier()
classifier.save_classification_to_excel(entity_extraction_df, 'field_config.xlsx',
                                       field_name_col='field name',
                                       field_value_col='model output')

# 2. User edits field_config.xlsx...

# 3. Load edited config
loader = FieldConfigLoader()
field_strategies = loader.load_from_excel('field_config.xlsx')

# 4. Evaluate
evaluator = FieldBasedEvaluator(field_strategies)
field_results = evaluator.evaluate_dataset(entity_extraction_df)

# 5. Calculate metrics
accuracy_ops = evaluator.calculate_accuracy(field_results, team='ops')
accuracy_dc = evaluator.calculate_accuracy(field_results, team='dc')
classification_metrics = evaluator.calculate_classification_metrics(field_results)

## Summarization / Context Rewriting Workflow
# 1. Extract quality metrics
quality_evaluator = QualityMetricsEvaluator()
quality_results = quality_evaluator.extract_quality_metrics(summarization_df)

# 2. Calculate summaries
quality_summary_ops = quality_evaluator.calculate_quality_summary(quality_results, team='ops')
quality_summary_dc = quality_evaluator.calculate_quality_summary(quality_results, team='dc')

## Aggregation & Reporting
aggregator = EvaluationAggregator()
overall_summary = aggregator.aggregate_overall(field_results, quality_results)
summary_table = aggregator.generate_summary_table(overall_summary)

visualizer = EvaluationVisualizer()
visualizer.generate_report(overall_summary, 'evaluation_report.html')
```

## Output

### Summary Tables

**Accuracy by Category (Entity Extraction):**
| Category | Ops Accuracy | DC Accuracy | Agreement Rate |
|----------|-------------|-------------|----------------|
| Age 18-25 | 0.95 | 0.93 | 0.98 |
| Age 26-40 | 0.92 | 0.90 | 0.96 |
| Overall | 0.94 | 0.92 | 0.97 |

**Classification Metrics (per class):**
| Class | Precision | Recall | F1 Score | F-beta |
|-------|-----------|--------|----------|--------|
| Positive | 0.92 | 0.88 | 0.90 | 0.89 |
| Negative | 0.87 | 0.91 | 0.89 | 0.90 |

**Quality Metrics (Summarization):**
| Metric | Level/Rate | Agreement Rate |
|--------|-----------|----------------|
| Reference Alignment | Good: 45%, Average: 35%, Poor: 20% (Avg: 2.25) | 0.85 |
| Hallucination | Pass: 85%, Fail: 15% | 0.82 |
| Comprehensiveness | Pass: 78%, Fail: 22% | 0.88 |
| Relevance | Pass: 90%, Fail: 10% | 0.90 |

**Note on Quality Metrics:**
- **Reference Alignment**: 3 levels (Good, Average, Poor) - scored as 3, 2, 1
- **Hallucination, Comprehensiveness, Relevance**: 2 levels (Pass, Fail)

### Charts
- Accuracy by category (bar chart)
- Confusion matrix (heatmap)
- Quality metrics distribution (stacked bar chart)
- Agreement rates (line chart)
- Ops vs DC comparison (side-by-side bar charts)
```
