"""
Whisper Service for speech-to-text transcription.

This module provides a service for transcribing audio using the faster-whisper
implementation, which is optimized for GPU acceleration.
"""
from faster_whisper import WhisperModel
import torch
import tempfile
import os
from typing import Optional

from .logging_config import get_logger
from .config import WhisperConfig, DefaultSettings

logger = get_logger(__name__)


class WhisperService:
    """
    Service for speech-to-text transcription using faster-whisper.

    This service provides GPU-accelerated audio transcription using the
    faster-whisper implementation of OpenAI's Whisper model.
    """

    def __init__(self, model_name: str = DefaultSettings.WHISPER_MODEL):
        """
        Initialize Whisper service.

        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self.device = WhisperConfig.DEVICE if torch.cuda.is_available() else "cpu"
        self.compute_type = WhisperConfig.COMPUTE_TYPE if self.device == "cuda" else "int8"
        logger.info(f"WhisperService initialized: device={self.device}, compute_type={self.compute_type}")

    def load_model(self) -> None:
        """Load the Whisper model from disk or download if not cached."""
        if self.model is None:
            from .config import StorageConfig
            logger.info(f"Loading faster-whisper model: {self.model_name}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=StorageConfig.MODELS_DIR
            )
            logger.info(f"Model {self.model_name} loaded successfully")

    def _segments_to_text(self, segments) -> str:
        """
        Convert segments generator to text string.

        Args:
            segments: Generator of transcription segments

        Returns:
            Concatenated text from all segments
        """
        text_parts = [segment.text for segment in segments]
        return "".join(text_parts).strip()

    def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (WebM/Opus format from browser)
            language: Language code (en, pt, es, etc.)

        Returns:
            Transcribed text or None if transcription fails
        """
        temp_file_path = None
        try:
            if self.model is None:
                self.load_model()

            # Skip very small chunks (likely incomplete)
            if len(audio_data) < DefaultSettings.MIN_AUDIO_CHUNK_SIZE:
                logger.debug(f"Skipping tiny audio chunk ({len(audio_data)} bytes)")
                return None

            # Save audio data to temporary file
            # WebM needs to be decoded by ffmpeg, which faster-whisper handles automatically
            with tempfile.NamedTemporaryFile(
                suffix=f'.{DefaultSettings.AUDIO_FORMAT}',
                delete=False,
                prefix=DefaultSettings.TEMP_AUDIO_PREFIX
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            # Transcribe using file path (faster-whisper handles WebM decoding)
            segments, _ = self.model.transcribe(
                temp_file_path,
                language=language,
                beam_size=WhisperConfig.BEAM_SIZE,
                vad_filter=WhisperConfig.VAD_FILTER
            )

            transcribed_text = self._segments_to_text(segments)

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
