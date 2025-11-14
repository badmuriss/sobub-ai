import os
import shutil
from typing import List, Optional, Dict
from pathlib import Path
import logging

from app.database import (
    create_meme,
    get_all_memes,
    get_meme_by_id,
    update_meme_tags,
    delete_meme,
    get_memes_by_tags,
    increment_play_count
)
from app.config import StorageConfig

logger = logging.getLogger(__name__)

AUDIO_DIR = StorageConfig.AUDIO_DIR


class MemeManager:
    """Manages meme audio files and database operations."""
    
    def __init__(self):
        self.audio_path = Path(AUDIO_DIR)
        self.audio_path.mkdir(parents=True, exist_ok=True)
    
    async def add_meme(self, file_content: bytes, filename: str, tags: List[str]) -> Dict:
        """
        Add a new meme to the library.
        
        Args:
            file_content: Audio file bytes
            filename: Original filename
            tags: List of tags for the meme
            
        Returns:
            Created meme dict
        """
        # Ensure filename is safe
        safe_filename = self._sanitize_filename(filename)
        
        # Save file to disk
        file_path = self.audio_path / safe_filename
        
        # Handle duplicate filenames
        if file_path.exists():
            base, ext = os.path.splitext(safe_filename)
            counter = 1
            while file_path.exists():
                safe_filename = f"{base}_{counter}{ext}"
                file_path = self.audio_path / safe_filename
                counter += 1
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"Saved audio file: {safe_filename}")
        
        # Add to database
        meme_id = await create_meme(safe_filename, tags)
        
        # Return created meme
        meme = await get_meme_by_id(meme_id)
        return meme
    
    async def get_all(self) -> List[Dict]:
        """Get all memes from database."""
        return await get_all_memes()
    
    async def get_by_id(self, meme_id: int) -> Optional[Dict]:
        """Get a specific meme by ID."""
        return await get_meme_by_id(meme_id)
    
    async def update_tags(self, meme_id: int, tags: List[str]) -> bool:
        """Update tags for a meme."""
        meme = await get_meme_by_id(meme_id)
        if not meme:
            return False
        
        await update_meme_tags(meme_id, tags)
        logger.info(f"Updated tags for meme ID {meme_id}")
        return True
    
    async def delete(self, meme_id: int) -> bool:
        """
        Delete a meme from database and filesystem.
        
        Args:
            meme_id: ID of meme to delete
            
        Returns:
            True if successful
        """
        meme = await get_meme_by_id(meme_id)
        if not meme:
            return False
        
        # Delete file from disk
        file_path = self.audio_path / meme["filename"]
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted audio file: {meme['filename']}")
        
        # Delete from database
        await delete_meme(meme_id)
        logger.info(f"Deleted meme ID {meme_id} from database")
        
        return True
    
    async def get_by_tags(self, tags: List[str]) -> List[Dict]:
        """Get memes that match any of the provided tags."""
        return await get_memes_by_tags(tags)
    
    async def increment_play_count(self, meme_id: int):
        """Increment play count for a meme."""
        await increment_play_count(meme_id)
    
    def get_audio_file_path(self, filename: str) -> Path:
        """Get the full path to an audio file."""
        return self.audio_path / filename
    
    def audio_file_exists(self, filename: str) -> bool:
        """Check if an audio file exists."""
        return (self.audio_path / filename).exists()
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        # Remove any path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
        filename = "".join(c if c in safe_chars else "_" for c in filename)
        
        # Ensure it's not empty
        if not filename:
            filename = "audio.mp3"
        
        return filename
    
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags from all memes."""
        memes = await get_all_memes()
        all_tags = set()
        for meme in memes:
            all_tags.update(meme["tags"])
        return sorted(list(all_tags))


# Global instance
meme_manager = MemeManager()
