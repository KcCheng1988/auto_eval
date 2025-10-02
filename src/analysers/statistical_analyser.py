"""Statistical analysis for Excel data"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StatisticalAnalyser:
    """Performs statistical analysis on Excel data"""

    def __init__(self):
        pass

    def analyse(self, excel_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform statistical analysis on Excel sheets

        Args:
            excel_path: Path to Excel file
            sheet_name: Optional specific sheet to analyze (None = all sheets)

        Returns:
            Dictionary containing statistical analysis results
        """
        logger.info(f"Performing statistical analysis of: {excel_path}")

        results = {
            "file_path": excel_path,
            "sheets_analyzed": []
        }

        # Load workbook to get sheet names
        try:
            if sheet_name:
                sheets_to_analyze = [sheet_name]
            else:
                # Get all sheet names
                excel_file = pd.ExcelFile(excel_path)
                sheets_to_analyze = excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            return {"error": str(e)}

        for sheet in sheets_to_analyze:
            sheet_stats = self._analyse_sheet(excel_path, sheet)
            results["sheets_analyzed"].append(sheet_stats)

        logger.info(f"Statistical analysis complete for {len(results['sheets_analyzed'])} sheets")
        return results

    def _analyse_sheet(self, excel_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Perform statistical analysis on a single sheet

        Args:
            excel_path: Path to Excel file
            sheet_name: Name of the sheet

        Returns:
            Dictionary with sheet statistics
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
        except Exception as e:
            logger.error(f"Error reading sheet '{sheet_name}': {str(e)}")
            return {
                "sheet_name": sheet_name,
                "error": str(e)
            }

        analysis = {
            "sheet_name": sheet_name,
            "overview": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "total_cells": len(df) * len(df.columns),
                "non_empty_cells": int(df.notna().sum().sum()),
                "empty_cells": int(df.isna().sum().sum())
            },
            "column_statistics": {}
        }

        # Calculate fill rate
        if analysis["overview"]["total_cells"] > 0:
            analysis["overview"]["fill_rate"] = round(
                (analysis["overview"]["non_empty_cells"] / analysis["overview"]["total_cells"]) * 100, 2
            )
        else:
            analysis["overview"]["fill_rate"] = 0.0

        # Analyze each column
        for col in df.columns:
            col_stats = self._analyse_column(df[col], col)
            analysis["column_statistics"][col] = col_stats

        return analysis

    def _analyse_column(self, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """
        Analyze statistics for a single column

        Args:
            series: Pandas Series (column data)
            col_name: Name of the column

        Returns:
            Dictionary with column statistics
        """
        stats = {
            "column_name": col_name,
            "data_type": str(series.dtype),
            "total_values": len(series),
            "non_null_values": int(series.notna().sum()),
            "null_values": int(series.isna().sum()),
            "null_percentage": round((series.isna().sum() / len(series)) * 100, 2),
            "unique_values": int(series.nunique()),
            "unique_percentage": round((series.nunique() / len(series)) * 100, 2) if len(series) > 0 else 0
        }

        # Numeric statistics
        if pd.api.types.is_numeric_dtype(series):
            stats["type_category"] = "numeric"
            numeric_stats = self._numeric_statistics(series)
            stats.update(numeric_stats)

        # Text statistics
        elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            stats["type_category"] = "text"
            text_stats = self._text_statistics(series)
            stats.update(text_stats)

        # DateTime statistics
        elif pd.api.types.is_datetime64_any_dtype(series):
            stats["type_category"] = "datetime"
            datetime_stats = self._datetime_statistics(series)
            stats.update(datetime_stats)

        # Boolean statistics
        elif pd.api.types.is_bool_dtype(series):
            stats["type_category"] = "boolean"
            boolean_stats = self._boolean_statistics(series)
            stats.update(boolean_stats)

        else:
            stats["type_category"] = "other"

        # Top values (for all types)
        if stats["unique_values"] > 0:
            top_values = series.value_counts().head(5).to_dict()
            stats["top_values"] = {str(k): int(v) for k, v in top_values.items()}

        return stats

    def _numeric_statistics(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for numeric columns"""
        non_null = series.dropna()

        if len(non_null) == 0:
            return {
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std": None,
                "q25": None,
                "q75": None
            }

        return {
            "min": float(non_null.min()),
            "max": float(non_null.max()),
            "mean": round(float(non_null.mean()), 4),
            "median": float(non_null.median()),
            "std": round(float(non_null.std()), 4),
            "q25": float(non_null.quantile(0.25)),
            "q75": float(non_null.quantile(0.75)),
            "sum": float(non_null.sum()),
            "range": float(non_null.max() - non_null.min())
        }

    def _text_statistics(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for text columns"""
        non_null = series.dropna()

        if len(non_null) == 0:
            return {
                "min_length": None,
                "max_length": None,
                "avg_length": None
            }

        # Convert to string and calculate lengths
        lengths = non_null.astype(str).str.len()

        stats = {
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
            "avg_length": round(float(lengths.mean()), 2)
        }

        # Check for common patterns
        patterns = {
            "contains_email": non_null.astype(str).str.contains(r'@.*\.', regex=True, na=False).sum(),
            "contains_url": non_null.astype(str).str.contains(r'https?://', regex=True, na=False).sum(),
            "contains_numbers": non_null.astype(str).str.contains(r'\d', regex=True, na=False).sum(),
        }

        stats["patterns"] = {k: int(v) for k, v in patterns.items() if v > 0}

        return stats

    def _datetime_statistics(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for datetime columns"""
        non_null = series.dropna()

        if len(non_null) == 0:
            return {
                "min_date": None,
                "max_date": None,
                "date_range_days": None
            }

        min_date = non_null.min()
        max_date = non_null.max()
        date_range = (max_date - min_date).days

        return {
            "min_date": str(min_date),
            "max_date": str(max_date),
            "date_range_days": int(date_range)
        }

    def _boolean_statistics(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for boolean columns"""
        non_null = series.dropna()

        if len(non_null) == 0:
            return {
                "true_count": 0,
                "false_count": 0,
                "true_percentage": 0
            }

        true_count = int(non_null.sum())
        false_count = len(non_null) - true_count

        return {
            "true_count": true_count,
            "false_count": false_count,
            "true_percentage": round((true_count / len(non_null)) * 100, 2)
        }

    def get_statistics_summary(self, excel_path: str, sheet_name: Optional[str] = None) -> str:
        """
        Get a text summary of statistics

        Args:
            excel_path: Path to Excel file
            sheet_name: Optional specific sheet

        Returns:
            Formatted text summary
        """
        analysis = self.analyse(excel_path, sheet_name)

        if "error" in analysis:
            return f"Error: {analysis['error']}"

        summary = []
        summary.append("=" * 70)
        summary.append("STATISTICAL ANALYSIS")
        summary.append("=" * 70)
        summary.append(f"\nFile: {excel_path}")

        for sheet_stats in analysis['sheets_analyzed']:
            if 'error' in sheet_stats:
                summary.append(f"\nSheet: {sheet_stats['sheet_name']} - ERROR: {sheet_stats['error']}")
                continue

            summary.append("\n" + "-" * 70)
            summary.append(f"Sheet: {sheet_stats['sheet_name']}")
            summary.append("-" * 70)

            overview = sheet_stats['overview']
            summary.append(f"\nOverview:")
            summary.append(f"  Total Rows: {overview['total_rows']}")
            summary.append(f"  Total Columns: {overview['total_columns']}")
            summary.append(f"  Total Cells: {overview['total_cells']}")
            summary.append(f"  Non-Empty Cells: {overview['non_empty_cells']}")
            summary.append(f"  Fill Rate: {overview['fill_rate']}%")

            summary.append(f"\nColumn Statistics:")

            for col_name, col_stats in sheet_stats['column_statistics'].items():
                summary.append(f"\n  Column: {col_name}")
                summary.append(f"    Type: {col_stats['type_category']} ({col_stats['data_type']})")
                summary.append(f"    Non-Null: {col_stats['non_null_values']}/{col_stats['total_values']} ({100 - col_stats['null_percentage']:.1f}%)")
                summary.append(f"    Unique Values: {col_stats['unique_values']} ({col_stats['unique_percentage']:.1f}%)")

                # Type-specific statistics
                if col_stats['type_category'] == 'numeric':
                    if col_stats['min'] is not None:
                        summary.append(f"    Range: {col_stats['min']:.4f} to {col_stats['max']:.4f}")
                        summary.append(f"    Mean: {col_stats['mean']:.4f}, Median: {col_stats['median']:.4f}")
                        summary.append(f"    Std Dev: {col_stats['std']:.4f}")

                elif col_stats['type_category'] == 'text':
                    if col_stats['min_length'] is not None:
                        summary.append(f"    Length: {col_stats['min_length']} to {col_stats['max_length']} chars (avg: {col_stats['avg_length']})")
                        if 'patterns' in col_stats and col_stats['patterns']:
                            summary.append(f"    Patterns: {col_stats['patterns']}")

                elif col_stats['type_category'] == 'datetime':
                    if col_stats['min_date']:
                        summary.append(f"    Date Range: {col_stats['min_date']} to {col_stats['max_date']}")
                        summary.append(f"    Span: {col_stats['date_range_days']} days")

                elif col_stats['type_category'] == 'boolean':
                    summary.append(f"    True: {col_stats['true_count']} ({col_stats['true_percentage']}%)")
                    summary.append(f"    False: {col_stats['false_count']}")

                # Top values
                if 'top_values' in col_stats:
                    summary.append(f"    Top Values:")
                    for val, count in list(col_stats['top_values'].items())[:3]:
                        summary.append(f"      - '{val}': {count}")

        summary.append("\n" + "=" * 70)

        return "\n".join(summary)
