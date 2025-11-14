import aiosqlite
import json
import os
from typing import List, Optional, Dict, Tuple, Union
from pathlib import Path
from contextlib import asynccontextmanager

from .config import DatabaseConfig, DefaultSettings
from .logging_config import get_logger


DATABASE_PATH = DatabaseConfig.DATABASE_PATH
logger = get_logger(__name__)


# ============================================================================
# Database Connection Abstraction Layer
# ============================================================================

class DatabaseConnection:
    """
    Database connection abstraction that eliminates DRY violations.

    This class provides a centralized way to execute database queries
    without repeating the connection boilerplate code.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize database connection manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        """
        Get a database connection as a context manager.

        Yields:
            aiosqlite.Connection: Database connection
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
        commit: bool = True,
    ) -> Union[int, Optional[aiosqlite.Row], List[aiosqlite.Row]]:
        """
        Execute a database query with common patterns.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Whether to fetch one row
            fetch_all: Whether to fetch all rows
            commit: Whether to commit after execution

        Returns:
            Union[int, Optional[aiosqlite.Row], List[aiosqlite.Row]]:
                - int: lastrowid if neither fetch flag is set
                - Optional[aiosqlite.Row]: single row if fetch_one=True
                - List[aiosqlite.Row]: list of rows if fetch_all=True
        """
        async with self.get_connection() as db:
            cursor = await db.execute(query, params or ())

            if fetch_one:
                return await cursor.fetchone()
            elif fetch_all:
                return await cursor.fetchall()
            else:
                if commit:
                    await db.commit()
                return cursor.lastrowid

    async def execute_many(
        self,
        query: str,
        params_list: List[Tuple],
        commit: bool = True,
    ) -> None:
        """
        Execute a query multiple times with different parameters.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            commit: Whether to commit after execution
        """
        async with self.get_connection() as db:
            await db.executemany(query, params_list)
            if commit:
                await db.commit()


# Global database connection instance
_db = DatabaseConnection()


async def init_database() -> None:
    """Initialize the database with required tables."""
    # Ensure the data directory exists
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initializing database at {DATABASE_PATH}")

    async with _db.get_connection() as db:
        # Create memes table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                play_count INTEGER DEFAULT 0
            )
        """)

        # Create settings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Insert default settings if not exists
        default_settings = [
            ('cooldown_seconds', str(DefaultSettings.COOLDOWN_SECONDS)),
            ('trigger_probability', str(DefaultSettings.TRIGGER_PROBABILITY)),
            ('whisper_model', DefaultSettings.WHISPER_MODEL),
            ('chunk_length_seconds', str(DefaultSettings.CHUNK_LENGTH_SECONDS)),
            ('language', DefaultSettings.LANGUAGE),
            ('use_stemming', str(DefaultSettings.USE_STEMMING).lower()),
        ]

        for key, value in default_settings:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

        await db.commit()
        logger.info("Database initialized successfully")


async def get_all_memes() -> List[Dict]:
    """Retrieve all memes from database."""
    rows = await _db.execute_query(
        "SELECT * FROM memes ORDER BY created_at DESC",
        fetch_all=True
    )
    return [
        {
            "id": row["id"],
            "filename": row["filename"],
            "tags": json.loads(row["tags"]),
            "created_at": row["created_at"],
            "play_count": row["play_count"]
        }
        for row in rows
    ]


async def get_meme_by_id(meme_id: int) -> Optional[Dict]:
    """Retrieve a specific meme by ID."""
    row = await _db.execute_query(
        "SELECT * FROM memes WHERE id = ?",
        params=(meme_id,),
        fetch_one=True
    )
    if row:
        return {
            "id": row["id"],
            "filename": row["filename"],
            "tags": json.loads(row["tags"]),
            "created_at": row["created_at"],
            "play_count": row["play_count"]
        }
    return None


async def create_meme(filename: str, tags: List[str]) -> int:
    """Create a new meme entry."""
    meme_id = await _db.execute_query(
        "INSERT INTO memes (filename, tags) VALUES (?, ?)",
        params=(filename, json.dumps(tags))
    )
    logger.info(f"Created meme {meme_id} with {len(tags)} tags")
    return meme_id


async def update_meme_tags(meme_id: int, tags: List[str]) -> bool:
    """Update tags for a meme."""
    await _db.execute_query(
        "UPDATE memes SET tags = ? WHERE id = ?",
        params=(json.dumps(tags), meme_id)
    )
    logger.info(f"Updated meme {meme_id} with {len(tags)} tags")
    return True


async def delete_meme(meme_id: int) -> bool:
    """Delete a meme from database."""
    await _db.execute_query(
        "DELETE FROM memes WHERE id = ?",
        params=(meme_id,)
    )
    logger.info(f"Deleted meme {meme_id}")
    return True


async def increment_play_count(meme_id: int) -> None:
    """Increment the play count for a meme."""
    await _db.execute_query(
        "UPDATE memes SET play_count = play_count + 1 WHERE id = ?",
        params=(meme_id,)
    )


async def get_memes_by_tags(tags: List[str]) -> List[Dict]:
    """Get memes that match any of the provided tags."""
    rows = await _db.execute_query(
        "SELECT * FROM memes",
        fetch_all=True
    )

    matching_memes = []
    for row in rows:
        meme_tags = json.loads(row["tags"])
        if any(tag.lower() in [t.lower() for t in meme_tags] for tag in tags):
            matching_memes.append({
                "id": row["id"],
                "filename": row["filename"],
                "tags": meme_tags,
                "created_at": row["created_at"],
                "play_count": row["play_count"]
            })
    return matching_memes


async def get_setting(key: str) -> Optional[str]:
    """Get a setting value by key."""
    row = await _db.execute_query(
        "SELECT value FROM settings WHERE key = ?",
        params=(key,),
        fetch_one=True
    )
    return row[0] if row else None


async def update_setting(key: str, value: str) -> None:
    """Update a setting value."""
    await _db.execute_query(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        params=(key, value)
    )
    logger.debug(f"Updated setting '{key}'")


async def get_all_settings() -> Dict[str, str]:
    """Get all settings."""
    rows = await _db.execute_query(
        "SELECT key, value FROM settings",
        fetch_all=True
    )
    return {row["key"]: row["value"] for row in rows}
