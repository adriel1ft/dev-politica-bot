# API MCP - Projetos de Lei Brasil

Servidor MCP (Model Context Protocol) para fornecer dados sobre projetos de lei e legislações brasileiras.

## Recursos

- **Tools**: Buscar e analisar projetos de lei, notícias relacionadas
- **Resources**: Links importantes do e-Cidadania
- **Prompts**: Templates para análise de projetos

## Instalação

### Usando uv (recomendado)

```bash
# Instalar uv se ainda não tiver
curl -LsSf https://astral.sh/uv/install.sh | sh

# Criar ambiente e instalar dependências
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -e .
```

### Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
uv pip install -e ".[dev]"

# Rodar testes
pytest

# Formatação
black src/ tests/
ruff check src/ tests/

# Type checking
mypy src/
```

## Uso

### Via CLI

```bash
mcp-projetos-lei
```

### Via Python

```python
from api_mcp_projetos_lei.main import mcp

# O servidor MCP estará disponível
```

## Configuração

Copie `.env.example` para `.env` e configure as variáveis necessárias:

```bash
cp .env.example .env
```

## Estrutura do Projeto

```
src/api_mcp_projetos_lei/
├── __init__.py
├── __main__.py
├── main.py           # Servidor MCP + registros
├── config.py         # Configurações
├── tools.py          # Funções das tools
├── resources.py      # Funções dos resources
├── prompts.py        # Funções dos prompts
└── scrapers/
    ├── __init__.py
    └── camara_scraper.py
```

## Funcionalidades

### Tools Disponíveis

1. **buscar_projetos_recentes**: Busca projetos de lei por tema
2. **obter_detalhes_projeto**: Obtém detalhes completos de um projeto
3. **buscar_noticias_relacionadas**: Busca notícias sobre temas legislativos

### Resources

- **links://e-cidadania**: Links importantes para participação cidadã

### Prompts

- **prompt_analise_projeto**: Template para análise de projetos de lei

## Roadmap

- [ ] Implementar scrapers com SeleniumBase
  - [ ] Homepage do assunto
  - [ ] Notícia relacionada ao assunto
  - [ ] Projeto de lei relacionado ao assunto
- [ ] Adicionar cache de resultados
- [ ] Criar testes unitários
- [ ] Sistema de crawler periódico ou on-demand
- [ ] Adicionar rate limiting
- [ ] Extração de links de propostas de lei em notícias
