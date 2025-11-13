from faster_whisper import WhisperModel
import torch
import numpy as np
import io
import tempfile
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self, model_name: str = "base"):
        """Initialize Whisper model with GPU support."""
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        logger.info(f"Using device: {self.device} with compute_type: {self.compute_type}")

    def load_model(self):
        """Load the Whisper model."""
        if self.model is None:
            logger.info(f"Loading faster-whisper model: {self.model_name}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root="/app/models"
            )
            logger.info("faster-whisper model loaded successfully")

    def _segments_to_text(self, segments, info) -> str:
        """Convert segments generator to text string."""
        # Materialize all segments and concatenate text
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
        return "".join(text_parts).strip()

    def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (WebM/Opus format from browser)

        Returns:
            Transcribed text or None if transcription fails
        """
        temp_file = None
        temp_file_path = None
        try:
            if self.model is None:
                self.load_model()

            # Skip very small chunks (likely incomplete)
            if len(audio_data) < 1000:  # Less than 1KB
                logger.debug(f"Skipping tiny audio chunk ({len(audio_data)} bytes)")
                return None

            # Save audio data to temporary file
            # WebM needs to be decoded by ffmpeg, which faster-whisper handles automatically
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            # Transcribe using file path (faster-whisper handles WebM decoding)
            segments, info = self.model.transcribe(
                temp_file_path,
                language=language,  # Configurable language (en, es, pt, etc.)
                beam_size=5,        # Default faster-whisper beam size for better accuracy
                vad_filter=True     # Voice Activity Detection to filter out silence
            )

            transcribed_text = self._segments_to_text(segments, info)

            if transcribed_text:
                logger.info(f"Transcribed: {transcribed_text}")
                return transcribed_text

            return None

        except Exception as e:
            # Don't spam logs with invalid WebM chunk errors (common with MediaRecorder)
            if "Invalid data found" in str(e) or "1094995529" in str(e):
                logger.debug(f"Skipping invalid audio chunk (incomplete WebM data)")
            else:
                logger.error(f"Transcription error: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

    
# Global instance
whisper_service = WhisperService(model_name="base")
