"""
<<<<<<< HEAD
Audio Processing Pipeline for SOBUB AI.
=======
Audio Processing Pipeline for Sobub AI.
>>>>>>> 8a38096837c66815ff3d73c6d5cda79c89c6b57a

This module implements a clean, testable pipeline for processing audio chunks
following the Single Responsibility Principle.
"""
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from .whisper_service import WhisperService
from .context_analyzer import ContextAnalyzer
from .trigger_engine import TriggerEngine
from .meme_manager import MemeManager
from .database import get_setting
from .config import MessageType
from .logging_config import get_logger, PerformanceLogger


logger = get_logger(__name__)


# ============================================================================
# Data Classes for Pipeline Results
# ============================================================================

@dataclass
class TranscriptionResult:
    """Result from transcription step."""
    text: str
    language: str


@dataclass
class MatchResult:
    """Result from tag matching step."""
    matched_tags: List[str]
    match_scores: Dict[str, float]
    matching_memes: List[Dict]


@dataclass
class TriggerResult:
    """Result from trigger attempt."""
    triggered: bool
    meme: Optional[Dict] = None
    reason: Optional[str] = None  # Why it didn't trigger (if triggered=False)
    cooldown_remaining: Optional[int] = None


@dataclass
class ProcessingResult:
    """Complete result from audio processing pipeline."""
    transcription: Optional[TranscriptionResult] = None
    match: Optional[MatchResult] = None
    trigger: Optional[TriggerResult] = None
    error: Optional[str] = None


# ============================================================================
# Audio Processing Pipeline
# ============================================================================

class AudioProcessingPipeline:
    """
    Orchestrates the audio processing workflow.

    This class follows the Single Responsibility Principle by delegating
    specific tasks to specialized services while managing the overall flow.
    """

    def __init__(
        self,
        whisper_service: WhisperService,
        context_analyzer: ContextAnalyzer,
        trigger_engine: TriggerEngine,
        meme_manager: MemeManager,
    ):
        """
        Initialize the audio processing pipeline.

        Args:
            whisper_service: Service for audio transcription
            context_analyzer: Service for tag matching
            trigger_engine: Service for trigger logic
            meme_manager: Service for meme management
        """
        self.whisper = whisper_service
        self.analyzer = context_analyzer
        self.trigger = trigger_engine
        self.memes = meme_manager
        self.logger = logger

    async def process(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        use_stemming: bool = False,
    ) -> ProcessingResult:
        """
        Process an audio chunk through the complete pipeline.

        Args:
            audio_data: Raw audio bytes
            language: Language code for transcription (fetched from settings if None)
            use_stemming: Whether to use stemming for tag matching

        Returns:
            ProcessingResult containing all pipeline results
        """
        try:
            with PerformanceLogger("audio_processing_pipeline", self.logger):
                # Step 1: Get settings
                language = language or await self._get_language_setting()
                use_stemming = use_stemming or await self._get_stemming_setting()

                # Step 2: Transcribe audio
                transcription_result = await self._transcribe(audio_data, language)
                if not transcription_result:
                    return ProcessingResult(error="No transcription produced")

                # Step 3: Match tags
                match_result = await self._match_tags(
                    transcription_result.text,
                    use_stemming
                )
                if not match_result:
                    return ProcessingResult(
                        transcription=transcription_result,
                        error="No matching tags"
                    )

                # Step 4: Attempt trigger
                trigger_result = await self._attempt_trigger(match_result)

                # Step 5: Handle trigger success
                if trigger_result.triggered and trigger_result.meme:
                    await self._on_trigger_success(trigger_result.meme)

                return ProcessingResult(
                    transcription=transcription_result,
                    match=match_result,
                    trigger=trigger_result
                )

        except Exception as e:
            self.logger.error(f"Pipeline error: {e}", exc_info=True)
            return ProcessingResult(error=str(e))

    # ========================================================================
    # Pipeline Steps (Private Methods)
    # ========================================================================

    async def _get_language_setting(self) -> str:
        """Get language setting from database."""
        language = await get_setting("language")
        return language or "en"

    async def _get_stemming_setting(self) -> bool:
        """Get stemming setting from database."""
        use_stemming_str = await get_setting("use_stemming")
        return use_stemming_str and use_stemming_str.lower() == "true"

    async def _transcribe(
        self,
        audio_data: bytes,
        language: str
    ) -> Optional[TranscriptionResult]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes
            language: Language code

        Returns:
            TranscriptionResult or None if no transcription
        """
        with PerformanceLogger(f"whisper_transcription_{language}", self.logger):
            text = self.whisper.transcribe_audio(audio_data, language=language)

        if not text:
            self.logger.debug("No transcription from audio chunk")
            return None

        self.logger.info(f"Transcribed ({language}): {text}")
        return TranscriptionResult(text=text, language=language)

    async def _match_tags(
        self,
        transcription: str,
        use_stemming: bool
    ) -> Optional[MatchResult]:
        """
        Match tags from transcription.

        Args:
            transcription: Transcribed text
            use_stemming: Whether to use stemming

        Returns:
            MatchResult or None if no matches
        """
        # Get all memes
        all_memes = await self.memes.get_all()
        if not all_memes:
            self.logger.warning("No memes in database")
            return None

        # Extract unique tags
        all_tags = self.analyzer.get_unique_tags_from_memes(all_memes)

        # Match tags
        matched_tags, match_scores = self.analyzer.match_tags(
            transcription,
            all_tags,
            use_stemming=use_stemming
        )

        if not matched_tags:
            self.logger.debug(f"No tags matched for: {transcription}")
            return None

        self.logger.info(f"Matched tags: {matched_tags}")

        # Get matching memes
        matching_memes = await self.memes.get_by_tags(matched_tags)

        return MatchResult(
            matched_tags=matched_tags,
            match_scores=match_scores,
            matching_memes=matching_memes
        )

    async def _attempt_trigger(
        self,
        match_result: MatchResult
    ) -> TriggerResult:
        """
        Attempt to trigger a meme.

        Args:
            match_result: Result from tag matching

        Returns:
            TriggerResult indicating whether trigger succeeded
        """
        triggered_meme = self.trigger.attempt_trigger(
            match_result.matching_memes,
            match_result.match_scores
        )

        if triggered_meme:
            self.logger.info(f"✓ Triggered meme: {triggered_meme['filename']}")
            return TriggerResult(
                triggered=True,
                meme=triggered_meme
            )
        else:
            # Determine why it didn't trigger
            cooldown_remaining = self.trigger.get_cooldown_remaining()
            if cooldown_remaining > 0:
                self.logger.debug(f"Cooldown active: {cooldown_remaining}s remaining")
                return TriggerResult(
                    triggered=False,
                    reason="cooldown",
                    cooldown_remaining=cooldown_remaining
                )
            else:
                self.logger.debug("Probability check failed")
                return TriggerResult(
                    triggered=False,
                    reason="probability"
                )

    async def _on_trigger_success(self, meme: Dict) -> None:
        """
        Handle successful trigger (increment play count, etc.).

        Args:
            meme: The triggered meme
        """
        await self.memes.increment_play_count(meme["id"])
        self.logger.info(f"Incremented play count for meme {meme['id']}")


# ============================================================================
# Message Builder (Separates pipeline from messaging concerns)
# ============================================================================

class PipelineMessageBuilder:
    """
    Builds WebSocket messages from pipeline results.

    This separates the concern of message formatting from the
    audio processing pipeline logic.
    """

    @staticmethod
    def build_transcription_message(result: TranscriptionResult) -> Dict:
        """Build transcription message."""
        return {
            "type": MessageType.TRANSCRIPTION,
            "text": result.text
        }

    @staticmethod
    def build_match_message(
        result: MatchResult,
        transcription: str
    ) -> Dict:
        """Build match notification message."""
        return {
            "type": MessageType.MATCH,
            "matched_tags": result.matched_tags,
            "transcription": transcription
        }

    @staticmethod
    def build_trigger_message(
        trigger_result: TriggerResult,
        matched_tags: List[str]
    ) -> Dict:
        """Build trigger message."""
        return {
            "type": MessageType.TRIGGER,
            "meme_id": trigger_result.meme["id"],
            "filename": trigger_result.meme["filename"],
            "matched_tags": matched_tags
        }

    @staticmethod
    def build_no_memes_message() -> Dict:
        """Build 'no memes in database' message."""
        return {
            "type": MessageType.DEBUG,
            "level": "warning",
            "message": "No memes in database"
        }

    @staticmethod
    def build_no_match_message() -> Dict:
        """Build 'no matching tags' message."""
        return {
            "type": MessageType.DEBUG,
            "level": "info",
            "message": "No matching tags found"
        }

    @staticmethod
    def build_cooldown_message(seconds_remaining: int) -> Dict:
        """Build cooldown active message."""
        return {
            "type": MessageType.DEBUG,
            "level": "cooldown",
            "message": f"Cooldown active: {seconds_remaining}s remaining"
        }

    @staticmethod
    def build_probability_message() -> Dict:
        """Build probability check failed message."""
        return {
            "type": MessageType.DEBUG,
            "level": "probability",
            "message": "Probability check failed (unlucky roll)"
        }

    @staticmethod
    def build_error_message(error: str) -> Dict:
        """Build error message."""
        return {
            "type": MessageType.DEBUG,
            "level": "error",
            "message": f"Error: {error}"
        }

    @classmethod
    def build_messages_from_result(
        cls,
        result: ProcessingResult
    ) -> List[Dict]:
        """
        Build all relevant messages from a processing result.

        Args:
            result: ProcessingResult from pipeline

        Returns:
            List of messages to send to client
        """
        messages = []

        # Error handling
        if result.error:
            # No transcription is normal (silence, background noise) - don't show as error
            if "No transcription produced" in result.error:
                return []  # Return empty list - no message needed

            if "No memes in database" in result.error:
                messages.append(cls.build_no_memes_message())
            elif "No matching tags" in result.error:
                if result.transcription:
                    messages.append(cls.build_transcription_message(result.transcription))
                messages.append(cls.build_no_match_message())
            else:
                messages.append(cls.build_error_message(result.error))
            return messages

        # Transcription
        if result.transcription:
            messages.append(cls.build_transcription_message(result.transcription))

        # Match
        if result.match:
            messages.append(
                cls.build_match_message(result.match, result.transcription.text)
            )

        # Trigger
        if result.trigger:
            if result.trigger.triggered:
                messages.append(
                    cls.build_trigger_message(result.trigger, result.match.matched_tags)
                )
            else:
                # Send debug message explaining why it didn't trigger
                if result.trigger.reason == "cooldown":
                    messages.append(
                        cls.build_cooldown_message(result.trigger.cooldown_remaining)
                    )
                elif result.trigger.reason == "probability":
                    messages.append(cls.build_probability_message())

        return messages
