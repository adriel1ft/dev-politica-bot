"""
Serviço de Buffer de Mensagens

Agrupa mensagens do usuário antes de processar com o agente.
Fluxo:
1. Mensagem chega
2. Adiciona ao buffer
3. Inicia timer
4. Se nova mensagem em < 15s → reseta timer
5. Se timer expira (30s) → processa todas
"""
import asyncio
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Tipos de mensagem suportados"""
    CHAT = "chat"
    PTT = "ptt"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


@dataclass
class BufferedMessage:
    """Mensagem no buffer"""
    user_id: str
    message_type: MessageType
    message: str
    chatId: str
    timestamp: datetime
    media: Optional[dict] = None



class MessageBuffer:
    """Buffer de mensagens por sessão"""
    
    def __init__(
        self, 
        user_id: str,
        initial_timeout_seconds: int = 30,
        inter_message_timeout_seconds: int = 15
    ):
        self.user_id = user_id
        self.messages: List[BufferedMessage] = []
        self.initial_timeout_seconds = initial_timeout_seconds
        self.inter_message_timeout_seconds = inter_message_timeout_seconds
        self.timer_task: Optional[asyncio.Task] = None
        self.last_message_time = datetime.utcnow()
        self.is_processing = False
    
    def add_message(self, message: BufferedMessage) -> bool:
        """
        Adiciona mensagem ao buffer
        
        Retorna True se deve aguardar mais mensagens
        Retorna False se deve processar imediatamente
        """
        self.messages.append(message)
        self.last_message_time = datetime.utcnow()
        
        logger.info(
            f"📥 Mensagem adicionada ao buffer [{self.user_id}] "
            f"| Total: {len(self.messages)} | Tipo: {message.message_type}"
        )
        
        return True
    
    def should_process(self) -> bool:
        """Verifica se deve processar o buffer"""
        if not self.messages:
            return False
        
        time_since_last = (datetime.utcnow() - self.last_message_time).total_seconds()
        
        # Se passou o timeout entre mensagens
        if time_since_last > self.inter_message_timeout_seconds:
            logger.info(
                f"⏱️  Timeout entre mensagens atingido [{self.user_id}] "
                f"| {time_since_last:.1f}s > {self.inter_message_timeout_seconds}s"
            )
            return True
        
        return False
    
    def get_messages(self) -> List[BufferedMessage]:
        """Retorna e limpa mensagens do buffer"""
        messages = self.messages.copy()
        self.messages = []
        return messages
    
    def clear(self):
        """Limpa o buffer"""
        self.messages = []


class MessageBufferService:
    """Gerencia buffers de múltiplos usuários"""
    
    def __init__(
        self,
        initial_timeout_seconds: int = 30,
        inter_message_timeout_seconds: int = 15
    ):
        self.buffers: Dict[str, MessageBuffer] = {}
        self.initial_timeout_seconds = initial_timeout_seconds
        self.inter_message_timeout_seconds = inter_message_timeout_seconds
        self.timers: Dict[str, asyncio.Task] = {}
        self.processing_callbacks: Dict[str, callable] = {}
    
    def get_or_create_buffer(self, user_id: str) -> MessageBuffer:
        """Obtém ou cria buffer para usuário"""
        if user_id not in self.buffers:
            self.buffers[user_id] = MessageBuffer(
                user_id=user_id,
                initial_timeout_seconds=self.initial_timeout_seconds,
                inter_message_timeout_seconds=self.inter_message_timeout_seconds
            )
            logger.info(f"🆕 Buffer criado para usuário: {user_id}")
        
        return self.buffers[user_id]
    
    async def add_message(
        self,
        user_id: str,
        chatId: str,
        message_type: str,
        message: str,
        media: Optional[bytes] = None
    ) -> None:
        """
        Adiciona mensagem ao buffer e inicia/reinicia timer
        
        Fluxo:
        1. Adiciona ao buffer
        2. Cancela timer anterior (se existir)
        3. Inicia novo timer
        """
        buffer = self.get_or_create_buffer(user_id)
        
        # Não adicionar se já está processando
        if buffer.is_processing:
            logger.warning(f"⚠️  Usuário {user_id} já está sendo processado, ignorando mensagem")
            return
        
        # Adicionar mensagem
        message = BufferedMessage(
            user_id=user_id,
            chatId=chatId,
            message_type=MessageType(message_type),
            message=message,
            media=media,
            timestamp=datetime.utcnow()
        )
        buffer.add_message(message)
        
        # Cancelar timer anterior
        if user_id in self.timers:
            self.timers[user_id].cancel()
            logger.info(f"🔄 Timer anterior cancelado [{user_id}]")
        
        # Iniciar novo timer
        self.timers[user_id] = asyncio.create_task(
            self._process_after_timeout(user_id)
        )
        logger.info(f"⏲️  Timer iniciado [{user_id}] | {self.initial_timeout_seconds}s")
    
    async def _process_after_timeout(self, user_id: str) -> None:
        """
        Aguarda timeout e processa buffer
        
        Verifica a cada segundo se deve processar
        """
        buffer = self.get_or_create_buffer(user_id)
        elapsed = 0
        
        try:
            while elapsed < self.initial_timeout_seconds:
                # Aguardar 1 segundo
                await asyncio.sleep(1)
                elapsed += 1
                
                # Verificar se deve processar (timeout entre mensagens)
                if buffer.should_process():
                    logger.info(
                        f"🎯 Processando buffer [{user_id}] "
                        f"| Motivo: Timeout entre mensagens "
                        f"| Mensagens: {len(buffer.messages)}"
                    )
                    await self._trigger_processing(user_id)
                    return
            
            # Timeout inicial expirou
            logger.info(
                f"⏰ Timeout inicial atingido [{user_id}] "
                f"| Processando {len(buffer.messages)} mensagens"
            )
            await self._trigger_processing(user_id)
            
        except asyncio.CancelledError:
            logger.info(f"🔙 Timer cancelado para {user_id}")
    
    async def _trigger_processing(self, user_id: str) -> None:
        """Dispara processamento do buffer"""
        buffer = self.get_or_create_buffer(user_id)
        
        if not buffer.messages:
            logger.info(f"⚠️  Buffer vazio para {user_id}")
            return
        
        buffer.is_processing = True
        messages = buffer.get_messages()
        
        try:
            # Chamar callback registrado
            if user_id in self.processing_callbacks:
                callback = self.processing_callbacks[user_id]
                await callback(user_id, messages)
            else:
                logger.warning(f"❌ Nenhum callback registrado para {user_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao processar buffer [{user_id}]: {e}")
        finally:
            buffer.is_processing = False
            if user_id in self.timers:
                del self.timers[user_id]
    
    def register_processing_callback(
        self,
        user_id: str,
        callback: callable
    ) -> None:
        """Registra callback para quando buffer deve ser processado"""
        self.processing_callbacks[user_id] = callback
        logger.info(f"✅ Callback registrado para {user_id}")
    
    def get_buffer_status(self, user_id: str) -> Dict:
        """Retorna status do buffer"""
        buffer = self.buffers.get(user_id)
        
        if not buffer:
            return {"status": "no_buffer"}
        
        return {
            "user_id": user_id,
            "messages_count": len(buffer.messages),
            "is_processing": buffer.is_processing,
            "last_message": buffer.last_message_time.isoformat(),
            "messages": [
                {
                    "type": m.message_type.value,
                    "timestamp": m.timestamp.isoformat(),
                    "preview": m.message[:50] + "..." if len(m.message) > 50 else m.message
                }
                for m in buffer.messages
            ]
        }
    
    def cleanup_buffer(self, user_id: str) -> None:
        """Remove buffer de um usuário"""
        if user_id in self.buffers:
            del self.buffers[user_id]
        if user_id in self.timers:
            self.timers[user_id].cancel()
            del self.timers[user_id]
        if user_id in self.processing_callbacks:
            del self.processing_callbacks[user_id]
        logger.info(f"🗑️  Buffer limpo para {user_id}")