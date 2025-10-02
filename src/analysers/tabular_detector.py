"""Tabular structure detection for Excel sheets"""

import pandas as pd
import openpyxl
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TabularDetector:
    """Detects if Excel sheets contain tabular structures"""

    def __init__(self):
        self.workbook = None

    def analyse(self, excel_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect tabular structures in Excel sheets

        Args:
            excel_path: Path to Excel file
            sheet_name: Optional specific sheet to analyze (None = all sheets)

        Returns:
            Dictionary containing tabular structure detection results
        """
        logger.info(f"Detecting tabular structures in: {excel_path}")

        self.workbook = openpyxl.load_workbook(excel_path, data_only=False)

        results = {
            "file_path": excel_path,
            "sheets_analyzed": [],
            "tabular_sheets": [],
            "non_tabular_sheets": [],
            "summary": {
                "total_sheets": 0,
                "tabular_count": 0,
                "non_tabular_count": 0
            }
        }

        # Determine which sheets to analyze
        sheets_to_analyze = [sheet_name] if sheet_name else self.workbook.sheetnames

        for sheet in sheets_to_analyze:
            if sheet not in self.workbook.sheetnames:
                logger.warning(f"Sheet '{sheet}' not found, skipping")
                continue

            sheet_analysis = self._detect_tabular_structure(excel_path, sheet)
            results["sheets_analyzed"].append(sheet_analysis)

            if sheet_analysis["is_tabular"]:
                results["tabular_sheets"].append(sheet)
                results["summary"]["tabular_count"] += 1
            else:
                results["non_tabular_sheets"].append(sheet)
                results["summary"]["non_tabular_count"] += 1

            results["summary"]["total_sheets"] += 1

        logger.info(
            f"Tabular detection complete: {results['summary']['tabular_count']} tabular, "
            f"{results['summary']['non_tabular_count']} non-tabular"
        )
        return results

    def _detect_tabular_structure(self, excel_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Detect if a sheet has tabular structure

        Args:
            excel_path: Path to Excel file
            sheet_name: Name of the sheet

        Returns:
            Dictionary with detection results
        """
        try:
            # Read sheet with openpyxl for structure analysis
            sheet = self.workbook[sheet_name]

            # Try reading as DataFrame
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

        except Exception as e:
            logger.error(f"Error analyzing sheet '{sheet_name}': {str(e)}")
            return {
                "sheet_name": sheet_name,
                "error": str(e),
                "is_tabular": False
            }

        analysis = {
            "sheet_name": sheet_name,
            "is_tabular": False,
            "confidence_score": 0.0,
            "indicators": {
                "has_header_row": False,
                "has_consistent_columns": False,
                "has_data_rows": False,
                "minimal_merged_cells": False,
                "rectangular_structure": False
            },
            "structure_info": {},
            "reasons": []
        }

        # Check 1: Has header row (first row with text values)
        header_check = self._check_header_row(df)
        analysis["indicators"]["has_header_row"] = header_check["has_header"]
        if header_check["has_header"]:
            analysis["confidence_score"] += 25
            analysis["structure_info"]["detected_headers"] = header_check["headers"]
        else:
            analysis["reasons"].append("No clear header row detected")

        # Check 2: Consistent column structure
        column_consistency = self._check_column_consistency(df)
        analysis["indicators"]["has_consistent_columns"] = column_consistency["is_consistent"]
        if column_consistency["is_consistent"]:
            analysis["confidence_score"] += 25
        else:
            analysis["reasons"].append(column_consistency["reason"])

        # Check 3: Has data rows (not just headers)
        data_rows_check = self._check_data_rows(df)
        analysis["indicators"]["has_data_rows"] = data_rows_check["has_data"]
        if data_rows_check["has_data"]:
            analysis["confidence_score"] += 20
            analysis["structure_info"]["data_row_count"] = data_rows_check["row_count"]
        else:
            analysis["reasons"].append("No data rows found")

        # Check 4: Minimal merged cells (tables usually don't have many merged cells)
        merged_cells_check = self._check_merged_cells(sheet)
        analysis["indicators"]["minimal_merged_cells"] = merged_cells_check["is_minimal"]
        if merged_cells_check["is_minimal"]:
            analysis["confidence_score"] += 15
        else:
            analysis["reasons"].append(f"Too many merged cells ({merged_cells_check['count']})")

        analysis["structure_info"]["merged_cells_count"] = merged_cells_check["count"]

        # Check 5: Rectangular structure (data fills most of the defined area)
        rectangular_check = self._check_rectangular_structure(df)
        analysis["indicators"]["rectangular_structure"] = rectangular_check["is_rectangular"]
        if rectangular_check["is_rectangular"]:
            analysis["confidence_score"] += 15
        else:
            analysis["reasons"].append(rectangular_check["reason"])

        # Determine if tabular based on confidence score
        if analysis["confidence_score"] >= 60:
            analysis["is_tabular"] = True
        else:
            analysis["is_tabular"] = False

        # Additional structure info
        analysis["structure_info"].update({
            "row_count": len(df),
            "column_count": len(df.columns),
            "fill_rate": round((df.notna().sum().sum() / (len(df) * len(df.columns))) * 100, 2) if len(df) > 0 and len(df.columns) > 0 else 0
        })

        return analysis

    def _check_header_row(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if DataFrame has a clear header row"""
        if len(df.columns) == 0:
            return {"has_header": False, "headers": []}

        # Check if column names are meaningful (not Unnamed or generic)
        unnamed_count = sum(1 for col in df.columns if 'Unnamed' in str(col))

        # If more than 30% are unnamed, likely no proper header
        if unnamed_count / len(df.columns) > 0.3:
            return {"has_header": False, "headers": []}

        # Check if headers are not just numbers
        numeric_headers = sum(1 for col in df.columns if str(col).replace('.', '').replace('-', '').isdigit())

        if numeric_headers / len(df.columns) > 0.5:
            return {"has_header": False, "headers": []}

        return {
            "has_header": True,
            "headers": [str(col) for col in df.columns]
        }

    def _check_column_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if columns have consistent data types and structure"""
        if len(df) < 2:
            return {"is_consistent": False, "reason": "Insufficient rows for consistency check"}

        # Check if each column has a dominant data type
        consistent_columns = 0

        for col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            # Get type distribution
            types = [type(v).__name__ for v in non_null]
            type_counts = pd.Series(types).value_counts()

            # If one type dominates (>70%), column is consistent
            if len(type_counts) > 0 and type_counts.iloc[0] / len(types) > 0.7:
                consistent_columns += 1

        consistency_rate = consistent_columns / len(df.columns) if len(df.columns) > 0 else 0

        if consistency_rate >= 0.7:
            return {"is_consistent": True, "consistency_rate": consistency_rate}
        else:
            return {
                "is_consistent": False,
                "reason": f"Low column consistency ({consistency_rate:.1%})",
                "consistency_rate": consistency_rate
            }

    def _check_data_rows(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if DataFrame has actual data rows"""
        if len(df) == 0:
            return {"has_data": False, "row_count": 0}

        # Count rows that have at least some non-null values
        non_empty_rows = df.notna().any(axis=1).sum()

        if non_empty_rows >= 1:  # At least one row with data
            return {"has_data": True, "row_count": non_empty_rows}
        else:
            return {"has_data": False, "row_count": 0}

    def _check_merged_cells(self, sheet: openpyxl.worksheet.worksheet.Worksheet) -> Dict[str, Any]:
        """Check if sheet has minimal merged cells (indicator of tabular data)"""
        merged_count = len(sheet.merged_cells.ranges)

        # Tables typically have few merged cells
        # Allow up to 10% of rows to have merged cells
        max_allowed = max(5, sheet.max_row * 0.1)

        return {
            "count": merged_count,
            "is_minimal": merged_count <= max_allowed
        }

    def _check_rectangular_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if data forms a rectangular structure"""
        if len(df) == 0 or len(df.columns) == 0:
            return {"is_rectangular": False, "reason": "Empty sheet"}

        # Calculate fill rate per row
        row_fill_rates = df.notna().sum(axis=1) / len(df.columns)

        # Check if most rows have similar fill rates (rectangular)
        if len(row_fill_rates) > 0:
            fill_rate_std = row_fill_rates.std()
            mean_fill_rate = row_fill_rates.mean()

            # If standard deviation is low and mean fill rate is reasonable, it's rectangular
            if fill_rate_std < 0.3 and mean_fill_rate > 0.3:
                return {"is_rectangular": True, "fill_rate_std": fill_rate_std}
            else:
                return {
                    "is_rectangular": False,
                    "reason": f"Irregular data distribution (std: {fill_rate_std:.2f})",
                    "fill_rate_std": fill_rate_std
                }
        else:
            return {"is_rectangular": False, "reason": "No data to analyze"}

    def get_detection_summary(self, excel_path: str, sheet_name: Optional[str] = None) -> str:
        """
        Get a text summary of tabular structure detection

        Args:
            excel_path: Path to Excel file
            sheet_name: Optional specific sheet

        Returns:
            Formatted text summary
        """
        analysis = self.analyse(excel_path, sheet_name)

        summary = []
        summary.append("=" * 70)
        summary.append("TABULAR STRUCTURE DETECTION")
        summary.append("=" * 70)
        summary.append(f"\nFile: {excel_path}")
        summary.append(f"\nSummary:")
        summary.append(f"  Total Sheets: {analysis['summary']['total_sheets']}")
        summary.append(f"  Tabular Sheets: {analysis['summary']['tabular_count']}")
        summary.append(f"  Non-Tabular Sheets: {analysis['summary']['non_tabular_count']}")

        if analysis['tabular_sheets']:
            summary.append(f"\nTabular Sheets: {', '.join(analysis['tabular_sheets'])}")

        if analysis['non_tabular_sheets']:
            summary.append(f"Non-Tabular Sheets: {', '.join(analysis['non_tabular_sheets'])}")

        for sheet_analysis in analysis['sheets_analyzed']:
            summary.append("\n" + "-" * 70)
            summary.append(f"Sheet: {sheet_analysis['sheet_name']}")
            summary.append("-" * 70)

            if 'error' in sheet_analysis:
                summary.append(f"  ERROR: {sheet_analysis['error']}")
                continue

            summary.append(f"  Is Tabular: {'YES' if sheet_analysis['is_tabular'] else 'NO'}")
            summary.append(f"  Confidence Score: {sheet_analysis['confidence_score']}/100")

            summary.append(f"\n  Indicators:")
            for indicator, value in sheet_analysis['indicators'].items():
                status = "✓" if value else "✗"
                summary.append(f"    {status} {indicator.replace('_', ' ').title()}")

            if sheet_analysis['reasons']:
                summary.append(f"\n  Reasons for Non-Tabular Classification:")
                for reason in sheet_analysis['reasons']:
                    summary.append(f"    - {reason}")

            if sheet_analysis['structure_info']:
                summary.append(f"\n  Structure Info:")
                for key, value in sheet_analysis['structure_info'].items():
                    summary.append(f"    - {key.replace('_', ' ').title()}: {value}")

        summary.append("\n" + "=" * 70)

        return "\n".join(summary)
