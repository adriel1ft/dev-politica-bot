"""
Exemplo de cliente Agno para interagir com o MCP Server de Projetos de Lei.
Baseado na documentação: https://docs.agno.com/concepts/tools/mcp/transports/streamable_http
"""
import asyncio
import os

# Certifique-se de ter a biblioteca 'agno' e um modelo de LLM instalados
# uv pip install agno openai
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

# URL do nosso servidor MCP local
# O FastMCP com 'streamable-http' expõe as tools em /mcp por padrão
SERVER_URL = "http://localhost:8000/mcp"


async def run_agent(message: str) -> None:
    """
    Cria um agente Agno, conecta-se ao nosso MCP Server e envia uma mensagem.
    """
    print(f"🔌 Conectando ao MCP Server em {SERVER_URL}...")
    
    # Inicializa o MCPTools para se conectar ao nosso servidor
    # O 'async with' gerencia a conexão e o fechamento automaticamente
    async with MCPTools(transport="streamable-http", url=SERVER_URL) as mcp_tools:
        print("✅ Conectado! Criando agente...")

        agent = Agent(
            model=OpenAIChat(api_key=os.getenv("OPENAI_API_KEY")),
            tools=[mcp_tools],  # Fornece as tools do nosso servidor para o agente
            markdown=True,
        )

        print(f"🤖 Agente pronto. Enviando prompt: '{message}'\n---")
        
        # Envia a mensagem para o agente e imprime a resposta em stream
        await agent.aprint_response(input=message, stream=True)
        print("\n---")


if __name__ == "__main__":
    # Verifique se a chave da API da OpenAI está configurada
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("A variável de ambiente OPENAI_API_KEY não foi definida.")

    # Mensagem de exemplo que irá acionar a tool 'buscar_projetos_recentes'
    prompt = "Pode buscar os 3 projetos de lei mais recentes sobre inteligência artificial no Brasil?"
    
    try:
        asyncio.run(run_agent(prompt))
    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")
        print("   Certifique-se de que o servidor MCP está rodando em outro terminal.")
