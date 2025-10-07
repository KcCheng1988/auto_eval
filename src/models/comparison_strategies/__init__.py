"""Comparison strategies for field validation"""

from .base import ComparisonStrategy, MatchResult
from .name import ExactNameMatch, InvertedNameMatch
from .datetime import (
    ExactDateTimeStringMatch,
    ExactDateTimeMatch,
    ToleranceDateTimeMatch,
    DateOnlyMatch,
    TimeOnlyMatch,
    DateTimeRangeMatch
)
from .string import (
    ExactStringMatch,
    ContainsStringMatch
)
from .numeric import (
    ExactNumericMatch,
    ToleranceNumericMatch,
    RangeNumericMatch
)

__all__ = [
    # Base classes
    'ComparisonStrategy',
    'MatchResult',

    # Name strategies
    'ExactNameMatch',
    'InvertedNameMatch',

    # DateTime strategies
    'ExactDateTimeStringMatch',
    'ExactDateTimeMatch',
    'ToleranceDateTimeMatch',
    'DateOnlyMatch',
    'TimeOnlyMatch',
    'DateTimeRangeMatch',

    # String strategies
    'ExactStringMatch',
    'ContainsStringMatch',

    # Numeric strategies
    'ExactNumericMatch',
    'ToleranceNumericMatch',
    'RangeNumericMatch',
]
