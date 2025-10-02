"""Main entry point for the auto-evaluation tool"""

import argparse
import sys
from pathlib import Path
from src.pipeline import AutoEvaluationPipeline


def main():
    """Main function to run the auto-evaluation tool"""
    parser = argparse.ArgumentParser(
        description="Auto-Evaluation Tool for GenAI Use Cases"
    )

    parser.add_argument(
        "excel_path",
        type=str,
        help="Path to the Excel template file to evaluate"
    )

    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="Directory containing configuration files (default: config)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory for output files (default: output)"
    )

    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Run only template validation (Task 1)"
    )

    parser.add_argument(
        "--evaluation-only",
        action="store_true",
        help="Run only model evaluation (Task 2)"
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Check if Excel file exists
    excel_path = Path(args.excel_path)
    if not excel_path.exists():
        print(f"Error: Excel file not found: {args.excel_path}")
        sys.exit(1)

    # Set log level
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO

    # Initialize pipeline
    pipeline = AutoEvaluationPipeline(
        config_dir=args.config_dir,
        log_level=log_level
    )

    try:
        # Run appropriate mode
        if args.validation_only:
            results = pipeline.run_validation_only(args.excel_path)
            print("\n=== Validation Results ===")
            print(f"Valid: {results['is_valid']}")
            print(f"Errors: {results['error_count']}")
            print(f"Warnings: {results['warning_count']}")

        elif args.evaluation_only:
            results = pipeline.run_evaluation_only(args.excel_path)
            print("\n=== Evaluation Results ===")
            print(f"Passed: {results['passed']}")
            for metric, value in results.get('metrics', {}).items():
                print(f"{metric}: {value}")

        else:
            # Run full pipeline
            results = pipeline.run(
                excel_path=args.excel_path,
                output_dir=args.output_dir,
                generate_report=not args.no_report
            )

            print("\n=== Pipeline Results ===")
            print(f"Overall Status: {results['overall_status']}")

            if results.get('report_path'):
                print(f"Report: {results['report_path']}")

        # Exit code based on results
        if isinstance(results, dict):
            if results.get('overall_status') == 'success' or results.get('is_valid'):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
