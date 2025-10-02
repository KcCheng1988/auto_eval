"""Main pipeline orchestrator for auto-evaluation tool"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from .utils.config_loader import ConfigLoader
from .utils.logger import setup_logger
from .validators.template_validator import TemplateValidator
from .evaluators.evaluation_orchestrator import EvaluationOrchestrator
from .reporters.report_generator import ReportGenerator


class AutoEvaluationPipeline:
    """Main orchestrator for the auto-evaluation pipeline"""

    def __init__(
        self,
        config_dir: str = "config",
        log_level: int = logging.INFO
    ):
        """
        Initialize the auto-evaluation pipeline

        Args:
            config_dir: Directory containing configuration files
            log_level: Logging level
        """
        # Setup logging
        self.logger = setup_logger(log_level=log_level)
        self.logger.info("Initializing Auto-Evaluation Pipeline")

        # Load configurations
        self.config_loader = ConfigLoader(config_dir)
        self.template_config = self.config_loader.load_template_config()
        self.evaluation_config = self.config_loader.load_evaluation_config()
        self.report_config = self.config_loader.load_report_config()

        # Initialize components
        self.validator = None
        self.evaluator = None
        self.reporter = None

    def run(
        self,
        excel_path: str,
        output_dir: str = "output",
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete auto-evaluation pipeline

        Args:
            excel_path: Path to Excel file to evaluate
            output_dir: Directory for output files
            generate_report: Whether to generate email report

        Returns:
            Dictionary with pipeline results
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting Auto-Evaluation Pipeline")
        self.logger.info(f"Excel file: {excel_path}")
        self.logger.info("=" * 80)

        results = {
            "excel_path": excel_path,
            "timestamp": datetime.now().isoformat(),
            "validation": None,
            "evaluation": None,
            "report_path": None,
            "overall_status": "pending"
        }

        try:
            # Task 1: Template Validation
            self.logger.info("\n>>> TASK 1: Template Validation")
            validation_result = self._run_validation(excel_path)
            results["validation"] = validation_result.get_summary()

            if not validation_result.is_valid:
                self.logger.error("Template validation failed. Cannot proceed with evaluation.")
                results["overall_status"] = "validation_failed"

                # Still generate report to show validation errors
                if generate_report:
                    self._generate_failure_report(
                        validation_result, output_dir, excel_path
                    )

                return results

            self.logger.info("✓ Template validation passed")

            # Extract data for evaluation
            extracted_data = self.validator.get_extracted_data(excel_path)
            results["extracted_data"] = extracted_data

            # Task 2: Model Evaluation
            self.logger.info("\n>>> TASK 2: Model Evaluation")
            evaluation_result = self._run_evaluation(extracted_data, excel_path)
            results["evaluation"] = evaluation_result.get_summary()

            # Task 3: Report Generation
            if generate_report:
                self.logger.info("\n>>> TASK 3: Report Generation")
                report_path = self._generate_report(
                    validation_result,
                    evaluation_result,
                    extracted_data,
                    output_dir,
                    excel_path
                )
                results["report_path"] = report_path

            # Determine overall status
            if evaluation_result.passed:
                results["overall_status"] = "success"
                self.logger.info("\n✓ All evaluations passed!")
            else:
                results["overall_status"] = "evaluation_failed"
                self.logger.warning("\n⚠ Evaluation metrics below threshold")

            self.logger.info("=" * 80)
            self.logger.info("Pipeline completed")
            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
            results["overall_status"] = "error"
            results["error"] = str(e)

        return results

    def _run_validation(self, excel_path: str):
        """Run template validation (Task 1)"""
        self.validator = TemplateValidator(self.template_config)
        validation_result = self.validator.validate_template(excel_path)

        # Log validation summary
        summary = validation_result.get_summary()
        self.logger.info(f"Validation errors: {summary['error_count']}")
        self.logger.info(f"Validation warnings: {summary['warning_count']}")

        if summary['errors']:
            self.logger.error("Validation errors found:")
            for error in summary['errors']:
                self.logger.error(f"  - {error}")

        if summary['warnings']:
            self.logger.warning("Validation warnings found:")
            for warning in summary['warnings']:
                self.logger.warning(f"  - {warning}")

        return validation_result

    def _run_evaluation(self, extracted_data: Dict[str, Dict[str, Any]], excel_path: str):
        """Run model evaluation (Task 2)"""
        self.evaluator = EvaluationOrchestrator(self.evaluation_config)
        evaluation_result = self.evaluator.run_evaluation(extracted_data, excel_path)

        # Log evaluation summary
        summary = evaluation_result.get_summary()
        self.logger.info(f"Evaluation passed: {summary['passed']}")

        if summary['metrics']:
            self.logger.info("Evaluation metrics:")
            for metric, value in summary['metrics'].items():
                self.logger.info(f"  - {metric}: {value}")

        if summary['threshold_checks']:
            self.logger.info("Threshold checks:")
            for metric, check in summary['threshold_checks'].items():
                status = "PASS" if check['passed'] else "FAIL"
                self.logger.info(
                    f"  - {metric}: {check['actual']} vs {check['threshold']} [{status}]"
                )

        return evaluation_result

    def _generate_report(
        self,
        validation_result,
        evaluation_result,
        extracted_data: Dict[str, Dict[str, Any]],
        output_dir: str,
        excel_path: str
    ) -> str:
        """Generate evaluation report (Task 3)"""
        self.reporter = ReportGenerator(self.report_config)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate timestamped report filename
        excel_name = Path(excel_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"evaluation_report_{excel_name}_{timestamp}.html"
        report_path = output_path / report_filename

        # Generate HTML report
        html_report = self.reporter.generate_email_report(
            validation_result,
            evaluation_result,
            extracted_data,
            output_path=str(report_path)
        )

        self.logger.info(f"Report generated: {report_path}")

        # Also generate text summary for console
        text_summary = self.reporter.generate_summary_text(
            validation_result,
            evaluation_result
        )
        self.logger.info(f"\n{text_summary}")

        return str(report_path)

    def _generate_failure_report(
        self,
        validation_result,
        output_dir: str,
        excel_path: str
    ):
        """Generate report for validation failures"""
        from .evaluators.evaluation_orchestrator import EvaluationResult

        # Create empty evaluation result
        empty_eval = EvaluationResult()

        self.reporter = ReportGenerator(self.report_config)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        excel_name = Path(excel_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"validation_failure_{excel_name}_{timestamp}.html"
        report_path = output_path / report_filename

        self.reporter.generate_email_report(
            validation_result,
            empty_eval,
            {},
            output_path=str(report_path)
        )

        self.logger.info(f"Validation failure report generated: {report_path}")

    def run_validation_only(self, excel_path: str) -> Dict[str, Any]:
        """
        Run only template validation (Task 1)

        Args:
            excel_path: Path to Excel file

        Returns:
            Validation results
        """
        self.logger.info("Running validation only")
        validation_result = self._run_validation(excel_path)
        return validation_result.get_summary()

    def run_evaluation_only(
        self,
        excel_path: str,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Run only model evaluation (Task 2)

        Args:
            excel_path: Path to Excel file
            skip_validation: Skip validation and extract data directly

        Returns:
            Evaluation results
        """
        self.logger.info("Running evaluation only")

        if not skip_validation:
            validation_result = self._run_validation(excel_path)
            if not validation_result.is_valid:
                raise ValueError("Template validation failed. Cannot run evaluation.")

        # Extract data
        self.validator = TemplateValidator(self.template_config)
        extracted_data = self.validator.get_extracted_data(excel_path)

        # Run evaluation
        evaluation_result = self._run_evaluation(extracted_data, excel_path)
        return evaluation_result.get_summary()

    def reload_configs(self):
        """Reload all configurations"""
        self.logger.info("Reloading configurations")
        self.config_loader.reload_configs()
        self.template_config = self.config_loader.load_template_config()
        self.evaluation_config = self.config_loader.load_evaluation_config()
        self.report_config = self.config_loader.load_report_config()
        self.logger.info("Configurations reloaded successfully")
