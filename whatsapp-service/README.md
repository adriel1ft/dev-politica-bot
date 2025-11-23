# WhatsApp Service

Serviço de integração com WhatsApp para o projeto DevsImpacto. Atua como ponte entre o WhatsApp Web e a API orquestradora, recebendo e enviando mensagens de forma automatizada.

## Visão Geral

Este serviço é responsável por:

- **Receber mensagens** do WhatsApp e encaminhá-las para a API orquestradora
- **Enviar mensagens** via WhatsApp através de comandos recebidos por webhook
- **Gerenciar sessão** persistente do WhatsApp Web
- Atuar como um **intermediário simples** sem lógica de negócio

## Arquitetura

```
WhatsApp Web ←→ WhatsApp Service ←→ API Orquestradora
                      ↓
                 Webhook Server
                 (porta 3001)
```

### Fluxo de Mensagens

**Recebimento (WhatsApp → Orquestrador):**

1. Usuário envia mensagem no WhatsApp
2. `handlers.js` captura a mensagem
3. Payload é enviado via POST para a API orquestradora
4. Orquestrador processa e decide a resposta

**Envio (Orquestrador → WhatsApp):**

1. Orquestrador faz POST para `/send-message`
2. `webhookServer.js` recebe o comando
3. Mensagem é enviada via WhatsApp Web
4. Confirmação é retornada ao orquestrador

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

1. **Node.js 18+**
2. **npm** ou **yarn**
3. **Chromium/Chrome** (usado pelo Puppeteer para WhatsApp Web)

## Instalação e Configuração

### 1. Instalar Dependências

```bash
cd whatsapp-service
npm install
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```dotenv
# .env
WEBHOOK_PORT=3001
WHATSAPP_SESSION=default
ORCHESTRATOR_URL=http://localhost:5000/process-message
```

**Variáveis Disponíveis:**

- `WEBHOOK_PORT`: Porta do servidor webhook (padrão: 3001)
- `WHATSAPP_SESSION`: Nome da sessão para múltiplas instâncias (padrão: default)
- `ORCHESTRATOR_URL`: URL da API orquestradora que processará as mensagens

### 3. Primeira Execução - Autenticação

Na primeira vez que você executar o serviço, será necessário escanear um QR Code:

```bash
npm start
```

1. Abra o WhatsApp no seu celular
2. Vá em **Dispositivos Conectados** → **Conectar um dispositivo**
3. Escaneie o QR Code exibido no terminal
4. Aguarde a mensagem `[✅] WhatsApp conectado!`

A sessão ficará salva em `.wwebjs_auth/session-{nome}/` e não será necessário escanear novamente.

## Uso

### Iniciar o Serviço

```bash
# Modo produção
npm start

# Modo desenvolvimento (com auto-reload)
npm run dev
```

### Testar o Webhook

**Enviar uma mensagem:**

```bash
curl -X POST "http://localhost:3001/send-message" \
-H "Content-Type: application/json" \
-d '{
  "chatId": "5585988123456@c.us",
  "message": "Olá! Esta é uma mensagem de teste."
}'
```

**Enviar mensagem com mídia:**

```bash
curl -X POST "http://localhost:3001/send-message" \
-H "Content-Type: application/json" \
-d '{
  "chatId": "5585988123456@c.us",
  "message": "Confira este áudio!",
  "mediaUrl": "https://example.com/audio.mp3",
  "mimetype": "audio/mpeg"
}'
```

**Verificar saúde do serviço:**

```bash
curl http://localhost:3001/health
```

## Estrutura do Projeto

```
whatsapp-service/
├── .env                    # Variáveis de ambiente (não versionar)
├── .env.example            # Exemplo de configuração
├── package.json            # Dependências do projeto
├── index.js                # Ponto de entrada principal
├── client.js               # Cliente WhatsApp (wwebjs)
├── handlers.js             # Handlers de mensagens recebidas
├── webhookServer.js        # Servidor HTTP para receber comandos
├── messageQueue.js         # Fila de mensagens (opcional)
├── .wwebjs_auth/           # Sessões autenticadas (não versionar)
└── .wwebjs_cache/          # Cache do WhatsApp Web
```

### Componentes Principais

#### `client.js` - WhatsAppClient

Gerencia a conexão com o WhatsApp Web usando `whatsapp-web.js`.

```javascript
const whatsappClient = new WhatsAppClient({
  sessionName: "minha-sessao",
});
await whatsappClient.initialize();
```

#### `handlers.js` - MessageHandlers

Captura mensagens recebidas e as encaminha para o orquestrador.

```javascript
const handlers = new MessageHandlers({
  orchestratorUrl: "http://localhost:8002/process-message",
});
handlers.setup(client);
```

#### `webhookServer.js`

Servidor Express que expõe endpoints para controle externo.

**Endpoints:**

- `GET /health` - Status do serviço
- `POST /send-message` - Enviar mensagem via WhatsApp

## Desenvolvimento

### Estrutura de Dados

**Payload de Mensagem Recebida (enviado ao orquestrador):**

```json
{
  "messageId": "3EB0XXXXX",
  "from": "5585988123456@c.us",
  "to": "5585988654321@c.us",
  "author": null,
  "body": "Olá, preciso de ajuda!",
  "type": "chat",
  "timestamp": 1700000000,
  "isGroup": false,
  "sender": {
    "id": "5585988123456@c.us",
    "name": "João Silva",
    "shortName": "João",
    "isMe": false,
    "isUser": true,
    "isGroup": false
  }
}
```

**Payload com Mídia:**

```json
{
  "messageId": "3EB0XXXXX",
  "from": "5585988123456@c.us",
  "body": "",
  "type": "ptt",
  "media": {
    "mimetype": "audio/ogg; codecs=opus",
    "filename": null
  },
  "sender": { ... }
}
```

### Formato de Chat ID

- **Contato individual**: `5585988123456@c.us`
- **Grupo**: `123456789-1234567890@g.us`

Use sempre o formato com DDD + número + `@c.us` para contatos.

### Logs e Debugging

O serviço usa emojis para facilitar a leitura dos logs:

- 🚀 Inicialização
- ✅ Sucesso
- ❌ Erro
- 📨 Mensagem recebida
- 📤 Mensagem enviada
- 📥 Download de mídia
- 🌐 Servidor web

### Tratamento de Erros

O serviço implementa:

- **Graceful shutdown**: Desconecta corretamente ao receber SIGINT (Ctrl+C)
- **Timeout de 10s**: Para requisições ao orquestrador
- **Retry automático**: Reconnect do WhatsApp Web em caso de desconexão
