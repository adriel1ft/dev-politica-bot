"""
Serviços para processamento de áudio
"""
import logging
from typing import Optional
from pathlib import Path
import uuid
from datetime import datetime

from openai import OpenAI
import boto3

from .config import settings
from .models import TextToSpeechResponse, SpeechToTextResponse

logger = logging.getLogger(__name__)


class AudioService:
    """Serviço principal de processamento de áudio"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Garante que o bucket existe no S3/LocalStack"""
        try:
            self.s3_client.head_bucket(Bucket=settings.s3_bucket_name)
        except Exception:
            logger.info(f"Criando bucket {settings.s3_bucket_name}")
            self.s3_client.create_bucket(Bucket=settings.s3_bucket_name)

    async def text_to_speech(
        self, text: str, voice: str = "alloy", speed: float = 1.0
    ) -> TextToSpeechResponse:
        """
        Converte texto em áudio usando OpenAI TTS
        """
        logger.info(f"Gerando áudio para: {text[:50]}...")

        try:
            # Chamada ao OpenAI TTS
            response = self.openai_client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=voice,
                input=text,
                speed=speed,
            )

            # Gerar nome único para o arquivo
            audio_id = str(uuid.uuid4())
            audio_key = f"tts/{datetime.now().strftime('%Y%m%d')}/{audio_id}.mp3"

            # Upload para S3
            self.s3_client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=audio_key,
                Body=response.content,
                ContentType="audio/mpeg",
            )

            audio_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket_name, "Key": audio_key},
                ExpiresIn=3600,
            )
            
            logger.info(f"Áudio salvo em: {audio_url}")

            return TextToSpeechResponse(
                audio_url=audio_url,
                voice=voice,
                text_length=len(text),
            )

        except Exception as e:
            logger.error(f"Erro ao gerar áudio: {str(e)}")
            raise

    async def speech_to_text(self, audio_file_path: str) -> SpeechToTextResponse:
        """
        Transcreve áudio para texto usando OpenAI Whisper
        """
        logger.info(f"Transcrevendo áudio: {audio_file_path}")

        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=settings.openai_whisper_model,
                    file=audio_file,
                    language="pt",  # Português
                )

            logger.info(f"Transcrição concluída: {transcript.text[:50]}...")

            return SpeechToTextResponse(
                text=transcript.text,
                language="pt-BR",
            )

        except Exception as e:
            logger.error(f"Erro ao transcrever: {str(e)}")
            raise

    def get_download_url(self, s3_key: str) -> str:
        """
        Gera URL de download assinada (válida por 1 hora)
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket_name, "Key": s3_key},
                ExpiresIn=3600,
            )
            return url
        except Exception as e:
            logger.error(f"Erro ao gerar URL: {str(e)}")
            raise