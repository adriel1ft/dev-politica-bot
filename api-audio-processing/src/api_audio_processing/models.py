"""
Modelos de dados para a API
"""
from pydantic import BaseModel
from typing import Optional


class TextToSpeechRequest(BaseModel):
    """Request para converter texto em áudio"""
    text: str
    voice: Optional[str] = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    speed: Optional[float] = 1.0


class TextToSpeechResponse(BaseModel):
    """Response com URL do áudio gerado"""
    audio_url: str
    duration_seconds: Optional[float] = None
    voice: str
    text_length: int


class SpeechToTextResponse(BaseModel):
    """Response com transcrição do áudio"""
    text: str
    duration_seconds: Optional[float] = None
    language: Optional[str] = "pt-BR"


class AudioJobStatus(BaseModel):
    """Status de um job de processamento"""
    job_id: str
    status: str  # pending, processing, completed, error
    result: Optional[dict] = None
    error_message: Optional[str] = None