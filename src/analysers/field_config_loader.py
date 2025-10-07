"""Load field configuration from Excel and instantiate comparison strategies"""

import pandas as pd
from typing import Dict, Any

try:
    # Try relative import first
    from ..models.comparison_strategies import (
        ComparisonStrategy,
        ExactNameMatch,
        InvertedNameMatch,
        ExactDateTimeStringMatch,
        ExactDateTimeMatch,
        ToleranceDateTimeMatch,
        DateOnlyMatch,
        TimeOnlyMatch,
        DateTimeRangeMatch,
        ExactStringMatch,
        ContainsStringMatch,
        ExactNumericMatch,
        ToleranceNumericMatch,
        RangeNumericMatch
    )
except ImportError:
    # Fall back to absolute import
    from src.models.comparison_strategies import (
        ComparisonStrategy,
        ExactNameMatch,
        InvertedNameMatch,
        ExactDateTimeStringMatch,
        ExactDateTimeMatch,
        ToleranceDateTimeMatch,
        DateOnlyMatch,
        TimeOnlyMatch,
        DateTimeRangeMatch,
        ExactStringMatch,
        ContainsStringMatch,
        ExactNumericMatch,
        ToleranceNumericMatch,
        RangeNumericMatch
    )


class FieldConfigLoader:
    """
    Load field configuration from Excel and create comparison strategy instances

    This class reads the user-edited Excel file created by FieldClassifier
    and instantiates the appropriate comparison strategies with settings.
    """

    # Map strategy names to classes
    STRATEGY_MAP = {
        'ExactNameMatch': ExactNameMatch,
        'InvertedNameMatch': InvertedNameMatch,
        'ExactDateTimeStringMatch': ExactDateTimeStringMatch,
        'ExactDateTimeMatch': ExactDateTimeMatch,
        'ToleranceDateTimeMatch': ToleranceDateTimeMatch,
        'DateOnlyMatch': DateOnlyMatch,
        'TimeOnlyMatch': TimeOnlyMatch,
        'DateTimeRangeMatch': DateTimeRangeMatch,
        'ExactStringMatch': ExactStringMatch,
        'ContainsStringMatch': ContainsStringMatch,
        'ExactNumericMatch': ExactNumericMatch,
        'ToleranceNumericMatch': ToleranceNumericMatch,
        'RangeNumericMatch': RangeNumericMatch
    }

    def __init__(self):
        pass

    def load_from_excel(self, excel_path: str, sheet_name: str = 'Field Classification') -> Dict[str, ComparisonStrategy]:
        """
        Load field configuration from Excel and create strategy instances

        Args:
            excel_path: Path to Excel file
            sheet_name: Sheet name containing configuration

        Returns:
            Dictionary mapping field names to strategy instances
        """
        df = pd.read_excel(excel_path, sheet_name=sheet_name)

        field_strategies = {}

        for _, row in df.iterrows():
            field_name = row['field_name']
            strategy_name = row['recommended_strategy']

            # Extract settings from columns prefixed with 'setting_'
            settings = {}
            for col in df.columns:
                if col.startswith('setting_'):
                    setting_key = col.replace('setting_', '')
                    setting_value = row[col]

                    # Skip NaN values
                    if pd.notna(setting_value):
                        # Convert string 'True'/'False' to boolean
                        if isinstance(setting_value, str):
                            if setting_value.lower() == 'true':
                                setting_value = True
                            elif setting_value.lower() == 'false':
                                setting_value = False

                        settings[setting_key] = setting_value

            # Instantiate strategy
            strategy = self._create_strategy(strategy_name, settings)
            field_strategies[field_name] = strategy

        return field_strategies

    def _create_strategy(self, strategy_name: str, settings: Dict[str, Any]) -> ComparisonStrategy:
        """
        Create a comparison strategy instance

        Args:
            strategy_name: Name of the strategy class
            settings: Dictionary of strategy settings

        Returns:
            Instantiated ComparisonStrategy object
        """
        strategy_class = self.STRATEGY_MAP.get(strategy_name)

        if strategy_class is None:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available strategies: {list(self.STRATEGY_MAP.keys())}")

        # Instantiate with settings
        try:
            return strategy_class(**settings)
        except TypeError as e:
            raise ValueError(f"Invalid settings for {strategy_name}: {settings}. Error: {e}")

    def load_as_dataframe(self, excel_path: str, sheet_name: str = 'Field Classification') -> pd.DataFrame:
        """
        Load field configuration as DataFrame without instantiating strategies

        Useful for reviewing or further processing the configuration.

        Args:
            excel_path: Path to Excel file
            sheet_name: Sheet name containing configuration

        Returns:
            DataFrame with field configuration
        """
        return pd.read_excel(excel_path, sheet_name=sheet_name)

    def validate_configuration(self, excel_path: str, sheet_name: str = 'Field Classification') -> Dict[str, Any]:
        """
        Validate field configuration without instantiating strategies

        Args:
            excel_path: Path to Excel file
            sheet_name: Sheet name containing configuration

        Returns:
            Dictionary with validation results
        """
        df = pd.read_excel(excel_path, sheet_name=sheet_name)

        validation_results = {
            'valid': True,
            'total_fields': len(df),
            'errors': [],
            'warnings': []
        }

        for idx, row in df.iterrows():
            field_name = row['field_name']
            strategy_name = row['recommended_strategy']

            # Check if strategy exists
            if strategy_name not in self.STRATEGY_MAP:
                validation_results['valid'] = False
                validation_results['errors'].append({
                    'row': idx + 2,  # +2 for Excel row (header + 0-index)
                    'field': field_name,
                    'error': f"Unknown strategy: {strategy_name}"
                })

            # Check for missing field name
            if pd.isna(field_name) or str(field_name).strip() == '':
                validation_results['valid'] = False
                validation_results['errors'].append({
                    'row': idx + 2,
                    'field': field_name,
                    'error': "Missing field name"
                })

        return validation_results
