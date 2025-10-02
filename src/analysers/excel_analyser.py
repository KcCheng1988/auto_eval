"""Main Excel analyser orchestrator"""

from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import json

from .structure_analyser import StructureAnalyser
from .data_quality_analyser import DataQualityAnalyser
from .statistical_analyser import StatisticalAnalyser
from .tabular_detector import TabularDetector

logger = logging.getLogger(__name__)


class ExcelAnalyser:
    """Main orchestrator for comprehensive Excel analysis"""

    def __init__(self):
        self.structure_analyser = StructureAnalyser()
        self.quality_analyser = DataQualityAnalyser()
        self.stats_analyser = StatisticalAnalyser()
        self.tabular_detector = TabularDetector()

    def analyse_all(
        self,
        excel_path: str,
        sheet_name: Optional[str] = None,
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on Excel file

        Args:
            excel_path: Path to Excel file
            sheet_name: Optional specific sheet to analyze
            output_format: Output format ('text', 'json', 'dict')

        Returns:
            Analysis results in specified format
        """
        logger.info(f"Starting comprehensive analysis of: {excel_path}")

        results = {
            "file_path": excel_path,
            "analysis_type": "comprehensive",
            "structure_analysis": None,
            "quality_analysis": None,
            "statistical_analysis": None,
            "tabular_detection": None
        }

        try:
            # 1. Structure Analysis
            logger.info("Running structure analysis...")
            results["structure_analysis"] = self.structure_analyser.analyse(excel_path)

            # 2. Data Quality Analysis
            logger.info("Running data quality analysis...")
            results["quality_analysis"] = self.quality_analyser.analyse(excel_path, sheet_name)

            # 3. Statistical Analysis
            logger.info("Running statistical analysis...")
            results["statistical_analysis"] = self.stats_analyser.analyse(excel_path, sheet_name)

            # 4. Tabular Structure Detection
            logger.info("Running tabular structure detection...")
            results["tabular_detection"] = self.tabular_detector.analyse(excel_path, sheet_name)

            logger.info("Comprehensive analysis complete")

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            results["error"] = str(e)

        # Format output
        if output_format == "text":
            return self._format_text_output(results)
        elif output_format == "json":
            return json.dumps(results, indent=2)
        else:  # dict
            return results

    def analyse_structure(self, excel_path: str) -> Dict[str, Any]:
        """Run only structure analysis"""
        logger.info(f"Running structure analysis on: {excel_path}")
        return self.structure_analyser.analyse(excel_path)

    def analyse_quality(self, excel_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Run only data quality analysis"""
        logger.info(f"Running quality analysis on: {excel_path}")
        return self.quality_analyser.analyse(excel_path, sheet_name)

    def analyse_statistics(self, excel_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Run only statistical analysis"""
        logger.info(f"Running statistical analysis on: {excel_path}")
        return self.stats_analyser.analyse(excel_path, sheet_name)

    def detect_tabular(self, excel_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Run only tabular structure detection"""
        logger.info(f"Running tabular detection on: {excel_path}")
        return self.tabular_detector.analyse(excel_path, sheet_name)

    def _format_text_output(self, results: Dict[str, Any]) -> str:
        """Format comprehensive results as text"""
        output = []
        output.append("=" * 80)
        output.append("COMPREHENSIVE EXCEL ANALYSIS REPORT")
        output.append("=" * 80)
        output.append(f"\nFile: {results['file_path']}\n")

        # Structure Analysis
        if results["structure_analysis"]:
            output.append("\n" + "█" * 80)
            output.append("SECTION 1: STRUCTURE ANALYSIS")
            output.append("█" * 80)
            output.append(self.structure_analyser.get_sheet_summary(results['file_path']))

        # Data Quality Analysis
        if results["quality_analysis"]:
            output.append("\n" + "█" * 80)
            output.append("SECTION 2: DATA QUALITY ANALYSIS")
            output.append("█" * 80)
            output.append(self.quality_analyser.get_quality_summary(results['file_path']))

        # Statistical Analysis
        if results["statistical_analysis"]:
            output.append("\n" + "█" * 80)
            output.append("SECTION 3: STATISTICAL ANALYSIS")
            output.append("█" * 80)
            output.append(self.stats_analyser.get_statistics_summary(results['file_path']))

        # Tabular Detection
        if results["tabular_detection"]:
            output.append("\n" + "█" * 80)
            output.append("SECTION 4: TABULAR STRUCTURE DETECTION")
            output.append("█" * 80)
            output.append(self.tabular_detector.get_detection_summary(results['file_path']))

        output.append("\n" + "=" * 80)
        output.append("END OF REPORT")
        output.append("=" * 80)

        return "\n".join(output)

    def save_report(
        self,
        excel_path: str,
        output_path: str,
        sheet_name: Optional[str] = None,
        format: str = "text"
    ):
        """
        Run analysis and save report to file

        Args:
            excel_path: Path to Excel file to analyze
            output_path: Path to save report
            sheet_name: Optional specific sheet
            format: Output format ('text' or 'json')
        """
        logger.info(f"Generating analysis report for: {excel_path}")

        # Run analysis
        results = self.analyse_all(excel_path, sheet_name, output_format=format)

        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            if isinstance(results, str):
                f.write(results)
            else:
                f.write(json.dumps(results, indent=2))

        logger.info(f"Report saved to: {output_path}")
        print(f"✓ Analysis report saved to: {output_path}")

    def get_quick_summary(self, excel_path: str) -> str:
        """
        Get a quick summary of the Excel file

        Args:
            excel_path: Path to Excel file

        Returns:
            Quick summary text
        """
        structure = self.structure_analyser.analyse(excel_path)
        quality = self.quality_analyser.analyse(excel_path)
        tabular = self.tabular_detector.analyse(excel_path)

        summary = []
        summary.append("=" * 60)
        summary.append("QUICK EXCEL SUMMARY")
        summary.append("=" * 60)
        summary.append(f"\nFile: {excel_path}")
        summary.append(f"\n📊 STRUCTURE:")
        summary.append(f"  • Total Sheets: {structure['total_sheets']}")
        summary.append(f"  • Active: {len(structure['active_sheets'])}, Hidden: {len(structure['hidden_sheets'])}")
        summary.append(f"  • Images: {structure['images_summary']['total_images']}")
        summary.append(f"  • Charts: {structure['charts_summary']['total_charts']}")

        summary.append(f"\n✅ QUALITY:")
        summary.append(f"  • Overall Score: {quality['overall_quality_score']:.1f}/100")
        summary.append(f"  • Issues: {quality['issues_summary']['total_issues']} (Critical: {quality['issues_summary']['critical_issues']})")

        summary.append(f"\n📋 TABULAR STRUCTURE:")
        summary.append(f"  • Tabular Sheets: {tabular['summary']['tabular_count']}/{tabular['summary']['total_sheets']}")
        if tabular['tabular_sheets']:
            summary.append(f"  • Tabular: {', '.join(tabular['tabular_sheets'])}")
        if tabular['non_tabular_sheets']:
            summary.append(f"  • Non-Tabular: {', '.join(tabular['non_tabular_sheets'])}")

        summary.append("\n" + "=" * 60)

        return "\n".join(summary)
