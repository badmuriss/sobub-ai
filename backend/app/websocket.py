from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict

from app.whisper_service import whisper_service
from app.context_analyzer import context_analyzer
from app.trigger_engine import trigger_engine
from app.meme_manager import meme_manager
from app.database import get_setting

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        for connection in self.active_connections.values():
            await connection.send_json(message)


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


async def process_audio_chunk(client_id: str, audio_data: bytes):
    """
    Process an audio chunk: transcribe, analyze, and potentially trigger a meme.

    Args:
        client_id: Client identifier
        audio_data: Raw audio bytes
    """
    try:
        # Get settings
        language = await get_setting("language") or "en"
        use_stemming_str = await get_setting("use_stemming") or "true"
        use_stemming = use_stemming_str.lower() == "true"

        # Transcribe audio
        transcribed_text = whisper_service.transcribe_audio(audio_data, language=language)

        if not transcribed_text:
            logger.debug("No transcription from audio chunk")
            return

        logger.info(f"Transcribed ({language}): {transcribed_text}")

        # Send transcription back to client
        await manager.send_message(client_id, {
            "type": "transcription",
            "text": transcribed_text
        })

        # Get all memes to extract tags
        all_memes = await meme_manager.get_all()

        if not all_memes:
            logger.warning("No memes in database")
            await manager.send_message(client_id, {
                "type": "debug",
                "level": "warning",
                "message": "No memes in database"
            })
            return

        # Extract all available tags
        all_tags = context_analyzer.get_unique_tags_from_memes(all_memes)

        # Match tags from transcribed text with optional stemming
        matched_tags, match_scores = context_analyzer.match_tags(transcribed_text, all_tags, use_stemming=use_stemming)

        if not matched_tags:
            logger.debug(f"No tags matched for: {transcribed_text}")
            await manager.send_message(client_id, {
                "type": "debug",
                "level": "info",
                "message": f"No matching tags found"
            })
            return

        # Send match notification
        logger.info(f"Matched tags: {matched_tags}")
        await manager.send_message(client_id, {
            "type": "match",
            "matched_tags": matched_tags,
            "transcription": transcribed_text
        })

        # Get memes that match the tags
        matching_memes = await meme_manager.get_by_tags(matched_tags)

        # Attempt to trigger a meme (pass scores for preference-based selection)
        triggered_meme = trigger_engine.attempt_trigger(matching_memes, match_scores)

        if triggered_meme:
            # Increment play count
            await meme_manager.increment_play_count(triggered_meme["id"])

            # Send trigger event to client
            await manager.send_message(client_id, {
                "type": "trigger",
                "meme_id": triggered_meme["id"],
                "filename": triggered_meme["filename"],
                "matched_tags": matched_tags
            })

            logger.info(f"✓ Triggered meme {triggered_meme['filename']} for client {client_id}")
        else:
            # Send status update (for debugging)
            cooldown_remaining = trigger_engine.get_cooldown_remaining()
            if cooldown_remaining > 0:
                logger.debug(f"Cooldown active: {cooldown_remaining}s remaining")
                await manager.send_message(client_id, {
                    "type": "debug",
                    "level": "cooldown",
                    "message": f"Cooldown active: {cooldown_remaining}s remaining"
                })
            else:
                logger.debug("Probability check failed")
                await manager.send_message(client_id, {
                    "type": "debug",
                    "level": "probability",
                    "message": "Probability check failed (unlucky roll)"
                })

    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        await manager.send_message(client_id, {
            "type": "debug",
            "level": "error",
            "message": f"Error: {str(e)}"
        })


async def handle_control_message(client_id: str, data: dict):
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
        status = trigger_engine.get_status()
        await manager.send_message(client_id, {
            "type": "status",
            "data": status
        })

    elif message_type == "audio_ended":
        # Start cooldown when audio finishes playing
        trigger_engine.start_cooldown()
        logger.info(f"Audio ended for client {client_id}, cooldown started")

    else:
        logger.warning(f"Unknown control message type: {message_type}")
