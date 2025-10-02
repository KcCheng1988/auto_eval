"""CLI tool for Excel analysis"""

import argparse
import sys
from pathlib import Path
import logging

from src.analysers.excel_analyser import ExcelAnalyser
from src.utils.logger import setup_logger


def main():
    """Main function for Excel analysis CLI"""
    parser = argparse.ArgumentParser(
        description="Excel Analyser - Comprehensive Excel file analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick summary
  python analyse_excel.py file.xlsx --quick

  # Full comprehensive analysis
  python analyse_excel.py file.xlsx

  # Specific analysis types
  python analyse_excel.py file.xlsx --structure
  python analyse_excel.py file.xlsx --quality
  python analyse_excel.py file.xlsx --statistics
  python analyse_excel.py file.xlsx --tabular

  # Analyze specific sheet
  python analyse_excel.py file.xlsx --sheet "Sheet1" --quality

  # Save report to file
  python analyse_excel.py file.xlsx --output report.txt
  python analyse_excel.py file.xlsx --output report.json --format json
        """
    )

    parser.add_argument(
        "excel_path",
        type=str,
        help="Path to the Excel file to analyze"
    )

    parser.add_argument(
        "--sheet",
        type=str,
        default=None,
        help="Specific sheet name to analyze (default: all sheets)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save analysis report"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )

    # Analysis type flags
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick summary only"
    )

    parser.add_argument(
        "--structure",
        action="store_true",
        help="Run only structure analysis"
    )

    parser.add_argument(
        "--quality",
        action="store_true",
        help="Run only data quality analysis"
    )

    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Run only statistical analysis"
    )

    parser.add_argument(
        "--tabular",
        action="store_true",
        help="Run only tabular structure detection"
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

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(name="excel_analyser", log_level=log_level)

    # Initialize analyser
    analyser = ExcelAnalyser()

    try:
        # Determine analysis type
        if args.quick:
            # Quick summary
            result = analyser.get_quick_summary(args.excel_path)
            print(result)

        elif args.structure:
            # Structure only
            structure = analyser.structure_analyser
            result = structure.get_sheet_summary(args.excel_path)
            print(result)

        elif args.quality:
            # Quality only
            quality = analyser.quality_analyser
            result = quality.get_quality_summary(args.excel_path, args.sheet)
            print(result)

        elif args.statistics:
            # Statistics only
            stats = analyser.stats_analyser
            result = stats.get_statistics_summary(args.excel_path, args.sheet)
            print(result)

        elif args.tabular:
            # Tabular detection only
            tabular = analyser.tabular_detector
            result = tabular.get_detection_summary(args.excel_path, args.sheet)
            print(result)

        else:
            # Comprehensive analysis
            if args.output:
                analyser.save_report(
                    args.excel_path,
                    args.output,
                    args.sheet,
                    args.format
                )
            else:
                result = analyser.analyse_all(
                    args.excel_path,
                    args.sheet,
                    output_format=args.format
                )
                print(result)

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
