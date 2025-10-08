"""Test field-based evaluator for Entity Extraction and Classification tasks"""

import pytest
import pandas as pd
from src.evaluators.field_based_evaluator import FieldBasedEvaluator
from src.models.evaluation_models import (
    FieldEvaluationResult,
    AccuracyMetrics,
    ClassificationMetrics,
    TaskType,
    EvaluationTeam
)
from src.models.comparison_strategies import (
    ExactNameMatch,
    ExactStringMatch,
    ExactNumericMatch,
    MatchResult
)


class TestFieldBasedEvaluator:
    """Test FieldBasedEvaluator basic functionality"""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator with sample strategies"""
        field_strategies = {
            'customer_name': ExactNameMatch(),
            'contract_amount': ExactNumericMatch(),
            'status': ExactStringMatch()
        }
        return FieldBasedEvaluator(field_strategies)

    def test_evaluate_sample_exact_match(self, evaluator):
        """Test evaluating a single sample with exact match"""
        result = evaluator.evaluate_sample(
            field_name='customer_name',
            model_output='John Smith',
            golden_answer='John Smith',
            category='Age 18-25',
            file_name='sample_001',
            ops_evaluation=True,
            dc_evaluation=True
        )

        assert result.field_name == 'customer_name'
        assert result.model_output == 'John Smith'
        assert result.golden_answer == 'John Smith'
        assert result.match_result == MatchResult.EXACT_MATCH.value
        assert result.strategy_used == 'ExactNameMatch'
        assert result.ops_evaluation is True
        assert result.dc_evaluation is True
        assert result.evaluation_agreement is True

    def test_evaluate_sample_no_match(self, evaluator):
        """Test evaluating a single sample with no match"""
        result = evaluator.evaluate_sample(
            field_name='customer_name',
            model_output='John Smith',
            golden_answer='Jane Doe',
            category='Age 18-25',
            file_name='sample_001',
            ops_evaluation=False,
            dc_evaluation=False
        )

        assert result.match_result == MatchResult.NO_MATCH.value
        assert result.ops_evaluation is False
        assert result.dc_evaluation is False
        assert result.evaluation_agreement is True

    def test_evaluate_sample_disagreement(self, evaluator):
        """Test evaluating sample with Ops/DC disagreement"""
        result = evaluator.evaluate_sample(
            field_name='customer_name',
            model_output='John Smith',
            golden_answer='John Smith Jr.',
            category='Age 18-25',
            file_name='sample_001',
            ops_evaluation=True,
            dc_evaluation=False
        )

        assert result.ops_evaluation is True
        assert result.dc_evaluation is False
        assert result.evaluation_agreement is False

    def test_evaluate_sample_no_strategy(self, evaluator):
        """Test evaluating field without configured strategy"""
        result = evaluator.evaluate_sample(
            field_name='unknown_field',
            model_output='value',
            golden_answer='value',
            category='Age 18-25',
            file_name='sample_001'
        )

        assert result.field_name == 'unknown_field'
        assert result.match_result is None
        assert result.similarity_score is None
        assert result.strategy_used is None


class TestAccuracyCalculation:
    """Test accuracy metric calculations"""

    def test_calculate_accuracy_ops(self):
        """Test calculating accuracy for Ops team"""
        results = [
            FieldEvaluationResult(
                category='Age 18-25', file_name='s1', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=True
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s2', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=False
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s3', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=False, dc_evaluation=False
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s4', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=True
            )
        ]

        evaluator = FieldBasedEvaluator({})
        metrics = evaluator.calculate_accuracy(results, team=EvaluationTeam.OPS)

        assert metrics.total_samples == 4
        assert metrics.correct_samples == 3
        assert metrics.accuracy == 0.75

    def test_calculate_accuracy_dc(self):
        """Test calculating accuracy for DC team"""
        results = [
            FieldEvaluationResult(
                category='Age 18-25', file_name='s1', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=True
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s2', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=False
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s3', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=False, dc_evaluation=False
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s4', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=True
            )
        ]

        evaluator = FieldBasedEvaluator({})
        metrics = evaluator.calculate_accuracy(results, team=EvaluationTeam.DC)

        assert metrics.total_samples == 4
        assert metrics.correct_samples == 2
        assert metrics.accuracy == 0.5

    def test_calculate_accuracy_by_category(self):
        """Test calculating accuracy per category"""
        results = [
            FieldEvaluationResult(
                category='Age 18-25', file_name='s1', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True
            ),
            FieldEvaluationResult(
                category='Age 18-25', file_name='s2', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=False
            ),
            FieldEvaluationResult(
                category='Age 26-40', file_name='s3', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True
            ),
            FieldEvaluationResult(
                category='Age 26-40', file_name='s4', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True
            )
        ]

        evaluator = FieldBasedEvaluator({})
        category_metrics = evaluator.calculate_accuracy_by_category(results, team=EvaluationTeam.OPS)

        assert 'Age 18-25' in category_metrics
        assert 'Age 26-40' in category_metrics

        assert category_metrics['Age 18-25'].accuracy == 0.5
        assert category_metrics['Age 26-40'].accuracy == 1.0


class TestClassificationMetrics:
    """Test classification metric calculations"""

    def test_calculate_classification_metrics(self):
        """Test calculating classification metrics for binary classification"""
        results = [
            # True Positives for 'Positive' class
            FieldEvaluationResult(
                category='test', file_name='s1', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Positive', golden_answer='Positive',
                ops_evaluation=True
            ),
            FieldEvaluationResult(
                category='test', file_name='s2', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Positive', golden_answer='Positive',
                ops_evaluation=True
            ),
            # False Positives for 'Positive' class
            FieldEvaluationResult(
                category='test', file_name='s3', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Positive', golden_answer='Negative',
                ops_evaluation=False
            ),
            # False Negatives for 'Positive' class
            FieldEvaluationResult(
                category='test', file_name='s4', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Negative', golden_answer='Positive',
                ops_evaluation=False
            ),
            # True Negatives for 'Positive' class
            FieldEvaluationResult(
                category='test', file_name='s5', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Negative', golden_answer='Negative',
                ops_evaluation=True
            ),
            FieldEvaluationResult(
                category='test', file_name='s6', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Negative', golden_answer='Negative',
                ops_evaluation=True
            )
        ]

        evaluator = FieldBasedEvaluator({})
        metrics = evaluator.calculate_classification_metrics(results, team=EvaluationTeam.OPS)

        # Check Positive class metrics
        assert 'Positive' in metrics
        pos_metrics = metrics['Positive']
        assert pos_metrics.true_positives == 2
        assert pos_metrics.false_positives == 1
        assert pos_metrics.false_negatives == 1
        assert pos_metrics.true_negatives == 2

        # Precision = TP / (TP + FP) = 2 / 3
        assert abs(pos_metrics.precision - 0.6667) < 0.001

        # Recall = TP / (TP + FN) = 2 / 3
        assert abs(pos_metrics.recall - 0.6667) < 0.001

        # F1 = 2 * (P * R) / (P + R)
        assert abs(pos_metrics.f1_score - 0.6667) < 0.001

    def test_calculate_classification_metrics_by_category(self):
        """Test calculating classification metrics per category"""
        results = [
            FieldEvaluationResult(
                category='Age 18-25', file_name='s1', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Positive', golden_answer='Positive',
                ops_evaluation=True
            ),
            FieldEvaluationResult(
                category='Age 26-40', file_name='s2', task_type=TaskType.CLASSIFICATION,
                field_name='sentiment', model_output='Negative', golden_answer='Negative',
                ops_evaluation=True
            )
        ]

        evaluator = FieldBasedEvaluator({})
        category_metrics = evaluator.calculate_classification_metrics_by_category(
            results, team=EvaluationTeam.OPS
        )

        assert 'Age 18-25' in category_metrics
        assert 'Age 26-40' in category_metrics


class TestAgreementRate:
    """Test agreement rate calculation"""

    def test_calculate_agreement_rate(self):
        """Test calculating agreement rate between Ops and DC"""
        results = [
            FieldEvaluationResult(
                category='test', file_name='s1', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=True
            ),
            FieldEvaluationResult(
                category='test', file_name='s2', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=False
            ),
            FieldEvaluationResult(
                category='test', file_name='s3', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=False, dc_evaluation=False
            ),
            FieldEvaluationResult(
                category='test', file_name='s4', task_type=TaskType.ENTITY_EXTRACTION,
                field_name='name', ops_evaluation=True, dc_evaluation=True
            )
        ]

        evaluator = FieldBasedEvaluator({})
        agreement_rate = evaluator.calculate_agreement_rate(results)

        # 3 out of 4 agree (s1, s3, s4)
        assert agreement_rate == 0.75


class TestDataFrameEvaluation:
    """Test evaluating entire DataFrame"""

    def test_evaluate_dataset(self):
        """Test evaluating DataFrame with multiple samples"""
        data = {
            'category': ['Age 18-25', 'Age 18-25', 'Age 26-40'],
            'task categorization': ['Entity Extraction', 'Entity Extraction', 'Classification'],
            'file name or unique identifier': ['s1', 's2', 's3'],
            'field name': ['customer_name', 'customer_name', 'status'],
            'model output': ['John Smith', 'Jane Doe', 'Active'],
            'golden answer': ['John Smith', 'Jane Smith', 'Active'],
            'ops evaluation (accuracy)': ['Pass', 'Fail', 'Pass'],
            'DC evaluation (accuracy)': ['Pass', 'Pass', 'Pass'],
            'base field': ['name', 'name', 'status']
        }
        df = pd.DataFrame(data)

        field_strategies = {
            'customer_name': ExactNameMatch(),
            'status': ExactStringMatch()
        }
        evaluator = FieldBasedEvaluator(field_strategies)
        results = evaluator.evaluate_dataset(df)

        assert len(results) == 3

        # Check first result
        assert results[0].field_name == 'customer_name'
        assert results[0].model_output == 'John Smith'
        assert results[0].golden_answer == 'John Smith'
        assert results[0].ops_evaluation is True
        assert results[0].dc_evaluation is True
        assert results[0].task_type == TaskType.ENTITY_EXTRACTION

        # Check third result (classification)
        assert results[2].task_type == TaskType.CLASSIFICATION


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
