"""Factory for creating quality check strategies"""

from typing import Dict, Type, List
from .base import QualityCheckStrategy
from .date_checks import DateFormatQualityCheck
from .numeric_checks import NumericFormatQualityCheck
from .string_checks import StringQualityCheck, EmailQualityCheck
from .consistency_checks import CrossFieldConsistencyCheck, DuplicateCheck


class QualityCheckFactory:
    """
    Factory to create appropriate quality check strategies

    Maps field types to quality check strategies
    """

    # Map field types to strategy classes
    STRATEGY_MAP: Dict[str, Type[QualityCheckStrategy]] = {
        'date': DateFormatQualityCheck,
        'datetime': DateFormatQualityCheck,
        'numeric': NumericFormatQualityCheck,
        'integer': NumericFormatQualityCheck,
        'string': StringQualityCheck,
        'text': StringQualityCheck,
        'name': StringQualityCheck,
        'email': EmailQualityCheck,
        'consistency': CrossFieldConsistencyCheck,
        'duplicate': DuplicateCheck,
    }

    @classmethod
    def get_checker(
        cls,
        field_type: str,
        **config
    ) -> QualityCheckStrategy:
        """
        Get quality check strategy for field type

        Args:
            field_type: Type of field (date, numeric, string, etc.)
            **config: Configuration parameters for the strategy

        Returns:
            Initialized quality check strategy

        Raises:
            ValueError: If field type not supported
        """
        strategy_class = cls.STRATEGY_MAP.get(field_type.lower())

        if strategy_class is None:
            raise ValueError(
                f"No quality check strategy for field type: {field_type}. "
                f"Supported types: {', '.join(cls.STRATEGY_MAP.keys())}"
            )

        return strategy_class(**config)

    @classmethod
    def register_strategy(
        cls,
        field_type: str,
        strategy_class: Type[QualityCheckStrategy]
    ):
        """
        Register custom quality check strategy

        Args:
            field_type: Type identifier
            strategy_class: Strategy class to register
        """
        cls.STRATEGY_MAP[field_type.lower()] = strategy_class

    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported field types"""
        return list(cls.STRATEGY_MAP.keys())
