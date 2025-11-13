from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MemeCreate(BaseModel):
    filename: str
    tags: List[str]


class MemeResponse(BaseModel):
    id: int
    filename: str
    tags: List[str]
    created_at: datetime
    play_count: int

    class Config:
        from_attributes = True


class MemeUpdate(BaseModel):
    tags: Optional[List[str]] = None


class SettingsResponse(BaseModel):
    cooldown_seconds: int
    trigger_probability: float
    whisper_model: str
    chunk_length_seconds: int
    language: str
    use_stemming: str


class SettingsUpdate(BaseModel):
    cooldown_seconds: Optional[int] = None
    trigger_probability: Optional[float] = None
    chunk_length_seconds: Optional[int] = None
    language: Optional[str] = None
    whisper_model: Optional[str] = None
    use_stemming: Optional[str] = None


class TranscriptionResponse(BaseModel):
    text: str
    timestamp: datetime


class TriggerEvent(BaseModel):
    triggered: bool
    meme_id: Optional[int] = None
    filename: Optional[str] = None
    matched_tags: List[str] = []
    cooldown_remaining: Optional[int] = None
