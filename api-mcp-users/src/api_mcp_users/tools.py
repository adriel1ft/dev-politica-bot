"""
Tools MCP para gerenciamento de usuários
"""
from typing import Optional, List, Dict, Any
import logging
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

# Conexão com MongoDB (reutilizar da config)
from .config import settings

client = MongoClient(settings.mongodb_url)
db = client[settings.mongodb_db]
users_collection = db["users"]


async def obter_ou_criar_usuario(user_id: str) -> Dict[str, Any]:
    """
    Obtém informações de um usuário existente ou cria um novo
    
    Args:
        user_id: ID único do usuário (WhatsApp ID)
        
    Returns:
        Dados do usuário (nome, idade, localização, preferências)
    """
    try:
        user_doc = users_collection.find_one({"user_id": user_id})
        
        if user_doc:
            logger.info(f"✅ Usuário encontrado: {user_id}")
            return {
                "user_id": user_doc.get("user_id"),
                "name": user_doc.get("name"),
                "age": user_doc.get("age"),
                "location": user_doc.get("location"),
                "topics_of_interest": user_doc.get("topics_of_interest", []),
                "prefer_audio": user_doc.get("prefer_audio", False),
                "created_at": str(user_doc.get("created_at")),
                "updated_at": str(user_doc.get("updated_at"))
            }
        
        logger.info(f"🆕 Novo usuário criado: {user_id}")
        new_user = {
            "user_id": user_id,
            "name": None,
            "age": None,
            "location": None,
            "topics_of_interest": [],
            "prefer_audio": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        users_collection.insert_one(new_user)
        
        return {k: v for k, v in new_user.items() if k not in ["created_at", "updated_at"]} | {
            "created_at": str(new_user["created_at"]),
            "updated_at": str(new_user["updated_at"])
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter/criar usuário: {e}")
        raise


async def atualizar_perfil_usuario(
    user_id: str,
    name: Optional[str] = None,
    age: Optional[int] = None,
    location: Optional[str] = None,
    topics_of_interest: Optional[List[str]] = None,
    prefer_audio: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Atualiza o perfil de um usuário com novas informações
    
    Args:
        user_id: ID do usuário
        name: Nome completo
        age: Idade
        location: Localização (bairro, cidade)
        topics_of_interest: Tópicos de interesse legislativo
        prefer_audio: Preferência por resposta em áudio
        
    Returns:
        Dados atualizados do usuário
    """
    try:
        update_data = {"updated_at": datetime.utcnow()}
        
        if name:
            update_data["name"] = name
        if age:
            update_data["age"] = age
        if location:
            update_data["location"] = location
        if topics_of_interest:
            update_data["topics_of_interest"] = topics_of_interest
        if prefer_audio is not None:
            update_data["prefer_audio"] = prefer_audio
        
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        logger.info(f"📝 Perfil atualizado: {user_id}")
        
        # Retornar dados atualizados
        user_doc = users_collection.find_one({"user_id": user_id})
        return {
            "user_id": user_doc.get("user_id"),
            "name": user_doc.get("name"),
            "age": user_doc.get("age"),
            "location": user_doc.get("location"),
            "topics_of_interest": user_doc.get("topics_of_interest", []),
            "prefer_audio": user_doc.get("prefer_audio", False),
            "updated_at": str(user_doc.get("updated_at"))
        }
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar perfil: {e}")
        raise


async def obter_preferencia_audio(user_id: str) -> Dict[str, Any]:
    """
    Obtém a preferência de áudio do usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Preferência de áudio e informações do usuário
    """
    try:
        user = await obter_ou_criar_usuario(user_id)
        return {
            "user_id": user_id,
            "prefer_audio": user.get("prefer_audio", False),
            "name": user.get("name")
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter preferência de áudio: {e}")
        raise


async def listar_topicos_interesse() -> Dict[str, List[str]]:
    """
    Lista tópicos disponíveis de interesse legislativo
    (baseado em comissões da Câmara dos Deputados)
    
    Returns:
        Lista de tópicos disponíveis
    """
    topicos = [
        "Saúde",
        "Educação",
        "Trabalho e Previdência",
        "Meio Ambiente",
        "Segurança Pública",
        "Economia e Finanças",
        "Agricultura",
        "Infraestrutura",
        "Direitos Humanos",
        "Tecnologia e Inovação"
    ]
    return {"topicos_disponiveis": topicos}

async def registrar_opiniao(
    user_id: str,
    texto: str,
    topicos: List[str],
    sentimento: str
) -> Dict[str, Any]:
    """
    Registra a opinião do usuário sobre temas legislativos
    
    Args:
        user_id: ID do usuário
        texto: Texto da opinião
        topicos: Tópicos relacionados
        sentimento: Sentimento associado (positivo, negativo, neutro)
        
    Returns:
        Confirmação de registro da opinião
    """
    try:
        opinion = {
            "opinion_id": str(datetime.utcnow().timestamp()).replace('.', ''),
            "user_id": user_id,
            "texto": texto,
            "topicos": topicos,
            "sentimento": sentimento,
            "created_at": datetime.utcnow()
        }
        db["opinions"].insert_one(opinion)
        
        logger.info(f"🗣️ Opinião registrada: {opinion['opinion_id']} para usuário {user_id}")
        
        return {
            "opinion_id": opinion["opinion_id"],
            "user_id": user_id,
            "status": "registrada",
            "created_at": str(opinion["created_at"])
        }
    except Exception as e:
        logger.error(f"❌ Erro ao registrar opinião: {e}")
        raise