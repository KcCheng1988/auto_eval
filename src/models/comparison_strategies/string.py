"""Comparison strategies for general string fields"""

from typing import Any
from .base import ComparisonStrategy, MatchResult
from .mixins import StringNormalizationMixin


# ============================================================================
# STRING COMPARISON STRATEGIES
# ============================================================================

class ExactStringMatch(StringNormalizationMixin, ComparisonStrategy):
    """
    Exact string matching with normalization

    This is the basic string comparison using the normalization mixin.
    """

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare strings for exact match after normalization

        Args:
            value1: First string value
            value2: Second string value

        Returns:
            MatchResult indicating exact match or not
        """
        str1 = self.normalize_string(value1)
        str2 = self.normalize_string(value2)

        if str1 is None or str2 is None:
            return MatchResult.MISSING_DATA

        if str1 == str2:
            return MatchResult.EXACT_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        return 1.0 if self.compare(value1, value2) == MatchResult.EXACT_MATCH else 0.0


class ContainsStringMatch(StringNormalizationMixin, ComparisonStrategy):
    """
    Check if one string contains the other (substring matching)

    Useful for flexible matching where one value might be abbreviated or partial.
    """

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Check if either string contains the other

        Args:
            value1: First string value
            value2: Second string value

        Returns:
            MatchResult (EXACT_MATCH if identical, PARTIAL_MATCH if contains)
        """
        str1 = self.normalize_string(value1)
        str2 = self.normalize_string(value2)

        if str1 is None or str2 is None:
            return MatchResult.MISSING_DATA

        if str1 == str2:
            return MatchResult.EXACT_MATCH

        if str1 in str2 or str2 in str1:
            return MatchResult.PARTIAL_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        str1 = self.normalize_string(value1)
        str2 = self.normalize_string(value2)

        if str1 is None or str2 is None:
            return 0.0

        if str1 == str2:
            return 1.0

        if str1 in str2:
            return len(str1) / len(str2)
        elif str2 in str1:
            return len(str2) / len(str1)

        return 0.0
