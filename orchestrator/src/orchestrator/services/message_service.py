import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, List
from pymongo import MongoClient
import json


from ..config import settings
from ..models_db import SessionDB
from .user_service import UserService
from .audio_service import AudioService
from .agent_service import AgentService
from .message_buffer_service import MessageBufferService, BufferedMessage
from .location_service import LocationService

logger = logging.getLogger(__name__)



class MessageService:
    """Orquestra o fluxo completo de mensagens"""
    
    def __init__(self):
        self.client = MongoClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_db]
        self.sessions_collection = self.db["sessions"]
        self.user_service = UserService()
        self.audio_service = AudioService()
        self.agent_service = AgentService()
        self.location_service = LocationService()
        
        # Inicializar buffer de mensagens
        self.buffer_service = MessageBufferService(
            initial_timeout_seconds=settings.message_batch_timeout_seconds,
            inter_message_timeout_seconds=settings.message_inter_timeout_seconds
        )
        
        logger.info(f"✅ MessageBufferService inicializado")
        logger.info(f"   - Timeout inicial: {settings.message_batch_timeout_seconds}s")
        logger.info(f"   - Timeout entre mensagens: {settings.message_inter_timeout_seconds}s")
    
    async def receive_message(
        self,
        user_id: str,
        chatId: str,
        message_type: str,
        message: str,
        media: Optional[bytes] = None
    ) -> Dict:
        """
        Recebe mensagem e adiciona ao buffer
        
        NÃO processa imediatamente - aguarda timeout
        """
        logger.info(
            f"\n{'='*70}\n"
            f"📨 MENSAGEM RECEBIDA (BUFFER)\n"
            f"   Usuário: {user_id}\n"
            f"   Tipo: {message_type}\n"
            f"   Tamanho: {len(message)} chars\n"
            f"{'='*70}"
        )
        
        # Registrar callback se ainda não foi feito
        if user_id not in self.buffer_service.processing_callbacks:
            self.buffer_service.register_processing_callback(
                user_id,
                self._process_buffered_messages
            )
        
        # Adicionar ao buffer
        await self.buffer_service.add_message(
            user_id=user_id,
            chatId=chatId,
            message_type=message_type,
            message=message,
            media=media
        )
        
        # Retornar status do buffer
        return {
            "status": "buffered",
            "buffer_status": self.buffer_service.get_buffer_status(user_id),
            "message": "Mensagem adicionada ao buffer, aguardando mais mensagens ou timeout..."
        }
    
    async def _process_buffered_messages(
        self,
        user_id: str,
        messages: List[BufferedMessage]
    ) -> None:
        """
        Processa todas as mensagens do buffer
        
        Chamado quando:
        - Timeout inicial expira (30s)
        - OU timeout entre mensagens expira (15s sem novas mensagens)
        """
        logger.info(
            f"\n{'='*70}\n"
            f"🎯 PROCESSANDO BUFFER ({len(messages)} mensagens)\n"
            f"   Usuário: {user_id}\n"
            f"{'='*70}"
        )
        
        try:
            # 1. Verificar/criar usuário
            user = await self.user_service.get_or_create_user(user_id)
            
            # 2. Obter/criar sessão
            session_id = await self.get_or_create_session(user_id)
            
            # 3. Agrupar mensagens em texto único
            combined_text = await self._combine_messages(user_id, messages)
            logger.info(f"📝 Mensagens combinadas ({len(combined_text)} chars)")
            
            # 3.5. VERIFICAR E PROCESSAR LOCALIZAÇÃO
            # Se usuário não tem localização, tentar extrair das mensagens
            if not user.cidade or not user.estado:
                logger.info("📍 Usuário sem localização cadastrada, tentando extrair do texto...")
                location_info = await self.location_service.extract_location_from_text(
                    text=combined_text,
                    cidade=user.cidade,
                    estado=user.estado,
                    cep=user.cep
                )
                
                if location_info.get("cidade") and location_info.get("estado"):
                    # Atualizar localização do usuário
                    await self.user_service.update_user_location(
                        user_id=user_id,
                        cidade=location_info["cidade"],
                        estado=location_info["estado"],
                        cep=location_info.get("cep"),
                        bairro=location_info.get("bairro"),
                        logradouro=location_info.get("logradouro")
                    )
                    logger.info(f"✅ Localização atualizada: {location_info['cidade']}/{location_info['estado']}")
                    
                    # Se não conseguiu extrair, pedir ao usuário
                    if not location_info.get("cidade"):
                        await self._send_location_request(user_id)
                        return
                else:
                    # Pedir localização explicitamente
                    await self._send_location_request(user_id)
                    return
            
            # 4. Chamar agente com texto combinado
            logger.info("🤖 Enviando para agente...")
            agent_response = await self.agent_service.process_message(
                user_message=combined_text,
                user_id=user_id,
                session_id=session_id,
                user_preferences={
                    "prefer_audio": user.prefer_audio,
                    "topics": user.topics_of_interest,
                    "cidade": user.cidade,
                    "estado": user.estado,
                    "cep": user.cep
                }
            )
            
            if not agent_response:
                await self._send_error_response(user_id, user_id, session_id)
                return
            
            response_text = agent_response.get("response_text", "")
            should_send_audio = agent_response.get("should_send_audio", False) or user.prefer_audio
            auxiliary_text = agent_response.get("auxiliary_text")
            
            # 5. Gerar áudio se necessário
            audio_url = None
            if should_send_audio:
                logger.info("🔊 Gerando áudio...")
                audio_url = await self.audio_service.text_to_speech(
                    response_text,
                    auxiliary_text
                )
            
            # 6. Retornar resposta
            result = {
                "chatId": user_id,
                "message": response_text,
                "mediaUrl": audio_url,
                "mimeType": "audio/ogg" if audio_url else None,
                "auxiliaryText": auxiliary_text
            }
            
            # Enviar para WhatsApp
            await self._send_to_whatsapp(result)
            
            # Salvar na sessão
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {
                        "messages": {
                            "user_messages": [
                                {
                                    "type": m.message_type.value,
                                    "data": m.message[:100],  # Preview
                                    "timestamp": m.timestamp
                                }
                                for m in messages
                            ],
                            "agent_response": response_text,
                            "grouped_count": len(messages),
                            "processed_at": datetime.utcnow()
                        }
                    },
                    "$set": {"last_activity": datetime.utcnow()}
                }
            )
            
            logger.info(f"✅ Buffer processado e salvo!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar buffer: {e}")
    
    async def _combine_messages(
        self,
        user_id: str,
        messages: List[BufferedMessage]
    ) -> str:
        """
        Combina múltiplas mensagens em um único texto
        
        Fluxo:
        1. Transcreve áudios
        2. Combina com separadores
        """
        combined_parts = []
        
        for i, msg in enumerate(messages, 1):
            if msg.message_type.value == "chat":
                # Texto simples
                combined_parts.append(msg.message)
                logger.info(f"   [{i}] Texto: {msg.message[:50]}...")
            elif msg.media:
                # Transcrever áudio
                logger.info(f"   [{i}] Áudio: transcrevendo...")
                transcribed = await self.audio_service.transcribe_audio(msg.media['data'])
                if transcribed:
                    combined_parts.append(transcribed)
                    logger.info(f"       ✅ {transcribed[:50]}...")
                else:
                    logger.warning(f"       ❌ Falha na transcrição")
            
            else:
                logger.warning(f"   [{i}] Tipo ignorado: {msg.message_type.value}")
        
        # Combinar com separadores claros
        combined = "\n---\n".join(combined_parts)
        return combined
    
    async def get_or_create_session(self, user_id: str) -> str:
        """Obtém ou cria sessão para o usuário"""
        recent_session = self.sessions_collection.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if recent_session:
            logger.info(f"📌 Sessão encontrada: {recent_session['session_id']}")
            return recent_session["session_id"]
        
        session_id = f"sess_{user_id}_{datetime.utcnow().timestamp()}"
        new_session = SessionDB(session_id=session_id, user_id=user_id)
        self.sessions_collection.insert_one(new_session.to_dict())
        logger.info(f"🆕 Nova sessão criada: {session_id}")
        return session_id
    
    async def _send_to_whatsapp(self, payload: Dict) -> bool:
        """Envia resposta para WhatsApp via webhook"""
        try:
            logger.info(f"📤 Enviando para WhatsApp: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.whatsapp_service_url}/send-message",
                    json=payload,
                    timeout=10.0
                )
            
            if response.status_code == 200:
                logger.info("📤 Mensagem enviada para WhatsApp!")
                return True
            else:
                logger.error(f"❌ Erro ao enviar para WhatsApp: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar para WhatsApp: {e}")
            return False
    
    async def _send_error_response(self, user_id: str, chatId: str, session_id: str) -> Dict:
        """Envia resposta de erro"""
        error_message = {
            "chatId": chatId,
            "message": "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
            "mediaUrl": None,
            "mimeType": None,
            "auxiliaryText": None
        }
        await self._send_to_whatsapp(error_message)
        return error_message
    
    async def _send_location_request(self, user_id: str) -> None:
        """Solicita informações de localização ao usuário"""
        logger.info(f"📍 Solicitando localização para usuário {user_id}")
        
        location_message = {
            "chatId": user_id,
            "message": (
                "Olá! Para poder te ajudar melhor, preciso saber sua localização. 📍\n\n"
                "Por favor, me informe:\n"
                "• Em qual *cidade* você mora?\n"
                "• Em qual *estado*?\n"
                "• Se possível, o *CEP* da sua região\n\n"
                "Exemplo: _\"Moro em São José dos Campos, São Paulo, CEP 12345-678\"_\n\n"
                "Ou se preferir, pode mencionar uma referência local (bairro, comunidade, etc) "
                "que eu tento descobrir o CEP para você! 😊"
            ),
            "mediaUrl": None,
            "mimeType": None,
            "auxiliaryText": None
        }
        
        await self._send_to_whatsapp(location_message)