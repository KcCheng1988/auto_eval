"""Test field name preprocessing mixin"""

import pytest
from src.models.comparison_strategies.mixins import FieldNamePreprocessingMixin


class TestFieldNamePreprocessing:
    """Test FieldNamePreprocessingMixin functionality"""

    def test_strip_leading_trailing_spaces(self):
        """Test removal of leading/trailing spaces"""
        result = FieldNamePreprocessingMixin.clean_field_name('  customer_name  ')
        assert result == 'customer_name'

    def test_remove_newlines(self):
        """Test removal of newline characters"""
        result = FieldNamePreprocessingMixin.clean_field_name('customer\nname')
        assert result == 'customer name'

    def test_remove_carriage_returns(self):
        """Test removal of carriage return characters"""
        result = FieldNamePreprocessingMixin.clean_field_name('customer\rname')
        assert result == 'customer name'

    def test_remove_tabs(self):
        """Test removal of tab characters"""
        result = FieldNamePreprocessingMixin.clean_field_name('customer\tname')
        assert result == 'customer name'

    def test_collapse_multiple_spaces(self):
        """Test collapsing multiple spaces into one"""
        result = FieldNamePreprocessingMixin.clean_field_name('customer    name')
        assert result == 'customer name'

    def test_combined_cleaning(self):
        """Test combined cleaning operations"""
        result = FieldNamePreprocessingMixin.clean_field_name('  customer\n\r  name  \t')
        assert result == 'customer name'

    def test_none_value(self):
        """Test handling None value"""
        result = FieldNamePreprocessingMixin.clean_field_name(None)
        assert result == ''

    def test_empty_string(self):
        """Test handling empty string"""
        result = FieldNamePreprocessingMixin.clean_field_name('')
        assert result == ''

    def test_whitespace_only(self):
        """Test field name with only whitespace"""
        result = FieldNamePreprocessingMixin.clean_field_name('   ')
        assert result == ''

    def test_numeric_input(self):
        """Test numeric input converted to string"""
        result = FieldNamePreprocessingMixin.clean_field_name(123)
        assert result == '123'

    def test_clean_field_names_in_list(self):
        """Test cleaning multiple field names"""
        input_list = [
            '  name  ',
            'age\n',
            'customer\taddress',
            None,
            'status'
        ]
        result = FieldNamePreprocessingMixin.clean_field_names_in_list(input_list)

        assert result == ['name', 'age', 'customer address', '', 'status']

    def test_preserves_underscores(self):
        """Test that underscores are preserved"""
        result = FieldNamePreprocessingMixin.clean_field_name('customer_name')
        assert result == 'customer_name'

    def test_preserves_hyphens(self):
        """Test that hyphens are preserved"""
        result = FieldNamePreprocessingMixin.clean_field_name('first-name')
        assert result == 'first-name'


class TestMixinUsage:
    """Test mixin usage in classes"""

    def test_mixin_in_class(self):
        """Test that mixin can be used in a class"""

        class TestClass(FieldNamePreprocessingMixin):
            def process_field(self, field_name):
                return self.clean_field_name(field_name)

        obj = TestClass()
        result = obj.process_field('  test\nfield  ')
        assert result == 'test field'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
