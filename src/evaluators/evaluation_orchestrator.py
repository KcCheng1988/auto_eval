"""Evaluation orchestrator for Task 2"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from .inhouse_evaluator import InHouseEvaluator

logger = logging.getLogger(__name__)


class EvaluationResult:
    """Stores evaluation results and metrics"""

    def __init__(self):
        self.metrics = {}
        self.miit_results = {}
        self.threshold_checks = {}
        self.passed = True

    def add_metrics(self, metric_dict: Dict[str, float]):
        """Add evaluation metrics"""
        self.metrics.update(metric_dict)

    def add_miit_results(self, miit_dict: Dict[str, Any]):
        """Add MIIT evaluation results"""
        self.miit_results.update(miit_dict)

    def check_thresholds(self, thresholds: Dict[str, float]):
        """
        Check if metrics meet thresholds

        Args:
            thresholds: Dictionary of metric_name: threshold_value
        """
        for metric_name, threshold in thresholds.items():
            if metric_name in self.metrics:
                actual_value = self.metrics[metric_name]
                passed = actual_value >= threshold

                self.threshold_checks[metric_name] = {
                    "threshold": threshold,
                    "actual": actual_value,
                    "passed": passed
                }

                if not passed:
                    self.passed = False
                    logger.warning(
                        f"Metric '{metric_name}' failed: {actual_value} < {threshold}"
                    )
            else:
                logger.warning(f"Threshold defined for '{metric_name}' but metric not found")

    def get_summary(self) -> Dict[str, Any]:
        """Get evaluation summary"""
        return {
            "passed": self.passed,
            "metrics": self.metrics,
            "miit_results": self.miit_results,
            "threshold_checks": self.threshold_checks
        }


class EvaluationOrchestrator:
    """Orchestrates evaluation process for different use case types"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize evaluation orchestrator

        Args:
            config: Evaluation configuration from config_loader
        """
        self.config = config
        self.evaluator = InHouseEvaluator()
        self.result = EvaluationResult()

    def run_evaluation(
        self,
        extracted_data: Dict[str, Dict[str, Any]],
        excel_path: str
    ) -> EvaluationResult:
        """
        Main evaluation method

        Args:
            extracted_data: Data extracted from validated template
            excel_path: Path to Excel file for reading datasets

        Returns:
            EvaluationResult object with all metrics and checks
        """
        logger.info("Starting evaluation process")
        self.result = EvaluationResult()

        try:
            # Determine use case type from extracted data
            use_case_type = self._determine_use_case_type(extracted_data)
            logger.info(f"Detected use case type: {use_case_type}")

            # Load evaluation dataset
            eval_dataset = self._load_evaluation_dataset(excel_path)

            # Run appropriate evaluation based on use case type
            if use_case_type in ["classification", "entity_extraction"]:
                metrics = self._evaluate_simple_task(eval_dataset, use_case_type)
                self.result.add_metrics(metrics)
            else:
                # Complex tasks: summarization, QA, rewriting
                metrics = self._evaluate_complex_task(eval_dataset)
                self.result.add_metrics(metrics)

            # Evaluate MIIT dataset
            miit_results = self._evaluate_miit_dataset(excel_path)
            self.result.add_miit_results(miit_results)

            # Check thresholds
            use_case_stage = extracted_data.get("use_case_info", {}).get(
                "Stage", "human_in_loop"
            )
            thresholds = self._get_thresholds(use_case_stage)
            self.result.check_thresholds(thresholds)

            logger.info(f"Evaluation completed. Passed: {self.result.passed}")

        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            raise

        return self.result

    def _determine_use_case_type(self, extracted_data: Dict[str, Dict[str, Any]]) -> str:
        """
        Determine the use case type from extracted data

        Args:
            extracted_data: Extracted template data

        Returns:
            Use case type string
        """
        # Try to get use case type from model information
        model_info = extracted_data.get("model_info", {})
        use_case_info = extracted_data.get("use_case_info", {})

        # Look for use case type in common field names
        for field in ["Use Case Type", "Task Type", "Model Task", "Type"]:
            if field in use_case_info:
                return use_case_info[field].lower()
            if field in model_info:
                return model_info[field].lower()

        # Default to complex task
        logger.warning("Could not determine use case type, defaulting to 'complex'")
        return "complex"

    def _load_evaluation_dataset(self, excel_path: str) -> pd.DataFrame:
        """
        Load evaluation dataset from Excel

        Args:
            excel_path: Path to Excel file

        Returns:
            DataFrame with evaluation data
        """
        # Try common sheet names for evaluation data
        possible_sheet_names = [
            "Evaluation Samples",
            "Model Evaluation Samples",
            "Evaluation Dataset",
            "Test Data"
        ]

        for sheet_name in possible_sheet_names:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                logger.info(f"Loaded evaluation dataset from sheet: {sheet_name}")
                return df
            except Exception:
                continue

        # If no match, try first sheet
        logger.warning("Could not find evaluation sheet, using first sheet")
        return pd.read_excel(excel_path, sheet_name=0)

    def _evaluate_simple_task(
        self, dataset: pd.DataFrame, task_type: str
    ) -> Dict[str, float]:
        """
        Evaluate simple tasks (classification, entity extraction)

        Args:
            dataset: Evaluation dataset
            task_type: Type of task

        Returns:
            Dictionary of metrics
        """
        logger.info(f"Evaluating simple task: {task_type}")

        # Extract predictions and ground truth
        # Common column names
        pred_columns = ["Prediction", "Model Output", "Predicted", "Output"]
        truth_columns = ["Ground Truth", "Label", "True Label", "Expected"]

        pred_col = None
        truth_col = None

        for col in pred_columns:
            if col in dataset.columns:
                pred_col = col
                break

        for col in truth_columns:
            if col in dataset.columns:
                truth_col = col
                break

        if pred_col is None or truth_col is None:
            raise ValueError(
                f"Could not find prediction and ground truth columns. "
                f"Available columns: {list(dataset.columns)}"
            )

        predictions = dataset[pred_col].tolist()
        ground_truth = dataset[truth_col].tolist()

        # Call in-house evaluator
        if task_type == "classification":
            return self.evaluator.evaluate_classification(predictions, ground_truth)
        elif task_type == "entity_extraction":
            return self.evaluator.evaluate_entity_extraction(predictions, ground_truth)
        else:
            return self.evaluator.evaluate_classification(predictions, ground_truth)

    def _evaluate_complex_task(self, dataset: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate complex tasks using human annotations

        Args:
            dataset: Evaluation dataset with human annotations

        Returns:
            Dictionary of metrics
        """
        logger.info("Evaluating complex task with human annotations")

        # Extract required columns
        pred_col = self._find_column(dataset, ["Prediction", "Model Output", "Output"])
        ref_col = self._find_column(dataset, ["Reference", "Ground Truth", "Expected"])

        predictions = dataset[pred_col].tolist()
        references = dataset[ref_col].tolist()

        # Pass entire dataset as annotations (contains human judgment columns)
        return self.evaluator.evaluate_with_human_annotation(
            predictions, references, dataset
        )

    def _evaluate_miit_dataset(self, excel_path: str) -> Dict[str, Any]:
        """
        Evaluate MIIT dataset (sandbox vs UAT consistency)

        Args:
            excel_path: Path to Excel file

        Returns:
            Dictionary with MIIT evaluation results
        """
        logger.info("Evaluating MIIT dataset")

        try:
            # Try to find MIIT sheet
            miit_df = None
            for sheet_name in ["MIIT", "MIIT Dataset", "MIIT Evaluation"]:
                try:
                    miit_df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    logger.info(f"Loaded MIIT dataset from sheet: {sheet_name}")
                    break
                except Exception:
                    continue

            if miit_df is None:
                logger.warning("MIIT sheet not found, skipping MIIT evaluation")
                return {"status": "not_found"}

            # Extract sandbox and UAT responses
            sandbox_col = self._find_column(
                miit_df, ["Sandbox Response", "Sandbox Output", "Sandbox"]
            )
            uat_col = self._find_column(
                miit_df, ["UAT Response", "UAT Output", "UAT"]
            )
            query_col = self._find_column(
                miit_df, ["Query", "Input", "Question", "Prompt"]
            )

            sandbox_responses = miit_df[sandbox_col].tolist()
            uat_responses = miit_df[uat_col].tolist()
            queries = miit_df[query_col].tolist()

            # Call in-house evaluator
            return self.evaluator.evaluate_miit(
                sandbox_responses, uat_responses, queries
            )

        except Exception as e:
            logger.error(f"Error evaluating MIIT dataset: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> str:
        """
        Find column by trying multiple possible names

        Args:
            df: DataFrame to search
            possible_names: List of possible column names

        Returns:
            Actual column name found

        Raises:
            ValueError if column not found
        """
        for name in possible_names:
            if name in df.columns:
                return name

        raise ValueError(
            f"Could not find column. Tried: {possible_names}. "
            f"Available: {list(df.columns)}"
        )

    def _get_thresholds(self, use_case_stage: str) -> Dict[str, float]:
        """
        Get thresholds based on use case stage

        Args:
            use_case_stage: Stage of the use case (autonomous or human_in_loop)

        Returns:
            Dictionary of metric thresholds
        """
        thresholds_config = self.config.get("thresholds", {})

        # Normalize stage name
        stage = use_case_stage.lower().replace(" ", "_")

        if "autonomous" in stage:
            return thresholds_config.get("autonomous", {})
        else:
            return thresholds_config.get("human_in_loop", {})
