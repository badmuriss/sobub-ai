import whisper
import torch
import numpy as np
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self, model_name: str = "base"):
        """Initialize Whisper model with GPU support."""
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
    def load_model(self):
        """Load the Whisper model."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
    
    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes (WAV format expected)
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            if self.model is None:
                self.load_model()
            
            # Convert bytes to numpy array
            # Assuming 16-bit PCM audio
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Whisper expects audio at 16kHz
            # If the audio is already at 16kHz, we can use it directly
            result = self.model.transcribe(
                audio_np,
                language="en",  # Can be made configurable
                fp16=(self.device == "cuda")  # Use FP16 on GPU for speed
            )
            
            transcribed_text = result["text"].strip()
            
            if transcribed_text:
                logger.info(f"Transcribed: {transcribed_text}")
                return transcribed_text
            
            return None
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio from file path.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            if self.model is None:
                self.load_model()
            
            result = self.model.transcribe(
                audio_path,
                language="en",
                fp16=(self.device == "cuda")
            )
            
            return result["text"].strip()
            
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return None


# Global instance
whisper_service = WhisperService(model_name="base")
