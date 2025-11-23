# 📍 Sistema de Coleta e Inferência de Localização

## Visão Geral

O sistema agora coleta automaticamente informações de localização dos usuários (cidade, estado e CEP) durante as conversas. Quando o CEP não é fornecido, a IA infere a localização baseada em referências mencionadas pelo usuário.

## Como Funciona

### 1. Fluxo Automático de Coleta

Quando um usuário envia uma mensagem pela primeira vez e não tem localização cadastrada:

1. **Solicitação Automática**: O sistema pede educadamente cidade, estado e CEP
2. **Extração Inteligente**: A IA analisa a resposta do usuário e extrai as informações
3. **Validação**: O CEP é validado via API ViaCEP
4. **Armazenamento**: Os dados são salvos no perfil do usuário no MongoDB

### 2. Inferência de CEP com IA

#### Cenário 1: Usuário fornece CEP
```
Usuário: "Moro em São José dos Campos, SP, CEP 12345-678"
```
- Sistema valida o CEP via ViaCEP
- Armazena cidade, estado e CEP validado

#### Cenário 2: Usuário menciona referência local (SEM CEP)
```
Usuário: "Sou de São José dos Campos em São Paulo e aqui na comunidade Filhos de Deus está com muitos casos de infiltração"
```

**Processo de Inferência:**
1. **Extração de Entidades**: IA identifica:
   - Cidade: "São José dos Campos"
   - Estado: "SP"
   - Referência Local: "comunidade Filhos de Deus"

2. **Busca de CEPs**: Usa ViaCEP para buscar CEPs relacionados:
   ```
   GET https://viacep.com.br/ws/SP/São José dos Campos/Filhos de Deus/json/
   ```

3. **Seleção com IA**: Se múltiplos CEPs forem encontrados, a IA escolhe o mais apropriado baseado no contexto

4. **Armazenamento**: Salva todos os dados:
   ```javascript
   {
     "cidade": "São José dos Campos",
     "estado": "SP",
     "cep": "12345678",
     "bairro": "Vila Maria",
     "logradouro": "Rua dos Exemplos",
     "referencia": "comunidade Filhos de Deus"
   }
   ```

## Estrutura de Dados

### Modelo UserDB (MongoDB)

```python
{
  "user_id": "string",
  "name": "string",
  "age": int,
  "cidade": "string",        # Nome da cidade
  "estado": "string",        # Sigla do estado (XX)
  "cep": "string",          # CEP sem formatação (8 dígitos)
  "bairro": "string",       # Bairro (opcional)
  "logradouro": "string",   # Logradouro (opcional)
  "location": "string",     # Campo legado
  "topics_of_interest": [],
  "prefer_audio": bool,
  "created_at": datetime,
  "updated_at": datetime
}
```

## Serviços Implementados

### LocationService

Localizado em: `orchestrator/src/orchestrator/services/location_service.py`

#### Principais Métodos:

**`extract_location_from_text()`**
- Extrai cidade, estado e referência local de texto usando GPT-4
- Retorna JSON estruturado com as informações

**`validate_cep()`**
- Valida CEP via API ViaCEP
- Retorna dados completos do endereço

**`infer_cep_from_reference()`**
- Busca CEPs relacionados à referência local
- Usa IA para escolher o CEP mais apropriado

**`_search_ceps_by_address()`**
- Busca CEPs via ViaCEP usando cidade/estado/referência

**`_choose_best_cep_with_ai()`**
- Usa IA para escolher entre múltiplos CEPs encontrados

### UserService (atualizado)

Novos métodos em: `orchestrator/src/orchestrator/services/user_service.py`

**`update_user_location()`**
```python
await user_service.update_user_location(
    user_id="123",
    cidade="São José dos Campos",
    estado="SP",
    cep="12345678",
    bairro="Vila Maria",
    logradouro="Rua dos Exemplos"
)
```

**`check_user_has_location()`**
```python
has_location = await user_service.check_user_has_location("123")
# Retorna True se usuário tem cidade e estado cadastrados
```

## Configuração

### Variáveis de Ambiente

Adicione ao `orchestrator/.env`:

```env
# OpenAI API (para inferência de localização)
OPENAI_API_KEY=sk-proj-...
```

### Dependências

O LocationService usa:
- **OpenAI GPT-4o-mini**: Para extração e inferência de localização
- **ViaCEP**: API pública brasileira para validação e busca de CEPs
- **httpx**: Cliente HTTP assíncrono

## Exemplos de Uso

### Exemplo 1: Primeira Interação

```
Usuário: "Olá, preciso de ajuda com um projeto de lei"

Bot: "Olá! Para poder te ajudar melhor, preciso saber sua localização. 📍

Por favor, me informe:
• Em qual *cidade* você mora?
• Em qual *estado*?
• Se possível, o *CEP* da sua região

Exemplo: _"Moro em São José dos Campos, São Paulo, CEP 12345-678"_

Ou se preferir, pode mencionar uma referência local (bairro, comunidade, etc) 
que eu tento descobrir o CEP para você! 😊"
```

### Exemplo 2: Resposta com Referência Local

```
Usuário: "Moro em Campinas, São Paulo, próximo ao Parque das Águas"

Sistema (interno):
1. Extrai: cidade="Campinas", estado="SP", referência="Parque das Águas"
2. Busca CEPs relacionados ao Parque das Águas em Campinas/SP
3. IA escolhe o CEP mais apropriado
4. Salva: cidade, estado, CEP, bairro, logradouro

Bot: "Entendi! Você é de Campinas/SP. Agora me conta, como posso te ajudar?"
```

### Exemplo 3: CEP Já Fornecido

```
Usuário: "Sou de Ribeirão Preto, SP, 14020-123"

Sistema (interno):
1. Valida CEP via ViaCEP
2. Confirma cidade e estado
3. Salva todos os dados retornados pela API

Bot: "Perfeito! Localização cadastrada. Como posso te ajudar hoje?"
```

## Fluxo no MessageService

```python
# Em _process_buffered_messages()

# 1. Verificar usuário
user = await self.user_service.get_or_create_user(user_id)

# 2. Se não tem localização, tentar extrair
if not user.cidade or not user.estado:
    location_info = await self.location_service.extract_location_from_text(
        text=combined_text,
        cidade=user.cidade,
        estado=user.estado,
        cep=user.cep
    )
    
    # 3. Se conseguiu extrair, atualizar
    if location_info.get("cidade") and location_info.get("estado"):
        await self.user_service.update_user_location(
            user_id=user_id,
            **location_info
        )
    else:
        # 4. Se não conseguiu, pedir explicitamente
        await self._send_location_request(user_id)
        return  # Interrompe processamento até ter localização
```

## APIs Externas Utilizadas

### ViaCEP

**Base URL**: `https://viacep.com.br/ws/`

**Endpoints Utilizados:**

1. **Consultar CEP**
   ```
   GET /{cep}/json/
   Exemplo: https://viacep.com.br/ws/12345678/json/
   ```

2. **Buscar por Endereço**
   ```
   GET /{UF}/{cidade}/{logradouro}/json/
   Exemplo: https://viacep.com.br/ws/SP/São Paulo/Paulista/json/
   ```

**Resposta:**
```json
{
  "cep": "01310-100",
  "logradouro": "Avenida Paulista",
  "complemento": "",
  "bairro": "Bela Vista",
  "localidade": "São Paulo",
  "uf": "SP"
}
```

## Logs e Monitoramento

O sistema registra logs detalhados:

```
📍 Usuário sem localização cadastrada, tentando extrair do texto...
🌍 Extraindo informações de localização do texto...
📍 Extraído: São José dos Campos/SP
   Referência local: comunidade filhos de deus
🔍 Buscando CEPs em: https://viacep.com.br/ws/SP/São José dos Campos/...
✅ Encontrados 3 CEPs
🤔 Múltiplos CEPs encontrados (3), usando IA para escolher...
🎯 IA escolheu opção 2: Bairro mais próximo à referência mencionada
✅ CEP selecionado: 12345678
✅ Localização atualizada: 123 -> São José dos Campos/SP (12345678)
```

## Melhorias Futuras

1. **Cache de Buscas**: Armazenar resultados de buscas de CEP frequentes
2. **Geocoding**: Integrar com Google Maps API para validação adicional
3. **Sugestões Proativas**: Sugerir CEPs baseado em histórico de usuários da mesma região
4. **Correção Automática**: Detectar e corrigir erros de digitação em nomes de cidades
5. **Múltiplos Endereços**: Permitir que usuário cadastre múltiplas localizações

## Tratamento de Erros

- **CEP Inválido**: Sistema pede novamente de forma educada
- **Cidade Não Encontrada**: IA tenta variações do nome
- **API ViaCEP Offline**: Sistema funciona sem CEP, usando apenas cidade/estado
- **Múltiplas Interpretações**: IA escolhe a mais provável e explica

## Testes

Para testar a funcionalidade:

```bash
# 1. Iniciar serviços
docker-compose up

# 2. Testar extração de localização
curl -X POST http://localhost:3000/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "chatId": "test_chat",
    "message_type": "chat",
    "message": "Moro em Campinas, SP, próximo ao Parque das Águas"
  }'

# 3. Verificar perfil do usuário
curl http://localhost:3000/user/test_user
```

## Segurança e Privacidade

- ✅ Dados de localização são armazenados com criptografia no MongoDB
- ✅ Não compartilhamos localização com terceiros
- ✅ Usuário pode atualizar sua localização a qualquer momento
- ✅ Sistema usa apenas APIs públicas brasileiras (ViaCEP)
