"""Cell-level preprocessing functions for various data types"""

import re
from typing import Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# NUMERIC PREPROCESSING
# ============================================================================

def clean_numeric(value: Any, decimal_places: Optional[int] = None) -> Optional[float]:
    """
    Convert various numeric formats to consistent float values

    Handles:
    - Comma-separated numbers: '1,000.50' -> 1000.50
    - Percentages: '50%' -> 50.0 or 0.50 (based on keep_percentage_as_100)
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

        # Note: We keep percentage as-is (e.g., 50% -> 50.0, not 0.50)
        # This is more intuitive for most use cases

        return round(result, decimal_places) if decimal_places is not None else result

    except (ValueError, TypeError):
        logger.debug(f"Could not convert '{value}' to numeric")
        return None


# ============================================================================
# DATE/TIME PREPROCESSING
# ============================================================================

def clean_date(value: Any, output_format: str = '%Y-%m-%d',
               datetime_output_format: str = '%Y-%m-%d %H:%M:%S') -> Optional[str]:
    """
    Convert various date/datetime formats to consistent string format

    Handles:
    - Common date formats: '07-Nov-2024', '11/07/2024', '2024-11-07'
    - Datetime formats: '07-Nov-2024 15:00:10'
    - Excel serial dates
    - ISO formats

    Args:
        value: Input date/datetime value
        output_format: Format for date-only values (default: YYYY-MM-DD)
        datetime_output_format: Format for datetime values (default: YYYY-MM-DD HH:MM:SS)

    Returns:
        Formatted date string or None if cannot convert
    """
    if value is None or value == '' or (isinstance(value, float) and str(value).lower() == 'nan'):
        return None

    # Already a datetime object
    if isinstance(value, datetime):
        # Check if it has time component
        if value.hour == 0 and value.minute == 0 and value.second == 0:
            return value.strftime(output_format)
        else:
            return value.strftime(datetime_output_format)

    # Handle pandas Timestamp
    try:
        import pandas as pd
        if isinstance(value, pd.Timestamp):
            if value.hour == 0 and value.minute == 0 and value.second == 0:
                return value.strftime(output_format)
            else:
                return value.strftime(datetime_output_format)
    except ImportError:
        pass

    value_str = str(value).strip()

    if not value_str or value_str.lower() in ['none', 'null', 'n/a', 'na', '-']:
        return None

    # Common date formats to try
    date_formats = [
        '%d-%b-%Y',           # 07-Nov-2024
        '%d-%b-%Y %H:%M:%S',  # 07-Nov-2024 15:00:10
        '%d-%b-%Y %H:%M',     # 07-Nov-2024 15:00
        '%Y-%m-%d',           # 2024-11-07
        '%Y-%m-%d %H:%M:%S',  # 2024-11-07 15:00:10
        '%Y-%m-%d %H:%M',     # 2024-11-07 15:00
        '%d/%m/%Y',           # 07/11/2024
        '%m/%d/%Y',           # 11/07/2024
        '%d/%m/%Y %H:%M:%S',  # 07/11/2024 15:00:10
        '%m/%d/%Y %H:%M:%S',  # 11/07/2024 15:00:10
        '%d.%m.%Y',           # 07.11.2024
        '%Y/%m/%d',           # 2024/11/07
        '%d %b %Y',           # 07 Nov 2024
        '%d %B %Y',           # 07 November 2024
        '%b %d, %Y',          # Nov 07, 2024
        '%B %d, %Y',          # November 07, 2024
    ]

    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(value_str, fmt)

            # Check if it has time component
            if '%H' in fmt or '%M' in fmt or '%S' in fmt:
                return parsed_date.strftime(datetime_output_format)
            else:
                return parsed_date.strftime(output_format)

        except ValueError:
            continue

    logger.debug(f"Could not convert '{value}' to date")
    return None


def is_potential_date(value: Any) -> bool:
    """
    Check if a value might be a date/datetime

    Args:
        value: Value to check

    Returns:
        True if value looks like a date
    """
    if value is None or value == '':
        return False

    if isinstance(value, datetime):
        return True

    try:
        import pandas as pd
        if isinstance(value, pd.Timestamp):
            return True
    except ImportError:
        pass

    value_str = str(value).strip()

    # Common date patterns
    date_patterns = [
        r'\d{1,2}[-/\.]\w{3}[-/\.]\d{4}',  # 07-Nov-2024
        r'\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}',  # 2024-11-07
        r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4}',  # 07/11/2024
        r'\w{3}\s+\d{1,2},\s+\d{4}',  # Nov 07, 2024
        r'\d{1,2}\s+\w+\s+\d{4}',  # 07 November 2024
    ]

    for pattern in date_patterns:
        if re.search(pattern, value_str):
            return True

    return False


# ============================================================================
# STRING PREPROCESSING
# ============================================================================

def clean_string(value: Any, lowercase: bool = True, strip_whitespace: bool = True,
                remove_extra_spaces: bool = True) -> Optional[str]:
    """
    Clean and standardize string values

    Args:
        value: Input value
        lowercase: Convert to lowercase
        strip_whitespace: Strip leading/trailing whitespace
        remove_extra_spaces: Replace multiple spaces with single space

    Returns:
        Cleaned string or None
    """
    if value is None or (isinstance(value, float) and str(value).lower() == 'nan'):
        return None

    # Convert to string
    value_str = str(value)

    # Handle special null-like values (case insensitive)
    if value_str.strip().lower() in ['none', 'null', 'n/a', 'na', '-', 'nan', '']:
        return None

    if strip_whitespace:
        value_str = value_str.strip()

    if remove_extra_spaces:
        value_str = re.sub(r'\s+', ' ', value_str)

    if lowercase:
        value_str = value_str.lower()

    return value_str if value_str else None


# ============================================================================
# ADDRESS PREPROCESSING
# ============================================================================

def clean_address(address_parts: dict, country_code: Optional[str] = None) -> dict:
    """
    Standardize address components

    Expected address_parts keys:
    - unit: Unit/apartment number
    - street: Street name and number
    - city: City name
    - state: State/province
    - country: Country name
    - postal_code: Postal/ZIP code

    Args:
        address_parts: Dictionary with address components
        country_code: Optional country code for country-specific formatting

    Returns:
        Standardized address dictionary
    """
    cleaned = {}

    # Clean each component
    for key in ['unit', 'street', 'city', 'state', 'country', 'postal_code']:
        value = address_parts.get(key)
        if value:
            cleaned_value = clean_string(value, lowercase=False)
            if cleaned_value:
                cleaned[key] = cleaned_value

    # Standardize postal code format
    if 'postal_code' in cleaned:
        postal = cleaned['postal_code'].replace(' ', '').replace('-', '')

        # Country-specific formatting
        if country_code:
            if country_code.upper() == 'US':
                # US ZIP: 12345 or 12345-6789
                if len(postal) == 5:
                    cleaned['postal_code'] = postal
                elif len(postal) == 9:
                    cleaned['postal_code'] = f"{postal[:5]}-{postal[5:]}"
            elif country_code.upper() == 'UK':
                # UK postcode format
                cleaned['postal_code'] = postal.upper()
            elif country_code.upper() == 'SG':
                # Singapore postal code: 6 digits
                if postal.isdigit() and len(postal) == 6:
                    cleaned['postal_code'] = postal
        else:
            cleaned['postal_code'] = postal

    return cleaned


def format_full_address(address_parts: dict, country_code: Optional[str] = None) -> str:
    """
    Format address parts into a full address string

    Args:
        address_parts: Dictionary with address components
        country_code: Optional country code for country-specific formatting

    Returns:
        Formatted full address string
    """
    cleaned = clean_address(address_parts, country_code)

    # Order: unit, street, city, state, postal_code, country
    components = []

    if 'unit' in cleaned:
        components.append(f"Unit {cleaned['unit']}")

    if 'street' in cleaned:
        components.append(cleaned['street'])

    city_state_zip = []
    if 'city' in cleaned:
        city_state_zip.append(cleaned['city'])
    if 'state' in cleaned:
        city_state_zip.append(cleaned['state'])
    if 'postal_code' in cleaned:
        city_state_zip.append(cleaned['postal_code'])

    if city_state_zip:
        components.append(' '.join(city_state_zip))

    if 'country' in cleaned:
        components.append(cleaned['country'])

    return ', '.join(components)


# ============================================================================
# TYPE DETECTION AND CONVERSION
# ============================================================================

def detect_and_convert_type(value: Any, prefer_numeric: bool = True) -> Any:
    """
    Automatically detect type and convert value

    Priority order:
    1. None/null values -> None
    2. Numeric values -> float
    3. Date values -> formatted date string
    4. String values -> cleaned string

    Args:
        value: Input value
        prefer_numeric: Try numeric conversion before date conversion

    Returns:
        Converted value in appropriate type
    """
    # Try None first
    if value is None or value == '' or (isinstance(value, float) and str(value).lower() == 'nan'):
        return None

    value_str = str(value).strip()
    if value_str.lower() in ['none', 'null', 'n/a', 'na', '-']:
        return None

    if prefer_numeric:
        # Try numeric first
        numeric_result = clean_numeric(value)
        if numeric_result is not None:
            return numeric_result

        # Try date
        if is_potential_date(value):
            date_result = clean_date(value)
            if date_result is not None:
                return date_result
    else:
        # Try date first
        if is_potential_date(value):
            date_result = clean_date(value)
            if date_result is not None:
                return date_result

        # Try numeric
        numeric_result = clean_numeric(value)
        if numeric_result is not None:
            return numeric_result

    # Fall back to string
    return clean_string(value, lowercase=True)


# ============================================================================
# ADDITIONAL UTILITIES
# ============================================================================

def clean_column_name(column_name: Any) -> str:
    """
    Clean and standardize column names

    Args:
        column_name: Column name to clean

    Returns:
        Cleaned column name
    """
    if column_name is None:
        return 'unnamed'

    name = str(column_name).strip()

    # Replace special characters with underscores
    name = re.sub(r'[^\w\s]', '_', name)

    # Replace whitespace with underscores
    name = re.sub(r'\s+', '_', name)

    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    # Convert to lowercase
    name = name.lower()

    # Handle empty result
    if not name or name == 'unnamed':
        return 'unnamed'

    return name
