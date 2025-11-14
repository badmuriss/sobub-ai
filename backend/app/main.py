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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
<<<<<<< Updated upstream
    logger.info("Starting Sobub AI backend...")
    
=======
    logger.info("Starting SOBUB AI backend...")

>>>>>>> Stashed changes
    # Initialize database
    await init_database()
    logger.info("Database initialized")
    
    # Load Whisper model
    whisper_service.load_model()
    logger.info("Whisper model loaded")
    
    # Load settings into trigger engine
    settings = await get_all_settings()
    trigger_engine.set_cooldown(int(settings.get("cooldown_seconds", "300")))
    trigger_engine.set_probability(float(settings.get("trigger_probability", "30")))
    logger.info("Trigger engine configured")
<<<<<<< Updated upstream
    
    logger.info("Sobub AI backend started successfully")
=======

    logger.info("SOBUB AI backend started successfully")
>>>>>>> Stashed changes


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "SOBUB AI",
        "description": "Silence Occasionally Broken Up By AI",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
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
@app.get("/api/memes", response_model=List[MemeResponse])
async def get_memes():
    """Get all memes."""
    memes = await meme_manager.get_all()
    return memes


@app.post("/api/memes", response_model=MemeResponse)
async def create_meme(
    file: UploadFile = File(...),
    tags: str = Form(...)
):
    """
    Upload a new meme audio file.
    
    Args:
        file: Audio file (MP3)
        tags: Comma-separated tags
    """
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    if not tag_list:
        raise HTTPException(status_code=400, detail="At least one tag is required")
    
    # Read file content
    file_content = await file.read()
    
    # Validate file extension
    if not file.filename.lower().endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only MP3 files are supported")
    
    # Add meme
    meme = await meme_manager.add_meme(file_content, file.filename, tag_list)
    
    return meme


@app.get("/api/memes/{meme_id}", response_model=MemeResponse)
async def get_meme(meme_id: int):
    """Get a specific meme by ID."""
    meme = await meme_manager.get_by_id(meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    return meme


@app.put("/api/memes/{meme_id}")
async def update_meme(meme_id: int, tags: str = Form(...)):
    """
    Update meme tags.
    
    Args:
        meme_id: Meme ID
        tags: Comma-separated tags
    """
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    if not tag_list:
        raise HTTPException(status_code=400, detail="At least one tag is required")
    
    success = await meme_manager.update_tags(meme_id, tag_list)
    
    if not success:
        raise HTTPException(status_code=404, detail="Meme not found")
    
    return {"message": "Meme updated successfully"}


@app.delete("/api/memes/{meme_id}")
async def delete_meme(meme_id: int):
    """Delete a meme."""
    success = await meme_manager.delete(meme_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Meme not found")
    
    return {"message": "Meme deleted successfully"}


@app.get("/api/memes/{meme_id}/audio")
async def get_meme_audio(meme_id: int):
    """
    Get the audio file for a meme.
    
    Args:
        meme_id: Meme ID
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


@app.get("/api/tags")
async def get_all_tags():
    """Get all unique tags from all memes."""
    tags = await meme_manager.get_all_tags()
    return {"tags": tags}


# Settings endpoints
@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current settings."""
    settings = await get_all_settings()
    return {
        "cooldown_seconds": int(settings.get("cooldown_seconds", "300")),
        "trigger_probability": float(settings.get("trigger_probability", "30")),
        "whisper_model": settings.get("whisper_model", "base"),
        "chunk_length_seconds": int(settings.get("chunk_length_seconds", "3")),
        "language": settings.get("language", "en"),
        "use_stemming": settings.get("use_stemming", "true")
    }


@app.put("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """
    Update settings.

    Args:
        settings: Updated settings
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


@app.get("/api/status")
async def get_status():
    """Get current trigger engine status."""
    status = trigger_engine.get_status()
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
