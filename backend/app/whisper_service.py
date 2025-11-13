from faster_whisper import WhisperModel
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
            # faster-whisper returns (segments, info) tuple
            segments, info = self.model.transcribe(
                audio_np,
                language="en",  # Can be made configurable
                beam_size=5,     # Default faster-whisper beam size for better accuracy
                vad_filter=True  # Voice Activity Detection to filter out silence
            )

            transcribed_text = self._segments_to_text(segments, info)

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

            # faster-whisper returns (segments, info) tuple
            segments, info = self.model.transcribe(
                audio_path,
                language="en",
                beam_size=5,
                vad_filter=True
            )

            return self._segments_to_text(segments, info)

        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return None


# Global instance
whisper_service = WhisperService(model_name="base")
