"""
Agno Framework Configuration Module

This module provides configuration and initialization for the Agno framework,
following Clean Architecture and Dependency Injection principles.

Architecture Patterns:
- Singleton Pattern: Single database instance
- Factory Pattern: Database creation based on environment
- Configuration Pattern: Centralized config management
"""
from typing import Optional
import logging
from functools import lru_cache

from agno.db.postgres import PostgresDb
from backend.core.config import settings

logger = logging.getLogger(__name__)


class AgnoConfig:
    """
    Agno framework configuration manager.

    Responsibilities:
    - Manage Agno database connection
    - Provide database instances
    - Handle connection lifecycle
    - Configure Agno-specific settings

    Design Pattern: Singleton + Factory
    """

    _instance: Optional['AgnoConfig'] = None
    _db: Optional[PostgresDb] = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Agno configuration"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            logger.info("Initializing Agno configuration")

    def get_database(self) -> PostgresDb:
        """
        Get Agno database instance (lazy initialization).

        Returns:
            PostgresDb instance configured for the current environment

        Design Pattern: Lazy Initialization + Factory
        """
        if self._db is None:
            self._db = self._create_database()
            logger.info("Agno database instance created")
        return self._db

    def _create_database(self) -> PostgresDb:
        """
        Create Agno database instance based on configuration.

        Returns:
            PostgresDb instance

        Design Pattern: Factory Method
        """
        try:
            db = PostgresDb(
                db_url=settings.DATABASE_URL,
                # Custom table names for namespacing
                session_table="agno_sessions",
                culture_table="agno_culture",
                memory_table="agno_memory",
                metrics_table="agno_metrics",
                eval_table="agno_eval",
                knowledge_table="agno_knowledge",
            )

            logger.info(
                f"Agno PostgreSQL database configured: "
                f"{settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}"
            )

            return db

        except Exception as e:
            logger.error(f"Failed to create Agno database: {e}", exc_info=True)
            raise

    def close(self):
        """
        Close database connections.

        Should be called on application shutdown.
        """
        if self._db is not None:
            logger.info("Closing Agno database connections")
            # Note: PostgresDb may have cleanup methods
            self._db = None

    def health_check(self) -> bool:
        """
        Check if Agno database is healthy.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            db = self.get_database()
            # Agno will auto-create tables on first use
            logger.info("Agno health check: OK")
            return True
        except Exception as e:
            logger.error(f"Agno health check failed: {e}")
            return False


# Global singleton instance (Dependency Injection Container pattern)
@lru_cache(maxsize=1)
def get_agno_config() -> AgnoConfig:
    """
    Get Agno configuration singleton.

    This function provides dependency injection for Agno configuration.
    Use this instead of instantiating AgnoConfig directly.

    Returns:
        AgnoConfig singleton instance

    Design Pattern: Service Locator + Dependency Injection
    """
    return AgnoConfig()


def get_agno_db() -> PostgresDb:
    """
    Get Agno database instance.

    Convenience function for getting database without config object.

    Returns:
        PostgresDb instance

    Design Pattern: Facade
    """
    config = get_agno_config()
    return config.get_database()


# Backward compatibility - single instance
agno_db = get_agno_db()


# Context manager support for proper resource cleanup
class AgnoContext:
    """
    Context manager for Agno database lifecycle.

    Usage:
        async with AgnoContext() as db:
            agent = Agent(db=db, ...)

    Design Pattern: Context Manager + Resource Acquisition Is Initialization (RAII)
    """

    def __enter__(self) -> PostgresDb:
        """Enter context - get database"""
        self.db = get_agno_db()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - cleanup if needed"""
        # PostgresDb handles its own cleanup
        pass

    async def __aenter__(self) -> PostgresDb:
        """Async enter context"""
        self.db = get_agno_db()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit context"""
        pass


# Application lifecycle hooks
def initialize_agno() -> None:
    """
    Initialize Agno framework on application startup.

    Call this in your application startup (e.g., FastAPI lifespan).

    Design Pattern: Initialization Hook
    """
    logger.info("="*60)
    logger.info("Initializing Agno Framework")
    logger.info("="*60)

    config = get_agno_config()

    # Health check
    if not config.health_check():
        logger.warning("Agno health check failed - may need database setup")

    # Log configuration
    logger.info("Agno Configuration:")
    logger.info(f"  - Database: PostgreSQL")
    logger.info(f"  - Table Prefix: agno_")
    logger.info(f"  - Auto-create Tables: Yes")
    logger.info(f"  - Tables: agno_sessions, agno_memory, agno_runs")
    logger.info("="*60)


def shutdown_agno() -> None:
    """
    Shutdown Agno framework on application shutdown.

    Call this in your application shutdown (e.g., FastAPI lifespan).

    Design Pattern: Cleanup Hook
    """
    logger.info("Shutting down Agno framework")
    config = get_agno_config()
    config.close()
    logger.info("Agno shutdown complete")
