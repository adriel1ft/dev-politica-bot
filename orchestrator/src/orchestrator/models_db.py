from datetime import datetime
from typing import Optional, List


class UserDB:
    """Modelo de usuário para MongoDB"""
    
    def __init__(self, user_id: str, name: str = None, age: int = None, 
                 location: str = None, prefer_audio: bool = False,
                 cidade: str = None, estado: str = None, cep: str = None,
                 bairro: str = None, logradouro: str = None):
        self.user_id = user_id
        self.name = name
        self.age = age
        self.location = location
        self.cidade = cidade
        self.estado = estado
        self.cep = cep
        self.bairro = bairro
        self.logradouro = logradouro
        self.topics_of_interest = []
        self.prefer_audio = prefer_audio
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "location": self.location,
            "cidade": self.cidade,
            "estado": self.estado,
            "cep": self.cep,
            "bairro": self.bairro,
            "logradouro": self.logradouro,
            "topics_of_interest": self.topics_of_interest,
            "prefer_audio": self.prefer_audio,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SessionDB:
    """Modelo de sessão para MongoDB"""
    
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.messages = []
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_active = True
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": self.messages,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_active": self.is_active,
        }