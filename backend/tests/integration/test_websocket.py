"""
Integration tests for WebSocket functionality.

Tests the WebSocket connection manager and message handling.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.websocket import ConnectionManager
from app.config import MessageType


@pytest.mark.integration
class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()
        ws.receive = AsyncMock()
        ws.receive_text = AsyncMock()
        ws.receive_bytes = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_client(self, manager, mock_websocket):
        """Test connecting a client."""
        client_id = "test_client_1"

        await manager.connect(client_id, mock_websocket)

        assert client_id in manager.active_connections
        assert manager.active_connections[client_id] == mock_websocket
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_client(self, manager, mock_websocket):
        """Test disconnecting a client."""
        client_id = "test_client_1"

        await manager.connect(client_id, mock_websocket)
        manager.disconnect(client_id)

        assert client_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(self, manager):
        """Test disconnecting a client that doesn't exist."""
        # Should not raise an error
        manager.disconnect("nonexistent_client")

    @pytest.mark.asyncio
    async def test_send_message_to_client(self, manager, mock_websocket):
        """Test sending a message to a specific client."""
        client_id = "test_client_1"
        message = {"type": "test", "data": "hello"}

        await manager.connect(client_id, mock_websocket)
        await manager.send_message(client_id, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_client(self, manager):
        """Test sending a message to a client that doesn't exist."""
        message = {"type": "test", "data": "hello"}

        # Should not raise an error
        await manager.send_message("nonexistent_client", message)

    @pytest.mark.asyncio
    async def test_send_multiple_messages(self, manager, mock_websocket):
        """Test sending multiple messages to a client."""
        client_id = "test_client_1"
        messages = [
            {"type": "test1", "data": "hello"},
            {"type": "test2", "data": "world"}
        ]

        await manager.connect(client_id, mock_websocket)
        await manager.send_messages(client_id, messages)

        assert mock_websocket.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_message(self, manager, mock_websocket):
        """Test broadcasting a message to all connected clients."""
        # Connect multiple clients
        ws1 = Mock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = Mock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect("client_1", ws1)
        await manager.connect("client_2", ws2)

        message = {"type": "broadcast", "data": "hello all"}
        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_multiple_clients(self, manager):
        """Test managing multiple clients simultaneously."""
        ws1 = Mock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = Mock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect("client_1", ws1)
        await manager.connect("client_2", ws2)

        assert len(manager.active_connections) == 2
        assert "client_1" in manager.active_connections
        assert "client_2" in manager.active_connections

        manager.disconnect("client_1")

        assert len(manager.active_connections) == 1
        assert "client_2" in manager.active_connections

    @pytest.mark.asyncio
    @patch('app.websocket.get_container')
    async def test_pipeline_lazy_initialization(self, mock_get_container, manager):
        """Test that pipeline is lazily initialized."""
        # Initially, pipeline should be None
        assert manager._pipeline is None

        # Mock the container
        mock_container = Mock()
        mock_container.whisper_service = Mock()
        mock_container.context_analyzer = Mock()
        mock_container.trigger_engine = Mock()
        mock_container.meme_manager = Mock()
        mock_get_container.return_value = mock_container

        # Access pipeline property
        pipeline = manager.pipeline

        assert pipeline is not None
        assert manager._pipeline is not None
        mock_get_container.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnect_same_client(self, manager, mock_websocket):
        """Test reconnecting the same client ID."""
        client_id = "test_client_1"

        # First connection
        await manager.connect(client_id, mock_websocket)
        assert client_id in manager.active_connections

        # Reconnect with new websocket
        new_ws = Mock()
        new_ws.accept = AsyncMock()
        await manager.connect(client_id, new_ws)

        # Should replace the old connection
        assert manager.active_connections[client_id] == new_ws


@pytest.mark.integration
class TestWebSocketMessageTypes:
    """Tests for different WebSocket message types."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_transcription_message(self, manager, mock_websocket):
        """Test sending a transcription message."""
        client_id = "test_client"
        message = {
            "type": MessageType.TRANSCRIPTION,
            "text": "test transcription"
        }

        await manager.connect(client_id, mock_websocket)
        await manager.send_message(client_id, message)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.TRANSCRIPTION
        assert call_args["text"] == "test transcription"

    @pytest.mark.asyncio
    async def test_match_message(self, manager, mock_websocket):
        """Test sending a match message."""
        client_id = "test_client"
        message = {
            "type": MessageType.MATCH,
            "matched_tags": ["tag1", "tag2"],
            "transcription": "test text"
        }

        await manager.connect(client_id, mock_websocket)
        await manager.send_message(client_id, message)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.MATCH
        assert call_args["matched_tags"] == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_trigger_message(self, manager, mock_websocket):
        """Test sending a trigger message."""
        client_id = "test_client"
        message = {
            "type": MessageType.TRIGGER,
            "meme_id": 1,
            "filename": "test.mp3",
            "matched_tags": ["tag1"]
        }

        await manager.connect(client_id, mock_websocket)
        await manager.send_message(client_id, message)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.TRIGGER
        assert call_args["meme_id"] == 1
        assert call_args["filename"] == "test.mp3"

    @pytest.mark.asyncio
    async def test_debug_message(self, manager, mock_websocket):
        """Test sending a debug message."""
        client_id = "test_client"
        message = {
            "type": MessageType.DEBUG,
            "level": "info",
            "message": "Test debug message"
        }

        await manager.connect(client_id, mock_websocket)
        await manager.send_message(client_id, message)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.DEBUG
        assert call_args["level"] == "info"

    @pytest.mark.asyncio
    async def test_error_message(self, manager, mock_websocket):
        """Test sending an error message."""
        client_id = "test_client"
        message = {
            "type": MessageType.DEBUG,
            "level": "error",
            "message": "Test error"
        }

        await manager.connect(client_id, mock_websocket)
        await manager.send_message(client_id, message)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.DEBUG
        assert call_args["level"] == "error"


@pytest.mark.integration
class TestConnectionManagerEdgeCases:
    """Tests for edge cases in connection management."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_send_to_disconnected_client(self, manager):
        """Test sending a message after client disconnects."""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()

        client_id = "test_client"
        await manager.connect(client_id, ws)
        manager.disconnect(client_id)

        # Should not raise an error
        await manager.send_message(client_id, {"type": "test"})

        # Message should not be sent
        ws.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_no_clients(self, manager):
        """Test broadcasting when no clients are connected."""
        # Should not raise an error
        await manager.broadcast({"type": "test"})

    @pytest.mark.asyncio
    async def test_empty_client_id(self, manager):
        """Test connecting with empty client ID."""
        ws = Mock()
        ws.accept = AsyncMock()

        await manager.connect("", ws)

        assert "" in manager.active_connections

    @pytest.mark.asyncio
    async def test_unicode_client_id(self, manager):
        """Test connecting with Unicode client ID."""
        ws = Mock()
        ws.accept = AsyncMock()

        client_id = "client_日本語_café"
        await manager.connect(client_id, ws)

        assert client_id in manager.active_connections
