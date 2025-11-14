from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MemeCreate(BaseModel):
    """Request model for creating a new meme."""
    filename: str = Field(
        ...,
        description="Name of the audio file",
        examples=["epic_goal.mp3"]
    )
    tags: List[str] = Field(
        ...,
        description="List of tags for context matching",
        examples=[["goal", "football", "sports"]]
    )


class MemeResponse(BaseModel):
    """Response model for meme data."""
    id: int = Field(
        ...,
        description="Unique identifier for the meme",
        examples=[1]
    )
    filename: str = Field(
        ...,
        description="Name of the audio file",
        examples=["epic_goal.mp3"]
    )
    tags: List[str] = Field(
        ...,
        description="List of tags for context matching",
        examples=[["goal", "football", "sports"]]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the meme was created",
        examples=["2024-01-01T12:00:00"]
    )
    play_count: int = Field(
        ...,
        description="Number of times this meme has been played",
        examples=[5]
    )

    class Config:
        from_attributes = True


class MemeUpdate(BaseModel):
    """Request model for updating meme tags."""
    tags: Optional[List[str]] = Field(
        None,
        description="Updated list of tags",
        examples=[["new_tag1", "new_tag2"]]
    )


class SettingsResponse(BaseModel):
    """Response model for application settings."""
    cooldown_seconds: int = Field(
        ...,
        description="Cooldown period in seconds between triggers",
        examples=[180]
    )
    trigger_probability: float = Field(
        ...,
        description="Probability (0-100) that a matching tag will trigger audio playback",
        examples=[50.0],
        ge=0.0,
        le=100.0
    )
    whisper_model: str = Field(
        ...,
        description="Whisper model size (tiny, base, small, medium, large)",
        examples=["base"]
    )
    chunk_length_seconds: int = Field(
        ...,
        description="Length of audio chunks to process (in seconds)",
        examples=[3]
    )
    language: str = Field(
        ...,
        description="Language code for transcription (en, pt, es, fr, etc.)",
        examples=["en"]
    )
    use_stemming: str = Field(
        ...,
        description="Whether to use word stemming for tag matching (true/false)",
        examples=["false"]
    )


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""
    cooldown_seconds: Optional[int] = Field(
        None,
        description="Cooldown period in seconds between triggers",
        examples=[180],
        ge=0
    )
    trigger_probability: Optional[float] = Field(
        None,
        description="Probability (0-100) that a matching tag will trigger audio playback",
        examples=[50.0],
        ge=0.0,
        le=100.0
    )
    chunk_length_seconds: Optional[int] = Field(
        None,
        description="Length of audio chunks to process (in seconds)",
        examples=[3],
        ge=1,
        le=30
    )
    language: Optional[str] = Field(
        None,
        description="Language code for transcription (en, pt, es, fr, etc.)",
        examples=["pt"]
    )
    whisper_model: Optional[str] = Field(
        None,
        description="Whisper model size (tiny, base, small, medium, large)",
        examples=["base"]
    )
    use_stemming: Optional[str] = Field(
        None,
        description="Whether to use word stemming for tag matching (true/false)",
        examples=["false"]
    )


class TranscriptionResponse(BaseModel):
    """Response model for transcription data."""
    text: str = Field(
        ...,
        description="Transcribed text from audio",
        examples=["that goal was amazing"]
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of the transcription",
        examples=["2024-01-01T12:00:00"]
    )


class TriggerEvent(BaseModel):
    """Response model for trigger events."""
    triggered: bool = Field(
        ...,
        description="Whether a meme was triggered",
        examples=[True]
    )
    meme_id: Optional[int] = Field(
        None,
        description="ID of the triggered meme (if triggered)",
        examples=[1]
    )
    filename: Optional[str] = Field(
        None,
        description="Filename of the triggered meme (if triggered)",
        examples=["epic_goal.mp3"]
    )
    matched_tags: List[str] = Field(
        default=[],
        description="List of tags that matched",
        examples=[["goal", "football"]]
    )
    cooldown_remaining: Optional[int] = Field(
        None,
        description="Remaining cooldown time in seconds (if not triggered due to cooldown)",
        examples=[60]
    )
