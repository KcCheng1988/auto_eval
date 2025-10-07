"""Test null-like value handling across all strategies"""

import pytest
from src.models.comparison_strategies import (
    is_null_like,
    MatchResult,
    ExactNameMatch,
    ExactStringMatch,
    ExactNumericMatch,
    ExactDateTimeMatch,
    DateOnlyMatch
)


class TestNullLikeDetection:
    """Test the is_null_like utility function"""

    def test_none_detection(self):
        """Test None is detected as null-like"""
        assert is_null_like(None) is True

    def test_empty_string_detection(self):
        """Test empty string is detected as null-like"""
        assert is_null_like('') is True
        assert is_null_like('   ') is True  # Whitespace only

    def test_null_string_variations(self):
        """Test various string representations of null"""
        null_strings = [
            'none', 'None', 'NONE',
            'null', 'Null', 'NULL',
            'nil', 'Nil', 'NIL',
            'n/a', 'N/A',
            'na', 'NA',
            'nan', 'NaN', 'NAN',
            '-',
            '#n/a', '#N/A',
            '#na', '#NA',
            'undefined', 'Undefined',
            'empty', 'Empty',
            'missing', 'Missing'
        ]

        for null_str in null_strings:
            assert is_null_like(null_str) is True, f"'{null_str}' should be detected as null-like"

    def test_nan_float_detection(self):
        """Test NaN float is detected as null-like"""
        assert is_null_like(float('nan')) is True

    def test_non_null_values(self):
        """Test that valid values are NOT detected as null-like"""
        valid_values = [
            'John Smith',
            '123',
            '2024-01-01',
            0,
            False,  # Important: False should NOT be null
            'actual data'
        ]

        for value in valid_values:
            assert is_null_like(value) is False, f"'{value}' should NOT be null-like"


class TestNullHandlingInStrategies:
    """Test that all strategies properly handle null-like values"""

    @pytest.fixture
    def null_values(self):
        """Fixture providing various null-like values"""
        return [None, '', 'null', 'None', 'n/a', 'NA', '-', '#N/A', float('nan')]

    def test_name_strategy_null_handling(self, null_values):
        """Test name strategies handle null values"""
        strategy = ExactNameMatch()

        for null_val in null_values:
            # Comparing null with null should return MISSING_DATA
            result = strategy.compare(null_val, null_val)
            assert result == MatchResult.MISSING_DATA, f"Failed for value: {null_val}"

            # Comparing null with valid value should return MISSING_DATA
            result = strategy.compare(null_val, 'John Smith')
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare('John Smith', null_val)
            assert result == MatchResult.MISSING_DATA

    def test_string_strategy_null_handling(self, null_values):
        """Test string strategies handle null values"""
        strategy = ExactStringMatch()

        for null_val in null_values:
            result = strategy.compare(null_val, null_val)
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare(null_val, 'valid text')
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare('valid text', null_val)
            assert result == MatchResult.MISSING_DATA

    def test_numeric_strategy_null_handling(self, null_values):
        """Test numeric strategies handle null values"""
        strategy = ExactNumericMatch()

        for null_val in null_values:
            result = strategy.compare(null_val, null_val)
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare(null_val, 100)
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare(100, null_val)
            assert result == MatchResult.MISSING_DATA

    def test_date_strategy_null_handling(self, null_values):
        """Test date strategies handle null values"""
        strategy = DateOnlyMatch()

        for null_val in null_values:
            result = strategy.compare(null_val, null_val)
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare(null_val, '2024-01-01')
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare('2024-01-01', null_val)
            assert result == MatchResult.MISSING_DATA

    def test_datetime_strategy_null_handling(self, null_values):
        """Test datetime strategies handle null values"""
        strategy = ExactDateTimeMatch()

        for null_val in null_values:
            result = strategy.compare(null_val, null_val)
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare(null_val, '2024-01-01 10:00:00')
            assert result == MatchResult.MISSING_DATA

            result = strategy.compare('2024-01-01 10:00:00', null_val)
            assert result == MatchResult.MISSING_DATA


class TestNullVsActualMinus:
    """Test that actual '-' symbols in data are distinguished from null '-'"""

    def test_minus_in_numeric_context(self):
        """Standalone '-' is null, but '-100' is a valid negative number"""
        strategy = ExactNumericMatch()

        # Standalone '-' should be null
        assert strategy.compare('-', 100) == MatchResult.MISSING_DATA

        # '-100' should be valid negative number
        assert strategy.compare('-100', -100) == MatchResult.EXACT_MATCH
        assert strategy.compare('-100', '-100.00') == MatchResult.EXACT_MATCH

    def test_minus_in_string_context(self):
        """Standalone '-' is null, but '-' as part of text is valid"""
        strategy = ExactStringMatch()

        # Standalone '-' should be null
        assert strategy.compare('-', 'text') == MatchResult.MISSING_DATA

        # '-' as part of text should be valid
        assert strategy.compare('well-known', 'well-known') == MatchResult.EXACT_MATCH


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
