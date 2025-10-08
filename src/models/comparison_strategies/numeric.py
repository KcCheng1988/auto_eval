"""Comparison strategies for numeric fields"""

from typing import Any, Optional
from .base import ComparisonStrategy, MatchResult
from .utils import NumericConverter


# ============================================================================
# NUMERIC COMPARISON STRATEGIES
# ============================================================================

class ExactNumericMatch(ComparisonStrategy):
    """
    Exact numeric matching after normalization

    Handles various numeric formats:
    - "15,000" vs "15000.00" -> EXACT_MATCH
    - "$1,234.56" vs "1234.56" -> EXACT_MATCH
    - "(100)" vs "-100" -> EXACT_MATCH (accounting notation)
    """

    def __init__(self, decimal_precision: Optional[int] = None, **kwargs):
        """
        Initialize with optional decimal precision

        Args:
            decimal_precision: Number of decimal places to round to (None = no rounding)
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.decimal_precision = decimal_precision

    def _normalize_numeric(self, value: Any) -> Optional[float]:
        """
        Convert various numeric formats to float using NumericConverter

        Args:
            value: Value to convert

        Returns:
            Float value or None if cannot convert
        """
        return NumericConverter.to_float(value, self.decimal_precision)

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare numeric values for exact match

        Args:
            value1: First numeric value
            value2: Second numeric value

        Returns:
            MatchResult indicating exact match or not
        """
        num1 = self._normalize_numeric(value1)
        num2 = self._normalize_numeric(value2)

        # Both null = both correctly empty = EXACT_MATCH
        if num1 is None and num2 is None:
            return MatchResult.EXACT_MATCH

        # One null, one not = mismatch = NO_MATCH
        if num1 is None or num2 is None:
            return MatchResult.NO_MATCH

        if num1 == num2:
            return MatchResult.EXACT_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        return 1.0 if self.compare(value1, value2) == MatchResult.EXACT_MATCH else 0.0


class ToleranceNumericMatch(ComparisonStrategy):
    """
    Numeric matching with absolute or percentage tolerance

    Allows for small differences in numeric values.
    """

    def __init__(
        self,
        absolute_tolerance: Optional[float] = None,
        percentage_tolerance: Optional[float] = None,
        decimal_precision: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize with tolerance thresholds

        Args:
            absolute_tolerance: Maximum absolute difference allowed (e.g., 0.01)
            percentage_tolerance: Maximum percentage difference allowed (e.g., 0.05 for 5%)
            decimal_precision: Number of decimal places to round to (None = no rounding)
            **kwargs: Additional parameters

        Note: If both tolerances are provided, the value matches if EITHER tolerance is satisfied
        """
        super().__init__(**kwargs)

        if absolute_tolerance is None and percentage_tolerance is None:
            raise ValueError("At least one of absolute_tolerance or percentage_tolerance must be provided")

        self.absolute_tolerance = absolute_tolerance
        self.percentage_tolerance = percentage_tolerance
        self.decimal_precision = decimal_precision

    def _normalize_numeric(self, value: Any) -> Optional[float]:
        """Convert various numeric formats to float using NumericConverter"""
        return NumericConverter.to_float(value, self.decimal_precision)

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare numeric values with tolerance

        Args:
            value1: First numeric value
            value2: Second numeric value

        Returns:
            MatchResult based on tolerance thresholds
        """
        num1 = self._normalize_numeric(value1)
        num2 = self._normalize_numeric(value2)

        # Both null = both correctly empty = EXACT_MATCH
        if num1 is None and num2 is None:
            return MatchResult.EXACT_MATCH

        # One null, one not = mismatch = NO_MATCH
        if num1 is None or num2 is None:
            return MatchResult.NO_MATCH

        if num1 == num2:
            return MatchResult.EXACT_MATCH

        # Calculate absolute difference
        abs_diff = abs(num1 - num2)

        # Check absolute tolerance
        if self.absolute_tolerance is not None and abs_diff <= self.absolute_tolerance:
            return MatchResult.FUZZY_MATCH

        # Check percentage tolerance
        if self.percentage_tolerance is not None:
            # Use the larger of the two values as the base for percentage calculation
            base = max(abs(num1), abs(num2))
            if base > 0:
                pct_diff = abs_diff / base
                if pct_diff <= self.percentage_tolerance:
                    return MatchResult.FUZZY_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        num1 = self._normalize_numeric(value1)
        num2 = self._normalize_numeric(value2)

        # Both null = both correctly empty = perfect match
        if num1 is None and num2 is None:
            return 1.0

        # One null, one not = mismatch = no similarity
        if num1 is None or num2 is None:
            return 0.0

        if num1 == num2:
            return 1.0

        abs_diff = abs(num1 - num2)

        # Calculate score based on tolerance
        if self.absolute_tolerance is not None:
            if abs_diff <= self.absolute_tolerance:
                # Linear decay within absolute tolerance
                return 1.0 - (abs_diff / self.absolute_tolerance) * 0.15

        if self.percentage_tolerance is not None:
            base = max(abs(num1), abs(num2))
            if base > 0:
                pct_diff = abs_diff / base
                if pct_diff <= self.percentage_tolerance:
                    # Linear decay within percentage tolerance
                    return 1.0 - (pct_diff / self.percentage_tolerance) * 0.15

        # Exponential decay beyond tolerance
        base = max(abs(num1), abs(num2))
        if base > 0:
            pct_diff = abs_diff / base
            return max(0.0, 0.85 * (1 - pct_diff))

        return 0.0


class RangeNumericMatch(ComparisonStrategy):
    """
    Check if numeric values fall within the same range/bucket

    Useful for grouping values into categories or bins.
    """

    def __init__(self, bucket_size: float, decimal_precision: Optional[int] = None, **kwargs):
        """
        Initialize with bucket size

        Args:
            bucket_size: Size of each numeric bucket (e.g., 100 for 0-99, 100-199, etc.)
            decimal_precision: Number of decimal places to round to (None = no rounding)
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        if bucket_size <= 0:
            raise ValueError("bucket_size must be positive")
        self.bucket_size = bucket_size
        self.decimal_precision = decimal_precision

    def _normalize_numeric(self, value: Any) -> Optional[float]:
        """Convert various numeric formats to float using NumericConverter"""
        return NumericConverter.to_float(value, self.decimal_precision)

    def _get_bucket(self, num: float) -> int:
        """Get the bucket index for a number"""
        return int(num // self.bucket_size)

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare numeric values by bucket

        Args:
            value1: First numeric value
            value2: Second numeric value

        Returns:
            MatchResult based on whether values fall in same bucket
        """
        num1 = self._normalize_numeric(value1)
        num2 = self._normalize_numeric(value2)

        # Both null = both correctly empty = EXACT_MATCH
        if num1 is None and num2 is None:
            return MatchResult.EXACT_MATCH

        # One null, one not = mismatch = NO_MATCH
        if num1 is None or num2 is None:
            return MatchResult.NO_MATCH

        if num1 == num2:
            return MatchResult.EXACT_MATCH

        bucket1 = self._get_bucket(num1)
        bucket2 = self._get_bucket(num2)

        if bucket1 == bucket2:
            return MatchResult.FUZZY_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        num1 = self._normalize_numeric(value1)
        num2 = self._normalize_numeric(value2)

        # Both null = both correctly empty = perfect match
        if num1 is None and num2 is None:
            return 1.0

        # One null, one not = mismatch = no similarity
        if num1 is None or num2 is None:
            return 0.0

        if num1 == num2:
            return 1.0

        bucket1 = self._get_bucket(num1)
        bucket2 = self._get_bucket(num2)

        if bucket1 == bucket2:
            return 0.9

        # Score decays based on bucket distance
        bucket_diff = abs(bucket1 - bucket2)
        return max(0.0, 0.9 - (bucket_diff * 0.1))
