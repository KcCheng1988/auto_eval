"""Comparison strategies for field validation"""

from .base import ComparisonStrategy, MatchResult
from .utils import is_null_like, NULL_LIKE_VALUES
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

    # Utilities
    'is_null_like',
    'NULL_LIKE_VALUES',

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
