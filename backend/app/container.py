"""
<<<<<<< HEAD
Dependency Injection Container for SOBUB AI.
=======
Dependency Injection Container for Sobub AI.
>>>>>>> 8a38096837c66815ff3d73c6d5cda79c89c6b57a

This module implements a simple dependency injection container to manage
service instances and their dependencies. This replaces the global singleton
pattern and improves testability.
"""
from typing import Optional
import asyncio

from .config import DefaultSettings, DatabaseConfig
from .whisper_service import WhisperService
from .context_analyzer import ContextAnalyzer
from .trigger_engine import TriggerEngine
from .meme_manager import MemeManager
from .logging_config import get_logger


class ServiceContainer:
    """
    Dependency injection container that manages service instances.

    This container follows the Dependency Inversion Principle by providing
    a central location for service creation and dependency management.
    """

    def __init__(
        self,
        whisper_model: str = DefaultSettings.WHISPER_MODEL,
        database_path: str = DatabaseConfig.DATABASE_PATH,
    ):
        """
        Initialize the service container.

        Args:
            whisper_model: Whisper model name to use
            database_path: Path to SQLite database
        """
        self.logger = get_logger(__name__)
        self.whisper_model = whisper_model
        self.database_path = database_path

        # Service instances (lazy-loaded)
        self._whisper_service: Optional[WhisperService] = None
        self._context_analyzer: Optional[ContextAnalyzer] = None
        self._trigger_engine: Optional[TriggerEngine] = None
        self._meme_manager: Optional[MemeManager] = None

        self.logger.info("ServiceContainer initialized")

    # ========================================================================
    # Service Getters (Lazy Loading)
    # ========================================================================

    @property
    def whisper_service(self) -> WhisperService:
        """
        Get or create WhisperService instance.

        Returns:
            WhisperService instance
        """
        if self._whisper_service is None:
            self.logger.info(f"Creating WhisperService with model: {self.whisper_model}")
            self._whisper_service = WhisperService(model_name=self.whisper_model)
        return self._whisper_service

    @property
    def context_analyzer(self) -> ContextAnalyzer:
        """
        Get or create ContextAnalyzer instance.

        Returns:
            ContextAnalyzer instance
        """
        if self._context_analyzer is None:
            self.logger.info("Creating ContextAnalyzer")
            self._context_analyzer = ContextAnalyzer()
        return self._context_analyzer

    @property
    def trigger_engine(self) -> TriggerEngine:
        """
        Get or create TriggerEngine instance.

        Returns:
            TriggerEngine instance
        """
        if self._trigger_engine is None:
            self.logger.info("Creating TriggerEngine")
            self._trigger_engine = TriggerEngine()
        return self._trigger_engine

    @property
    def meme_manager(self) -> MemeManager:
        """
        Get or create MemeManager instance.

        Returns:
            MemeManager instance
        """
        if self._meme_manager is None:
            self.logger.info("Creating MemeManager")
            self._meme_manager = MemeManager()
        return self._meme_manager

    # ========================================================================
    # Service Management
    # ========================================================================

    def reload_whisper_service(self, model_name: str) -> None:
        """
        Reload WhisperService with a different model.

        Args:
            model_name: New Whisper model name
        """
        self.logger.info(f"Reloading WhisperService with model: {model_name}")
        self.whisper_model = model_name
        self._whisper_service = None  # Will be recreated on next access

    def reset_trigger_engine(self) -> None:
        """Reset TriggerEngine state (cooldowns, etc.)."""
        self.logger.info("Resetting TriggerEngine")
        self._trigger_engine = None

    def cleanup(self) -> None:
        """Clean up all services and release resources."""
        self.logger.info("Cleaning up ServiceContainer")

        # Clean up WhisperService if it was initialized
        if self._whisper_service is not None:
            try:
                # WhisperService doesn't have explicit cleanup, but we can release the reference
                self._whisper_service = None
                self.logger.debug("WhisperService cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up WhisperService: {e}")

        # Reset all service instances
        self._context_analyzer = None
        self._trigger_engine = None
        self._meme_manager = None

        self.logger.info("ServiceContainer cleanup complete")

    # ========================================================================
    # Factory Methods (for testing)
    # ========================================================================

    @classmethod
    def create_test_container(cls) -> 'ServiceContainer':
        """
        Create a container configured for testing.

        Returns:
            ServiceContainer configured for testing
        """
        return cls(
            whisper_model="tiny",  # Use smallest model for tests
            database_path=":memory:",  # In-memory database
        )

    @classmethod
    def create_production_container(
        cls,
        whisper_model: Optional[str] = None,
        database_path: Optional[str] = None,
    ) -> 'ServiceContainer':
        """
        Create a container configured for production.

        Args:
            whisper_model: Whisper model name (defaults to config value)
            database_path: Database path (defaults to config value)

        Returns:
            ServiceContainer configured for production
        """
        return cls(
            whisper_model=whisper_model or DefaultSettings.WHISPER_MODEL,
            database_path=database_path or DatabaseConfig.DATABASE_PATH,
        )


# ============================================================================
# Global Container Instance
# ============================================================================

# This will be initialized in main.py
_global_container: Optional[ServiceContainer] = None
_container_lock = asyncio.Lock()  # Async lock for thread-safe initialization

logger = get_logger(__name__)


def get_container() -> ServiceContainer:
    """
    Get the global service container instance.

    Returns:
        Global ServiceContainer instance

    Raises:
        RuntimeError: If container hasn't been initialized
    """
    if _global_container is None:
        raise RuntimeError(
            "ServiceContainer not initialized. Call initialize_container() first."
        )
    return _global_container


async def initialize_container_async(
    whisper_model: Optional[str] = None,
    database_path: Optional[str] = None,
) -> ServiceContainer:
    """
    Initialize the global service container (async, thread-safe).

    This is the recommended initialization method when called from async context.

    Args:
        whisper_model: Whisper model name
        database_path: Database path

    Returns:
        Initialized ServiceContainer
    """
    global _global_container

    async with _container_lock:
        if _global_container is not None:
            logger.warning("ServiceContainer already initialized. Replacing existing container.")

        _global_container = ServiceContainer.create_production_container(
            whisper_model=whisper_model,
            database_path=database_path,
        )

    return _global_container


def initialize_container(
    whisper_model: Optional[str] = None,
    database_path: Optional[str] = None,
) -> ServiceContainer:
    """
    Initialize the global service container (synchronous version).

    Note: This is a synchronous wrapper for backwards compatibility.
    Consider using initialize_container_async() in async contexts for thread safety.

    Args:
        whisper_model: Whisper model name
        database_path: Database path

    Returns:
        Initialized ServiceContainer
    """
    global _global_container

    if _global_container is not None:
        logger.warning("ServiceContainer already initialized. Replacing existing container.")

    _global_container = ServiceContainer.create_production_container(
        whisper_model=whisper_model,
        database_path=database_path,
    )

    return _global_container


def cleanup_container() -> None:
    """Clean up the global service container."""
    global _global_container

    if _global_container is not None:
        _global_container.cleanup()
        _global_container = None
