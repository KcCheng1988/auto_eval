"""Test suite for FieldClassifier"""

import pytest
import pandas as pd
from src.analysers.field_classifier import FieldClassifier, FieldType


@pytest.fixture
def classifier():
    """Fixture to create FieldClassifier instance"""
    return FieldClassifier()


@pytest.fixture
def sample_name_data():
    """Sample data for name field testing"""
    return {
        'field_name': ['customer_name'] * 5,
        'field_value': ['John Smith', 'Jane Doe', 'Robert Brown', 'Alice Johnson', 'Bob Wilson']
    }


@pytest.fixture
def sample_date_data():
    """Sample data for date field testing"""
    return {
        'field_name': ['date_of_birth'] * 4,
        'field_value': ['1990-05-15', '1985-12-20', '1992-08-10', '1988-03-25']
    }


@pytest.fixture
def sample_numeric_data():
    """Sample data for numeric field testing"""
    return {
        'field_name': ['contract_amount'] * 5,
        'field_value': ['15,000', '$25,500.50', '(1,000)', '30000.00', '12,345']
    }


@pytest.fixture
def sample_datetime_data():
    """Sample data for datetime field testing"""
    return {
        'field_name': ['created_at'] * 4,
        'field_value': [
            '2024-01-15 10:30:00',
            '2024-02-20 14:45:30',
            '2024-03-10 09:15:00',
            '2024-04-05 16:20:15'
        ]
    }


@pytest.fixture
def sample_string_data():
    """Sample data for string field testing"""
    return {
        'field_name': ['email_address'] * 4,
        'field_value': [
            'john@example.com',
            'jane@example.com',
            'robert@example.com',
            'alice@example.com'
        ]
    }


@pytest.fixture
def mixed_data(sample_name_data, sample_date_data, sample_numeric_data):
    """Combined sample data with multiple field types"""
    data = {
        'field_name': (
            sample_name_data['field_name'] +
            sample_date_data['field_name'] +
            sample_numeric_data['field_name']
        ),
        'field_value': (
            sample_name_data['field_value'] +
            sample_date_data['field_value'] +
            sample_numeric_data['field_value']
        )
    }
    return pd.DataFrame(data)


class TestFieldClassifierInitialization:
    """Test FieldClassifier initialization"""

    def test_classifier_creation(self, classifier):
        """Test that classifier can be created"""
        assert classifier is not None
        assert isinstance(classifier, FieldClassifier)

    def test_classifier_has_keywords(self, classifier):
        """Test that classifier has keyword lists"""
        assert hasattr(classifier, 'name_keywords')
        assert hasattr(classifier, 'date_keywords')
        assert hasattr(classifier, 'numeric_keywords')
        assert len(classifier.name_keywords) > 0
        assert len(classifier.date_keywords) > 0


class TestFieldTypeDetection:
    """Test field type detection"""

    def test_name_field_detection(self, classifier, sample_name_data):
        """Test detection of name fields"""
        result = classifier.classify_field(
            sample_name_data['field_name'][0],
            sample_name_data['field_value']
        )
        assert result['field_type'] == FieldType.NAME
        assert result['recommended_strategy'] == 'ExactNameMatch'
        assert result['confidence'] > 0.5

    def test_date_field_detection(self, classifier, sample_date_data):
        """Test detection of date fields"""
        result = classifier.classify_field(
            sample_date_data['field_name'][0],
            sample_date_data['field_value']
        )
        assert result['field_type'] == FieldType.DATE
        assert result['recommended_strategy'] == 'DateOnlyMatch'
        assert result['confidence'] > 0.5

    def test_numeric_field_detection(self, classifier, sample_numeric_data):
        """Test detection of numeric fields"""
        result = classifier.classify_field(
            sample_numeric_data['field_name'][0],
            sample_numeric_data['field_value']
        )
        assert result['field_type'] == FieldType.NUMERIC
        assert result['recommended_strategy'] == 'ExactNumericMatch'
        assert result['confidence'] > 0.5

    def test_datetime_field_detection(self, classifier, sample_datetime_data):
        """Test detection of datetime fields"""
        result = classifier.classify_field(
            sample_datetime_data['field_name'][0],
            sample_datetime_data['field_value']
        )
        assert result['field_type'] == FieldType.DATETIME
        assert result['recommended_strategy'] == 'ExactDateTimeMatch'
        assert result['confidence'] > 0.5

    def test_string_field_detection(self, classifier, sample_string_data):
        """Test detection of string fields"""
        result = classifier.classify_field(
            sample_string_data['field_name'][0],
            sample_string_data['field_value']
        )
        # Email addresses should be detected as string
        assert result['field_type'] == FieldType.STRING
        assert result['recommended_strategy'] == 'ExactStringMatch'


class TestDataFrameClassification:
    """Test DataFrame-level classification"""

    def test_classify_dataframe(self, classifier, mixed_data):
        """Test classification of entire DataFrame"""
        result = classifier.classify_dataframe(mixed_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # 3 unique field names
        assert 'field_name' in result.columns
        assert 'field_type' in result.columns
        assert 'confidence' in result.columns
        assert 'recommended_strategy' in result.columns

    def test_dataframe_has_all_fields(self, classifier, mixed_data):
        """Test that all unique fields are classified"""
        result = classifier.classify_dataframe(mixed_data)
        unique_fields = mixed_data['field_name'].unique()
        result_fields = result['field_name'].unique()

        assert len(result_fields) == len(unique_fields)
        for field in unique_fields:
            assert field in result_fields.tolist()

    def test_settings_flattened(self, classifier, sample_name_data):
        """Test that settings are flattened into separate columns"""
        df = pd.DataFrame(sample_name_data)
        result = classifier.classify_dataframe(df)

        # Check that setting columns exist
        setting_columns = [col for col in result.columns if col.startswith('setting_')]
        assert len(setting_columns) > 0

        # For name fields, should have normalization settings
        if 'setting_case_sensitive' in result.columns:
            assert result['setting_case_sensitive'].iloc[0] == False


class TestRecommendedSettings:
    """Test recommended settings generation"""

    def test_name_field_settings(self, classifier, sample_name_data):
        """Test settings for name fields"""
        result = classifier.classify_field(
            sample_name_data['field_name'][0],
            sample_name_data['field_value']
        )
        settings = result['recommended_settings']

        assert 'case_sensitive' in settings
        assert 'trim_whitespace' in settings
        assert 'normalize_unicode' in settings
        assert settings['case_sensitive'] == False
        assert settings['trim_whitespace'] == True

    def test_numeric_field_settings(self, classifier, sample_numeric_data):
        """Test settings for numeric fields"""
        result = classifier.classify_field(
            sample_numeric_data['field_name'][0],
            sample_numeric_data['field_value']
        )
        settings = result['recommended_settings']

        assert 'decimal_precision' in settings
        # Should recommend decimal precision since we have decimal values
        assert settings['decimal_precision'] == 2

    def test_date_field_settings(self, classifier, sample_date_data):
        """Test settings for date fields"""
        result = classifier.classify_field(
            sample_date_data['field_name'][0],
            sample_date_data['field_value']
        )
        settings = result['recommended_settings']

        # Date fields typically have no special settings
        assert isinstance(settings, dict)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_values(self, classifier):
        """Test classification with empty values"""
        result = classifier.classify_field(
            'empty_field',
            [None, None, '', '']
        )
        assert result['field_type'] == FieldType.UNKNOWN
        assert result['confidence'] == 0.0

    def test_mixed_types(self, classifier):
        """Test classification with mixed data types"""
        mixed_values = ['John Smith', '123', '2024-01-01', 'random text']
        result = classifier.classify_field('mixed_field', mixed_values)

        # Should classify as STRING (fallback)
        assert result['field_type'] == FieldType.STRING

    def test_small_sample(self, classifier):
        """Test classification with small sample size"""
        result = classifier.classify_field(
            'small_field',
            ['value1', 'value2']
        )
        # Should still produce a result
        assert 'field_type' in result
        assert 'confidence' in result

    def test_large_sample(self, classifier):
        """Test classification with large sample (should be sampled)"""
        large_sample = [f'name_{i}' for i in range(200)]
        result = classifier.classify_field('large_field', large_sample)

        # Should still complete successfully
        assert 'field_type' in result
        assert result['field_type'] == FieldType.STRING


class TestExcelExport:
    """Test Excel export functionality"""

    def test_save_to_excel(self, classifier, mixed_data, tmp_path):
        """Test saving classification results to Excel"""
        output_path = tmp_path / "test_classification.xlsx"

        # Save to Excel
        classifier.save_classification_to_excel(
            mixed_data,
            str(output_path)
        )

        # Verify file was created
        assert output_path.exists()

        # Read back and verify contents
        result = pd.read_excel(output_path, sheet_name='Field Classification')
        assert len(result) == 3  # 3 unique fields
        assert 'field_name' in result.columns
        assert 'field_type' in result.columns


if __name__ == '__main__':
    # Allow running tests with: python tests/test_field_classifier.py
    pytest.main([__file__, '-v'])
