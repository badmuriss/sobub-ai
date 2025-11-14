"""
Unit tests for AudioProcessingPipeline.

Tests the pipeline orchestration logic with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.audio_pipeline import (
    AudioProcessingPipeline,
    PipelineMessageBuilder,
    TranscriptionResult,
    MatchResult,
    TriggerResult,
    ProcessingResult,
)
from app.config import MessageType


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_whisper():
    """Mock WhisperService."""
    mock = Mock()
    mock.transcribe_audio = Mock(return_value="test transcription")
    return mock


@pytest.fixture
def mock_analyzer():
    """Mock ContextAnalyzer."""
    mock = Mock()
    mock.get_unique_tags_from_memes = Mock(return_value=["goal", "football"])
    mock.match_tags = Mock(return_value=(["goal"], {"goal": 1}))
    return mock


@pytest.fixture
def mock_trigger():
    """Mock TriggerEngine."""
    mock = Mock()
    mock.attempt_trigger = Mock(return_value=None)
    mock.get_cooldown_remaining = Mock(return_value=0)
    return mock


@pytest.fixture
def mock_meme_manager():
    """Mock MemeManager."""
    mock = Mock()
    mock.get_all = AsyncMock(return_value=[
        {"id": 1, "filename": "test.mp3", "tags": ["goal", "football"]}
    ])
    mock.get_by_tags = AsyncMock(return_value=[
        {"id": 1, "filename": "test.mp3", "tags": ["goal", "football"]}
    ])
    mock.increment_play_count = AsyncMock()
    return mock


@pytest.fixture
def pipeline(mock_whisper, mock_analyzer, mock_trigger, mock_meme_manager):
    """Create a pipeline with mocked dependencies."""
    return AudioProcessingPipeline(
        whisper_service=mock_whisper,
        context_analyzer=mock_analyzer,
        trigger_engine=mock_trigger,
        meme_manager=mock_meme_manager,
    )


# =============================================================================
# Pipeline Tests
# =============================================================================

@pytest.mark.unit
class TestAudioProcessingPipeline:
    """Tests for the audio processing pipeline."""

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_full_success_path(
        self,
        mock_get_setting,
        pipeline,
        mock_trigger,
        mock_audio_data
    ):
        """Test complete successful processing pipeline."""
        # Mock settings
        mock_get_setting.side_effect = lambda key: {
            "language": "en",
            "use_stemming": "false"
        }.get(key)

        # Mock trigger success
        triggered_meme = {"id": 1, "filename": "test.mp3", "tags": ["goal"]}
        mock_trigger.attempt_trigger.return_value = triggered_meme

        result = await pipeline.process(mock_audio_data)

        assert result.transcription is not None
        assert result.transcription.text == "test transcription"
        assert result.match is not None
        assert result.match.matched_tags == ["goal"]
        assert result.trigger is not None
        assert result.trigger.triggered is True
        assert result.trigger.meme == triggered_meme
        assert result.error is None

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_no_transcription(
        self,
        mock_get_setting,
        pipeline,
        mock_whisper,
        mock_audio_data
    ):
        """Test pipeline when no transcription is produced."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        mock_whisper.transcribe_audio.return_value = ""

        result = await pipeline.process(mock_audio_data)

        assert result.transcription is None
        assert result.error == "No transcription produced"

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_no_matching_tags(
        self,
        mock_get_setting,
        pipeline,
        mock_analyzer,
        mock_audio_data
    ):
        """Test pipeline when no tags match."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        mock_analyzer.match_tags.return_value = ([], {})

        result = await pipeline.process(mock_audio_data)

        assert result.transcription is not None
        assert result.match is None
        assert result.error == "No matching tags"

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_no_memes_in_database(
        self,
        mock_get_setting,
        pipeline,
        mock_meme_manager,
        mock_audio_data
    ):
        """Test pipeline when database has no memes."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        mock_meme_manager.get_all.return_value = []

        result = await pipeline.process(mock_audio_data)

        assert result.transcription is not None
        assert result.match is None

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_cooldown_active(
        self,
        mock_get_setting,
        pipeline,
        mock_trigger,
        mock_audio_data
    ):
        """Test pipeline when cooldown is active."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        mock_trigger.attempt_trigger.return_value = None
        mock_trigger.get_cooldown_remaining.return_value = 60

        result = await pipeline.process(mock_audio_data)

        assert result.trigger is not None
        assert result.trigger.triggered is False
        assert result.trigger.reason == "cooldown"
        assert result.trigger.cooldown_remaining == 60

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_probability_failed(
        self,
        mock_get_setting,
        pipeline,
        mock_trigger,
        mock_audio_data
    ):
        """Test pipeline when probability check fails."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        mock_trigger.attempt_trigger.return_value = None
        mock_trigger.get_cooldown_remaining.return_value = 0

        result = await pipeline.process(mock_audio_data)

        assert result.trigger is not None
        assert result.trigger.triggered is False
        assert result.trigger.reason == "probability"

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_increments_play_count(
        self,
        mock_get_setting,
        pipeline,
        mock_trigger,
        mock_meme_manager,
        mock_audio_data
    ):
        """Test that play count is incremented on successful trigger."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        triggered_meme = {"id": 1, "filename": "test.mp3", "tags": ["goal"]}
        mock_trigger.attempt_trigger.return_value = triggered_meme

        await pipeline.process(mock_audio_data)

        mock_meme_manager.increment_play_count.assert_called_once_with(1)

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_with_exception(
        self,
        mock_get_setting,
        pipeline,
        mock_whisper,
        mock_audio_data
    ):
        """Test pipeline handles exceptions gracefully."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "false"}.get(key)
        mock_whisper.transcribe_audio.side_effect = Exception("Test error")

        result = await pipeline.process(mock_audio_data)

        assert result.error == "Test error"
        assert result.transcription is None

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_uses_provided_language(
        self,
        mock_get_setting,
        pipeline,
        mock_whisper,
        mock_audio_data
    ):
        """Test that provided language overrides settings."""
        result = await pipeline.process(mock_audio_data, language="pt")

        mock_whisper.transcribe_audio.assert_called_once()
        call_args = mock_whisper.transcribe_audio.call_args
        assert call_args[1]['language'] == "pt"

    @pytest.mark.asyncio
    @patch('app.audio_pipeline.get_setting')
    async def test_process_uses_stemming_setting(
        self,
        mock_get_setting,
        pipeline,
        mock_analyzer,
        mock_audio_data
    ):
        """Test that stemming setting is used."""
        mock_get_setting.side_effect = lambda key: {"language": "en", "use_stemming": "true"}.get(key)

        await pipeline.process(mock_audio_data)

        mock_analyzer.match_tags.assert_called_once()
        call_args = mock_analyzer.match_tags.call_args
        assert call_args[1]['use_stemming'] is True


# =============================================================================
# Message Builder Tests
# =============================================================================

@pytest.mark.unit
class TestPipelineMessageBuilder:
    """Tests for the message builder."""

    def test_build_transcription_message(self):
        """Test building transcription message."""
        result = TranscriptionResult(text="hello world", language="en")
        message = PipelineMessageBuilder.build_transcription_message(result)

        assert message["type"] == MessageType.TRANSCRIPTION
        assert message["text"] == "hello world"

    def test_build_match_message(self):
        """Test building match message."""
        result = MatchResult(
            matched_tags=["goal", "football"],
            match_scores={"goal": 1, "football": 1},
            matching_memes=[]
        )
        message = PipelineMessageBuilder.build_match_message(result, "That goal was great")

        assert message["type"] == MessageType.MATCH
        assert message["matched_tags"] == ["goal", "football"]
        assert message["transcription"] == "That goal was great"

    def test_build_trigger_message(self):
        """Test building trigger message."""
        trigger_result = TriggerResult(
            triggered=True,
            meme={"id": 1, "filename": "test.mp3", "tags": ["goal"]}
        )
        message = PipelineMessageBuilder.build_trigger_message(
            trigger_result,
            ["goal", "football"]
        )

        assert message["type"] == MessageType.TRIGGER
        assert message["meme_id"] == 1
        assert message["filename"] == "test.mp3"
        assert message["matched_tags"] == ["goal", "football"]

    def test_build_no_memes_message(self):
        """Test building no memes message."""
        message = PipelineMessageBuilder.build_no_memes_message()

        assert message["type"] == MessageType.DEBUG
        assert message["level"] == "warning"
        assert "No memes" in message["message"]

    def test_build_no_match_message(self):
        """Test building no match message."""
        message = PipelineMessageBuilder.build_no_match_message()

        assert message["type"] == MessageType.DEBUG
        assert message["level"] == "info"
        assert "No matching tags" in message["message"]

    def test_build_cooldown_message(self):
        """Test building cooldown message."""
        message = PipelineMessageBuilder.build_cooldown_message(60)

        assert message["type"] == MessageType.DEBUG
        assert message["level"] == "cooldown"
        assert "60s" in message["message"]

    def test_build_probability_message(self):
        """Test building probability message."""
        message = PipelineMessageBuilder.build_probability_message()

        assert message["type"] == MessageType.DEBUG
        assert message["level"] == "probability"
        assert "Probability" in message["message"]

    def test_build_error_message(self):
        """Test building error message."""
        message = PipelineMessageBuilder.build_error_message("Test error")

        assert message["type"] == MessageType.DEBUG
        assert message["level"] == "error"
        assert "Test error" in message["message"]

    def test_build_messages_from_result_success(self):
        """Test building messages from successful result."""
        result = ProcessingResult(
            transcription=TranscriptionResult(text="hello", language="en"),
            match=MatchResult(
                matched_tags=["goal"],
                match_scores={"goal": 1},
                matching_memes=[]
            ),
            trigger=TriggerResult(
                triggered=True,
                meme={"id": 1, "filename": "test.mp3", "tags": ["goal"]}
            )
        )

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 3  # transcription, match, trigger
        assert messages[0]["type"] == MessageType.TRANSCRIPTION
        assert messages[1]["type"] == MessageType.MATCH
        assert messages[2]["type"] == MessageType.TRIGGER

    def test_build_messages_from_result_no_transcription(self):
        """Test building messages when no transcription produced."""
        result = ProcessingResult(error="No transcription produced")

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 0  # Should return empty list (silence is normal)

    def test_build_messages_from_result_no_match(self):
        """Test building messages when no tags match."""
        result = ProcessingResult(
            transcription=TranscriptionResult(text="hello", language="en"),
            error="No matching tags"
        )

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 2  # transcription + no match debug
        assert messages[0]["type"] == MessageType.TRANSCRIPTION
        assert messages[1]["type"] == MessageType.DEBUG

    def test_build_messages_from_result_cooldown(self):
        """Test building messages when cooldown is active."""
        result = ProcessingResult(
            transcription=TranscriptionResult(text="hello", language="en"),
            match=MatchResult(
                matched_tags=["goal"],
                match_scores={"goal": 1},
                matching_memes=[]
            ),
            trigger=TriggerResult(
                triggered=False,
                reason="cooldown",
                cooldown_remaining=60
            )
        )

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 3  # transcription, match, cooldown debug
        assert messages[2]["type"] == MessageType.DEBUG
        assert messages[2]["level"] == "cooldown"

    def test_build_messages_from_result_probability(self):
        """Test building messages when probability check fails."""
        result = ProcessingResult(
            transcription=TranscriptionResult(text="hello", language="en"),
            match=MatchResult(
                matched_tags=["goal"],
                match_scores={"goal": 1},
                matching_memes=[]
            ),
            trigger=TriggerResult(
                triggered=False,
                reason="probability"
            )
        )

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 3  # transcription, match, probability debug
        assert messages[2]["type"] == MessageType.DEBUG
        assert messages[2]["level"] == "probability"

    def test_build_messages_from_result_no_memes(self):
        """Test building messages when no memes in database."""
        result = ProcessingResult(error="No memes in database")

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 1
        assert messages[0]["type"] == MessageType.DEBUG
        assert messages[0]["level"] == "warning"

    def test_build_messages_from_result_generic_error(self):
        """Test building messages for generic error."""
        result = ProcessingResult(error="Some unexpected error")

        messages = PipelineMessageBuilder.build_messages_from_result(result)

        assert len(messages) == 1
        assert messages[0]["type"] == MessageType.DEBUG
        assert messages[0]["level"] == "error"
