"""
<<<<<<< HEAD
Configuration module for SOBUB AI.
=======
Configuration module for Sobub AI.
>>>>>>> 8a38096837c66815ff3d73c6d5cda79c89c6b57a

This module centralizes all configuration values, default settings,
and constants to eliminate magic numbers and improve maintainability.
"""
import os
from typing import Final


# ============================================================================
# Default Application Settings
# ============================================================================

class DefaultSettings:
    """Default values for application settings."""

    # Audio Processing Settings
    COOLDOWN_SECONDS: Final[int] = 180  # 3 minutes
    TRIGGER_PROBABILITY: Final[float] = 50.0  # 50% chance
    CHUNK_LENGTH_SECONDS: Final[int] = 3  # 3-second audio chunks

    # Whisper Model Settings
    WHISPER_MODEL: Final[str] = "base"  # base model (74M parameters)
    LANGUAGE: Final[str] = "pt"  # Portuguese
    USE_STEMMING: Final[bool] = False  # Disable stemming by default

    # File Processing
    MIN_AUDIO_CHUNK_SIZE: Final[int] = 1024  # 1KB minimum chunk size
    TEMP_AUDIO_PREFIX: Final[str] = "audio_chunk_"

    # Audio Recording
    SAMPLE_RATE: Final[int] = 16000  # 16kHz sample rate
    AUDIO_FORMAT: Final[str] = "webm"  # WebM container format
    AUDIO_CODEC: Final[str] = "opus"  # Opus audio codec


# ============================================================================
# Whisper Model Configuration
# ============================================================================

class WhisperConfig:
    """Configuration for Whisper speech recognition."""

    # Available model sizes
    AVAILABLE_MODELS: Final[list] = ["tiny", "base", "small", "medium", "large"]

    # Model specifications (approximate)
    MODEL_SPECS: Final[dict] = {
        "tiny": {"parameters": "39M", "vram_gb": 1, "speed": "0.2-0.5s"},
        "base": {"parameters": "74M", "vram_gb": 1.5, "speed": "0.5-2s"},
        "small": {"parameters": "244M", "vram_gb": 2.5, "speed": "1-4s"},
        "medium": {"parameters": "769M", "vram_gb": 5, "speed": "3-10s"},
        "large": {"parameters": "1550M", "vram_gb": 10, "speed": "8-20s"},
    }

    # Supported languages (ISO 639-1 codes)
    SUPPORTED_LANGUAGES: Final[list] = [
        "en", "pt", "es", "fr", "de", "it", "ja", "ko", "zh",
        "ru", "ar", "hi", "nl", "pl", "tr", "vi", "id", "th"
    ]

    # Device configuration
    DEVICE: Final[str] = "cuda"  # Use GPU if available
    COMPUTE_TYPE: Final[str] = "float16"  # FP16 for GPU, int8 for CPU

    # Transcription settings
    BEAM_SIZE: Final[int] = 5  # Beam size for better accuracy
    VAD_FILTER: Final[bool] = True  # Voice Activity Detection to filter silence


# ============================================================================
# Database Configuration
# ============================================================================

class DatabaseConfig:
    """Configuration for SQLite database."""

    DATABASE_NAME: Final[str] = "memes.db"
    DATABASE_PATH: Final[str] = "./data/memes.db"

    # Table names
    TABLE_MEMES: Final[str] = "memes"
    TABLE_SETTINGS: Final[str] = "settings"

    # Connection settings
    CONNECTION_TIMEOUT: Final[int] = 30  # seconds


# ============================================================================
# File Storage Configuration
# ============================================================================

class StorageConfig:
    """Configuration for file storage."""

    DATA_DIR: Final[str] = os.getenv("DATA_DIR", "./data")
    AUDIO_DIR: Final[str] = os.getenv("AUDIO_DIR", "./data/audio_files")
    MODELS_DIR: Final[str] = os.getenv("MODELS_DIR", "./models")
    LOGS_DIR: Final[str] = os.getenv("LOGS_DIR", "./data/logs")

    # File extensions
    ALLOWED_AUDIO_EXTENSIONS: Final[set] = {".mp3"}
    AUDIO_MIME_TYPE: Final[str] = "audio/mpeg"

    # File naming
    AUDIO_FILE_PATTERN: Final[str] = "{id}.mp3"

    # Safety limits
    MAX_FILENAME_LENGTH: Final[int] = 255
    UNSAFE_FILENAME_CHARS: Final[str] = r'[^\w\s\-\.]'


# ============================================================================
# API Configuration
# ============================================================================

class APIConfig:
    """Configuration for FastAPI server."""

    HOST: Final[str] = "0.0.0.0"
    PORT: Final[int] = 8000

    # CORS settings
    ALLOW_ORIGINS: Final[list] = ["*"]  # For development
    ALLOW_CREDENTIALS: Final[bool] = True
    ALLOW_METHODS: Final[list] = ["*"]
    ALLOW_HEADERS: Final[list] = ["*"]

    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: Final[int] = 30  # seconds
    WS_MAX_MESSAGE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB

    # Static files
    STATIC_AUDIO_DIR: Final[str] = os.getenv("AUDIO_DIR", "./data/audio_files")


# ============================================================================
# Logging Configuration
# ============================================================================

class LoggingConfig:
    """Configuration for logging."""

    # Default log level (can be overridden by LOG_LEVEL env var)
    LOG_LEVEL: Final[str] = "INFO"
    LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

    # File logging configuration (can be overridden by ENABLE_FILE_LOGGING env var)
    ENABLE_FILE_LOGGING: Final[bool] = True  # Set to False to disable file logging
    LOG_FILE: Final[str] = "./data/logs/sobub.log"
    MAX_LOG_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: Final[int] = 5

    # Console logging
    ENABLE_CONSOLE_LOGGING: Final[bool] = True
    ENABLE_COLORED_LOGS: Final[bool] = True


# ============================================================================
# Message Types (WebSocket)
# ============================================================================

class MessageType:
    """WebSocket message types."""

    # Server -> Client messages
    TRANSCRIPTION: Final[str] = "transcription"
    MATCH: Final[str] = "match"
    TRIGGER: Final[str] = "trigger"
    DEBUG: Final[str] = "debug"
    ERROR: Final[str] = "error"

    # Client -> Server messages
    AUDIO_ENDED: Final[str] = "audio_ended"
    CONTROL: Final[str] = "control"


# ============================================================================
# Validation Rules
# ============================================================================

class ValidationRules:
    """Validation rules for user inputs."""

    # Settings validation
    MIN_COOLDOWN_SECONDS: Final[int] = 0
    MAX_COOLDOWN_SECONDS: Final[int] = 3600  # 1 hour

    MIN_TRIGGER_PROBABILITY: Final[float] = 0.0
    MAX_TRIGGER_PROBABILITY: Final[float] = 100.0

    MIN_CHUNK_LENGTH: Final[int] = 1
    MAX_CHUNK_LENGTH: Final[int] = 30  # 30 seconds

    # Tag validation
    MIN_TAG_LENGTH: Final[int] = 1
    MAX_TAG_LENGTH: Final[int] = 50
    MAX_TAGS_PER_MEME: Final[int] = 20

    # File validation
    MIN_AUDIO_DURATION: Final[float] = 0.1  # seconds
    MAX_AUDIO_DURATION: Final[float] = 300.0  # 5 minutes
    MAX_AUDIO_FILE_SIZE: Final[int] = 50 * 1024 * 1024  # 50MB


# ============================================================================
# Feature Flags
# ============================================================================

class FeatureFlags:
    """Feature flags for experimental or optional features."""

    ENABLE_STEMMING: Final[bool] = True
    ENABLE_TEXT_NORMALIZATION: Final[bool] = True
    ENABLE_GPU_ACCELERATION: Final[bool] = True
    ENABLE_DEBUG_LOGGING: Final[bool] = False
    ENABLE_PERFORMANCE_METRICS: Final[bool] = False
