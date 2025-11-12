import aiosqlite
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path


DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/memes.db")


async def init_database():
    """Initialize the database with required tables."""
    # Ensure the data directory exists
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
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
        await db.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES 
            ('cooldown_seconds', '300'),
            ('trigger_probability', '30'),
            ('whisper_model', 'base')
        """)
        
        await db.commit()


async def get_all_memes() -> List[Dict]:
    """Retrieve all memes from database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memes ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memes WHERE id = ?", (meme_id,)) as cursor:
            row = await cursor.fetchone()
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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO memes (filename, tags) VALUES (?, ?)",
            (filename, json.dumps(tags))
        )
        await db.commit()
        return cursor.lastrowid


async def update_meme_tags(meme_id: int, tags: List[str]) -> bool:
    """Update tags for a meme."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE memes SET tags = ? WHERE id = ?",
            (json.dumps(tags), meme_id)
        )
        await db.commit()
        return True


async def delete_meme(meme_id: int) -> bool:
    """Delete a meme from database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM memes WHERE id = ?", (meme_id,))
        await db.commit()
        return True


async def increment_play_count(meme_id: int):
    """Increment the play count for a meme."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE memes SET play_count = play_count + 1 WHERE id = ?",
            (meme_id,)
        )
        await db.commit()


async def get_memes_by_tags(tags: List[str]) -> List[Dict]:
    """Get memes that match any of the provided tags."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memes") as cursor:
            rows = await cursor.fetchall()
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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def update_setting(key: str, value: str):
    """Update a setting value."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()


async def get_all_settings() -> Dict[str, str]:
    """Get all settings."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}
