"""
Database Initialization and Migration Management

This module handles database schema creation, versioning, and migrations.

Answers the question: "Is schema_sqlite.sql triggered just once?"

Answer: It depends on your strategy! This module implements MULTIPLE approaches:
1. Simple: Run once manually
2. Auto-initialize: Run on first startup
3. Migration-based: Version-controlled schema changes (RECOMMENDED)
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Database initialization and migration manager

    Supports multiple initialization strategies:
    - One-time manual setup
    - Auto-initialize on startup
    - Version-controlled migrations
    """

    def __init__(self, db_path: str, schema_dir: Optional[str] = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
            schema_dir: Directory containing schema files (default: ./database/)
        """
        self.db_path = Path(db_path)
        self.schema_dir = Path(schema_dir) if schema_dir else Path(__file__).parent

    # ============================================================================
    # Approach 1: One-Time Manual Initialization
    # ============================================================================

    def initialize_once(self, force: bool = False):
        """
        Initialize database schema once

        This is the simplest approach:
        - Run schema_sqlite.sql once when setting up
        - Good for development, proof-of-concepts
        - Manual control over when schema is created

        Args:
            force: If True, recreate tables even if they exist

        Usage:
            # During initial setup (run once manually)
            initializer = DatabaseInitializer('evaluation.db')
            initializer.initialize_once()

            # Or in deployment script:
            python -c "from database_initialization import DatabaseInitializer; \
                       DatabaseInitializer('evaluation.db').initialize_once()"
        """
        logger.info(f"Initializing database: {self.db_path}")

        # Check if database already exists
        if self.db_path.exists() and not force:
            logger.warning(f"Database {self.db_path} already exists. Use force=True to recreate.")
            return

        # Create parent directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Read schema file
        schema_file = self.schema_dir / 'schema_sqlite.sql'
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(schema_sql)
            conn.commit()
            logger.info(f"Database initialized successfully: {self.db_path}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            conn.close()

    # ============================================================================
    # Approach 2: Auto-Initialize on Startup (Recommended for Simple Apps)
    # ============================================================================

    def auto_initialize(self):
        """
        Auto-initialize database on application startup

        This approach:
        - Checks if database exists
        - Creates schema if missing
        - Safe to call on every startup (idempotent)
        - Uses CREATE TABLE IF NOT EXISTS

        Usage:
            # In main.py or app initialization
            from database_initialization import DatabaseInitializer

            def startup():
                db_init = DatabaseInitializer('evaluation.db')
                db_init.auto_initialize()  # Safe to call every time
                # Continue with app startup...

        This works because schema uses "IF NOT EXISTS":
            CREATE TABLE IF NOT EXISTS use_cases (...);

        If tables exist, nothing happens. If missing, they're created.
        """
        logger.info(f"Auto-initializing database: {self.db_path}")

        # Create parent directory
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if database file exists
        is_new_db = not self.db_path.exists()

        if is_new_db:
            logger.info("Database file not found, creating new database")

        # Read schema
        schema_file = self.schema_dir / 'schema_sqlite.sql'
        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Execute schema (safe because of IF NOT EXISTS)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(schema_sql)
            conn.commit()

            if is_new_db:
                logger.info("New database created and initialized")
                self._record_schema_version(conn, version='1.0.0', description='Initial schema')
            else:
                logger.info("Database schema verified/updated")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to auto-initialize database: {e}")
            raise
        finally:
            conn.close()

    # ============================================================================
    # Approach 3: Version-Controlled Migrations (RECOMMENDED for Production)
    # ============================================================================

    def setup_migration_tracking(self):
        """
        Create migration tracking table

        This table tracks which migrations have been applied:
        - migration_version: Sequential version number (1, 2, 3, ...)
        - migration_name: Descriptive name
        - applied_at: When it was applied
        - checksum: Hash of migration file (detect tampering)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                checksum TEXT NOT NULL,
                execution_time_ms INTEGER,
                description TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def apply_migrations(self, migrations_dir: Optional[str] = None):
        """
        Apply pending database migrations

        Migration files are named: 001_initial_schema.sql, 002_add_models.sql, etc.

        This approach:
        - Tracks which migrations have been applied
        - Runs only new migrations
        - Maintains schema version history
        - Safe to run on every deployment

        Args:
            migrations_dir: Directory containing migration files

        Usage:
            # During deployment or startup
            db_init = DatabaseInitializer('evaluation.db')
            db_init.apply_migrations()  # Applies only new migrations

        Migration file naming:
            001_initial_schema.sql       # Version 1
            002_add_model_evaluation_table.sql  # Version 2
            003_add_state_history_indexes.sql   # Version 3
        """
        migrations_path = Path(migrations_dir) if migrations_dir else self.schema_dir / 'migrations'

        # Ensure migration tracking table exists
        self.setup_migration_tracking()

        # Get applied migrations
        applied_versions = self._get_applied_migrations()

        # Find migration files
        if not migrations_path.exists():
            logger.warning(f"Migrations directory not found: {migrations_path}")
            return

        migration_files = sorted(migrations_path.glob('*.sql'))

        if not migration_files:
            logger.info("No migration files found")
            return

        # Apply pending migrations
        conn = sqlite3.connect(self.db_path)

        for migration_file in migration_files:
            # Extract version from filename (e.g., "001" from "001_initial_schema.sql")
            version = migration_file.stem.split('_')[0]

            if version in applied_versions:
                logger.debug(f"Migration {version} already applied, skipping")
                continue

            logger.info(f"Applying migration {version}: {migration_file.name}")

            # Read migration SQL
            with open(migration_file, 'r') as f:
                migration_sql = f.read()

            # Calculate checksum
            checksum = hashlib.sha256(migration_sql.encode()).hexdigest()

            # Execute migration
            try:
                start_time = datetime.now()
                conn.executescript(migration_sql)

                # Record migration
                execution_time = (datetime.now() - start_time).total_seconds() * 1000

                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO schema_migrations
                    (version, name, checksum, execution_time_ms, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    version,
                    migration_file.stem,
                    checksum,
                    int(execution_time),
                    f"Applied migration {migration_file.name}"
                ))

                conn.commit()
                logger.info(f"Migration {version} applied successfully ({execution_time:.0f}ms)")

            except Exception as e:
                conn.rollback()
                logger.error(f"Migration {version} failed: {e}")
                raise

        conn.close()

    def _get_applied_migrations(self) -> set:
        """Get set of applied migration versions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT version FROM schema_migrations')
            versions = {row[0] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            versions = set()

        conn.close()
        return versions

    def _record_schema_version(self, conn: sqlite3.Connection, version: str, description: str):
        """Record schema version in migration tracking"""
        try:
            self.setup_migration_tracking()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO schema_migrations (version, name, checksum, description)
                VALUES (?, ?, ?, ?)
            ''', (version, 'initial', 'auto-init', description))
            conn.commit()
        except Exception:
            # Ignore if tracking table doesn't exist
            pass

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_schema_version(self) -> Optional[str]:
        """Get current schema version"""
        if not self.db_path.exists():
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT version FROM schema_migrations
                ORDER BY applied_at DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            version = row[0] if row else None
        except sqlite3.OperationalError:
            version = None

        conn.close()
        return version

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get full migration history"""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT version, name, applied_at, execution_time_ms, description
                FROM schema_migrations
                ORDER BY applied_at
            ''')

            history = []
            for row in cursor.fetchall():
                history.append({
                    'version': row[0],
                    'name': row[1],
                    'applied_at': row[2],
                    'execution_time_ms': row[3],
                    'description': row[4]
                })

        except sqlite3.OperationalError:
            history = []

        conn.close()
        return history

    def verify_schema(self) -> bool:
        """Verify database schema integrity"""
        if not self.db_path.exists():
            logger.error("Database file does not exist")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check essential tables
        required_tables = [
            'use_cases',
            'models',
            'state_transitions',
            'evaluation_results',
            'activity_log'
        ]

        try:
            cursor.execute('''
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ''')
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing_tables = set(required_tables) - existing_tables

            if missing_tables:
                logger.error(f"Missing required tables: {missing_tables}")
                return False

            logger.info("Schema verification passed")
            return True

        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False

        finally:
            conn.close()


# ============================================================================
# Recommended Usage Patterns
# ============================================================================

def initialize_for_development():
    """
    Development setup (simplest approach)

    Run once when starting development:
        python -m database.database_initialization
    """
    db_init = DatabaseInitializer('data/evaluation_dev.db')
    db_init.auto_initialize()
    print(f"✓ Development database initialized")
    print(f"  Schema version: {db_init.get_schema_version()}")


def initialize_for_production():
    """
    Production setup (migration-based approach)

    Run during deployment:
        python -c "from database.database_initialization import initialize_for_production; \
                   initialize_for_production()"
    """
    db_init = DatabaseInitializer('data/evaluation.db')

    # Apply migrations
    db_init.apply_migrations()

    # Verify
    if db_init.verify_schema():
        version = db_init.get_schema_version()
        print(f"✓ Production database ready (schema version: {version})")

        # Show migration history
        history = db_init.get_migration_history()
        if history:
            print(f"\nMigration history:")
            for entry in history:
                print(f"  • {entry['version']}: {entry['name']} ({entry['applied_at']})")
    else:
        raise RuntimeError("Schema verification failed")


def initialize_on_app_startup(db_path: str):
    """
    Application startup (auto-initialize approach)

    Call this in your main.py or FastAPI startup event:

        from database.database_initialization import initialize_on_app_startup

        @app.on_event("startup")
        async def startup():
            initialize_on_app_startup('data/evaluation.db')
    """
    db_init = DatabaseInitializer(db_path)
    db_init.auto_initialize()  # Safe to call every time
    logger.info(f"Database ready: {db_path} (version: {db_init.get_schema_version()})")


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    """
    Command-line interface for database initialization

    Usage:
        # Initialize database
        python database/database_initialization.py

        # Force recreate
        python database/database_initialization.py --force

        # Apply migrations
        python database/database_initialization.py --migrate

        # Check version
        python database/database_initialization.py --version
    """
    import sys

    if '--version' in sys.argv:
        db_init = DatabaseInitializer('data/evaluation.db')
        version = db_init.get_schema_version()
        print(f"Schema version: {version or 'Not initialized'}")

    elif '--migrate' in sys.argv:
        initialize_for_production()

    elif '--force' in sys.argv:
        db_init = DatabaseInitializer('data/evaluation.db')
        db_init.initialize_once(force=True)
        print("✓ Database recreated")

    else:
        initialize_for_development()
