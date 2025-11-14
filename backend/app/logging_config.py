"""
Centralized logging configuration for Sobub AI.

This module provides unified logging setup and utilities for consistent
logging across all application components.

Environment Variables:
    LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    ENABLE_FILE_LOGGING: Enable/disable file logging (true/false)
"""
import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional

from .config import LoggingConfig


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color codes."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: Optional[bool] = None,
    enable_file: Optional[bool] = None,
    enable_colors: Optional[bool] = None,
) -> None:
    """
    Configure logging for the application.

    Configuration is read from environment variables first, then falls back to
    config.py defaults, then to function arguments.

    Environment Variables:
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        ENABLE_FILE_LOGGING: Enable file logging (true/false/1/0)

    Args:
        log_level: Logging level (overrides env var and config)
        log_file: Path to log file (overrides config)
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging (overrides env var and config)
        enable_colors: Whether to use colored output in console
    """
    # Read from environment variables or use config defaults
    log_level = log_level or LoggingConfig.LOG_LEVEL

    if enable_file is None:  # Not explicitly set by caller
        enable_file = LoggingConfig.ENABLE_FILE_LOGGING

    # Other settings - LOG_FILE can be overridden by environment variable
    log_file = log_file or LoggingConfig.LOG_FILE
    enable_console = enable_console if enable_console is not None else LoggingConfig.ENABLE_CONSOLE_LOGGING
    enable_colors = enable_colors if enable_colors is not None else LoggingConfig.ENABLE_COLORED_LOGS

    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if enable_colors:
        console_formatter = ColoredFormatter(
            fmt=LoggingConfig.LOG_FORMAT,
            datefmt=LoggingConfig.LOG_DATE_FORMAT
        )
    else:
        console_formatter = logging.Formatter(
            fmt=LoggingConfig.LOG_FORMAT,
            datefmt=LoggingConfig.LOG_DATE_FORMAT
        )

    file_formatter = logging.Formatter(
        fmt=LoggingConfig.LOG_FORMAT,
        datefmt=LoggingConfig.LOG_DATE_FORMAT
    )

    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Add file handler with rotation
    if enable_file and log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=LoggingConfig.MAX_LOG_SIZE,
            backupCount=LoggingConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Log startup message
    file_status = f"file={log_file}" if enable_file else "file=disabled"
    logging.info(f"Logging configured: level={log_level}, {file_status}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin class that provides a logger property to any class.

    Usage:
        class MyService(LoggerMixin):
            def my_method(self):
                self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(self.__class__.__name__)


# ============================================================================
# Logging Utilities
# ============================================================================

def log_function_call(func):
    """
    Decorator that logs function calls with arguments and return values.

    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return result
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


def log_async_function_call(func):
    """
    Decorator that logs async function calls with arguments and return values.

    Usage:
        @log_async_function_call
        async def my_async_function(arg1, arg2):
            return result
    """
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = await func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


class PerformanceLogger:
    """
    Context manager for logging performance metrics.

    Usage:
        with PerformanceLogger("process_audio"):
            # Do expensive operation
            pass
    """

    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize performance logger.

        Args:
            operation_name: Name of the operation being timed
            logger: Logger to use (defaults to root logger)
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log duration."""
        import time
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name} (took {duration:.2f}s)")
        else:
            self.logger.error(
                f"Failed: {self.operation_name} (took {duration:.2f}s) - {exc_type.__name__}: {exc_val}"
            )
        # Don't suppress the exception
        return False


# ============================================================================
# Module-level logger setup (for backward compatibility)
# ============================================================================

# This will be replaced by setup_logging() call in main.py
logging.basicConfig(
    level=logging.INFO,
    format=LoggingConfig.LOG_FORMAT,
    datefmt=LoggingConfig.LOG_DATE_FORMAT
)
