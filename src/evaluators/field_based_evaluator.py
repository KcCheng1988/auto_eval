"""Field-based evaluator for Entity Extraction and Classification tasks"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from collections import defaultdict

from ..models.evaluation_models import (
    FieldEvaluationResult,
    AccuracyMetrics,
    ClassificationMetrics,
    TaskType,
    EvaluationTeam
)
from ..models.comparison_strategies import ComparisonStrategy, MatchResult
from ..analysers.field_config_loader import FieldConfigLoader


class FieldBasedEvaluator:
    """Evaluates Entity Extraction and Classification tasks using field-based comparison"""

    def __init__(self, field_strategies: Dict[str, ComparisonStrategy]):
        """
        Initialize evaluator with field comparison strategies

        Args:
            field_strategies: Map of field_name -> ComparisonStrategy instance
        """
        self.field_strategies = field_strategies

    @classmethod
    def from_config_file(cls, config_file_path: str) -> 'FieldBasedEvaluator':
        """
        Create evaluator from edited configuration Excel file

        Args:
            config_file_path: Path to Excel file with field configurations

        Returns:
            FieldBasedEvaluator instance
        """
        loader = FieldConfigLoader()
        field_strategies = loader.load_from_excel(config_file_path)
        return cls(field_strategies)

    def evaluate_sample(
        self,
        field_name: str,
        model_output: any,
        golden_answer: any,
        category: str = "",
        file_name: str = "",
        task_type: TaskType = TaskType.ENTITY_EXTRACTION,
        ops_evaluation: Optional[bool] = None,
        dc_evaluation: Optional[bool] = None,
        prompt_id: Optional[str] = None,
        input_text: Optional[str] = None,
        base_field: Optional[str] = None
    ) -> FieldEvaluationResult:
        """
        Evaluate a single field comparison

        Args:
            field_name: Name of the field being evaluated
            model_output: Model's output value
            golden_answer: Ground truth value
            category: Category/group for this sample
            file_name: File identifier
            task_type: Type of task
            ops_evaluation: Manual Ops evaluation (Pass=True, Fail=False)
            dc_evaluation: Manual DC evaluation (Pass=True, Fail=False)
            prompt_id: Prompt identifier
            input_text: Input text used
            base_field: Base field in hierarchy

        Returns:
            FieldEvaluationResult object
        """
        # Get strategy for this field
        strategy = self.field_strategies.get(field_name)

        if strategy is None:
            # No strategy configured for this field
            return FieldEvaluationResult(
                category=category,
                file_name=file_name,
                task_type=task_type,
                field_name=field_name,
                base_field=base_field,
                model_output=model_output,
                golden_answer=golden_answer,
                match_result=None,
                similarity_score=None,
                strategy_used=None,
                ops_evaluation=ops_evaluation,
                dc_evaluation=dc_evaluation,
                evaluation_agreement=(ops_evaluation == dc_evaluation) if (ops_evaluation is not None and dc_evaluation is not None) else None,
                prompt_id=prompt_id,
                input_text=input_text
            )

        # Apply strategy
        match_result = strategy.compare(model_output, golden_answer)
        similarity_score = strategy.similarity_score(model_output, golden_answer)

        return FieldEvaluationResult(
            category=category,
            file_name=file_name,
            task_type=task_type,
            field_name=field_name,
            base_field=base_field,
            model_output=model_output,
            golden_answer=golden_answer,
            match_result=match_result.value if match_result else None,
            similarity_score=similarity_score,
            strategy_used=strategy.__class__.__name__,
            ops_evaluation=ops_evaluation,
            dc_evaluation=dc_evaluation,
            evaluation_agreement=(ops_evaluation == dc_evaluation) if (ops_evaluation is not None and dc_evaluation is not None) else None,
            prompt_id=prompt_id,
            input_text=input_text
        )

    def evaluate_dataset(
        self,
        df: pd.DataFrame,
        field_name_col: str = 'field name',
        model_output_col: str = 'model output',
        golden_answer_col: str = 'golden answer',
        category_col: str = 'category',
        file_name_col: str = 'file name or unique identifier',
        task_type_col: str = 'task categorization',
        ops_eval_col: str = 'ops evaluation (accuracy)',
        dc_eval_col: str = 'DC evaluation (accuracy)',
        base_field_col: str = 'base field',
        prompt_id_col: str = 'prompt or prompt id',
        input_text_col: str = 'input text'
    ) -> List[FieldEvaluationResult]:
        """
        Evaluate entire dataset

        Args:
            df: DataFrame with evaluation data
            field_name_col: Column name for field names
            model_output_col: Column name for model outputs
            golden_answer_col: Column name for golden answers
            category_col: Column name for categories
            file_name_col: Column name for file identifiers
            task_type_col: Column name for task types
            ops_eval_col: Column name for Ops evaluations
            dc_eval_col: Column name for DC evaluations
            base_field_col: Column name for base field
            prompt_id_col: Column name for prompt ID
            input_text_col: Column name for input text

        Returns:
            List of FieldEvaluationResult objects
        """
        results = []

        for _, row in df.iterrows():
            # Parse task type
            task_type_str = str(row.get(task_type_col, '')).strip()
            if 'Classification' in task_type_str and 'Extraction' in task_type_str:
                task_type = TaskType.CLASSIFICATION_AND_EXTRACTION
            elif 'Classification' in task_type_str:
                task_type = TaskType.CLASSIFICATION
            elif 'Entity Extraction' in task_type_str:
                task_type = TaskType.ENTITY_EXTRACTION
            else:
                task_type = TaskType.ENTITY_EXTRACTION  # Default

            # Parse evaluations (Pass/Fail -> True/False)
            ops_eval_str = str(row.get(ops_eval_col, '')).strip().lower()
            ops_evaluation = True if ops_eval_str == 'pass' else (False if ops_eval_str == 'fail' else None)

            dc_eval_str = str(row.get(dc_eval_col, '')).strip().lower()
            dc_evaluation = True if dc_eval_str == 'pass' else (False if dc_eval_str == 'fail' else None)

            result = self.evaluate_sample(
                field_name=str(row.get(field_name_col, '')).strip(),
                model_output=row.get(model_output_col),
                golden_answer=row.get(golden_answer_col),
                category=str(row.get(category_col, '')),
                file_name=str(row.get(file_name_col, '')),
                task_type=task_type,
                ops_evaluation=ops_evaluation,
                dc_evaluation=dc_evaluation,
                prompt_id=str(row.get(prompt_id_col, '')) if prompt_id_col in row else None,
                input_text=str(row.get(input_text_col, '')) if input_text_col in row else None,
                base_field=str(row.get(base_field_col, '')) if base_field_col in row else None
            )

            results.append(result)

        return results

    def calculate_accuracy(
        self,
        results: List[FieldEvaluationResult],
        team: EvaluationTeam = EvaluationTeam.OPS
    ) -> AccuracyMetrics:
        """
        Calculate accuracy metrics from evaluation results

        Args:
            results: List of evaluation results
            team: Which team's evaluation to use (OPS or DC)

        Returns:
            AccuracyMetrics object
        """
        metrics = AccuracyMetrics()

        for result in results:
            # Determine if this result is correct based on team evaluation
            if team == EvaluationTeam.OPS:
                is_correct = result.ops_evaluation
            else:
                is_correct = result.dc_evaluation

            # Skip if no evaluation available
            if is_correct is None:
                continue

            metrics.total_samples += 1
            if is_correct:
                metrics.correct_samples += 1

        metrics.calculate()
        return metrics

    def calculate_accuracy_by_category(
        self,
        results: List[FieldEvaluationResult],
        team: EvaluationTeam = EvaluationTeam.OPS
    ) -> Dict[str, AccuracyMetrics]:
        """
        Calculate accuracy metrics per category

        Args:
            results: List of evaluation results
            team: Which team's evaluation to use

        Returns:
            Dictionary mapping category -> AccuracyMetrics
        """
        category_results = defaultdict(list)

        for result in results:
            category_results[result.category].append(result)

        category_metrics = {}
        for category, cat_results in category_results.items():
            category_metrics[category] = self.calculate_accuracy(cat_results, team)

        return category_metrics

    def calculate_classification_metrics(
        self,
        results: List[FieldEvaluationResult],
        team: EvaluationTeam = EvaluationTeam.OPS,
        beta: float = 1.0
    ) -> Dict[str, ClassificationMetrics]:
        """
        Calculate classification metrics (precision, recall, F-scores) per class

        Args:
            results: List of evaluation results
            team: Which team's evaluation to use
            beta: Beta value for F-beta score

        Returns:
            Dictionary mapping class_name -> ClassificationMetrics
        """
        # Filter only classification tasks
        classification_results = [
            r for r in results
            if r.task_type in [TaskType.CLASSIFICATION, TaskType.CLASSIFICATION_AND_EXTRACTION]
        ]

        # Collect all unique class names from golden answers
        class_names = set()
        for result in classification_results:
            if result.golden_answer is not None:
                class_names.add(str(result.golden_answer))

        # Initialize metrics for each class
        metrics_dict = {}
        for class_name in class_names:
            metrics_dict[class_name] = ClassificationMetrics(class_name=class_name)

        # Calculate TP, FP, FN, TN for each class
        for class_name in class_names:
            for result in classification_results:
                predicted = str(result.model_output) if result.model_output is not None else None
                actual = str(result.golden_answer) if result.golden_answer is not None else None

                # Determine if evaluation passed
                if team == EvaluationTeam.OPS:
                    evaluation_passed = result.ops_evaluation
                else:
                    evaluation_passed = result.dc_evaluation

                # Skip if no evaluation
                if evaluation_passed is None or actual is None or predicted is None:
                    continue

                # Binary classification for this class (one-vs-rest)
                actual_is_class = (actual == class_name)
                predicted_is_class = (predicted == class_name)

                if actual_is_class and predicted_is_class:
                    metrics_dict[class_name].true_positives += 1
                elif not actual_is_class and predicted_is_class:
                    metrics_dict[class_name].false_positives += 1
                elif actual_is_class and not predicted_is_class:
                    metrics_dict[class_name].false_negatives += 1
                else:  # not actual_is_class and not predicted_is_class
                    metrics_dict[class_name].true_negatives += 1

        # Calculate metrics for each class
        for metrics in metrics_dict.values():
            metrics.calculate(beta=beta)

        return metrics_dict

    def calculate_classification_metrics_by_category(
        self,
        results: List[FieldEvaluationResult],
        team: EvaluationTeam = EvaluationTeam.OPS,
        beta: float = 1.0
    ) -> Dict[str, Dict[str, ClassificationMetrics]]:
        """
        Calculate classification metrics per category

        Args:
            results: List of evaluation results
            team: Which team's evaluation to use
            beta: Beta value for F-beta score

        Returns:
            Dictionary mapping category -> (class_name -> ClassificationMetrics)
        """
        category_results = defaultdict(list)

        for result in results:
            if result.task_type in [TaskType.CLASSIFICATION, TaskType.CLASSIFICATION_AND_EXTRACTION]:
                category_results[result.category].append(result)

        category_metrics = {}
        for category, cat_results in category_results.items():
            category_metrics[category] = self.calculate_classification_metrics(
                cat_results, team, beta
            )

        return category_metrics

    def calculate_agreement_rate(self, results: List[FieldEvaluationResult]) -> float:
        """
        Calculate agreement rate between Ops and DC evaluations

        Args:
            results: List of evaluation results

        Returns:
            Agreement rate (0.0 to 1.0)
        """
        total = 0
        agreements = 0

        for result in results:
            if result.ops_evaluation is not None and result.dc_evaluation is not None:
                total += 1
                if result.ops_evaluation == result.dc_evaluation:
                    agreements += 1

        return agreements / total if total > 0 else 0.0
