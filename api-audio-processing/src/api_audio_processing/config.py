"""
Configurações da API de processamento de áudio
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Configurações da aplicação"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # API
    api_title: str = "Audio Processing API"
    api_version: str = "0.1.0"
    api_port: int = 8001

    # OpenAI (para TTS e Whisper)
    openai_api_key: str = ""
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"
    openai_whisper_model: str = "whisper-1"

    # AWS S3 / LocalStack
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_region: str = "us-east-1"
    s3_endpoint_url: str = "http://localhost:4566"  # LocalStack
    s3_bucket_name: str = "audio-processing"

    # Cache / Temp
    temp_dir: Path = Path("./data/temp")
    cache_dir: Path = Path("./data/cache")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()