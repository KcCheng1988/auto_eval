"""
Example: Field Classification Workflow

This demonstrates the complete workflow:
1. Classify fields from a DataFrame
2. Save classification to Excel for manual review
3. Load edited configuration and instantiate strategies
"""

import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysers.field_classifier import FieldClassifier
from src.analysers.field_config_loader import FieldConfigLoader


def create_sample_data():
    """Create sample data for demonstration"""
    data = {
        'field_name': [
            'customer_name', 'customer_name', 'customer_name',
            'date_of_birth', 'date_of_birth', 'date_of_birth',
            'contract_amount', 'contract_amount', 'contract_amount',
            'email_address', 'email_address', 'email_address',
            'created_at', 'created_at', 'created_at'
        ],
        'field_value': [
            'John Smith', 'Jane Doe', 'Robert Brown',
            '1990-05-15', '1985-12-20', '1992-08-10',
            '15,000', '$25,500.50', '(1,000)',
            'john@example.com', 'jane@example.com', 'robert@example.com',
            '2024-01-15 10:30:00', '2024-02-20 14:45:30', '2024-03-10 09:15:00'
        ]
    }
    return pd.DataFrame(data)


def main():
    print("=" * 80)
    print("Field Classification Workflow Example")
    print("=" * 80)

    # Step 1: Create sample data
    print("\n1. Creating sample data...")
    df = create_sample_data()
    print(f"   Sample data shape: {df.shape}")
    print(f"\n{df.head(10)}")

    # Step 2: Classify fields
    print("\n2. Classifying fields...")
    classifier = FieldClassifier()
    classification_df = classifier.classify_dataframe(df)

    print(f"\n   Classification results:")
    print(classification_df[['field_name', 'field_type', 'confidence', 'recommended_strategy']])

    # Step 3: Save to Excel
    output_path = 'field_classification.xlsx'
    print(f"\n3. Saving classification to {output_path}...")
    classifier.save_classification_to_excel(df, output_path)

    # Step 4: Load configuration (simulating user edits)
    print(f"\n4. Loading configuration from {output_path}...")
    loader = FieldConfigLoader()

    # Validate first
    validation = loader.validate_configuration(output_path)
    print(f"   Valid: {validation['valid']}")
    print(f"   Total fields: {validation['total_fields']}")

    if validation['errors']:
        print(f"   Errors: {validation['errors']}")

    # Load strategies
    field_strategies = loader.load_from_excel(output_path)
    print(f"\n   Loaded {len(field_strategies)} field strategies:")
    for field_name, strategy in field_strategies.items():
        print(f"   - {field_name}: {strategy.__class__.__name__}")

    # Step 5: Use strategies for comparison (example)
    print("\n5. Example usage of loaded strategies:")

    # Compare customer names
    customer_strategy = field_strategies.get('customer_name')
    if customer_strategy:
        result = customer_strategy.compare('John Smith', 'john smith')
        score = customer_strategy.get_similarity_score('John Smith', 'john smith')
        print(f"   customer_name comparison:")
        print(f"     'John Smith' vs 'john smith': {result.value} (score: {score})")

    # Compare amounts
    amount_strategy = field_strategies.get('contract_amount')
    if amount_strategy:
        result = amount_strategy.compare('15,000', '15000.00')
        score = amount_strategy.get_similarity_score('15,000', '15000.00')
        print(f"   contract_amount comparison:")
        print(f"     '15,000' vs '15000.00': {result.value} (score: {score})")

    # Compare dates
    dob_strategy = field_strategies.get('date_of_birth')
    if dob_strategy:
        result = dob_strategy.compare('1990-05-15', '1990-05-15')
        score = dob_strategy.get_similarity_score('1990-05-15', '1990-05-15')
        print(f"   date_of_birth comparison:")
        print(f"     '1990-05-15' vs '1990-05-15': {result.value} (score: {score})")

    print("\n" + "=" * 80)
    print("Workflow completed successfully!")
    print("=" * 80)
    print(f"\nNext steps:")
    print(f"1. Open {output_path} in Excel")
    print(f"2. Review and edit field types, strategies, and settings")
    print(f"3. Use FieldConfigLoader to load the edited configuration")
    print(f"4. Use the loaded strategies for field matching")


if __name__ == '__main__':
    main()
