"""
API de processamento de áudio - Text to Speech / Speech to Text
"""
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import tempfile

from .config import settings
from .services import AudioService
from .models import (
    TextToSpeechRequest,
    TextToSpeechResponse,
    SpeechToTextResponse,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="API para conversão de áudio bidirecional",
)

# Inicializar serviço
audio_service = AudioService()


@app.get("/", tags=["Health"])
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": settings.api_title,
        "version": settings.api_version,
    }


@app.post("/text-to-speech", response_model=TextToSpeechResponse, tags=["Audio"])
async def text_to_speech(request: TextToSpeechRequest):
    """
    Converte texto em áudio MP3
    
    **Parâmetros:**
    - `text`: Texto a ser convertido
    - `voice`: Voz a usar (alloy, echo, fable, onyx, nova, shimmer)
    - `speed`: Velocidade da fala (0.25 a 4.0)
    
    **Exemplo:**
    ```json
    {
        "text": "Olá, bem-vindo ao sistema de processamento de áudio!",
        "voice": "nova",
        "speed": 1.0
    }
    ```
    """
    try:
        response = await audio_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
        )
        logger.info(f"TTS concluído: {request.text[:30]}...")
        return response

    except Exception as e:
        logger.error(f"Erro em TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speech-to-text", response_model=SpeechToTextResponse, tags=["Audio"])
async def speech_to_text(file: UploadFile = File(...)):
    """
    Transcreve áudio para texto (Português)
    
    **Parâmetros:**
    - `file`: Arquivo de áudio (MP3, WAV, OGG, etc)
    
    **Exemplo:** Use `curl` ou Postman para enviar um arquivo
    ```bash
    curl -X POST "http://localhost:8001/speech-to-text" \\
      -F "file=@seu_audio.mp3"
    ```
    """
    try:
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # Transcrever
        response = await audio_service.speech_to_text(tmp_path)
        logger.info(f"STT concluído: {response.text[:30]}...")
        return response

    except Exception as e:
        logger.error(f"Erro em STT: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        import os

        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/health", tags=["Health"])
async def health():
    """Status da API"""
    return {
        "status": "healthy",
        "s3_bucket": settings.s3_bucket_name,
        "openai_model_tts": settings.openai_tts_model,
        "openai_model_stt": settings.openai_whisper_model,
    }


def main():
    """Ponto de entrada"""
    import uvicorn

    logger.info(
        f"Iniciando {settings.api_title} v{settings.api_version} "
        f"na porta {settings.api_port}"
    )
    uvicorn.run(
        "api_audio_processing.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()