"""
Exemplo de cliente para testar o WhatsApp Service.
Simula um orquestrador que recebe e envia mensagens via webhook.

Este teste:
1. Inicia um servidor FastAPI mock (simulando o orquestrador)
2. Testa o recebimento de mensagens do WhatsApp
3. Testa o envio de mensagens via webhook

Uso:
    python test-whatsapp-service.py

Pré-requisitos:
    - WhatsApp Service rodando em http://localhost:3001
    - FastAPI e httpx instalados: uv pip install fastapi uvicorn httpx
"""
import asyncio
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# SERVIDOR MOCK DO ORQUESTRADOR
# ============================================================================

# Armazenar mensagens recebidas para análise
received_messages = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    print("🚀 Servidor Mock do Orquestrador iniciado")
    yield
    print("🛑 Servidor Mock do Orquestrador encerrado")


app = FastAPI(title="Orchestrator Mock", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Endpoint de health check do orquestrador."""
    return {
        "status": "ok",
        "service": "orchestrator-mock",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/process-message")
async def process_message(payload: dict):
    """
    Recebe mensagens do WhatsApp Service.
    
    Simula o processamento de uma mensagem e armazena para análise.
    """
    print(f"\n📨 [Orquestrador] Mensagem recebida!")
    print(f"   De: {payload.get('sender', {}).get('name', 'Desconhecido')}")
    print(f"   Corpo: {payload.get('body', '(sem texto)')}")
    print(f"   Tipo: {payload.get('type', 'desconhecido')}")

    # Validar payload
    required_fields = ["messageId", "from", "body", "sender"]
    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Campos obrigatórios faltando: {missing_fields}",
        )

    # Armazenar mensagem
    received_messages.append(payload)

    # Simular processamento
    response_text = f"Obrigado pela sua mensagem: '{payload.get('body')}'. Estou processando..."

    print(f"   ✅ Mensagem processada com sucesso!")

    return {
        "success": True,
        "messageId": payload.get("messageId"),
        "processedAt": datetime.now().isoformat(),
        "responseText": response_text,
    }


@app.get("/messages")
async def get_messages():
    """Retorna todas as mensagens recebidas durante o teste."""
    return {
        "count": len(received_messages),
        "messages": received_messages,
    }


# ============================================================================
# CLIENTE DE TESTE
# ============================================================================

WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8002")


async def test_health_check() -> bool:
    """
    Verifica se o WhatsApp Service está saudável.
    """
    print("\n🏥 Verificando saúde do WhatsApp Service...")
    print("-" * 70)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHATSAPP_SERVICE_URL}/health",
                timeout=5.0,
            )
            response.raise_for_status()

            result = response.json()
            print(f"✅ WhatsApp Service está saudável! Status: {response.status_code}")
            print(f"\n📊 Informações do Serviço:")
            print(f"  - Status: {result.get('status')}")
            print(f"  - Serviço: {result.get('service')}")
            print(f"  - Timestamp: {result.get('timestamp')}")

            return True

    except httpx.RequestError as e:
        print(f"❌ Erro na requisição: {e}")
        print(f"   💡 Dica: O WhatsApp Service não está respondendo.")
        print(f"      Inicie-o com: npm start (no diretório whatsapp-service)")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


async def test_send_message_without_media() -> bool:
    """
    Testa o envio de uma mensagem simples de texto.
    """
    print("\n📤 Testando envio de mensagem (texto simples)...")
    print("-" * 70)

    # Payload de exemplo
    payload = {
        "chatId": os.getenv("TEST_CHAT_ID", "5585988123456@c.us"),  # Substitua pelo seu número real
        "message": "🤖 Olá! Esta é uma mensagem de teste do sistema DevsImpacto. "
        "O teste está funcionando corretamente!",
    }

    print(f"📨 Enviando para: {payload['chatId']}")
    print(f"📝 Mensagem: {payload['message']}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/send-message",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()

            result = response.json()
            print(f"\n✅ Mensagem enviada com sucesso!")
            print(f"   - Message ID: {result['messageId']}")
            print(f"   - Status: {result['success']}")

            return True

    except httpx.HTTPStatusError as e:
        print(f"❌ Erro HTTP: {e.response.status_code}")
        print(f"   Detalhes: {e.response.text}")
        return False
    except httpx.RequestError as e:
        print(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


async def test_send_message_with_media() -> bool:
    """
    Testa o envio de uma mensagem com mídia (áudio, imagem, etc).
    """
    print("\n📤 Testando envio de mensagem (com mídia)...")
    print("-" * 70)

    # Payload de exemplo com mídia
    # Neste teste, usamos uma URL de exemplo (você pode substituir por um áudio real)
    payload = {
        "chatId": os.getenv("TEST_CHAT_ID", "5585988123456@c.us"),  # Substitua pelo seu número real
        "message": "🎵 Aqui está um arquivo de áudio para você!",
        "mediaUrl": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "mimetype": "audio/mpeg",
    }

    print(f"📨 Enviando para: {payload['chatId']}")
    print(f"📝 Mensagem: {payload['message']}")
    print(f"📥 Mídia: {payload['mediaUrl']}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_SERVICE_URL}/send-message",
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()

            result = response.json()
            print(f"\n✅ Mensagem com mídia enviada com sucesso!")
            print(f"   - Message ID: {result['messageId']}")
            print(f"   - Status: {result['success']}")

            return True

    except httpx.HTTPStatusError as e:
        print(f"❌ Erro HTTP: {e.response.status_code}")
        print(f"   Detalhes: {e.response.text}")
        return False
    except httpx.RequestError as e:
        print(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


async def test_receiving_messages() -> bool:
    """
    Simula o recebimento de uma mensagem (para ser testado manualmente).
    
    Este teste apenas exibe instruções, pois o recebimento é feito
    automaticamente quando uma mensagem chega no WhatsApp.
    """
    print("\n📨 Instruções para testar recebimento de mensagens...")
    print("-" * 70)

    print(
        """
    Para testar o recebimento de mensagens, você precisa:
    
    1. Envie uma mensagem via WhatsApp para o número conectado ao serviço
    2. O WhatsApp Service irá capturar a mensagem
    3. A mensagem será encaminhada para o Orquestrador em:
       → POST {}/process-message
    
    ✅ Se você vir logs como "[📨 Mensagem recebida]" no console do
       WhatsApp Service e "[📨 [Orquestrador] Mensagem recebida]" abaixo,
       o teste foi bem-sucedido!
    
    ⏰ Aguardando 30 segundos para que você envie uma mensagem...
    """.format(
            ORCHESTRATOR_URL
        )
    )

    # Aguardar por mensagens
    initial_count = len(received_messages)
    for i in range(30):
        if len(received_messages) > initial_count:
            print(f"\n✅ Mensagem recebida pelo orquestrador!")
            return True
        await asyncio.sleep(1)
        if i % 5 == 0:
            print(f"   ⏳ Aguardando... ({30 - i}s restantes)")

    print(f"\n⚠️  Nenhuma mensagem foi recebida nos últimos 30 segundos.")
    print(f"   (Você pode tentar enviar uma mensagem novamente)")
    return False


async def test_orchestrator_health() -> bool:
    """
    Verifica se o servidor mock do orquestrador está saudável.
    """
    print("\n🏥 Verificando saúde do Orquestrador Mock...")
    print("-" * 70)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ORCHESTRATOR_URL}/health",
                timeout=5.0,
            )
            response.raise_for_status()

            result = response.json()
            print(f"✅ Orquestrador Mock está saudável!")
            print(f"   - Status: {result['status']}")

            return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


async def display_messages_summary():
    """
    Exibe um resumo de todas as mensagens recebidas.
    """
    if not received_messages:
        print("\n📋 Nenhuma mensagem foi recebida durante o teste.")
        return

    print("\n" + "=" * 70)
    print("📋 RESUMO DAS MENSAGENS RECEBIDAS")
    print("=" * 70)

    for idx, msg in enumerate(received_messages, 1):
        sender = msg.get("sender", {})
        print(f"\n📨 Mensagem #{idx}")
        print(f"   De: {sender.get('name', 'Desconhecido')} ({sender.get('id')})")
        print(f"   Corpo: {msg.get('body', '(sem texto)')}")
        print(f"   Tipo: {msg.get('type')}")
        print(f"   Timestamp: {msg.get('timestamp')}")
        if msg.get("media"):
            print(f"   Mídia: {msg['media'].get('mimetype')}")


async def main():
    """
    Executa todos os testes de forma sequencial.
    """
    print("\n" + "=" * 70)
    print("💬 TESTES DO WHATSAPP SERVICE")
    print("=" * 70)

    # Verificar se o WhatsApp Service está rodando
    is_healthy = await test_health_check()
    if not is_healthy:
        print("\n⚠️  Não foi possível conectar ao WhatsApp Service.")
        print("   Abortando testes.")
        return

    # Verificar saúde do orquestrador
    await test_orchestrator_health()

    # Testar envio de mensagem (texto)
    send_text_success = await test_send_message_without_media()

    # Aguardar um pouco antes de enviar a próxima mensagem
    await asyncio.sleep(2)

    # Testar envio de mensagem (com mídia)
    send_media_success = await test_send_message_with_media()

    # Testar recebimento de mensagens
    receive_success = await test_receiving_messages()

    # Exibir resumo
    await display_messages_summary()

    # Resumo final
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    print(f"✅ Health Check: Sucesso")
    print(f"✅ Envio de Texto: {'Sucesso' if send_text_success else 'Falha'}")
    print(f"✅ Envio com Mídia: {'Falha' if send_media_success else 'Falha'}")
    print(f"✅ Recebimento: {'Sucesso' if receive_success else 'Aguardando'}")
    print("\n" + "=" * 70)


def run_server():
    """
    Executa o servidor FastAPI mock do orquestrador em uma thread separada.
    """
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")


if __name__ == "__main__":
    print(
        """
    🚀 INICIANDO TESTES DO WHATSAPP SERVICE
    
    ⚠️  ATENÇÃO: Certifique-se de que:
       1. O WhatsApp Service está rodando: npm start (em whatsapp-service/)
       2. O número está autenticado (já fez login uma vez)
    
    Este script irá:
    1. Iniciar um servidor mock do Orquestrador (porta 8002)
    2. Testar o envio de mensagens
    3. Aguardar recebimento de mensagens (envie uma via WhatsApp)
    
    Pressione Ctrl+C para interromper.
    """
    )

    # Iniciar servidor mock em uma thread separada
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Aguardar servidor iniciar
    time.sleep(2)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")