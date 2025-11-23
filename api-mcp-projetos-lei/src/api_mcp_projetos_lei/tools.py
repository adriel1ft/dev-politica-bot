"""
Definição das ferramentas do MCP
Não importamos mcp aqui, apenas definimos as funções
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


async def buscar_projetos_recentes(
    tema: str,
    limite: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca projetos de lei recentes sobre um tema específico.
    
    Args:
        tema: Tema ou palavra-chave para buscar
        limite: Número máximo de resultados (padrão: 10)
    
    Returns:
        Lista de projetos de lei com informações básicas
    """
    logger.info(f"Buscando projetos sobre: {tema}")
    
    return [{
        "id": "PL-XXXX/2024",
        "titulo": f"Projeto sobre {tema}",
        "ementa": "Ementa do projeto...",
        "data_apresentacao": "2024-11-20",
        "autor": "Deputado(a) X",
        "status": "Em tramitação",
        "link": "https://camara.leg.br/..."
    }]


async def obter_detalhes_projeto(projeto_id: str) -> Dict[str, Any]:
    """
    Obtém detalhes completos de um projeto de lei específico.
    
    Args:
        projeto_id: ID do projeto (ex: PL-1234/2024)
    
    Returns:
        Detalhes completos do projeto
    """
    logger.info(f"Obtendo detalhes do projeto: {projeto_id}")
    
    return {
        "id": projeto_id,
        "titulo": "Título do projeto",
        "ementa": "Ementa completa...",
        "texto_integral": "Texto da proposta...",
        "tramitacao": [],
        "votacoes": [],
        "pareceres": []
    }


async def buscar_noticias_relacionadas(
    tema: str,
    dias_atras: int = 7
) -> List[Dict[str, Any]]:
    """
    Busca notícias relacionadas a temas legislativos.
    
    Args:
        tema: Tema para buscar notícias
        dias_atras: Período de busca em dias (padrão: 7)
    
    Returns:
        Lista de notícias com links para projetos relacionados
    """
    logger.info(f"Buscando notícias sobre: {tema}")
    
    return [{
        "titulo": f"Notícia sobre {tema}",
        "resumo": "Resumo da notícia...",
        "data": "2024-11-22",
        "link": "https://...",
        "projetos_relacionados": ["PL-XXXX/2024"]
    }]