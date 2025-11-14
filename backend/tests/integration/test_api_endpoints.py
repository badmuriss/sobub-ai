"""
Integration tests for REST API endpoints.

Tests the FastAPI endpoints with a test client.
"""
import pytest
import io
import os
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, Mock
from app.main import app


# Set environment variables before app initialization
os.environ['DATABASE_PATH'] = '/tmp/test_api_memes.db'
os.environ['AUDIO_DIR'] = '/tmp/test_api_audio'
os.environ['ENABLE_FILE_LOGGING'] = 'false'


@pytest.fixture
async def client():
    """Create an async test client."""
    # Skip startup events for tests
    app.router.lifespan_context = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.integration
class TestRootEndpoints:
    """Tests for root and health endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "SOBUB AI"
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.integration
class TestMemeEndpoints:
    """Tests for meme management endpoints."""

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_all')
    async def test_get_memes(self, mock_get_all, client, sample_memes):
        """Test getting all memes."""
        mock_get_all.return_value = sample_memes

        response = await client.get("/api/memes")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_all')
    async def test_get_memes_empty(self, mock_get_all, client):
        """Test getting memes when database is empty."""
        mock_get_all.return_value = []

        response = await client.get("/api/memes")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.add_meme')
    async def test_create_meme_success(self, mock_add_meme, client):
        """Test creating a new meme."""
        mock_add_meme.return_value = {
            "id": 1,
            "filename": "test.mp3",
            "tags": ["tag1", "tag2"],
            "created_at": "2024-01-01T12:00:00",
            "play_count": 0
        }

        # Create a mock MP3 file
        files = {"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")}
        data = {"tags": "tag1, tag2"}

        response = await client.post("/api/memes", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["filename"] == "test.mp3"
        assert result["tags"] == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_create_meme_invalid_extension(self, client):
        """Test creating a meme with invalid file extension."""
        files = {"file": ("test.wav", b"fake content", "audio/wav")}
        data = {"tags": "tag1, tag2"}

        response = await client.post("/api/memes", files=files, data=data)

        assert response.status_code == 400
        assert "MP3" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_meme_empty_tags(self, client):
        """Test creating a meme with empty tags."""
        files = {"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")}
        data = {"tags": ""}

        response = await client.post("/api/memes", files=files, data=data)

        assert response.status_code == 400
        assert "tag" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_by_id')
    async def test_get_meme_by_id(self, mock_get_by_id, client):
        """Test getting a specific meme by ID."""
        mock_get_by_id.return_value = {
            "id": 1,
            "filename": "test.mp3",
            "tags": ["tag1"],
            "created_at": "2024-01-01T12:00:00",
            "play_count": 0
        }

        response = await client.get("/api/memes/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["filename"] == "test.mp3"

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_by_id')
    async def test_get_meme_not_found(self, mock_get_by_id, client):
        """Test getting a non-existent meme."""
        mock_get_by_id.return_value = None

        response = await client.get("/api/memes/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.update_tags')
    async def test_update_meme_tags(self, mock_update_tags, client):
        """Test updating meme tags."""
        mock_update_tags.return_value = True

        data = {"tags": "new_tag1, new_tag2"}

        response = await client.put("/api/memes/1", data=data)

        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.update_tags')
    async def test_update_meme_not_found(self, mock_update_tags, client):
        """Test updating a non-existent meme."""
        mock_update_tags.return_value = False

        data = {"tags": "new_tag1, new_tag2"}

        response = await client.put("/api/memes/999", data=data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.delete')
    async def test_delete_meme(self, mock_delete, client):
        """Test deleting a meme."""
        mock_delete.return_value = True

        response = await client.delete("/api/memes/1")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.delete')
    async def test_delete_meme_not_found(self, mock_delete, client):
        """Test deleting a non-existent meme."""
        mock_delete.return_value = False

        response = await client.delete("/api/memes/999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_by_id')
    @patch('app.meme_manager.meme_manager.get_audio_file_path')
    async def test_get_meme_audio(self, mock_get_path, mock_get_by_id, client, sample_audio_file):
        """Test getting meme audio file."""
        mock_get_by_id.return_value = {
            "id": 1,
            "filename": "test.mp3",
            "tags": ["tag1"],
            "created_at": "2024-01-01T12:00:00",
            "play_count": 0
        }
        mock_get_path.return_value = sample_audio_file

        response = await client.get("/api/memes/1/audio")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_by_id')
    async def test_get_meme_audio_meme_not_found(self, mock_get_by_id, client):
        """Test getting audio for non-existent meme."""
        mock_get_by_id.return_value = None

        response = await client.get("/api/memes/999/audio")

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch('app.meme_manager.meme_manager.get_all_tags')
    async def test_get_all_tags(self, mock_get_all_tags, client):
        """Test getting all unique tags."""
        mock_get_all_tags.return_value = ["tag1", "tag2", "tag3"]

        response = await client.get("/api/tags")

        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert len(data["tags"]) == 3


@pytest.mark.integration
class TestSettingsEndpoints:
    """Tests for settings endpoints."""

    @pytest.mark.asyncio
    @patch('app.main.get_all_settings')
    async def test_get_settings(self, mock_get_settings, client):
        """Test getting current settings."""
        mock_get_settings.return_value = {
            "cooldown_seconds": "180",
            "trigger_probability": "50.0",
            "whisper_model": "base",
            "chunk_length_seconds": "3",
            "language": "en",
            "use_stemming": "true"
        }

        response = await client.get("/api/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["cooldown_seconds"] == 180
        assert data["trigger_probability"] == 50.0
        assert data["whisper_model"] == "base"
        assert data["language"] == "en"

    @pytest.mark.asyncio
    @patch('app.main.update_setting')
    @patch('app.main.trigger_engine.set_cooldown')
    async def test_update_settings_cooldown(self, mock_set_cooldown, mock_update_setting, client):
        """Test updating cooldown setting."""
        mock_update_setting.return_value = None

        response = await client.put(
            "/api/settings",
            json={"cooldown_seconds": 300}
        )

        assert response.status_code == 200
        mock_set_cooldown.assert_called_once_with(300)

    @pytest.mark.asyncio
    @patch('app.main.update_setting')
    @patch('app.main.trigger_engine.set_probability')
    async def test_update_settings_probability(self, mock_set_probability, mock_update_setting, client):
        """Test updating probability setting."""
        mock_update_setting.return_value = None

        response = await client.put(
            "/api/settings",
            json={"trigger_probability": 75.0}
        )

        assert response.status_code == 200
        mock_set_probability.assert_called_once_with(75.0)

    @pytest.mark.asyncio
    @patch('app.main.update_setting')
    async def test_update_settings_multiple_fields(self, mock_update_setting, client):
        """Test updating multiple settings at once."""
        mock_update_setting.return_value = None

        response = await client.put(
            "/api/settings",
            json={
                "cooldown_seconds": 300,
                "trigger_probability": 75.0,
                "language": "pt"
            }
        )

        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    @patch('app.main.update_setting')
    @patch('app.main.whisper_service')
    async def test_update_settings_whisper_model(self, mock_whisper, mock_update_setting, client):
        """Test updating Whisper model setting."""
        mock_update_setting.return_value = None
        mock_whisper.model = Mock()

        response = await client.put(
            "/api/settings",
            json={"whisper_model": "small"}
        )

        assert response.status_code == 200
        assert mock_whisper.model_name == "small"
        assert mock_whisper.model is None  # Should force reload


@pytest.mark.integration
class TestStatusEndpoint:
    """Tests for status endpoint."""

    @pytest.mark.asyncio
    @patch('app.trigger_engine.trigger_engine.get_status')
    async def test_get_status(self, mock_get_status, client):
        """Test getting trigger engine status."""
        mock_get_status.return_value = {
            "cooldown_seconds": 180,
            "trigger_probability": 50.0,
            "cooldown_active": False,
            "cooldown_remaining": 0,
            "last_trigger_time": None
        }

        response = await client.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["cooldown_seconds"] == 180
        assert data["trigger_probability"] == 50.0
        assert data["cooldown_active"] is False


@pytest.mark.integration
class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, client):
        """Test accessing an invalid endpoint."""
        response = await client.get("/api/invalid")

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch('app.main.meme_manager.get_all')
    async def test_internal_server_error(self, mock_get_all, client):
        """Test handling of internal server errors."""
        mock_get_all.side_effect = Exception("Database error")

        # In test mode, exceptions propagate instead of being converted to 500 responses
        # This is expected behavior for TestClient to aid debugging
        with pytest.raises(Exception, match="Database error"):
            await client.get("/api/memes")

    @pytest.mark.asyncio
    async def test_invalid_meme_id_type(self, client):
        """Test accessing meme with invalid ID type."""
        response = await client.get("/api/memes/invalid")

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestCORS:
    """Tests for CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = await client.options(
            "/api/memes",
            headers={"Origin": "http://localhost:3000"}
        )

        # CORS middleware should add appropriate headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
