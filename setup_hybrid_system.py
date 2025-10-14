"""
Setup script for SQLite + S3 Hybrid System
Run this to initialize your evaluation system with local SQLite and S3 storage
"""

import os
import sys
import sqlite3
from pathlib import Path


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Checking Dependencies")

    missing = []

    # Check sqlite3 (built-in)
    try:
        import sqlite3
        print("✅ sqlite3 available (built-in)")
    except ImportError:
        missing.append("sqlite3 (should be built-in)")

    # Check boto3
    try:
        import boto3
        print(f"✅ boto3 installed (version: {boto3.__version__})")
    except ImportError:
        missing.append("boto3")
        print("❌ boto3 not installed")

    if missing:
        print("\n⚠️  Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nInstall missing dependencies:")
        print("   pip install boto3")
        return False

    return True


def get_s3_credentials():
    """Get S3 credentials from user"""
    print_section("S3 Configuration")

    print("Enter your S3 bucket details:")
    print("(You can also set these as environment variables later)\n")

    bucket_name = input("S3 Bucket Name: ").strip()
    if not bucket_name:
        print("❌ Bucket name is required!")
        sys.exit(1)

    region = input("AWS Region [us-east-1]: ").strip()
    if not region:
        region = "us-east-1"

    print("\nAWS Credentials:")
    print("(Leave blank if using IAM role or env variables)")

    access_key = input("AWS Access Key ID (optional): ").strip()
    secret_key = input("AWS Secret Access Key (optional): ").strip()

    return {
        'bucket_name': bucket_name,
        'region': region,
        'access_key': access_key if access_key else None,
        'secret_key': secret_key if secret_key else None
    }


def test_s3_connection(s3_config):
    """Test S3 connection"""
    print_section("Testing S3 Connection")

    try:
        import boto3

        session_kwargs = {'region_name': s3_config['region']}
        if s3_config['access_key'] and s3_config['secret_key']:
            session_kwargs['aws_access_key_id'] = s3_config['access_key']
            session_kwargs['aws_secret_access_key'] = s3_config['secret_key']

        s3_client = boto3.client('s3', **session_kwargs)

        # Try to list bucket (check if accessible)
        s3_client.head_bucket(Bucket=s3_config['bucket_name'])

        print(f"✅ Successfully connected to S3 bucket: {s3_config['bucket_name']}")
        return True

    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        print("\nPossible issues:")
        print("  1. Bucket doesn't exist")
        print("  2. Wrong credentials")
        print("  3. No permissions to access bucket")
        print("  4. Wrong region")
        return False


def create_database():
    """Create SQLite database and schema"""
    print_section("Creating SQLite Database")

    db_path = Path.cwd() / 'evaluation_system.db'
    schema_file = Path.cwd() / 'proposed_architecture' / 'database' / 'schema_sqlite.sql'

    # Check if schema file exists
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        print("\nMake sure you're running this from the project root directory.")
        return None

    # Check if database already exists
    if db_path.exists():
        response = input(f"\nDatabase already exists at {db_path}. Overwrite? (yes/no) [no]: ").strip().lower()
        if response != 'yes':
            print("Using existing database.")
            return str(db_path)
        else:
            db_path.unlink()
            print(f"Deleted existing database.")

    try:
        # Create database
        print(f"Creating database at: {db_path}")
        conn = sqlite3.connect(str(db_path))

        # Read and execute schema
        print(f"Reading schema from: {schema_file}")
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        print("Creating tables, indexes, and triggers...")
        conn.executescript(schema_sql)
        conn.commit()

        # Verify tables created
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"\n✅ Created {len(tables)} tables:")
            for (table_name,) in tables:
                # Count columns
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print(f"   • {table_name:25} ({len(columns)} columns)")
        else:
            print("⚠️  No tables found!")
            conn.close()
            return None

        conn.close()
        print(f"\n✅ Database created successfully!")
        return str(db_path)

    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return None


def test_database(db_path):
    """Test database operations"""
    print_section("Testing Database Operations")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test INSERT
        print("1. Testing INSERT...")
        cursor.execute("""
            INSERT INTO use_cases (id, name, team_email, state, created_at, updated_at)
            VALUES ('test-001', 'Test Use Case', 'test@example.com', 'template_generation',
                    datetime('now'), datetime('now'))
        """)
        print("   ✅ Inserted test use case")

        # Test SELECT
        print("\n2. Testing SELECT...")
        cursor.execute("SELECT id, name, state FROM use_cases WHERE id = 'test-001'")
        result = cursor.fetchone()
        print(f"   ✅ Retrieved: {result[1]} (State: {result[2]})")

        # Test UPDATE
        print("\n3. Testing UPDATE...")
        cursor.execute("""
            UPDATE use_cases
            SET state = 'awaiting_config', updated_at = datetime('now')
            WHERE id = 'test-001'
        """)
        print("   ✅ Updated state to: awaiting_config")

        # Test DELETE
        print("\n4. Testing DELETE...")
        cursor.execute("DELETE FROM use_cases WHERE id = 'test-001'")
        print("   ✅ Deleted test use case")

        conn.commit()
        conn.close()

        print("\n✅ All database operations working correctly!")
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def create_env_file(db_path, s3_config):
    """Create .env file with configuration"""
    print_section("Saving Configuration")

    env_file = Path.cwd() / '.env'

    # Check if .env already exists
    if env_file.exists():
        response = input(f"\n.env file already exists. Overwrite? (yes/no) [no]: ").strip().lower()
        if response != 'yes':
            print("Skipping .env file creation.")
            return

    # Create .env content
    env_content = f"""# Hybrid SQLite + S3 Configuration
# Generated by setup_hybrid_system.py

# SQLite Database
DATABASE_PATH={db_path}

# S3 Storage
S3_BUCKET_NAME={s3_config['bucket_name']}
S3_REGION={s3_config['region']}
"""

    if s3_config['access_key'] and s3_config['secret_key']:
        env_content += f"""AWS_ACCESS_KEY_ID={s3_config['access_key']}
AWS_SECRET_ACCESS_KEY={s3_config['secret_key']}
"""
    else:
        env_content += """# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# (Using IAM role or environment variables)
"""

    env_content += """
# File Storage
LOCAL_CACHE_DIR=/home/cdsw/evaluation_cache
FILE_STORAGE_PATH=/home/cdsw/evaluation_files

# Email Configuration (set these later)
# SMTP_HOST=smtp.yourcompany.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@yourcompany.com
# SMTP_PASSWORD=your-password
# SMTP_FROM_EMAIL=auto-eval@yourcompany.com
"""

    try:
        with open(env_file, 'w') as f:
            f.write(env_content)

        print(f"✅ Saved configuration to {env_file}")

        # Make sure .env is in .gitignore
        gitignore_file = Path.cwd() / '.gitignore'
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()

            if '.env' not in gitignore_content:
                with open(gitignore_file, 'a') as f:
                    f.write('\n# Environment variables (secrets)\n.env\n')
                print(f"✅ Added .env to .gitignore")

    except Exception as e:
        print(f"⚠️  Failed to save .env file: {e}")


def create_directory_structure():
    """Create necessary local directories"""
    print_section("Creating Directory Structure")

    directories = [
        '/home/cdsw/evaluation_cache',
        '/home/cdsw/evaluation_files',
        '/home/cdsw/evaluation_files/configs',
        '/home/cdsw/evaluation_files/datasets',
        '/home/cdsw/evaluation_files/results',
    ]

    for directory in directories:
        path = Path(directory)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {directory}")
            except Exception as e:
                print(f"⚠️  Could not create {directory}: {e}")
        else:
            print(f"✓  Already exists: {directory}")


def main():
    """Main setup flow"""
    print("\n" + "=" * 70)
    print("SQLite + S3 Hybrid System Setup")
    print("=" * 70)

    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Step 2: Get S3 credentials
    s3_config = get_s3_credentials()

    # Step 3: Test S3 connection
    if not test_s3_connection(s3_config):
        response = input("\nS3 connection failed. Continue anyway? (yes/no) [no]: ").strip().lower()
        if response != 'yes':
            print("\nSetup cancelled. Fix S3 connection and try again.")
            sys.exit(1)

    # Step 4: Create database
    db_path = create_database()
    if not db_path:
        sys.exit(1)

    # Step 5: Test database
    if not test_database(db_path):
        print("\n⚠️  Database created but operations test failed.")
        print("You may need to check the schema or SQLite installation.")

    # Step 6: Create directories
    create_directory_structure()

    # Step 7: Save .env file
    create_env_file(db_path, s3_config)

    # Success!
    print_section("🎉 Setup Complete!")

    print("Your hybrid SQLite + S3 system is ready!")
    print("\nSystem details:")
    print(f"  • Database: {db_path}")
    print(f"  • S3 Bucket: {s3_config['bucket_name']}")
    print(f"  • Region: {s3_config['region']}")
    print(f"  • Tables: 7 (use_cases, models, state_transitions, etc.)")

    print("\nNext steps:")
    print("  1. Your configuration is saved in .env file")
    print("  2. Test S3 integration:")
    print("     python -c \"from proposed_architecture.storage.s3_service import S3StorageService; print('✅ S3 service ready!')\"")
    print("  3. Check out proposed_architecture/HYBRID_GUIDE.md for usage examples")
    print("  4. Start using the system with your existing evaluators!")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
