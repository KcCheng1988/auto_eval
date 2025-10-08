from typing import Any, Optional
from .base import ComparisonStrategy, MatchResult
from .mixins import StringNormalizationMixin

# ============================================================================
# NAME COMPARISON STRATEGIES
# ============================================================================
class ExactNameMatch(StringNormalizationMixin, ComparisonStrategy):
    """Exact name matching with normalization"""

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        name1 = self.normalize_string(value1)
        name2 = self.normalize_string(value2)

        # Both null = both correctly empty = EXACT_MATCH
        if name1 is None and name2 is None:
            return MatchResult.EXACT_MATCH

        # One null, one not = mismatch = NO_MATCH
        if name1 is None or name2 is None:
            return MatchResult.NO_MATCH

        if name1 == name2:
            return MatchResult.EXACT_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        return 1.0 if self.compare(value1, value2) == MatchResult.EXACT_MATCH else 0.0


class InvertedNameMatch(StringNormalizationMixin, ComparisonStrategy):
    """Match names even if first/last are swapped"""

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        name1 = self.normalize_string(value1)
        name2 = self.normalize_string(value2)

        # Both null = both correctly empty = EXACT_MATCH
        if name1 is None and name2 is None:
            return MatchResult.EXACT_MATCH

        # One null, one not = mismatch = NO_MATCH
        if name1 is None or name2 is None:
            return MatchResult.NO_MATCH

        if name1 == name2:
            return MatchResult.EXACT_MATCH
        
        # Check invertged
        parts1 = name1.split()
        parts2 = name2.split()

        if len(parts1) == 2 and len(parts2) == 2:
            if parts1[0] == parts2[1] and parts1[1] == parts2[0]:
                return MatchResult.PARTIAL_MATCH
        
        if len(parts1) > 2 and len(parts2) > 2 and len(parts1) == len(parts2):
            if parts1[0] == parts2[-1] and parts1[1:] == parts2[:-1]:
                return MatchResult.PARTIAL_MATCH
        
        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        result = self.compare(value1, value2)
        if result == MatchResult.EXACT_MATCH:
            return 1.0
        elif result == MatchResult.PARTIAL_MATCH:
            return 0.9
        return 0.0    