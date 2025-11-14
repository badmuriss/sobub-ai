"""
Shared test fixtures and configuration.

This file contains pytest fixtures that can be used across all test modules.
"""
import pytest
import tempfile
import os
from typing import AsyncGenerator
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import aiosqlite
import json

from app.context_analyzer import ContextAnalyzer
from app.trigger_engine import TriggerEngine
from app.database import DatabaseConnection


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
async def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def test_db(temp_db_path):
    """Create an initialized test database."""
    db = DatabaseConnection(temp_db_path)

    # Initialize schema
    async with db.get_connection() as conn:
        # Create memes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                play_count INTEGER DEFAULT 0
            )
        """)

        # Create settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await conn.commit()

    yield db


@pytest.fixture
async def populated_db(test_db):
    """Create a test database with sample data."""
    # Insert sample memes
    sample_memes = [
        ("goal.mp3", json.dumps(["goal", "football", "sports"])),
        ("chef.mp3", json.dumps(["cooking", "chef", "food"])),
        ("hello.mp3", json.dumps(["greeting", "hello", "hi"])),
    ]

    async with test_db.get_connection() as conn:
        for filename, tags in sample_memes:
            await conn.execute(
                "INSERT INTO memes (filename, tags) VALUES (?, ?)",
                (filename, tags)
            )

        # Insert sample settings
        settings = [
            ('cooldown_seconds', '180'),
            ('trigger_probability', '50.0'),
            ('whisper_model', 'base'),
            ('chunk_length_seconds', '3'),
            ('language', 'pt'),
            ('use_stemming', 'false'),
        ]

        for key, value in settings:
            await conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

        await conn.commit()

    yield test_db


# =============================================================================
# Component Fixtures
# =============================================================================

@pytest.fixture
def context_analyzer():
    """Create a fresh ContextAnalyzer instance."""
    return ContextAnalyzer()


@pytest.fixture
def trigger_engine():
    """Create a fresh TriggerEngine instance with reset state."""
    engine = TriggerEngine()
    engine.reset_cooldown()  # Ensure clean state
    return engine


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_whisper_service():
    """Mock WhisperService to avoid GPU dependency."""
    mock = Mock()
    mock.transcribe_audio = AsyncMock(return_value="test transcription")
    mock.model = "base"
    mock.is_loaded = True
    return mock


@pytest.fixture
def mock_audio_data():
    """Mock audio data (small binary blob)."""
    # Simulate 1KB of audio data
    return b'\x00' * 1024


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_memes():
    """Sample meme data for testing."""
    return [
        {
            "id": 1,
            "filename": "goal.mp3",
            "tags": ["goal", "football", "sports"],
            "created_at": "2024-01-01T12:00:00",
            "play_count": 0
        },
        {
            "id": 2,
            "filename": "chef.mp3",
            "tags": ["cooking", "chef", "food"],
            "created_at": "2024-01-01T12:05:00",
            "play_count": 5
        },
        {
            "id": 3,
            "filename": "hello.mp3",
            "tags": ["greeting", "hello", "hi"],
            "created_at": "2024-01-01T12:10:00",
            "play_count": 2
        }
    ]


@pytest.fixture
def sample_transcription():
    """Sample transcription text for testing."""
    return "That goal was absolutely incredible"


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def temp_audio_path():
    """Create a temporary directory for audio files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_file(temp_audio_path):
    """Create a sample audio file for testing."""
    audio_file = temp_audio_path / "test.mp3"
    # Create a minimal valid MP3 file header
    mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 100
    audio_file.write_bytes(mp3_header)
    return audio_file


# =============================================================================
# Settings Fixtures
# =============================================================================

@pytest.fixture
def sample_settings():
    """Sample settings data."""
    return {
        "cooldown_seconds": 180,
        "trigger_probability": 50.0,
        "whisper_model": "base",
        "chunk_length_seconds": 3,
        "language": "pt",
        "use_stemming": "false"
    }
