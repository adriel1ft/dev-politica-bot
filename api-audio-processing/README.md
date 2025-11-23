# API de Processamento de Áudio

Esta API serve como um worker para processamento de áudio, oferecendo funcionalidades de conversão de texto em fala (Text-to-Speech) e de fala em texto (Speech-to-Text) utilizando os modelos da OpenAI.

## Funcionalidades

- **Text-to-Speech**: Converte um texto fornecido em um arquivo de áudio MP3 e o armazena em um bucket S3 (via LocalStack).
- **Speech-to-Text**: Transcreve um arquivo de áudio para texto em português.
- **Integração S3**: Utiliza LocalStack para simular um ambiente AWS S3 para armazenamento de arquivos.
- **Síncrono**: As operações são síncronas, retornando o resultado diretamente na requisição.

## Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados:

1.  **Python 3.10+**
2.  **[uv](https://github.com/astral-sh/uv)**: Um instalador e resolvedor de pacotes Python extremamente rápido.
3.  **[LocalStack](https://docs.localstack.cloud/aws/getting-started/installation/)**: Um emulador de nuvem totalmente funcional para desenvolver e testar suas aplicações AWS localmente.
4.  **Chave de API da OpenAI**: Você precisará de uma chave de API válida da OpenAI.

## Instalação e Configuração

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

### 1. Instalar `uv`

Se você ainda não tem o `uv` instalado, execute o comando abaixo:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configurar o Ambiente Python

Clone o repositório, crie o ambiente virtual e instale as dependências.

```bash
# Crie o ambiente virtual
uv venv

# Ative o ambiente (Linux/macOS)
source .venv/bin/activate

# Instale as dependências do projeto
uv pip install -e .
```

### 3. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env` e preencha com suas credenciais.

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave da OpenAI:

```dotenv
# .env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ... outras variáveis podem ser mantidas como padrão para uso local
```

### 4. Iniciar o LocalStack

Para simular o ambiente da AWS localmente, inicie o LocalStack em modo detached. A aplicação cuidará de criar o bucket S3 necessário.

```bash
localstack start -d
```

## Uso

Com o ambiente ativado e o LocalStack rodando, inicie a API com o Uvicorn:

```bash
uvicorn api_audio_processing.main:app --host 0.0.0.0 --port 5001 --reload
```

A API estará disponível em `http://localhost:5001` e a documentação interativa (Swagger UI) em `http://localhost:5001/docs`.

## Endpoints da API

### `POST /text-to-speech`

Converte texto em áudio.

**Exemplo de requisição com `curl`:**

```bash
curl -X POST "http://localhost:5001/text-to-speech" \
-H "Content-Type: application/json" \
-d '{
  "text": "Olá, mundo! Este é um teste de conversão de texto para áudio.",
  "voice": "nova",
  "speed": 1.0
}'
```

**Resposta esperada:**

```json
{
  "audio_url": "https://s3.amazonaws.com/audio-processing/tts/20251122/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
  "duration_seconds": null,
  "voice": "nova",
  "text_length": 65
}
```

### `POST /speech-to-text`

Transcreve um arquivo de áudio para texto.

**Exemplo de requisição com `curl`:**

```bash
curl -X POST "http://localhost:5001/speech-to-text" \
-F "file=@/caminho/para/seu/audio.mp3"
```

**Resposta esperada:**

```json
{
  "text": "olá mundo este é um teste de conversão de áudio para texto.",
  "duration_seconds": null,
  "language": "pt-BR"
}
```

## Desenvolvimento

Para contribuir com o projeto, instale as dependências de desenvolvimento:

```bash
uv pip install -e ".[dev]"
```

### Ferramentas de Qualidade de Código

- **Formatação (Black):**
  ```bash
  black src/
  ```
- **Linting (Ruff):**
  ```bash
  ruff check src/
  ```
- **Checagem de Tipos (Mypy):**
  ```bash
  mypy src/
  ```

## Estrutura do Projeto

```
api-audio-processing/
├── .env.example        # Exemplo de variáveis de ambiente
├── pyproject.toml      # Dependências e configuração do projeto
├── src/
│   └── api_audio_processing/
│       ├── __init__.py
│       ├── main.py     # Endpoints da API (FastAPI)
│       ├── config.py   # Configurações da aplicação (Pydantic)
│       ├── models.py   # Modelos de dados (Pydantic)
│       └── services.py # Lógica de negócio (OpenAI, Boto3)
└── data/               # Diretórios para arquivos temporários e cache
```
