from abc import ABC, abstractmethod
from typing import Any, Optional
from enum import Enum

class MatchResult(Enum):
    """Result of a comparison strategy"""
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    FUZZY_MATCH = "fuzzy_match"
    NO_MATCH = "no_match"
    MISSING_DATA = "missing_data"

class ComparisonStrategy(ABC):
    """Base class for comparison strategies"""
    @abstractmethod
    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """Compare two values and return match result"""
        pass

    @abstractmethod
    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        """Return similarity score between 0 and 1"""
        pass