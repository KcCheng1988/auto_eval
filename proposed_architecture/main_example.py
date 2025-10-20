"""
Example application startup showing proper configuration and dependency management.

This demonstrates how to:
1. Load configuration (database path, environment)
2. Initialize database
3. Create repositories with correct database path
4. Create services with proper dependency injection
"""

import logging
from config import AppConfig
from database.database_initialization import initialize_on_app_startup
from repositories.model_evaluation_repository import ModelEvaluationRepository
from services.evaluation_service import EvaluationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory pattern.

    Creates and wires up all dependencies.
    Returns everything needed to run the application.
    """
    # 1. Load configuration
    config = AppConfig.load()
    logger.info(f"Starting application in {config.environment} mode")
    logger.info(f"Database path: {config.get_db_path()}")

    # 2. Initialize database
    db_path = initialize_on_app_startup(config.get_db_path())
    logger.info(f"✓ Database initialized")

    # 3. Create repositories (all use same db_path from config)
    model_repo = ModelEvaluationRepository(db_path)
    # use_case_repo = UseCaseRepository(db_path)
    # quality_check_repo = QualityCheckRepository(db_path)
    logger.info(f"✓ Repositories created")

    # 4. Create services (inject repositories)
    # quality_check_service = QualityCheckService(quality_check_repo)
    # evaluation_service = EvaluationService(
    #     model_repo=model_repo,
    #     use_case_repo=use_case_repo,
    #     quality_check_service=quality_check_service
    # )
    logger.info(f"✓ Services created")

    # 5. Return everything
    return {
        'config': config,
        'db_path': db_path,
        'repositories': {
            'model': model_repo,
            # 'use_case': use_case_repo,
            # 'quality_check': quality_check_repo
        },
        'services': {
            # 'evaluation': evaluation_service,
            # 'quality_check': quality_check_service
        }
    }


# ============================================================================
# Example 1: Simple Script
# ============================================================================

def simple_script_example():
    """
    Example: Simple script that needs database access.

    Good for: One-off scripts, data migration, manual operations
    """
    # Load config and initialize
    config = AppConfig.load()
    db_path = initialize_on_app_startup(config.get_db_path())

    # Create repositories
    model_repo = ModelEvaluationRepository(db_path)

    # Use repositories
    # models = model_repo.get_all()
    # for model in models:
    #     print(model.to_dict())


# ============================================================================
# Example 2: FastAPI Application
# ============================================================================

def fastapi_example():
    """
    Example: FastAPI application with proper dependency injection.

    Good for: REST APIs, web services
    """
    from fastapi import FastAPI, Depends

    app = FastAPI()

    # Global app state (initialized once at startup)
    app_state = {}

    @app.on_event("startup")
    async def startup():
        """Initialize database and dependencies on startup"""
        config = AppConfig.load()
        db_path = initialize_on_app_startup(config.get_db_path())

        # Store in app state
        app_state['config'] = config
        app_state['db_path'] = db_path

        logger.info("✓ Application started")

    # Dependency: Get database path
    def get_db_path() -> str:
        return app_state['db_path']

    # Dependency: Get model repository
    def get_model_repo(db_path: str = Depends(get_db_path)) -> ModelEvaluationRepository:
        return ModelEvaluationRepository(db_path)

    # Routes use dependency injection
    @app.get("/models")
    def list_models(repo: ModelEvaluationRepository = Depends(get_model_repo)):
        # Repository automatically injected with correct db_path
        # models = repo.get_all()
        # return [model.to_dict() for model in models]
        return {"message": "List models"}

    @app.post("/models/{model_id}/evaluate")
    def evaluate_model(
        model_id: str,
        repo: ModelEvaluationRepository = Depends(get_model_repo)
    ):
        # Use repository
        # result = repo.evaluate(model_id)
        return {"message": f"Evaluate model {model_id}"}

    return app


# ============================================================================
# Example 3: Testing Setup
# ============================================================================

def testing_example():
    """
    Example: Testing with in-memory database.

    Good for: Unit tests, integration tests
    """
    import pytest

    @pytest.fixture
    def test_config():
        """Fixture providing test configuration"""
        return AppConfig.load('testing')

    @pytest.fixture
    def test_db(test_config):
        """Fixture providing initialized test database"""
        db_path = initialize_on_app_startup(test_config.get_db_path())
        return db_path

    @pytest.fixture
    def model_repo(test_db):
        """Fixture providing model repository"""
        return ModelEvaluationRepository(test_db)

    # Test using fixtures
    def test_create_model(model_repo):
        """Test creating a model"""
        # model = Model.create_new(...)
        # model_repo.save(model)
        # assert model_repo.get_by_id(model.id) is not None
        pass


# ============================================================================
# Example 4: Environment-Specific Configuration
# ============================================================================

def environment_example():
    """
    Example: Running in different environments.

    Good for: Development vs Production
    """
    import os

    # Set environment before loading config
    os.environ['ENV'] = 'production'
    os.environ['DATABASE_PATH'] = '/var/lib/auto_eval/production.db'

    # Load config (reads environment variables)
    config = AppConfig.load()

    print(f"Environment: {config.environment}")
    print(f"Database: {config.get_db_path()}")
    print(f"Debug: {config.debug}")

    # Initialize with production database
    db_path = initialize_on_app_startup(config.get_db_path())

    # Create repositories
    model_repo = ModelEvaluationRepository(db_path)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    """
    Run the application.

    Usage:
        # Development (default)
        python main_example.py

        # Production
        ENV=production python main_example.py

        # Custom database
        DATABASE_PATH=/custom/path/db.sqlite python main_example.py
    """
    # Create and start application
    app = create_app()

    logger.info("Application ready!")
    logger.info("Available repositories: " + ", ".join(app['repositories'].keys()))
    logger.info("Available services: " + ", ".join(app['services'].keys()))

    # Your application logic here
    # ...
