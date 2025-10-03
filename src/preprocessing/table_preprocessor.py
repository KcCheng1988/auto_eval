"""Table-level preprocessing orchestrator"""

import pandas as pd
from typing import Dict, List, Any, Optional, Callable
import logging
from .cell_preprocessors import (
    clean_numeric,
    clean_date,
    clean_string,
    detect_and_convert_type,
    clean_column_name,
    is_potential_date
)

logger = logging.getLogger(__name__)


class PreprocessingConfig:
    """Configuration for preprocessing operations"""

    def __init__(self):
        # Row cleaning
        self.remove_all_nan_rows = True
        self.remove_all_nan_columns = True

        # Column name cleaning
        self.clean_column_names = True

        # Type detection and conversion
        self.auto_detect_types = True
        self.prefer_numeric = True  # Try numeric before date when auto-detecting

        # Date formatting
        self.date_format = '%Y-%m-%d'
        self.datetime_format = '%Y-%m-%d %H:%M:%S'

        # Numeric formatting
        self.numeric_decimal_places = None  # None = no rounding

        # String cleaning
        self.lowercase_strings = True
        self.strip_whitespace = True
        self.remove_extra_spaces = True

        # Custom column type hints
        self.column_types = {}  # {column_name: 'numeric'|'date'|'string'}


class TablePreprocessor:
    """Orchestrates preprocessing operations on DataFrames"""

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Initialize TablePreprocessor

        Args:
            config: Optional preprocessing configuration
        """
        self.config = config or PreprocessingConfig()

    def preprocess(self, df: pd.DataFrame, config: Optional[PreprocessingConfig] = None) -> pd.DataFrame:
        """
        Apply all preprocessing steps to a DataFrame

        Args:
            df: Input DataFrame
            config: Optional config to override instance config

        Returns:
            Preprocessed DataFrame
        """
        if df is None or df.empty:
            return df

        config = config or self.config
        df_clean = df.copy()

        # Step 1: Clean column names
        if config.clean_column_names:
            df_clean = self.clean_column_names(df_clean)

        # Step 2: Remove all-NaN rows and columns
        if config.remove_all_nan_rows:
            df_clean = self.remove_empty_rows(df_clean)

        if config.remove_all_nan_columns:
            df_clean = self.remove_empty_columns(df_clean)

        # Step 3: Type detection and conversion
        if config.auto_detect_types:
            df_clean = self.auto_convert_types(df_clean, config)
        else:
            # Manual type conversion based on column_types
            df_clean = self.apply_column_types(df_clean, config)

        return df_clean

    def remove_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows that are completely empty (all NaN/None)

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with empty rows removed
        """
        before_count = len(df)
        df_clean = df.dropna(how='all').reset_index(drop=True)
        after_count = len(df_clean)

        if before_count != after_count:
            logger.info(f"Removed {before_count - after_count} empty rows")

        return df_clean

    def remove_empty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove columns that are completely empty (all NaN/None)

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with empty columns removed
        """
        before_count = len(df.columns)
        df_clean = df.dropna(axis=1, how='all')
        after_count = len(df_clean.columns)

        if before_count != after_count:
            logger.info(f"Removed {before_count - after_count} empty columns")

        return df_clean

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize column names

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with cleaned column names
        """
        df_clean = df.copy()
        new_columns = [clean_column_name(col) for col in df_clean.columns]

        # Handle duplicate column names
        seen = {}
        for i, col in enumerate(new_columns):
            if col in seen:
                seen[col] += 1
                new_columns[i] = f"{col}_{seen[col]}"
            else:
                seen[col] = 0

        df_clean.columns = new_columns
        logger.info(f"Cleaned {len(new_columns)} column names")

        return df_clean

    def auto_convert_types(self, df: pd.DataFrame, config: PreprocessingConfig) -> pd.DataFrame:
        """
        Automatically detect and convert column types

        Args:
            df: Input DataFrame
            config: Preprocessing configuration

        Returns:
            DataFrame with converted types
        """
        df_clean = df.copy()

        for col in df_clean.columns:
            # Check if column has type hint
            if col in config.column_types:
                df_clean[col] = self.convert_column(
                    df_clean[col],
                    config.column_types[col],
                    config
                )
            else:
                # Auto-detect type
                df_clean[col] = df_clean[col].apply(
                    lambda x: detect_and_convert_type(x, prefer_numeric=config.prefer_numeric)
                )

        return df_clean

    def apply_column_types(self, df: pd.DataFrame, config: PreprocessingConfig) -> pd.DataFrame:
        """
        Apply explicit column type conversions based on config

        Args:
            df: Input DataFrame
            config: Preprocessing configuration

        Returns:
            DataFrame with converted types
        """
        df_clean = df.copy()

        for col, col_type in config.column_types.items():
            if col in df_clean.columns:
                df_clean[col] = self.convert_column(df_clean[col], col_type, config)

        return df_clean

    def convert_column(self, series: pd.Series, target_type: str,
                      config: PreprocessingConfig) -> pd.Series:
        """
        Convert a column to a specific type

        Args:
            series: Input Series
            target_type: Target type ('numeric', 'date', 'string')
            config: Preprocessing configuration

        Returns:
            Converted Series
        """
        if target_type == 'numeric':
            return series.apply(
                lambda x: clean_numeric(x, decimal_places=config.numeric_decimal_places)
            )
        elif target_type == 'date':
            return series.apply(
                lambda x: clean_date(
                    x,
                    output_format=config.date_format,
                    datetime_output_format=config.datetime_format
                )
            )
        elif target_type == 'string':
            return series.apply(
                lambda x: clean_string(
                    x,
                    lowercase=config.lowercase_strings,
                    strip_whitespace=config.strip_whitespace,
                    remove_extra_spaces=config.remove_extra_spaces
                )
            )
        else:
            logger.warning(f"Unknown target type '{target_type}', returning original series")
            return series

    def apply_custom_function(self, df: pd.DataFrame, func: Callable,
                             columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Apply a custom preprocessing function to specified columns

        Args:
            df: Input DataFrame
            func: Function to apply (should accept and return a value)
            columns: List of column names (None = all columns)

        Returns:
            DataFrame with function applied
        """
        df_clean = df.copy()
        target_columns = columns or df_clean.columns

        for col in target_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(func)

        return df_clean

    def get_preprocessing_summary(self, df_original: pd.DataFrame,
                                 df_processed: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a summary of preprocessing changes

        Args:
            df_original: Original DataFrame
            df_processed: Processed DataFrame

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'original_shape': df_original.shape,
            'processed_shape': df_processed.shape,
            'rows_removed': len(df_original) - len(df_processed),
            'columns_removed': len(df_original.columns) - len(df_processed.columns),
            'original_dtypes': df_original.dtypes.value_counts().to_dict(),
            'processed_dtypes': df_processed.dtypes.value_counts().to_dict(),
            'original_null_count': df_original.isnull().sum().sum(),
            'processed_null_count': df_processed.isnull().sum().sum()
        }

        return summary


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def quick_clean(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Quick preprocessing with default settings

    Args:
        df: Input DataFrame
        **kwargs: Optional config overrides (e.g., date_format='%d/%m/%Y')

    Returns:
        Cleaned DataFrame
    """
    config = PreprocessingConfig()

    # Apply any config overrides
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    preprocessor = TablePreprocessor(config)
    return preprocessor.preprocess(df)


def clean_extracted_tables(tables_dict: Dict[str, Any],
                          config: Optional[PreprocessingConfig] = None) -> Dict[str, Any]:
    """
    Clean all tables from TabularDetector.extract_tables() output

    Args:
        tables_dict: Output from TabularDetector.extract_tables()
        config: Optional preprocessing configuration

    Returns:
        Dictionary with cleaned tables
    """
    preprocessor = TablePreprocessor(config)
    cleaned_dict = {
        'file_path': tables_dict['file_path'],
        'sheets': []
    }

    for sheet_data in tables_dict['sheets']:
        cleaned_sheet = {
            'sheet_name': sheet_data['sheet_name'],
            'tables': []
        }

        if 'error' in sheet_data:
            cleaned_sheet['error'] = sheet_data['error']
            cleaned_dict['sheets'].append(cleaned_sheet)
            continue

        for table in sheet_data['tables']:
            if 'dataframe' not in table:
                cleaned_sheet['tables'].append(table)
                continue

            # Preprocess the table
            df_clean = preprocessor.preprocess(table['dataframe'])

            cleaned_table = table.copy()
            cleaned_table['dataframe'] = df_clean
            cleaned_table['shape'] = df_clean.shape
            cleaned_table['preprocessing_applied'] = True

            cleaned_sheet['tables'].append(cleaned_table)

        cleaned_dict['sheets'].append(cleaned_sheet)

    return cleaned_dict
