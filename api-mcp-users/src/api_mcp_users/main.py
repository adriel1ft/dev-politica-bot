"""
MCP Server para gerenciamento de usuários
"""
from fastmcp import FastMCP
import logging
import os
from dotenv import load_dotenv

from .tools import (
    obter_ou_criar_usuario,
    atualizar_perfil_usuario,
    obter_preferencia_audio,
    listar_topicos_interesse,
    registrar_opiniao
)
from .config import settings

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Inicializar servidor MCP
mcp = FastMCP("mcp-users")

# Registrar Tools
mcp.tool()(obter_ou_criar_usuario)
mcp.tool()(atualizar_perfil_usuario)
mcp.tool()(obter_preferencia_audio)
mcp.tool()(listar_topicos_interesse)
mcp.tool()(registrar_opiniao)


def main() -> None:
    """Ponto de entrada principal"""
    logger.info(
        f"Iniciando MCP Server de Usuários v{settings.mcp_server_version} "
        f"na porta {os.getenv('MCP_SERVER_PORT', 8001)}"
    )
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.getenv("MCP_SERVER_PORT", 8001))
    )


if __name__ == "__main__":
    main()