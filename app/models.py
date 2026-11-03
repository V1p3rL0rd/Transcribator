from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class WordItem(BaseModel):
    word: str
    start: float
    end: float
    probability: float


class TranscriptionSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: Optional[List[WordItem]] = None


class TranscriptionResult(BaseModel):
    task_id: str
    filename: str
    text: str
    language: str
    language_probability: float
    duration: float
    segments: List[TranscriptionSegment]


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: int = 0
    filename: str
    model_name: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[TranscriptionResult] = None


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    vram_ram: str
    relative_speed: str
