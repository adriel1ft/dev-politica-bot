from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime


class IncomingMessageRequest(BaseModel):
    """Mensagem recebida do WhatsApp Service"""
    messageId: str
    from_: str = Field(alias="from")
    to: str
    body: str
    type: str  # "chat", "ptt", etc
    timestamp: int  # Unix timestamp do WhatsApp
    isGroup: bool = False
    sender: Optional[dict] = None
    media: Optional[dict] = None
    
    # Propriedades derivadas para compatibilidade
    @property
    def user_id(self) -> str:
        return self.from_
    
    @property
    def chatId(self) -> str:
        return self.to
    
    @property
    def message_type(self) -> str:
        return self.type
    
    @property
    def message(self) -> str:
        return self.body


class ProcessedMessageResponse(BaseModel):
    """Resposta processada para o WhatsApp"""
    user_id: str
    chatId: str
    
    
    
    
    


class UserProfile(BaseModel):
    """Perfil de usuário"""
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    topics_of_interest: List[str] = []
    prefer_audio: bool = False
    created_at: datetime
    updated_at: datetime


class MessageHistory(BaseModel):
    """Histórico de mensagens de uma sessão"""
    session_id: str
    user_id: str
    messages: List[dict]
    created_at: datetime
    last_activity: datetime