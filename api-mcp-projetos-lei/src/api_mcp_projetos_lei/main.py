"""
MCP Server para projetos de lei e legislações brasileiras
"""
from fastmcp import FastMCP
from typing import List, Dict, Any
import logging
from .config import settings
from .tools import (
    buscar_projetos_recentes,
    obter_detalhes_projeto,
    buscar_noticias_relacionadas
)
from .resources import get_links_ecidadania
from .prompts import get_prompt_analise_projeto


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Inicializar servidor MCP
mcp = FastMCP(
    settings.mcp_server_name,
    dependencies=["seleniumbase", "httpx"]
)


# ===== REGISTRAR TOOLS =====
mcp.tool()(buscar_projetos_recentes)
mcp.tool()(obter_detalhes_projeto)
mcp.tool()(buscar_noticias_relacionadas)


# ===== REGISTRAR RESOURCES =====
@mcp.resource("links://e-cidadania")
async def links_ecidadania() -> str:
    """Links importantes do e-Cidadania"""
    return await get_links_ecidadania()


# ===== REGISTRAR PROMPTS =====
@mcp.prompt()
def prompt_analise_projeto() -> str:
    """Prompt para análise de projetos de lei"""
    return get_prompt_analise_projeto()


def main() -> None:
    """Ponto de entrada principal da aplicação"""
    logger.info(
        f"Iniciando {settings.mcp_server_name} v{settings.mcp_server_version} "
        f"com transporte 'streamable-http' na porta 8000"
    )
    mcp.run(transport="streamable-http", port=8000)


if __name__ == "__main__":
    main()