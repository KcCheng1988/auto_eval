"""
Set up PostgreSQL database for evaluation system
Run this after you have database credentials
"""

import psycopg2
import os
import sys

def load_env():
    """Load environment variables from .env file if exists"""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"Loading environment from {env_file}...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Environment loaded\n")
    else:
        print(f"⚠️  No .env file found. Using environment variables.\n")

def get_credentials():
    """Get database credentials"""
    host = os.getenv('DATABASE_HOST')
    port = os.getenv('DATABASE_PORT', '5432')
    user = os.getenv('DATABASE_USER')
    password = os.getenv('DATABASE_PASSWORD')

    if not all([host, user, password]):
        print("❌ Missing database credentials!")
        print("\nPlease set these environment variables:")
        print("  DATABASE_HOST")
        print("  DATABASE_USER")
        print("  DATABASE_PASSWORD")
        print("\nOr create a .env file with these values.")
        sys.exit(1)

    return host, int(port), user, password

def create_database(host, port, user, password):
    """Create evaluation_system database if it doesn't exist"""
    print("=" * 60)
    print("Step 1: Creating 'evaluation_system' database")
    print("=" * 60)

    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',
            user=user,
            password=password
        )
        conn.autocommit = True

        with conn.cursor() as cur:
            # Check if database exists
            cur.execute("""
                SELECT 1 FROM pg_database WHERE datname='evaluation_system';
            """)

            if cur.fetchone():
                print("✅ Database 'evaluation_system' already exists")
            else:
                print("Creating database 'evaluation_system'...")
                cur.execute("CREATE DATABASE evaluation_system;")
                print("✅ Database created successfully")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def create_schema(host, port, user, password):
    """Create tables from schema.sql"""
    print("\n" + "=" * 60)
    print("Step 2: Creating tables from schema")
    print("=" * 60)

    schema_file = 'proposed_architecture/database/schema.sql'

    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        return False

    try:
        # Connect to evaluation_system database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='evaluation_system',
            user=user,
            password=password
        )

        # Read schema file
        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        print(f"Reading schema from {schema_file}...")

        # Execute schema
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()

        print("✅ Schema created successfully")

        # Verify tables
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()

            print(f"\n✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        return False

def test_database(host, port, user, password):
    """Test database operations"""
    print("\n" + "=" * 60)
    print("Step 3: Testing database operations")
    print("=" * 60)

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='evaluation_system',
            user=user,
            password=password
        )

        with conn.cursor() as cur:
            # Test insert
            print("\n1. Testing INSERT...")
            cur.execute("""
                INSERT INTO use_cases (name, team_email, state)
                VALUES ('Test Use Case', 'test@example.com', 'template_generation')
                RETURNING id, name;
            """)
            result = cur.fetchone()
            use_case_id = result[0]
            print(f"   ✅ Inserted use case: {result[1]} (ID: {use_case_id})")

            # Test select
            print("\n2. Testing SELECT...")
            cur.execute("SELECT COUNT(*) FROM use_cases;")
            count = cur.fetchone()[0]
            print(f"   ✅ Found {count} use case(s)")

            # Test update
            print("\n3. Testing UPDATE...")
            cur.execute("""
                UPDATE use_cases
                SET state = 'awaiting_config'
                WHERE id = %s
                RETURNING state;
            """, (use_case_id,))
            new_state = cur.fetchone()[0]
            print(f"   ✅ Updated state to: {new_state}")

            # Test delete
            print("\n4. Testing DELETE...")
            cur.execute("DELETE FROM use_cases WHERE id = %s;", (use_case_id,))
            print(f"   ✅ Deleted test use case")

            conn.commit()

        conn.close()
        print("\n✅ All database tests passed!")
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("PostgreSQL Database Setup for Evaluation System")
    print("=" * 60)
    print()

    # Load environment
    load_env()

    # Get credentials
    host, port, user, password = get_credentials()

    print(f"Connecting to PostgreSQL:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}\n")

    # Step 1: Create database
    if not create_database(host, port, user, password):
        sys.exit(1)

    # Step 2: Create schema
    if not create_schema(host, port, user, password):
        sys.exit(1)

    # Step 3: Test database
    if not test_database(host, port, user, password):
        sys.exit(1)

    # Success!
    print("\n" + "=" * 60)
    print("🎉 Database Setup Complete!")
    print("=" * 60)
    print("\nYour evaluation system database is ready to use.")
    print("\nNext steps:")
    print("  1. Test the quality checks:")
    print("     python -m pytest proposed_architecture/quality_checks/")
    print("\n  2. Try the existing field-based evaluator:")
    print("     python -c \"from src.evaluators.field_based_evaluator import FieldBasedEvaluator; print('✅ Evaluator imported')\"")
    print("\n  3. Start building the full system following QUICK_START.md")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
