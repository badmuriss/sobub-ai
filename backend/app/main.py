from fastapi import FastAPI, WebSocket, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
import os

from app.database import (
    init_database,
    get_all_settings,
    update_setting
)
from app.models import (
    MemeResponse,
    SettingsResponse,
    SettingsUpdate
)
from app.meme_manager import meme_manager
from app.whisper_service import whisper_service
from app.trigger_engine import trigger_engine
from app.websocket import handle_websocket
from app.utils import parse_tags, validate_tags
from app.logging_config import setup_logging, get_logger
from app.container import initialize_container

# Configure logging (reads from environment variables)
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SOBUB AI API",
    description="Silence Occasionally Broken Up By AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting SOBUB AI backend...")

    # Initialize database
    await init_database()
    logger.info("Database initialized")

    # Initialize dependency injection container
    settings = await get_all_settings()
    whisper_model = settings.get("whisper_model", "base")
    initialize_container(whisper_model=whisper_model)
    logger.info("Service container initialized")

    # Load Whisper model (via container)
    from app.container import get_container
    container = get_container()
    container.whisper_service.load_model()
    logger.info("Whisper model loaded")

    # Load settings into trigger engine (via container)
    container.trigger_engine.set_cooldown(int(settings.get("cooldown_seconds", "300")))
    container.trigger_engine.set_probability(float(settings.get("trigger_probability", "30")))
    logger.info("Trigger engine configured")

    logger.info("SOBUB AI backend started successfully")


@app.get(
    "/",
    summary="Root endpoint",
    description="Get API information and status",
    response_description="API metadata",
    tags=["Info"]
)
async def root():
    """
    Root endpoint providing API information.

    Returns:
        Dictionary containing app name, description, and status
    """
    return {
        "app": "SOBUB AI",
        "description": "Silence Occasionally Broken Up By AI",
        "status": "running"
    }


@app.get(
    "/health",
    summary="Health check",
    description="Check if the API is running and healthy",
    response_description="Health status",
    tags=["Info"]
)
async def health():
    """
    Health check endpoint.

    Returns:
        Dictionary with health status
    """
    return {"status": "healthy"}


# WebSocket endpoint for audio streaming
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time audio processing.
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    await handle_websocket(websocket, client_id)


# Meme management endpoints
@app.get(
    "/api/memes",
    response_model=List[MemeResponse],
    summary="List all memes",
    description="Retrieve all meme audio files with metadata including tags, play count, and creation timestamp",
    response_description="List of all meme objects",
    tags=["Memes"]
)
async def get_memes():
    """Get all memes from the database."""
    memes = await meme_manager.get_all()
    return memes


@app.post(
    "/api/memes",
    response_model=MemeResponse,
    summary="Upload new meme",
    description="Upload a new meme audio file (MP3 format only) with associated tags for context matching",
    response_description="The created meme object",
    tags=["Memes"]
)
async def create_meme(
    file: UploadFile = File(..., description="MP3 audio file"),
    tags: str = Form(..., description="Comma-separated tags (e.g., 'goal, football, sports')")
):
    """
    Upload a new meme audio file.

    Args:
        file: Audio file in MP3 format
        tags: Comma-separated list of tags for context matching

    Returns:
        The created meme object with ID and metadata

    Raises:
        HTTPException: 400 if file is not MP3 or tags are invalid
    """
    # Parse and validate tags
    tag_list = parse_tags(tags)
    is_valid, error_message = validate_tags(tag_list)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # Read file content
    file_content = await file.read()

    # Validate file extension
    if not file.filename.lower().endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only MP3 files are supported")

    # Add meme
    meme = await meme_manager.add_meme(file_content, file.filename, tag_list)

    return meme


@app.get(
    "/api/memes/{meme_id}",
    response_model=MemeResponse,
    summary="Get meme by ID",
    description="Retrieve a specific meme by its unique identifier",
    response_description="The meme object",
    tags=["Memes"]
)
async def get_meme(meme_id: int):
    """
    Get a specific meme by ID.

    Args:
        meme_id: Unique meme identifier

    Returns:
        The meme object

    Raises:
        HTTPException: 404 if meme not found
    """
    meme = await meme_manager.get_by_id(meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    return meme


@app.put(
    "/api/memes/{meme_id}",
    summary="Update meme tags",
    description="Update the tags associated with a meme",
    response_description="Success message",
    tags=["Memes"]
)
async def update_meme(
    meme_id: int,
    tags: str = Form(..., description="Comma-separated tags (e.g., 'goal, football, sports')")
):
    """
    Update meme tags.

    Args:
        meme_id: Unique meme identifier
        tags: Comma-separated list of new tags

    Returns:
        Success message

    Raises:
        HTTPException: 400 if tags are invalid, 404 if meme not found
    """
    # Parse and validate tags
    tag_list = parse_tags(tags)
    is_valid, error_message = validate_tags(tag_list)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    success = await meme_manager.update_tags(meme_id, tag_list)

    if not success:
        raise HTTPException(status_code=404, detail="Meme not found")

    return {"message": "Meme updated successfully"}


@app.delete(
    "/api/memes/{meme_id}",
    summary="Delete meme",
    description="Permanently delete a meme and its associated audio file",
    response_description="Success message",
    tags=["Memes"]
)
async def delete_meme(meme_id: int):
    """
    Delete a meme.

    Args:
        meme_id: Unique meme identifier

    Returns:
        Success message

    Raises:
        HTTPException: 404 if meme not found
    """
    success = await meme_manager.delete(meme_id)

    if not success:
        raise HTTPException(status_code=404, detail="Meme not found")

    return {"message": "Meme deleted successfully"}


@app.get(
    "/api/memes/{meme_id}/audio",
    summary="Download meme audio",
    description="Stream or download the MP3 audio file for a specific meme",
    response_description="Audio file (MP3)",
    tags=["Memes"]
)
async def get_meme_audio(meme_id: int):
    """
    Get the audio file for a meme.

    Args:
        meme_id: Unique meme identifier

    Returns:
        FileResponse containing the MP3 audio file

    Raises:
        HTTPException: 404 if meme or audio file not found
    """
    meme = await meme_manager.get_by_id(meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")

    file_path = meme_manager.get_audio_file_path(meme["filename"])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=meme["filename"]
    )


@app.get(
    "/api/tags",
    summary="Get all tags",
    description="Retrieve all unique tags from all memes in the database",
    response_description="List of unique tags",
    tags=["Memes"]
)
async def get_all_tags():
    """
    Get all unique tags from all memes.

    Returns:
        Dictionary containing list of all unique tags
    """
    tags = await meme_manager.get_all_tags()
    return {"tags": tags}


# Settings endpoints
@app.get(
    "/api/settings",
    response_model=SettingsResponse,
    summary="Get settings",
    description="Retrieve current application settings including cooldown, probability, and Whisper configuration",
    response_description="Current settings",
    tags=["Settings"]
)
async def get_settings():
    """
    Get current settings.

    Returns:
        Current application settings including:
        - cooldown_seconds: Time between triggers
        - trigger_probability: Probability (0-100) of triggering
        - whisper_model: Speech recognition model size
        - chunk_length_seconds: Audio chunk length
        - language: Transcription language code
        - use_stemming: Whether to use word stemming
    """
    settings = await get_all_settings()
    return {
        "cooldown_seconds": int(settings.get("cooldown_seconds", "300")),
        "trigger_probability": float(settings.get("trigger_probability", "30")),
        "whisper_model": settings.get("whisper_model", "base"),
        "chunk_length_seconds": int(settings.get("chunk_length_seconds", "3")),
        "language": settings.get("language", "en"),
        "use_stemming": settings.get("use_stemming", "true")
    }


@app.put(
    "/api/settings",
    summary="Update settings",
    description="Update one or more application settings. Only provided fields will be updated.",
    response_description="Success message",
    tags=["Settings"]
)
async def update_settings(settings: SettingsUpdate):
    """
    Update settings.

    All fields are optional - only provided fields will be updated.

    Args:
        settings: Settings object with fields to update

    Returns:
        Success message

    Note:
        - Changing whisper_model will force model reload on next transcription
        - Changing cooldown_seconds or trigger_probability updates the trigger engine immediately
    """
    if settings.cooldown_seconds is not None:
        await update_setting("cooldown_seconds", str(settings.cooldown_seconds))
        trigger_engine.set_cooldown(settings.cooldown_seconds)

    if settings.trigger_probability is not None:
        await update_setting("trigger_probability", str(settings.trigger_probability))
        trigger_engine.set_probability(settings.trigger_probability)

    if settings.chunk_length_seconds is not None:
        await update_setting("chunk_length_seconds", str(settings.chunk_length_seconds))

    if settings.language is not None:
        await update_setting("language", settings.language)

    if settings.whisper_model is not None:
        await update_setting("whisper_model", settings.whisper_model)
        # Reload whisper model with new selection
        whisper_service.model_name = settings.whisper_model
        whisper_service.model = None  # Force reload on next transcription
        logger.info(f"Whisper model changed to: {settings.whisper_model}")

    if settings.use_stemming is not None:
        await update_setting("use_stemming", settings.use_stemming)
        logger.info(f"Use stemming set to: {settings.use_stemming}")

    return {"message": "Settings updated successfully"}


@app.get(
    "/api/status",
    summary="Get trigger status",
    description="Get current trigger engine status including cooldown state and last trigger time",
    response_description="Trigger engine status",
    tags=["Status"]
)
async def get_status():
    """
    Get current trigger engine status.

    Returns:
        Status object containing:
        - cooldown_seconds: Configured cooldown duration
        - trigger_probability: Configured trigger probability
        - cooldown_active: Whether cooldown is currently active
        - cooldown_remaining: Seconds remaining in cooldown (0 if inactive)
        - last_trigger_time: ISO timestamp of last trigger (null if never triggered)
    """
    status = trigger_engine.get_status()
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
