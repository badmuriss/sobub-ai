"""
Integration tests for database operations.

Tests the database CRUD operations with a real (test) SQLite database.
"""
import pytest
import json
from app.database import (
    get_all_memes,
    get_meme_by_id,
    create_meme,
    update_meme_tags,
    delete_meme,
    increment_play_count,
    get_memes_by_tags,
    get_setting,
    update_setting,
    get_all_settings,
    DatabaseConnection,
)


@pytest.mark.integration
class TestMemeOperations:
    """Tests for meme CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_meme(self, test_db):
        """Test creating a new meme."""
        # Override global database path temporarily
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            meme_id = await create_meme("test.mp3", ["tag1", "tag2"])

            assert meme_id > 0

            # Verify meme was created
            meme = await get_meme_by_id(meme_id)
            assert meme is not None
            assert meme["filename"] == "test.mp3"
            assert meme["tags"] == ["tag1", "tag2"]
            assert meme["play_count"] == 0
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_all_memes(self, populated_db):
        """Test retrieving all memes."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            memes = await get_all_memes()

            assert len(memes) == 3
            assert all("id" in m for m in memes)
            assert all("filename" in m for m in memes)
            assert all("tags" in m for m in memes)
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_meme_by_id(self, populated_db):
        """Test retrieving a specific meme by ID."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            meme = await get_meme_by_id(1)

            assert meme is not None
            assert meme["id"] == 1
            assert meme["filename"] == "goal.mp3"
            assert "goal" in meme["tags"]
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_meme_by_id_not_found(self, test_db):
        """Test retrieving a non-existent meme."""
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            meme = await get_meme_by_id(999)

            assert meme is None
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_update_meme_tags(self, populated_db):
        """Test updating meme tags."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            success = await update_meme_tags(1, ["new_tag1", "new_tag2"])

            assert success is True

            # Verify tags were updated
            meme = await get_meme_by_id(1)
            assert meme["tags"] == ["new_tag1", "new_tag2"]
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_delete_meme(self, populated_db):
        """Test deleting a meme."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            success = await delete_meme(1)

            assert success is True

            # Verify meme was deleted
            meme = await get_meme_by_id(1)
            assert meme is None
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_increment_play_count(self, populated_db):
        """Test incrementing play count."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            # Get initial play count
            meme_before = await get_meme_by_id(1)
            initial_count = meme_before["play_count"]

            # Increment
            await increment_play_count(1)

            # Verify incremented
            meme_after = await get_meme_by_id(1)
            assert meme_after["play_count"] == initial_count + 1
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_memes_by_tags(self, populated_db):
        """Test retrieving memes by tags."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            memes = await get_memes_by_tags(["football"])

            assert len(memes) == 1
            assert memes[0]["filename"] == "goal.mp3"
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_memes_by_multiple_tags(self, populated_db):
        """Test retrieving memes with multiple tags."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            memes = await get_memes_by_tags(["football", "cooking"])

            # Should return both goal.mp3 and chef.mp3
            assert len(memes) >= 2
            filenames = [m["filename"] for m in memes]
            assert "goal.mp3" in filenames
            assert "chef.mp3" in filenames
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_memes_by_tags_case_insensitive(self, populated_db):
        """Test that tag matching is case-insensitive."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            memes = await get_memes_by_tags(["FOOTBALL"])

            assert len(memes) == 1
            assert memes[0]["filename"] == "goal.mp3"
        finally:
            database._db = original_db


@pytest.mark.integration
class TestSettingsOperations:
    """Tests for settings operations."""

    @pytest.mark.asyncio
    async def test_get_setting(self, populated_db):
        """Test retrieving a setting."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            cooldown = await get_setting("cooldown_seconds")

            assert cooldown == "180"
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_setting_not_found(self, test_db):
        """Test retrieving a non-existent setting."""
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            value = await get_setting("nonexistent")

            assert value is None
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_update_setting(self, test_db):
        """Test updating a setting."""
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            # Create initial setting
            await update_setting("test_key", "test_value")

            # Verify it was created
            value = await get_setting("test_key")
            assert value == "test_value"

            # Update it
            await update_setting("test_key", "new_value")

            # Verify it was updated
            value = await get_setting("test_key")
            assert value == "new_value"
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_all_settings(self, populated_db):
        """Test retrieving all settings."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            settings = await get_all_settings()

            assert isinstance(settings, dict)
            assert "cooldown_seconds" in settings
            assert "trigger_probability" in settings
            assert "whisper_model" in settings
            assert settings["cooldown_seconds"] == "180"
        finally:
            database._db = original_db


@pytest.mark.integration
class TestDatabaseConnection:
    """Tests for DatabaseConnection abstraction layer."""

    @pytest.mark.asyncio
    async def test_execute_query_insert(self, test_db):
        """Test executing an INSERT query."""
        result = await test_db.execute_query(
            "INSERT INTO memes (filename, tags) VALUES (?, ?)",
            params=("test.mp3", json.dumps(["tag1"]))
        )

        assert result > 0  # Should return lastrowid

    @pytest.mark.asyncio
    async def test_execute_query_fetch_one(self, populated_db):
        """Test executing a query and fetching one result."""
        row = await populated_db.execute_query(
            "SELECT * FROM memes WHERE id = ?",
            params=(1,),
            fetch_one=True
        )

        assert row is not None
        assert row["id"] == 1

    @pytest.mark.asyncio
    async def test_execute_query_fetch_all(self, populated_db):
        """Test executing a query and fetching all results."""
        rows = await populated_db.execute_query(
            "SELECT * FROM memes",
            fetch_all=True
        )

        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_execute_many(self, test_db):
        """Test executing a query with multiple parameter sets."""
        params_list = [
            ("test1.mp3", json.dumps(["tag1"])),
            ("test2.mp3", json.dumps(["tag2"])),
            ("test3.mp3", json.dumps(["tag3"])),
        ]

        await test_db.execute_many(
            "INSERT INTO memes (filename, tags) VALUES (?, ?)",
            params_list
        )

        # Verify all were inserted
        rows = await test_db.execute_query(
            "SELECT COUNT(*) as count FROM memes",
            fetch_one=True
        )
        assert rows["count"] == 3

    @pytest.mark.asyncio
    async def test_connection_context_manager(self, test_db):
        """Test using the connection as a context manager."""
        async with test_db.get_connection() as conn:
            cursor = await conn.execute("SELECT 1 as value")
            row = await cursor.fetchone()
            assert row[0] == 1


@pytest.mark.integration
class TestDatabaseEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_meme_with_empty_tags(self, test_db):
        """Test creating a meme with empty tags list."""
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            meme_id = await create_meme("test.mp3", [])

            meme = await get_meme_by_id(meme_id)
            assert meme["tags"] == []
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_create_meme_with_unicode_tags(self, test_db):
        """Test creating a meme with Unicode characters in tags."""
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            meme_id = await create_meme("test.mp3", ["café", "niño", "日本語"])

            meme = await get_meme_by_id(meme_id)
            assert "café" in meme["tags"]
            assert "niño" in meme["tags"]
            assert "日本語" in meme["tags"]
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_update_tags_with_special_characters(self, populated_db):
        """Test updating tags with special characters."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            await update_meme_tags(1, ["tag@123", "tag#456", "tag$789"])

            meme = await get_meme_by_id(1)
            assert "tag@123" in meme["tags"]
            assert "tag#456" in meme["tags"]
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_get_memes_empty_database(self, test_db):
        """Test getting memes from empty database."""
        from app import database
        original_db = database._db
        database._db = test_db

        try:
            memes = await get_all_memes()

            assert memes == []
        finally:
            database._db = original_db

    @pytest.mark.asyncio
    async def test_increment_play_count_multiple_times(self, populated_db):
        """Test incrementing play count multiple times."""
        from app import database
        original_db = database._db
        database._db = populated_db

        try:
            for _ in range(5):
                await increment_play_count(1)

            meme = await get_meme_by_id(1)
            assert meme["play_count"] == 5
        finally:
            database._db = original_db
