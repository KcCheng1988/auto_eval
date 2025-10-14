"""
Test PostgreSQL connection in CML
Run this after you have credentials
"""

import psycopg2
import os
import sys

print("=" * 60)
print("PostgreSQL Connection Test")
print("=" * 60)

# Method 1: Try environment variables
host = os.getenv('DATABASE_HOST')
port = os.getenv('DATABASE_PORT', '5432')
database = os.getenv('DATABASE_NAME', 'postgres')
user = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')

# Method 2: Manual input if env vars not set
if not all([host, user, password]):
    print("\n⚠️  Environment variables not set.")
    print("Please provide credentials manually:\n")

    if not host:
        host = input("PostgreSQL Host: ")
    if not user:
        user = input("Username: ")
    if not password:
        import getpass
        password = getpass.getpass("Password: ")

print(f"\nConnecting to:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Database: {database}")
print(f"  User: {user}")
print(f"  Password: {'*' * len(password) if password else 'NOT SET'}")
print()

# Try to connect
try:
    print("Attempting connection...")
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

    print("✅ Connection successful!\n")

    # Get PostgreSQL version
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"PostgreSQL Version:")
        print(f"  {version}\n")

        # Check if evaluation_system database exists
        cur.execute("""
            SELECT datname FROM pg_database
            WHERE datname = 'evaluation_system';
        """)
        eval_db = cur.fetchone()

        if eval_db:
            print("✅ 'evaluation_system' database exists")
        else:
            print("❌ 'evaluation_system' database does NOT exist")
            print("\nYou need to create it:")
            print("  psql -h {} -U {} -c \"CREATE DATABASE evaluation_system;\"".format(host, user))

        # List all databases
        cur.execute("""
            SELECT datname FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        databases = cur.fetchall()
        print(f"\nAvailable databases ({len(databases)}):")
        for db in databases:
            print(f"  - {db[0]}")

    conn.close()

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("\n1. Save these credentials to .env file:")
    print("\n   # Create .env file in project root")
    print(f"   DATABASE_HOST={host}")
    print(f"   DATABASE_PORT={port}")
    print(f"   DATABASE_NAME=evaluation_system")
    print(f"   DATABASE_USER={user}")
    print(f"   DATABASE_PASSWORD=<your-password>")

    if not eval_db:
        print("\n2. Create 'evaluation_system' database:")
        print(f"\n   psql -h {host} -U {user} -d postgres")
        print("   postgres=# CREATE DATABASE evaluation_system;")
        print("   postgres=# \\q")

    print("\n3. Run the schema to create tables:")
    print(f"\n   psql -h {host} -U {user} -d evaluation_system -f proposed_architecture/database/schema.sql")

    print("\n4. Test the full setup:")
    print("\n   python setup_database.py")

    print("\n" + "=" * 60)

except psycopg2.OperationalError as e:
    print(f"❌ Connection failed!")
    print(f"\nError: {e}")
    print("\nCommon issues:")
    print("  1. Wrong host/port - Check with your admin")
    print("  2. Wrong username/password - Verify credentials")
    print("  3. Database doesn't exist - Try 'postgres' database first")
    print("  4. Firewall blocking connection - Contact network admin")
    print("  5. PostgreSQL not running - Contact DBA")
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
