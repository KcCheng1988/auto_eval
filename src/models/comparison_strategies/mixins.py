from typing import Optional, Any
import re

try:
    from .utils import is_null_like
except ImportError:
    from src.models.comparison_strategies.utils import is_null_like


class FieldNamePreprocessingMixin:
    """Mixin for consistent field name preprocessing across the application"""

    @staticmethod
    def clean_field_name(field_name: Any) -> str:
        """
        Clean and normalize field name

        Operations performed:
        1. Convert to string
        2. Strip leading/trailing whitespace
        3. Remove newlines (\\n) and carriage returns (\\r)
        4. Remove tabs (\\t)
        5. Collapse multiple spaces into single space

        Args:
            field_name: Raw field name (can be any type)

        Returns:
            Cleaned field name string

        Examples:
            >>> FieldNamePreprocessingMixin.clean_field_name('  customer_name  ')
            'customer_name'
            >>> FieldNamePreprocessingMixin.clean_field_name('customer\\nname')
            'customer name'
            >>> FieldNamePreprocessingMixin.clean_field_name('customer    name')
            'customer name'
        """
        if field_name is None:
            return ''

        # Convert to string and strip whitespace
        cleaned = str(field_name).strip()

        # Replace newlines, carriage returns, and tabs with space
        cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Collapse multiple spaces into single space
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned

    @staticmethod
    def clean_field_names_in_list(field_names: list) -> list:
        """
        Clean multiple field names

        Args:
            field_names: List of raw field names

        Returns:
            List of cleaned field names

        Examples:
            >>> FieldNamePreprocessingMixin.clean_field_names_in_list(['  name  ', 'age\\n'])
            ['name', 'age']
        """
        return [FieldNamePreprocessingMixin.clean_field_name(fn) for fn in field_names]


class StringNormalizationMixin:
    """Mixin providing common string normalization functionality"""

    def __init__(
        self,
        case_sensitive: bool = False,
        trim_whitespace: bool = True,
        normalize_unicode: bool = True,
        ignore_punctuation: bool = False,
        strip_line_breaks: bool = True,
        **kwargs, # Allow subclasses to pass additional parameters
    ):
        self.case_sensitive = case_sensitive
        self.trim_whitespace = trim_whitespace
        self.normalize_unicode = normalize_unicode
        self.ignore_punctuation = ignore_punctuation
        self.strip_line_breaks = strip_line_breaks
        super().__init__(**kwargs)  # Pass other parameters to the next class in the MRO

    def normalize_string(self, value: Any) -> Optional[str]:
        """
        Normalize a string value based on configuration

        Args:
            value: Value to normalize

        Returns:
            Normalized string or None if value is None/empty/null-like
        """
        # Check for null-like values
        if is_null_like(value):
            return None

        result = str(value)

        # Strip line breaks
        if self.strip_line_breaks:
            result = result.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            # Callapse multiple spaces into one
            import re
            result = re.sub(r'\s+', ' ', result)
        
        # Trim whitespace
        if self.trim_whitespace:
            result = result.strip()
        
        # Case normalization
        if not self.case_sensitive:
            result = result.lower()

        # Unicode normalization
        if self.normalize_unicode:
            import unicodedata
            result = unicodedata.normalize('NFKD', result)
            # Example: "café" -> "cafe", "x²" -> "x2"
            result = ''.join([c for c in result if not unicodedata.combining(c)])
        
        # Remove punctuation
        if self.ignore_punctuation:
            import string
            # Apply translation table to the result:
            # 1. Nothing to replace, hence empty strings in the first two arguments
            # 2. Delete any punctuation in the third argument
            result = result.translate(str.maketrans('', '', string.punctuation))
        
        return result if result else None