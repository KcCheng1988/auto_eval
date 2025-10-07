"""Utility functions and classes for comparison strategies"""

import re
from datetime import date, datetime, timedelta
from typing import Any, Optional


class DateTimeConverter:
    """Shared utilities for converting values to date/datetime objects"""

    @staticmethod
    def to_date(value: Any) -> Optional[date]:
        """
        Convert various formats to date object

        Args:
            value: Value to convert (date, datetime, string, Excel serial)

        Returns:
            date object or None if conversion fails
        """
        if value is None:
            return None

        # Already a date (but not datetime)
        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        # datetime -> date
        if isinstance(value, datetime):
            return value.date()

        # String -> date
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            # Try ISO format first
            try:
                return datetime.fromisoformat(value).date()
            except (ValueError, TypeError):
                pass

            # Try dateutil parser
            try:
                from dateutil import parser
                return parser.parse(value).date()
            except (ValueError, TypeError, ImportError):
                return None

        # Excel serial date (number of days since 1899-12-30)
        if isinstance(value, (int, float)):
            try:
                return date(1899, 12, 30) + timedelta(days=value)
            except (ValueError, OverflowError):
                return None

        return None

    @staticmethod
    def to_datetime(value: Any) -> Optional[datetime]:
        """
        Convert various formats to datetime object

        Args:
            value: Value to convert (datetime, date, string, Excel serial)

        Returns:
            datetime object or None if conversion fails
        """
        if value is None:
            return None

        # Already a datetime
        if isinstance(value, datetime):
            return value

        # date -> datetime (at midnight)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        # String -> datetime
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            # Try ISO format first
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass

            # Try dateutil parser
            try:
                from dateutil import parser
                return parser.parse(value)
            except (ValueError, TypeError, ImportError):
                return None

        # Excel serial datetime (number of days since 1899-12-30, with fractional days for time)
        if isinstance(value, (int, float)):
            try:
                base_date = datetime(1899, 12, 30)
                return base_date + timedelta(days=value)
            except (ValueError, OverflowError):
                return None

        return None


class NumericConverter:
    """Shared utilities for converting values to numeric types"""

    @staticmethod
    def to_float(value: Any, decimal_places: Optional[int] = None) -> Optional[float]:
        """
        Convert various numeric formats to float

        Handles:
        - Comma-separated numbers: '1,000.50' -> 1000.50
        - Percentages: '50%' -> 50.0
        - Parentheses for negatives: '(100)' -> -100.0
        - Currency symbols: '$1,000' -> 1000.0
        - String numbers: '123' -> 123.0
        - Actual numeric types: 123 -> 123.0

        Args:
            value: Input value to convert
            decimal_places: Optional number of decimal places to round to

        Returns:
            Float value or None if cannot convert
        """
        # Handle None, NaN, empty strings
        if value is None or value == '' or (isinstance(value, float) and str(value).lower() == 'nan'):
            return None

        # Already a number
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            result = float(value)
            return round(result, decimal_places) if decimal_places is not None else result

        # Convert to string for processing
        value_str = str(value).strip()

        if not value_str or value_str.lower() in ['none', 'null', 'n/a', 'na', '-', '#n/a']:
            return None

        # Handle percentage (keep as percentage value, not decimal)
        is_percentage = '%' in value_str
        value_str = value_str.replace('%', '')

        # Handle parentheses (accounting notation for negatives)
        is_negative = False
        if value_str.startswith('(') and value_str.endswith(')'):
            is_negative = True
            value_str = value_str[1:-1]

        # Remove currency symbols and spaces
        value_str = re.sub(r'[$£€¥₹]', '', value_str)
        value_str = value_str.replace(' ', '')

        # Remove thousand separators (commas)
        value_str = value_str.replace(',', '')

        # Try to convert
        try:
            result = float(value_str)

            if is_negative:
                result = -result

            return round(result, decimal_places) if decimal_places is not None else result

        except (ValueError, TypeError):
            return None

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        """
        Convert various numeric formats to integer

        Args:
            value: Input value to convert

        Returns:
            Integer value or None if cannot convert
        """
        float_value = NumericConverter.to_float(value)

        if float_value is None:
            return None

        # Check if it's close to an integer
        if abs(float_value - round(float_value)) < 1e-9:
            return int(round(float_value))

        return None

    @staticmethod
    def is_numeric(value: Any) -> bool:
        """
        Check if a value can be converted to a number

        Args:
            value: Value to check

        Returns:
            True if value can be converted to numeric
        """
        return NumericConverter.to_float(value) is not None
