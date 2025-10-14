"""
Quick script to check PostgreSQL availability in CML
Run this in your CML session terminal
"""

import sys

print("=" * 60)
print("PostgreSQL Availability Check")
print("=" * 60)

# Check 1: Can we import psycopg2?
print("\n1. Checking psycopg2 installation...")
try:
    import psycopg2
    print("   ✅ psycopg2 is installed")
    print(f"   Version: {psycopg2.__version__}")
except ImportError as e:
    print(f"   ❌ psycopg2 not installed: {e}")
    sys.exit(1)

# Check 2: Is psql command available?
print("\n2. Checking if psql command is available...")
import subprocess
try:
    result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ psql found at: {result.stdout.strip()}")

        # Get PostgreSQL version
        version_result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        print(f"   Version: {version_result.stdout.strip()}")
    else:
        print("   ❌ psql command not found")
except Exception as e:
    print(f"   ❌ Error checking psql: {e}")

# Check 3: Environment variables
print("\n3. Checking environment variables...")
import os

env_vars = [
    'DATABASE_HOST',
    'DATABASE_PORT',
    'DATABASE_NAME',
    'DATABASE_USER',
    'DATABASE_PASSWORD'
]

has_env_vars = False
for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask password
        if 'PASSWORD' in var:
            value = '*' * len(value)
        print(f"   ✅ {var}: {value}")
        has_env_vars = True
    else:
        print(f"   ❌ {var}: Not set")

if not has_env_vars:
    print("\n   ℹ️  No environment variables set yet. That's okay!")
    print("   You'll need to create a .env file or get credentials from admin.")

# Instructions
print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)

if has_env_vars:
    print("\n✅ You have environment variables set!")
    print("\nTry running: python test_postgres_connection.py")
else:
    print("\n📝 You need PostgreSQL credentials. Do ONE of these:")
    print("\n   Option 1: Ask your admin for credentials")
    print("   - Request: PostgreSQL host, port, database, username, password")
    print("   - They may need to create a database for you")
    print("\n   Option 2: Check if PostgreSQL is already configured in CML")
    print("   - Run: psql --help")
    print("   - Check CML documentation for database services")
    print("\n   Option 3: Look for existing connection info")
    print("   - Check: ~/.pgpass file")
    print("   - Check: environment variables in CML project settings")

print("\n" + "=" * 60)
