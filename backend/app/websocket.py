"""
WebSocket handler for SOBUB AI.

Handles real-time audio streaming, transcription, and meme triggering.
"""
from fastapi import WebSocket, WebSocketDisconnect
import json
from typing import Dict

from .audio_pipeline import AudioProcessingPipeline, PipelineMessageBuilder
from .container import get_container
from .config import MessageType
from .logging_config import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and audio processing pipeline."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self._pipeline: AudioProcessingPipeline = None

    @property
    def pipeline(self) -> AudioProcessingPipeline:
        """
        Get or create the audio processing pipeline.

        Returns:
            AudioProcessingPipeline instance
        """
        if self._pipeline is None:
            container = get_container()
            self._pipeline = AudioProcessingPipeline(
                whisper_service=container.whisper_service,
                context_analyzer=container.context_analyzer,
                trigger_engine=container.trigger_engine,
                meme_manager=container.meme_manager,
            )
        return self._pipeline

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """
        Accept and store a new WebSocket connection.

        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            client_id: Client identifier to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict) -> None:
        """
        Send a message to a specific client.

        Args:
            client_id: Target client identifier
            message: Message dictionary to send
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def send_messages(self, client_id: str, messages: list) -> None:
        """
        Send multiple messages to a client.

        Args:
            client_id: Target client identifier
            messages: List of message dictionaries to send
        """
        for message in messages:
            await self.send_message(client_id, message)

    async def broadcast(self, message: dict) -> None:
        """
        Send a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
        """
        for connection in self.active_connections.values():
            await connection.send_json(message)


# Global connection manager instance
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, client_id: str):
    """
    Handle WebSocket connection for audio streaming and transcription.
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            # Receive audio data or control messages
            message = await websocket.receive()
            
            # Handle binary audio data
            if "bytes" in message:
                audio_data = message["bytes"]
                await process_audio_chunk(client_id, audio_data)
            
            # Handle text/JSON messages (control signals)
            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                    await handle_control_message(client_id, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)


async def process_audio_chunk(client_id: str, audio_data: bytes) -> None:
    """
    Process an audio chunk through the pipeline and send results to client.

    This function is now much simpler, delegating the complex processing
    logic to AudioProcessingPipeline and using PipelineMessageBuilder
    for message creation.

    Args:
        client_id: Client identifier
        audio_data: Raw audio bytes
    """
    # Process through pipeline
    result = await manager.pipeline.process(audio_data)

    # Build and send messages from result
    messages = PipelineMessageBuilder.build_messages_from_result(result)
    await manager.send_messages(client_id, messages)


async def handle_control_message(client_id: str, data: dict) -> None:
    """
    Handle control messages from client.

    Args:
        client_id: Client identifier
        data: Control message data
    """
    message_type = data.get("type")

    if message_type == "ping":
        await manager.send_message(client_id, {"type": "pong"})

    elif message_type == "get_status":
        container = get_container()
        status = container.trigger_engine.get_status()
        await manager.send_message(client_id, {
            "type": "status",
            "data": status
        })

    elif message_type == MessageType.AUDIO_ENDED:
        # Start cooldown when audio finishes playing
        container = get_container()
        container.trigger_engine.start_cooldown()
        logger.info(f"Audio ended for client {client_id}, cooldown started")

    else:
        logger.warning(f"Unknown control message type: {message_type}")
