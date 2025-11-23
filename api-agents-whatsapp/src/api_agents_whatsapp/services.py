"""
Serviço de agentes para processar mensagens
"""
import logging
import os
from typing import Optional
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.tools.mcp import MultiMCPTools
from .config import settings
from .models import AgentRequest, AgentResponse
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentService:
    """Gerenciador de agentes Agno com suporte a múltiplos MCPs"""
    
    def __init__(self):
        self.agent = None
        self.mcp_context = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Inicializa o agente com modelo OpenAI e ferramentas MCP"""
        try:
            logger.info("🚀 Inicializando Agente Agno...")
            
            self.agent = Agent(
                model=OpenAIChat(
                    id=settings.agent_model,
                    api_key=settings.openai_api_key,
                ),
                markdown=True,
            )
            logger.info("✅ Agente Agno inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar agente: {e}")
            raise
    
    async def _setup_mcp_tools(self) -> Optional[MCPTools]:
        """
        Configura conexão com servidor MCP de Projetos de Lei
        
        Returns:
            MCPTools conectado ou None se falhar
        """
        mcp_tools_list = []

        try:
            logger.info(f"🔌 Conectando ao MCP: {settings.mcp_projetos_lei_url}")
            
            mcp_projetos_lei = MCPTools(
                transport="streamable-http",
                url=settings.mcp_projetos_lei_url
            )

            mcp_tools_list.append(mcp_projetos_lei)
            logger.info(f"✅ MCP conectado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao MCP: {e}")
        
        try:
            logger.info(f"🔌 Conectando ao MCP Usuários: {settings.mcp_users_url}")
            mcp_users = MCPTools(
                transport="streamable-http",
                url=settings.mcp_users_url
            )
            mcp_tools_list.append(mcp_users)
            logger.info("✅ MCP Usuários conectado")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar MCP Usuários: {e}")

        if not mcp_tools_list:
            logger.warning("⚠️  Nenhum MCP disponível, agente funcionará sem ferramentas")
            return None
        
        return mcp_tools_list
    
    async def process_message(self, request: AgentRequest) -> AgentResponse:
        """
        Processa uma mensagem do usuário usando o agente Agno
        
        Args:
            request: Requisição do agente
            
        Returns:
            Resposta do agente com metadados
        """
        try:
            logger.info(f"🤖 Processando mensagem de {request.user_id}")
            logger.info(f"   Tipo: {request.message_type}")
            logger.info(f"   Conteúdo: {request.user_message[:100]}...")
            
            # Construir prompt baseado no tipo de mensagem
            prompt = self._build_prompt(request)
            
            # Configurar ferramentas MCP
            mcp_tools_list = await self._setup_mcp_tools()
            
            # Executar agente com context manager se MCP disponível
            if mcp_tools_list:
                agent_with_tools = Agent(
                    model=OpenAIChat(
                        id=settings.agent_model,
                        api_key=settings.openai_api_key,
                    ),
                    tools=[tool for tool in mcp_tools_list],
                    markdown=True,
                    output_schema=AgentResponse
                )
                logger.info("📤 Enviando prompt para agente...")
                response_output = await agent_with_tools.arun(input=prompt)
            else:
                # Fallback: usar agente sem tools
                logger.warning("⚠️  Usando agente sem ferramentas MCP")
                response_output = await self.agent.arun(input=prompt)
            
            logger.info("📥 Resposta recebida do agente")
            try:
                logger.info(f"Resposta completa: {response_output.content.auxiliary_text}")
            except Exception:
                pass

            # Extrair texto da resposta
            response_text = self._extract_response_text(response_output)

            auxiliary_text = self._extract_auxiliary_text(response_output)
            
            logger.info(f"✅ Resposta recebida: {response_text[:80]}...")
            
            # Determinar se deve enviar áudio
            should_send_audio = self._should_send_audio(request, response_output)
            
            # Criar resposta
            response = AgentResponse(
                session_id=request.session_id,
                user_id=request.user_id,
                response_text=response_text,
                auxiliary_text=auxiliary_text,
                should_send_audio=should_send_audio,
                timestamp=datetime.now(),
            )
            
            logger.info(
                f"✅ Resposta gerada para {request.user_id} "
                f"(áudio: {should_send_audio})"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            logger.exception("Traceback completo:")
            raise
    
    def _extract_response_text(self, response_output) -> str:
        """
        Extrai o texto da resposta do agente
        
        Args:
            response_output: Output do agente (pode ter vários formatos)
            
        Returns:
            Texto extraído
        """
        # Tentar diferentes atributos comuns
        if hasattr(response_output, 'content'):
            text = response_output.content
            return text.response_text if hasattr(text, 'response_text') else text
        elif isinstance(response_output, dict):
            return response_output.get('response_text', '')
        return str(response_output)
    
    def _build_prompt(self, request: AgentRequest) -> str:
        """
        Constrói o prompt para o agente baseado na requisição
        
        Args:
            request: Requisição do agente
            
        Returns:
            Prompt formatado para o agente
        """
        base_prompt = f"""
Your Role: Especialista em legislação brasileira, com foco em traduzir temas complexos do Congresso Nacional para linguagem simples e acessível.

Short basic instruction: Responda perguntas sobre projetos de lei ou temas que impactam comunidades, adaptando a linguagem para pessoas com menor escolaridade.

What you should do:
- Analise a pergunta do usuário, que pode ser sobre um projeto de lei específico ou sobre um tema que afeta sua comunidade.
- Responda com linguagem simples, clara e acessível, adaptando o tom e o nível de detalhe ao tipo de resposta (áudio ou texto).
- Se for **áudio** (`should_send_audio = true`):
   - A resposta principal (`response_text`) deve ter até 1200 caracteres (ideal: ~800).
   - Use linguagem oral, fluída e expositiva, com explicações simples e exemplos se necessário.
   - **Não inclua links, emojis ou caracteres especiais**. 
   - O campo `auxiliary_text` deve conter observações extras ou complementares, caso precise. Também
   pode ser usado para destacar pontos importantes, fornecer contexto adicional ou incluir links.
- Se for **texto** (`should_send_audio = false`):
   - A resposta principal (`response_text`) deve conter mais informações, explicações adicionais e, se necessário, links úteis para fontes confiáveis (e-Cidadania, Câmara dos Deputados etc).
   - O `auxiliary_text` pode ser omitido ou usado para contextualizar ou destacar pontos relevantes.

Your Goal: Facilitar o entendimento de temas legislativos, aproximando o cidadão do Congresso Nacional, usando uma linguagem que respeite o nível de instrução do público.

Constraint:
- Em áudio: até 1200 caracteres, tom expositivo e acessível.
- Em texto: mais completo e informativo.
- Sem jargões técnicos. Use exemplos e explique termos difíceis.
- Links e fontes só quando realmente agregarem.

Context:
- O público é formado por cidadãos de diferentes regiões, muitos com baixa escolaridade.
- As perguntas podem ser sobre projetos de lei específicos ou temas que afetam diretamente a comunidade (mesmo que a relação com a lei não seja clara).
- O atendimento é feito via WhatsApp.
"""
        additional_prompt = f"""
📋 CONTEXTO DA MENSAGEM:
- Tipo: {request.message_type}
- Usuário: {request.user_id}
- Session: {request.session_id}

💬 MENSAGEM DO USUÁRIO:
{request.user_message}
⚙️ INFORMAÇÕES DO USUÁRIO:
"""
        base_prompt += additional_prompt
        
        # Adicionar preferências do usuário se disponíveis
        if request.user_preferences:
            if request.user_preferences.get("topics"):
                topics = ", ".join(request.user_preferences["topics"])
                base_prompt += f"\n- Tópicos de interesse: {topics}"
            
            if request.user_preferences.get("prefer_audio"):
                base_prompt += "\n- Preferência: Respostas em áudio (responda concisamente)"
        
        base_prompt += "\n\nAGORA, responda à mensagem do usuário:"
        
        return base_prompt
    
    def _extract_auxiliary_text(self, response_output) -> Optional[str]:
        """
        Retorna texto auxiliar para TTS se necessário
        
        Args:
            should_send_audio: Se deve enviar áudio
            
        Returns:
            Texto auxiliar ou None
        """
        if hasattr(response_output, 'content'):
            content = response_output.content
            if hasattr(content, 'auxiliary_text'):
                return content.auxiliary_text
            elif isinstance(content, dict):
                return content.get('auxiliary_text')
        
        return None
    
    def _should_send_audio(self, request: AgentRequest, response_output) -> bool:
        """
        Determina se a resposta deve ser enviada em áudio
        
        Args:
            request: Requisição do agente
            
        Returns:
            True se deve enviar áudio
        """
        if request.user_preferences:
            if request.user_preferences.get("prefer_audio"):
                return True

        if hasattr(response_output, 'content'):
            content = response_output.content
            if hasattr(content, 'should_send_audio'):
                return content.should_send_audio
            elif isinstance(content, dict):
                return content.get('should_send_audio', False)

        if request.message_type == "audio":
            return True
        
        
        return False


# Instância global do serviço
agent_service = AgentService()