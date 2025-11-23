"""
Exemplo de cliente para testar a API de Processamento de Áudio.
Baseado na documentação do projeto: README.md

Uso:
    python test_api.py
"""
import asyncio
import httpx
from pathlib import Path

# URL da API local
API_BASE_URL = "http://localhost:8001"

# Caminho do arquivo de áudio para teste (Speech-to-Text)
AUDIO_FILE_PATH = Path(__file__).parent / "resposta.mp3"


async def test_text_to_speech() -> str:
    """
    Testa o endpoint POST /text-to-speech
    Converte um texto em áudio e retorna a URL do arquivo gerado.
    """
    print("\n🎤 Testando Text-to-Speech (TTS)...")
    print("-" * 60)

    # Payload de exemplo
    payload = {
        "text": "Olá! Bem-vindo ao sistema de processamento de áudio do DevsImpacto. "
                "Este é um teste para demonstrar a conversão de texto para fala. "
                "A tecnologia utiliza inteligência artificial para gerar áudio natural e claro.",
        "voice": "nova",
        "speed": 1.0,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/text-to-speech",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()

            result = response.json()
            print(f"✅ Sucesso! Status: {response.status_code}")
            print(f"\n📊 Resposta:")
            print(f"  - URL do Áudio: {result['audio_url']}")
            print(f"  - Voz Utilizada: {result['voice']}")
            print(f"  - Tamanho do Texto: {result['text_length']} caracteres")
            if result.get("duration_seconds"):
                print(f"  - Duração: {result['duration_seconds']:.2f}s")

            return result["audio_url"]

    except httpx.HTTPStatusError as e:
        print(f"❌ Erro HTTP: {e.response.status_code}")
        print(f"   Detalhes: {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Erro na requisição: {e}")
        print(f"   💡 Dica: Verifique se a API está rodando em {API_BASE_URL}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    return None


async def test_speech_to_text() -> str:
    """
    Testa o endpoint POST /speech-to-text
    Transcreve um arquivo de áudio para texto em português.
    """
    print("\n🎵 Testando Speech-to-Text (STT)...")
    print("-" * 60)

    # Verificar se o arquivo existe
    if not AUDIO_FILE_PATH.exists():
        print(f"❌ Arquivo de áudio não encontrado: {AUDIO_FILE_PATH}")
        print(f"   Certifique-se de que 'resposta.mp3' existe no diretório do projeto.")
        return None

    print(f"📁 Arquivo a transcrever: {AUDIO_FILE_PATH.name}")

    try:
        async with httpx.AsyncClient() as client:
            with open(AUDIO_FILE_PATH, "rb") as audio_file:
                files = {"file": (AUDIO_FILE_PATH.name, audio_file, "audio/mpeg")}

                response = await client.post(
                    f"{API_BASE_URL}/speech-to-text",
                    files=files,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()
                print(f"✅ Sucesso! Status: {response.status_code}")
                print(f"\n📊 Resposta:")
                print(f"  - Texto Transcrito: \"{result['text']}\"")
                print(f"  - Idioma: {result['language']}")
                if result.get("duration_seconds"):
                    print(f"  - Duração do Áudio: {result['duration_seconds']:.2f}s")

                return result["text"]

    except httpx.HTTPStatusError as e:
        print(f"❌ Erro HTTP: {e.response.status_code}")
        print(f"   Detalhes: {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Erro na requisição: {e}")
        print(f"   💡 Dica: Verifique se a API está rodando em {API_BASE_URL}")
    except FileNotFoundError:
        print(f"❌ Não foi possível abrir o arquivo: {AUDIO_FILE_PATH}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    return None


async def test_health_check() -> bool:
    """
    Verifica se a API está saudável e pronta para receber requisições.
    """
    print("\n🏥 Verificando saúde da API...")
    print("-" * 60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/health",
                timeout=5.0,
            )
            response.raise_for_status()

            result = response.json()
            print(f"✅ API está saudável! Status: {response.status_code}")
            print(f"\n📊 Informações da API:")
            print(f"  - Status: {result['status']}")
            print(f"  - Bucket S3: {result['s3_bucket']}")
            print(f"  - Modelo TTS: {result['openai_model_tts']}")
            print(f"  - Modelo STT: {result['openai_model_stt']}")

            return True

    except httpx.RequestError as e:
        print(f"❌ Erro na requisição: {e}")
        print(f"   💡 Dica: A API não está respondendo. Inicie-a com:")
        print(f"      uvicorn api_audio_processing.main:app --port 8001 --reload")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


async def main():
    """
    Executa todos os testes da API de forma sequencial.
    """
    print("\n" + "=" * 60)
    print("🎙️  TESTES DA API DE PROCESSAMENTO DE ÁUDIO")
    print("=" * 60)

    # Verificar se a API está rodando
    is_healthy = await test_health_check()
    if not is_healthy:
        print("\n⚠️  Não foi possível conectar à API. Abortando testes.")
        return

    # Testar Text-to-Speech
    audio_url = await test_text_to_speech()

    # Testar Speech-to-Text
    transcribed_text = await test_speech_to_text()

    # Resumo dos testes
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"✅ Text-to-Speech: {'Sucesso' if audio_url else 'Falha'}")
    print(f"✅ Speech-to-Text: {'Sucesso' if transcribed_text else 'Falha'}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")