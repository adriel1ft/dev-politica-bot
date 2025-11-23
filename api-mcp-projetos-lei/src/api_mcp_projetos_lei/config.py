"""
Configurações do servidor MCP
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    openai_api_key: str = ""
    mcp_server_port: int = 8000
    
    # MCP Server
    mcp_server_name: str = "projetos-lei-mcp"
    mcp_server_version: str = "0.1.0"
    
    # Scraping
    scraping_timeout: int = 60
    scraping_headless: bool = True
    
    # Cache
    cache_dir: Path = Path("./data/cache")
    cache_ttl: int = 3600  # 1 hora
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Criar diretório de cache se não existir
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Instância global de configurações
settings = Settings()