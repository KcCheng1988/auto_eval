"""Comparison strategies for datetime fields"""

from typing import Any, Optional
from datetime import datetime, timedelta
from .base import ComparisonStrategy, MatchResult
from .mixins import StringNormalizationMixin
from .utils import DateTimeConverter


# ============================================================================
# DATETIME COMPARISON STRATEGIES
# ============================================================================

class ExactDateTimeStringMatch(StringNormalizationMixin, ComparisonStrategy):
    """
    Treat datetime as string and do exact match after normalization

    This is useful when you want to compare datetime values as strings
    without parsing them, ensuring the exact format is preserved.
    """

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare datetime values as normalized strings

        Args:
            value1: First datetime value (any type)
            value2: Second datetime value (any type)

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


class ExactDateTimeMatch(ComparisonStrategy):
    """
    Parse and compare datetime objects for exact match

    This converts both values to datetime objects and compares them,
    ignoring string formatting differences.
    """

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare datetime values as datetime objects

        Args:
            value1: First datetime value
            value2: Second datetime value

        Returns:
            MatchResult indicating exact match or not
        """
        dt1 = DateTimeConverter.to_datetime(value1)
        dt2 = DateTimeConverter.to_datetime(value2)

        if dt1 is None or dt2 is None:
            return MatchResult.MISSING_DATA

        if dt1 == dt2:
            return MatchResult.EXACT_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        return 1.0 if self.compare(value1, value2) == MatchResult.EXACT_MATCH else 0.0


class ToleranceDateTimeMatch(ComparisonStrategy):
    """
    Compare datetime objects with tolerance (within N seconds/minutes/hours)

    Allows for small differences in datetime values, useful when comparing
    timestamps that may have slight variations.
    """

    def __init__(self, tolerance_seconds: int = 60, **kwargs):
        """
        Initialize with tolerance threshold

        Args:
            tolerance_seconds: Maximum allowed difference in seconds (default: 60)
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.tolerance_seconds = tolerance_seconds

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare datetime values with tolerance

        Args:
            value1: First datetime value
            value2: Second datetime value

        Returns:
            MatchResult based on tolerance threshold
        """
        dt1 = DateTimeConverter.to_datetime(value1)
        dt2 = DateTimeConverter.to_datetime(value2)

        if dt1 is None or dt2 is None:
            return MatchResult.MISSING_DATA

        # Calculate absolute difference
        diff = abs((dt1 - dt2).total_seconds())

        if diff == 0:
            return MatchResult.EXACT_MATCH
        elif diff <= self.tolerance_seconds:
            return MatchResult.FUZZY_MATCH
        else:
            return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        dt1 = DateTimeConverter.to_datetime(value1)
        dt2 = DateTimeConverter.to_datetime(value2)

        if dt1 is None or dt2 is None:
            return 0.0

        diff = abs((dt1 - dt2).total_seconds())

        if diff == 0:
            return 1.0
        elif diff <= self.tolerance_seconds:
            # Linear decay within tolerance window
            return 1.0 - (diff / self.tolerance_seconds) * 0.15
        else:
            return 0.0


class DateOnlyMatch(ComparisonStrategy):
    """
    Compare only the date portion, ignoring time

    Useful when time component is not relevant or may vary.
    """

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare only date portions of datetime values

        Args:
            value1: First datetime value
            value2: Second datetime value

        Returns:
            MatchResult based on date-only comparison
        """
        date1 = DateTimeConverter.to_date(value1)
        date2 = DateTimeConverter.to_date(value2)

        if date1 is None or date2 is None:
            return MatchResult.MISSING_DATA

        if date1 == date2:
            return MatchResult.EXACT_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        return 1.0 if self.compare(value1, value2) == MatchResult.EXACT_MATCH else 0.0


class TimeOnlyMatch(ComparisonStrategy):
    """
    Compare only the time portion, ignoring date

    Useful for scheduled times that recur regardless of date.
    """

    def __init__(self, tolerance_seconds: int = 0, **kwargs):
        """
        Initialize with optional tolerance

        Args:
            tolerance_seconds: Maximum allowed difference in time (default: 0)
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.tolerance_seconds = tolerance_seconds

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare only time portions of datetime values

        Args:
            value1: First datetime value
            value2: Second datetime value

        Returns:
            MatchResult based on time-only comparison
        """
        dt1 = DateTimeConverter.to_datetime(value1)
        dt2 = DateTimeConverter.to_datetime(value2)

        if dt1 is None or dt2 is None:
            return MatchResult.MISSING_DATA

        # Extract time components
        time1 = dt1.time()
        time2 = dt2.time()

        # Convert times to seconds for comparison
        seconds1 = time1.hour * 3600 + time1.minute * 60 + time1.second
        seconds2 = time2.hour * 3600 + time2.minute * 60 + time2.second

        diff = abs(seconds1 - seconds2)

        if diff == 0:
            return MatchResult.EXACT_MATCH
        elif diff <= self.tolerance_seconds:
            return MatchResult.FUZZY_MATCH
        else:
            return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        dt1 = DateTimeConverter.to_datetime(value1)
        dt2 = DateTimeConverter.to_datetime(value2)

        if dt1 is None or dt2 is None:
            return 0.0

        time1 = dt1.time()
        time2 = dt2.time()

        seconds1 = time1.hour * 3600 + time1.minute * 60 + time1.second
        seconds2 = time2.hour * 3600 + time2.minute * 60 + time2.second

        diff = abs(seconds1 - seconds2)

        if diff == 0:
            return 1.0
        elif self.tolerance_seconds > 0 and diff <= self.tolerance_seconds:
            return 1.0 - (diff / self.tolerance_seconds) * 0.15
        else:
            # # Time differences beyond tolerance decay quickly
            # max_diff = 43200  # 12 hours in seconds
            # return max(0.0, 0.85 * (1 - diff / max_diff))
            return 0.0


class DateTimeRangeMatch(ComparisonStrategy):
    """
    Check if datetime values fall within same date range/bucket

    Useful for grouping events by time periods (same hour, day, week, etc.)
    """

    def __init__(self, granularity: str = "day", **kwargs):
        """
        Initialize with time granularity

        Args:
            granularity: Time bucket - "hour", "day", "week", "month", "year" (default: "day")
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        valid_granularities = ["hour", "day", "week", "month", "year"]
        if granularity not in valid_granularities:
            raise ValueError(f"granularity must be one of {valid_granularities}")
        self.granularity = granularity

    def _get_bucket(self, dt: datetime) -> tuple:
        """Get the time bucket for a datetime"""
        if self.granularity == "hour":
            return (dt.year, dt.month, dt.day, dt.hour)
        elif self.granularity == "day":
            return (dt.year, dt.month, dt.day)
        elif self.granularity == "week":
            return (dt.year, dt.isocalendar()[1])  # ISO week number
        elif self.granularity == "month":
            return (dt.year, dt.month)
        elif self.granularity == "year":
            return (dt.year,)

    def compare(self, value1: Any, value2: Any) -> MatchResult:
        """
        Compare datetime values by time bucket

        Args:
            value1: First datetime value
            value2: Second datetime value

        Returns:
            MatchResult based on whether values fall in same bucket
        """
        dt1 = DateTimeConverter.to_datetime(value1)
        dt2 = DateTimeConverter.to_datetime(value2)

        if dt1 is None or dt2 is None:
            return MatchResult.MISSING_DATA

        bucket1 = self._get_bucket(dt1)
        bucket2 = self._get_bucket(dt2)

        if bucket1 == bucket2:
            return MatchResult.EXACT_MATCH

        return MatchResult.NO_MATCH

    def get_similarity_score(self, value1: Any, value2: Any) -> float:
        return 1.0 if self.compare(value1, value2) == MatchResult.EXACT_MATCH else 0.0
