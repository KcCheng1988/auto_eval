from typing import Optional

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

    def normalize_string(self, value: str) -> Optional[str]:
        """
        Normalize a string value based on configuration

        Args:
            value: Value to normalize
        
        Returns:
            Normalized string or None if value is None/empty
        """
        if value is None:
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