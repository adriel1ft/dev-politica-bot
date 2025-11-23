import logging
import httpx
import json
from typing import Optional, Dict, Tuple
from openai import AsyncOpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class LocationService:
    """Serviço para extrair e inferir informações de localização usando IA"""
    
    def __init__(self):
        # Inicializar cliente OpenAI
        import os
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def extract_location_from_text(
        self, 
        text: str, 
        cidade: Optional[str] = None,
        estado: Optional[str] = None,
        cep: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Extrai informações de localização do texto usando IA
        
        Args:
            text: Texto da mensagem do usuário
            cidade: Cidade informada explicitamente (opcional)
            estado: Estado informado explicitamente (opcional)
            cep: CEP informado explicitamente (opcional)
            
        Returns:
            Dicionário com cidade, estado e cep inferidos
        """
        try:
            logger.info("🌍 Extraindo informações de localização do texto...")
            
            # Se já temos cidade, estado e CEP, retornar
            if cidade and estado and cep:
                logger.info(f"✅ Localização completa já fornecida: {cidade}/{estado} - {cep}")
                return {"cidade": cidade, "estado": estado, "cep": cep}
            
            # Preparar prompt para extração
            prompt = self._build_extraction_prompt(text, cidade, estado, cep)
            
            # Chamar OpenAI para extrair informações
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em extrair informações de localização de textos brasileiros. Retorne apenas JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            # Extrair resposta
            result = json.loads(response.choices[0].message.content)
            
            cidade_extraida = result.get("cidade") or cidade
            estado_extraido = result.get("estado") or estado
            referencia_local = result.get("referencia_local")
            
            logger.info(f"📍 Extraído: {cidade_extraida}/{estado_extraido}")
            if referencia_local:
                logger.info(f"   Referência local: {referencia_local}")
            
            # Se temos CEP, validar e usar
            if cep:
                cep_validado = await self.validate_cep(cep)
                if cep_validado:
                    return {
                        "cidade": cidade_extraida,
                        "estado": estado_extraido,
                        "cep": cep_validado["cep"],
                        "bairro": cep_validado.get("bairro"),
                        "logradouro": cep_validado.get("logradouro")
                    }
            
            # Se não temos CEP, tentar inferir
            if cidade_extraida and estado_extraido and referencia_local:
                cep_inferido = await self.infer_cep_from_reference(
                    cidade_extraida, 
                    estado_extraido, 
                    referencia_local
                )
                if cep_inferido:
                    return {
                        "cidade": cidade_extraida,
                        "estado": estado_extraido,
                        "cep": cep_inferido["cep"],
                        "bairro": cep_inferido.get("bairro"),
                        "logradouro": cep_inferido.get("logradouro"),
                        "referencia": referencia_local
                    }
            
            # Retornar o que conseguimos extrair
            return {
                "cidade": cidade_extraida,
                "estado": estado_extraido,
                "cep": None,
                "referencia": referencia_local
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair localização: {e}")
            return {
                "cidade": cidade,
                "estado": estado,
                "cep": cep
            }
    
    def _build_extraction_prompt(
        self, 
        text: str, 
        cidade: Optional[str],
        estado: Optional[str],
        cep: Optional[str]
    ) -> str:
        """Constrói prompt para extração de localização"""
        
        prompt = f"""Analise o texto abaixo e extraia informações de localização no Brasil:

TEXTO: "{text}"

INFORMAÇÕES JÁ FORNECIDAS:
- Cidade: {cidade or "NÃO FORNECIDA"}
- Estado: {estado or "NÃO FORNECIDA"}
- CEP: {cep or "NÃO FORNECIDO"}

TAREFA:
1. Extraia ou confirme a CIDADE mencionada no texto
2. Extraia ou confirme o ESTADO (sigla de 2 letras, ex: SP, RJ, MG)
3. Identifique qualquer REFERÊNCIA LOCAL específica (nome de bairro, comunidade, rua, estabelecimento)
   - Exemplos: "comunidade filhos de deus", "bairro vila maria", "rua das flores"

IMPORTANTE:
- Se já foi fornecida cidade/estado, use essas informações a menos que o texto contradiga
- Para referência local, procure por nomes de lugares específicos mencionados pelo usuário
- A referência local será usada para inferir o CEP depois

Retorne APENAS um JSON no formato:
{{
    "cidade": "nome da cidade ou null",
    "estado": "sigla do estado (XX) ou null",
    "referencia_local": "nome da referência local mencionada ou null"
}}
"""
        return prompt
    
    async def validate_cep(self, cep: str) -> Optional[Dict]:
        """
        Valida CEP usando API ViaCEP
        
        Args:
            cep: CEP a validar (com ou sem formatação)
            
        Returns:
            Dicionário com dados do CEP ou None se inválido
        """
        try:
            # Limpar CEP (remover pontuação)
            cep_limpo = "".join(filter(str.isdigit, cep))
            
            if len(cep_limpo) != 8:
                logger.warning(f"⚠️  CEP inválido (deve ter 8 dígitos): {cep}")
                return None
            
            logger.info(f"🔍 Validando CEP: {cep_limpo}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://viacep.com.br/ws/{cep_limpo}/json/",
                    timeout=10.0
                )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("erro"):
                    logger.warning(f"⚠️  CEP não encontrado: {cep_limpo}")
                    return None
                
                logger.info(f"✅ CEP validado: {data.get('localidade')}/{data.get('uf')}")
                return {
                    "cep": cep_limpo,
                    "logradouro": data.get("logradouro"),
                    "complemento": data.get("complemento"),
                    "bairro": data.get("bairro"),
                    "cidade": data.get("localidade"),
                    "estado": data.get("uf")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar CEP: {e}")
            return None
    
    async def infer_cep_from_reference(
        self, 
        cidade: str, 
        estado: str, 
        referencia: str
    ) -> Optional[Dict]:
        """
        Infere CEP a partir de referência local usando IA + APIs
        
        Args:
            cidade: Nome da cidade
            estado: Sigla do estado
            referencia: Referência local (bairro, comunidade, rua, etc)
            
        Returns:
            Dicionário com CEP inferido ou None
        """
        try:
            logger.info(f"🤖 Inferindo CEP: {referencia} em {cidade}/{estado}")
            
            # Buscar possíveis CEPs usando ViaCEP
            ceps_encontrados = await self._search_ceps_by_address(
                cidade, estado, referencia
            )
            
            if not ceps_encontrados:
                logger.warning(f"⚠️  Nenhum CEP encontrado para: {referencia}")
                return None
            
            # Se encontrou apenas um, usar esse
            if len(ceps_encontrados) == 1:
                logger.info(f"✅ CEP único encontrado: {ceps_encontrados[0]['cep']}")
                return ceps_encontrados[0]
            
            # Se encontrou múltiplos, usar IA para escolher o melhor
            logger.info(f"🤔 Múltiplos CEPs encontrados ({len(ceps_encontrados)}), usando IA para escolher...")
            melhor_cep = await self._choose_best_cep_with_ai(
                referencia, ceps_encontrados
            )
            
            if melhor_cep:
                logger.info(f"✅ CEP selecionado: {melhor_cep['cep']}")
                return melhor_cep
            
            # Fallback: retornar o primeiro
            logger.info(f"⚠️  Usando primeiro CEP como fallback")
            return ceps_encontrados[0]
            
        except Exception as e:
            logger.error(f"❌ Erro ao inferir CEP: {e}")
            return None
    
    async def _search_ceps_by_address(
        self, 
        cidade: str, 
        estado: str, 
        referencia: str
    ) -> list:
        """
        Busca CEPs usando API ViaCEP
        
        Args:
            cidade: Nome da cidade
            estado: Sigla do estado  
            referencia: Referência para buscar
            
        Returns:
            Lista de CEPs encontrados
        """
        try:
            # ViaCEP: formato GET /{UF}/{cidade}/{logradouro}/json/
            url = f"https://viacep.com.br/ws/{estado}/{cidade}/{referencia}/json/"
            
            logger.info(f"🔍 Buscando CEPs em: {url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    logger.info(f"✅ Encontrados {len(data)} CEPs")
                    return [
                        {
                            "cep": item.get("cep"),
                            "logradouro": item.get("logradouro"),
                            "complemento": item.get("complemento"),
                            "bairro": item.get("bairro"),
                            "cidade": item.get("localidade"),
                            "estado": item.get("uf")
                        }
                        for item in data[:5]  # Limitar a 5 resultados
                    ]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar CEPs: {e}")
            return []
    
    async def _choose_best_cep_with_ai(
        self, 
        referencia: str, 
        ceps: list
    ) -> Optional[Dict]:
        """
        Usa IA para escolher o CEP mais apropriado
        
        Args:
            referencia: Referência original do usuário
            ceps: Lista de CEPs encontrados
            
        Returns:
            CEP escolhido ou None
        """
        try:
            # Preparar lista de opções
            opcoes = "\n".join([
                f"{i+1}. CEP: {cep['cep']} - {cep.get('logradouro', '')} - Bairro: {cep.get('bairro', '')}"
                for i, cep in enumerate(ceps)
            ])
            
            prompt = f"""Baseado na referência local mencionada pelo usuário, escolha o CEP mais apropriado:

REFERÊNCIA DO USUÁRIO: "{referencia}"

OPÇÕES DE CEP:
{opcoes}

Retorne APENAS um JSON com:
{{
    "indice_escolhido": número de 1 a {len(ceps)} da melhor opção,
    "motivo": "breve explicação da escolha"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é especialista em localização brasileira. Retorne apenas JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            indice = result.get("indice_escolhido", 1) - 1
            motivo = result.get("motivo", "")
            
            logger.info(f"🎯 IA escolheu opção {indice + 1}: {motivo}")
            
            if 0 <= indice < len(ceps):
                return ceps[indice]
            
            return ceps[0]
            
        except Exception as e:
            logger.error(f"❌ Erro ao escolher CEP com IA: {e}")
            return ceps[0] if ceps else None
