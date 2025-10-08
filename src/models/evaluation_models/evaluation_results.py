"""Data models for evaluation results"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class TaskType(Enum):
    """Task types for evaluation"""
    CLASSIFICATION = "Classification"
    ENTITY_EXTRACTION = "Entity Extraction"
    CLASSIFICATION_AND_EXTRACTION = "Classification + Entity Extraction"
    SUMMARIZATION = "Summarization"
    CONTEXT_REWRITING = "Context Rewriting"


class EvaluationTeam(Enum):
    """Teams performing evaluation"""
    OPS = "ops"
    DC = "dc"


class ReferenceAlignmentLevel(Enum):
    """Quality levels for reference alignment (3 levels)"""
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"


class QualityLevel(Enum):
    """Quality levels for other quality metrics (2 levels)"""
    PASS = "Pass"
    FAIL = "Fail"


@dataclass
class FieldEvaluationResult:
    """Result of comparing model output vs golden answer for a single field"""

    # Identification
    category: str
    file_name: str
    task_type: TaskType
    field_name: str
    base_field: Optional[str] = None

    # Input/Output
    model_output: Any = None
    golden_answer: Any = None

    # Comparison results
    match_result: Optional[str] = None  # MatchResult enum value
    similarity_score: Optional[float] = None
    strategy_used: Optional[str] = None

    # Manual evaluations
    ops_evaluation: Optional[bool] = None  # True = Pass, False = Fail
    dc_evaluation: Optional[bool] = None   # True = Pass, False = Fail
    evaluation_agreement: Optional[bool] = None  # True if ops == dc

    # Metadata
    prompt_id: Optional[str] = None
    input_text: Optional[str] = None


@dataclass
class QualityMetricsResult:
    """Result for quality metrics (Summarization/Context Rewriting)"""

    # Identification
    category: str
    file_name: str
    task_type: TaskType

    # Input/Output
    model_output: str
    golden_answer: str

    # Ops team evaluations
    ops_reference_alignment: Optional[ReferenceAlignmentLevel] = None  # Good/Average/Poor
    ops_hallucination: Optional[QualityLevel] = None  # Pass/Fail
    ops_comprehensiveness: Optional[QualityLevel] = None  # Pass/Fail
    ops_relevance: Optional[QualityLevel] = None  # Pass/Fail

    # DC team evaluations
    dc_reference_alignment: Optional[ReferenceAlignmentLevel] = None  # Good/Average/Poor
    dc_hallucination: Optional[QualityLevel] = None  # Pass/Fail
    dc_comprehensiveness: Optional[QualityLevel] = None  # Pass/Fail
    dc_relevance: Optional[QualityLevel] = None  # Pass/Fail

    # Agreement checks
    reference_alignment_agreement: Optional[bool] = None
    hallucination_agreement: Optional[bool] = None
    comprehensiveness_agreement: Optional[bool] = None
    relevance_agreement: Optional[bool] = None

    # Metadata
    prompt_id: Optional[str] = None
    input_text: Optional[str] = None


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for a category or overall"""

    total_samples: int = 0
    correct_samples: int = 0
    accuracy: float = 0.0

    def calculate(self):
        """Calculate accuracy from counts"""
        if self.total_samples > 0:
            self.accuracy = self.correct_samples / self.total_samples
        else:
            self.accuracy = 0.0


@dataclass
class ClassificationMetrics:
    """Classification metrics (precision, recall, F-beta) per class"""

    class_name: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0

    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    f_beta_score: float = 0.0  # Configurable beta

    def calculate(self, beta: float = 1.0):
        """
        Calculate classification metrics

        Args:
            beta: Beta value for F-beta score (default 1.0 for F1)
        """
        # Precision
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        else:
            self.precision = 0.0

        # Recall
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        else:
            self.recall = 0.0

        # F1 Score
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = 0.0

        # F-beta Score
        if self.precision + self.recall > 0:
            beta_squared = beta ** 2
            self.f_beta_score = (1 + beta_squared) * (self.precision * self.recall) / \
                               (beta_squared * self.precision + self.recall)
        else:
            self.f_beta_score = 0.0


@dataclass
class QualityMetricsSummary:
    """Summary of quality metrics scores"""

    total_samples: int = 0

    # Reference alignment (Good/Average/Poor)
    reference_alignment_counts: Dict[str, int] = field(default_factory=dict)  # {'Good': 10, 'Average': 5, 'Poor': 2}
    avg_reference_alignment: float = 0.0  # Average score (Good=3, Average=2, Poor=1)
    reference_alignment_agreement_rate: float = 0.0

    # Hallucination (Pass/Fail)
    hallucination_pass_count: int = 0
    hallucination_fail_count: int = 0
    hallucination_pass_rate: float = 0.0  # Pass rate (Pass/Total)
    hallucination_agreement_rate: float = 0.0

    # Comprehensiveness (Pass/Fail)
    comprehensiveness_pass_count: int = 0
    comprehensiveness_fail_count: int = 0
    comprehensiveness_pass_rate: float = 0.0  # Pass rate (Pass/Total)
    comprehensiveness_agreement_rate: float = 0.0

    # Relevance (Pass/Fail)
    relevance_pass_count: int = 0
    relevance_fail_count: int = 0
    relevance_pass_rate: float = 0.0  # Pass rate (Pass/Total)
    relevance_agreement_rate: float = 0.0


@dataclass
class CategoryEvaluationSummary:
    """Evaluation summary for a specific category"""

    category: str
    task_type: TaskType
    team: EvaluationTeam

    # For Entity Extraction / Classification
    accuracy_metrics: Optional[AccuracyMetrics] = None
    classification_metrics: Optional[Dict[str, ClassificationMetrics]] = None  # class_name -> metrics

    # For Summarization / Context Rewriting
    quality_metrics: Optional[QualityMetricsSummary] = None


@dataclass
class OverallEvaluationSummary:
    """Overall evaluation summary across all categories"""

    task_type: TaskType
    team: EvaluationTeam

    # Category-level summaries
    category_summaries: Dict[str, CategoryEvaluationSummary] = field(default_factory=dict)

    # Overall metrics
    overall_accuracy: Optional[AccuracyMetrics] = None
    overall_classification_metrics: Optional[Dict[str, ClassificationMetrics]] = None
    overall_quality_metrics: Optional[QualityMetricsSummary] = None

    def add_category_summary(self, summary: CategoryEvaluationSummary):
        """Add a category summary"""
        self.category_summaries[summary.category] = summary
