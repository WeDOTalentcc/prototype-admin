# Teams Integration — Developer Handoff

> Status: Production-ready. Branch `feat/orch-migration-sprint-I`. Último update: 2026-04-27.

---

## 0. Quick Start (10 minutos para o bot funcionando)

```bash
# 1. Configure as env vars mínimas (ver Seção 1)
MICROSOFT_APP_ID=<guid>
MICROSOFT_APP_PASSWORD=<secret>
TEAMS_WEBHOOK_SECRET=<32+chars>

# 2. Rode as migrations do banco
alembic upgrade head
# (cria teams_conversations e demais tabelas — Migration 097 em diante)

# 3. Suba o servidor
uvicorn app.main:app --reload

# 4. Baixe o ZIP do app
curl https://{seu-dominio}/api/v1/teams/manifest-zip -o wedo-teams.zip

# 5. Instale no Teams (sideloading — ver Seção 8)

# 6. Mande "oi" para o bot no Teams → deve responder via LIA
```

---

## 1. Variáveis de Ambiente (15 catalogadas)

### Obrigatórias — Bot Framework

| Variável | Descrição | Como obter |
|---|---|---|
| `MICROSOFT_APP_ID` | Client ID do app registration do bot (GUID) | Azure Portal → App Registrations → Overview |
| `MICROSOFT_APP_PASSWORD` | Client secret do bot | Azure Portal → App Registrations → Certificates & Secrets → **Value** (não o ID) |
| `TEAMS_WEBHOOK_SECRET` | HMAC secret para validação do webhook (≥32 chars) | Gere com: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Obrigatórias — SSO Tab (autenticação na Tab)

| Variável | Descrição |
|---|---|
| `AZURE_CLIENT_ID` | Client ID do app registration do SSO (pode ser o mesmo do bot) |
| `AZURE_TENANT_ID` | Directory (tenant) ID do Azure AD. Use `common` para multi-tenant |

### Obrigatórias — Tabs e manifesto

| Variável | Descrição | Exemplo |
|---|---|---|
| `WEDOTALENT_PLATFORM_URL` | URL base da plataforma — usada nas Tabs e no manifesto | `https://app.wedotalent.cc` |

### Opcionais — Calendar / Graph

| Variável | Descrição |
|---|---|
| `AZURE_CLIENT_SECRET` | Secret para Calendar API (delegated permission) |
| `MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI` | Deve bater com o redirect registrado no Azure |
| `MICROSOFT_CALENDAR_DEFAULT_TIMEZONE` | Padrão: `America/Sao_Paulo` |
| `ENABLE_MICROSOFT_GRAPH` | Padrão: `true`. Setar `false` para desabilitar Graph. |

### Opcionais — manifesto e proatividade

| Variável | Descrição |
|---|---|
| `TEAMS_APP_ID` | UUID do app no manifesto do Teams. Auto-gerado se não configurado — **atenção**: muda a cada restart se não fixado, o que invalida o app instalado |
| `TEAMS_BOT_APP_ID` | Alias de `MICROSOFT_APP_ID` usado no manifesto |
| `TEAMS_APP_TENANT_ID` | Tenant ID do bot registration (se diferente do SSO) |
| `TEAMS_WEBHOOK_URL` | URL do webhook de saída opcional |
| `APP_ENV` | `production` ativa validação obrigatória do `TEAMS_WEBHOOK_SECRET` |

> **Atenção `TEAMS_APP_ID`:** fixe um UUID estático em produção. Se deixar auto-gerar, o app instalado no Teams vai "quebrar" a cada deploy porque o ID muda.

---

## 2. Banco de dados — Migrations

A tabela `teams_conversations` é criada pela Migration 097. **O deploy falha silenciosamente se não rodar antes.**

```bash
# No ambiente de deploy, antes de subir o servidor:
alembic upgrade head

# Para verificar se a tabela existe:
python -c "
from sqlalchemy import inspect
from app.database import engine
print('teams_conversations' in inspect(engine).get_table_names())
"
```

### Tabelas criadas pelo teams domain

| Tabela | Migration | Descrição |
|---|---|---|
| `teams_conversations` | 097 | Refs de conversa 1:1 e grupos/canais |

### Schema de `teams_conversations`

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | UUID PK | |
| `conversation_id` | VARCHAR UNIQUE | `19:xxx@thread.v2` |
| `service_url` | VARCHAR | URL para proactive messaging |
| `tenant_id` | VARCHAR | Azure AD tenant — isolamento multi-tenant |
| `channel_id` | VARCHAR | Sempre `msteams` |
| `user_id` | VARCHAR | `aad:<object-id>` em 1:1; `channel:<team-id>` em grupo (W9.1) |
| `user_name` | VARCHAR | Nome de exibição |
| `user_aad_object_id` | VARCHAR | ID do usuário no AAD (do OBO flow) |
| `conversation_reference` | JSONB | Activity completo para re-envio proativo |
| `company_id` | UUID FK | Populado na primeira mensagem via lookup de User |
| `last_message_at` | TIMESTAMP | |

---

## 3. Fluxo de primeiro uso / company_id

**Este é o failure mode mais comum num deploy fresh.**

### O que acontece na primeira mensagem de um usuário novo

```
1. Usuário manda mensagem no Teams
2. Webhook recebe → _store_conversation_reference() cria row em teams_conversations
   → tenta resolver company_id via User.email ou user_aad_object_id
3. Se o usuário NÃO tem conta na plataforma WeDOTalent:
   → company_id = None no teams_conversations
   → Orquestrador roda sem contexto de tenant
   → LIA responde como se fosse usuário anônimo (sem acesso aos dados da empresa)
4. Se o usuário TEM conta (email bate com AAD):
   → company_id é populado automaticamente
   → LIA tem acesso pleno ao contexto da empresa
```

### Como provisionar um novo cliente

```
1. Criar a empresa na plataforma WeDOTalent (Admin Panel)
2. Criar o(s) usuário(s) recrutadores com o email corporativo Microsoft deles
3. Instalar o app no Teams do cliente (ver Seção 8)
4. Usuário manda a primeira mensagem → company_id é resolvido automaticamente
```

### Como diagnosticar company_id = None nos logs

```
# Sinal no log (nível WARNING):
[TeamsOrchestratorBridge] could not resolve company_id for teams_user=<id>
  (row_found=True, aad_object_id=None)

# Causa mais comum: usuário Teams não tem conta na plataforma com o mesmo email.
# Fix: criar o usuário na plataforma com o email corporativo Microsoft correto.
```

---

## 4. Azure AD App Registration — Passo a Passo

### 4.1 Bot Registration

1. Azure Portal → **App Registrations** → New Registration
2. Nome: `WeDOTalent LIA Bot`
3. Supported account types: `Accounts in any organizational directory` (multi-tenant)
4. Redirect URI: não precisa para o bot
5. Após criar:
   - Copie **Application (client) ID** → `MICROSOFT_APP_ID`
   - Certificates & Secrets → New client secret → copie o **Value** → `MICROSOFT_APP_PASSWORD`
6. Azure Bot Services → Create → aponte o Messaging Endpoint para:
   `https://{platform-domain}/api/v1/teams/webhook`

### 4.2 SSO App Registration (Tab auth)

1. New Registration (pode ser o mesmo app ou separado)
2. Redirect URIs: `https://{platform-domain}/api/v1/teams/auth/callback`
3. Expose an API:
   - Application ID URI: `api://{platform-domain}/{AZURE_CLIENT_ID}`
   - Add scope: `access_as_user` (Admin + User consent)
   - Authorized client applications: adicione os dois IDs do cliente Teams:
     - `1fec8e78-bce4-4aaf-ab1b-5451cc387264` (Teams desktop/mobile)
     - `5e3ce6c0-2b1f-4285-8d4b-75ee78787346` (Teams web)
4. API Permissions: `User.Read`, `openid`, `profile`, `email`
5. Copie o client ID → `AZURE_CLIENT_ID`; copie o tenant ID → `AZURE_TENANT_ID`

### 4.3 Calendar Permissions (agendamento de entrevistas)

1. No app SSO (ou app daemon separado):
2. API Permissions → Add `Calendars.ReadWrite` (Delegated) + `offline_access`
3. Novo client secret → `AZURE_CLIENT_SECRET`
4. Configure `MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI` no Azure portal

---

## 5. Como adicionar o bot ao Teams

### Opção A — Sideloading (para testes, dev, staging)

Permite instalar o app para si mesmo ou para seu tenant sem aprovação do Admin.

```bash
# 1. Gere o ZIP do app (requer as env vars configuradas)
curl https://{platform-domain}/api/v1/teams/manifest-zip -o wedo-teams.zip

# Ou: inspecione o manifesto antes de baixar
curl https://{platform-domain}/api/v1/teams/manifest | python -m json.tool
```

```
2. No Teams Desktop ou Web:
   → Clique em "Apps" (ícone na barra lateral)
   → "Manage your apps" (parte inferior)
   → "Upload an app" → "Upload a custom app"
   → Selecione o wedo-teams.zip
   → "Add" → o bot aparece em Chats

3. Para adicionar a um canal/grupo:
   → No canal → "+" (Add a tab) → "More apps"
   → Busque "WeDO" na lista de apps instalados
```

> **Quando usar:** desenvolvimento local, staging, demonstrações para o cliente antes da aprovação do Admin.

### Opção B — Org-wide via Teams Admin Center (para clientes em produção)

Esta opção requer permissão de Teams Administrator no tenant do cliente.

```
1. Acesse: https://admin.teams.microsoft.com
   (O admin do tenant do cliente precisa fazer isso, não vocês)

2. Teams apps → Manage apps → Upload new app → selecione wedo-teams.zip

3. Após upload, o app fica em "Custom apps" com status "Blocked" por padrão.
   → Clique no app → "Allow" para liberar

4. Para distribuir automaticamente para todos:
   → Teams apps → Setup policies → Global (Org-wide default)
   → "Add apps" → busque "WeDO" → Add
   → O app aparece fixado para todos os usuários do tenant

5. Para distribuir apenas para um grupo:
   → Crie uma nova Setup Policy, adicione o WeDO, aplique ao grupo de recrutadores
```

> **Importante:** cada cliente tem seu próprio tenant Azure. O processo acima precisa ser feito pelo **Teams Administrator do cliente**, não pela WeDOTalent. Vocês entregam o ZIP e o guia; o admin do cliente executa.

### Opção C — Microsoft AppSource (distribição pública futura)

Para distribuição sem precisar de sideloading em cada cliente, o app precisa passar pela validação do AppSource. Não está no escopo atual — documentado aqui apenas para roadmap futuro.

---

## 6. Desenvolvimento local com devtunnel

O Bot Framework requer uma URL pública para entregar webhooks. Em dev local, use o **devtunnel** (ferramenta oficial Microsoft, gratuita):

```bash
# Instalar devtunnel (uma vez)
# macOS
brew install microsoft/devtunnel/devtunnel

# Windows
winget install Microsoft.devtunnel

# Linux
curl -sL https://aka.ms/DevTunnelCliInstall | bash

# 1. Login (conta Microsoft pessoal ou corporativa)
devtunnel user login

# 2. Criar tunnel persistente (o ID não muda entre restarts)
devtunnel create --allow-anonymous

# 3. Hospedar a porta do servidor local
devtunnel host -p 8000
# Saída: https://abc123-8000.brs.devtunnels.ms → sua URL pública

# 4. Configure no Azure Bot Service:
#    Messaging endpoint: https://abc123-8000.brs.devtunnels.ms/api/v1/teams/webhook

# 5. Configure o env var:
WEDOTALENT_PLATFORM_URL=https://abc123-8000.brs.devtunnels.ms
```

> **Alternativa:** `ngrok http 8000` também funciona, mas o URL muda a cada restart no plano gratuito (exige reconfigurar o Azure Bot Service a cada vez). O devtunnel com tunnel persistente resolve isso.

### Testando sem Teams real (Bot Framework Emulator)

Para testar o webhook localmente sem instalar o app no Teams:

```bash
# Download: https://github.com/microsoft/BotFramework-Emulator/releases

# No emulator:
# 1. "Open Bot" → Bot URL: http://localhost:8000/api/v1/teams/webhook
# 2. Microsoft App ID: <MICROSOFT_APP_ID>
# 3. Microsoft App Password: <MICROSOFT_APP_PASSWORD>

# Limitação: o emulator não simula Adaptive Cards nem SSO.
# Para testar Cards, use o sideloading (Opção A acima).
```

---

## 7. Slash Commands — comportamento real

O manifesto registra comandos como `/buscar`, `/triagem`, `/pipeline` etc. Isso faz o Teams mostrar **sugestões visuais** quando o usuário digita `/`.

**Importante: esses comandos NÃO têm routing diferente no backend.** Quando o usuário manda `/buscar sênior Python`, o webhook recebe o texto `"/buscar sênior Python"` e passa diretamente para o orquestrador LIA — igual a qualquer mensagem de texto. A LIA entende o contexto pelo texto, não pelo prefixo.

```python
# O que chega no webhook:
activity["text"] = "/buscar sênior Python"

# O que o bridge faz:
await self.process_message(activity, db=db)
# → orquestrador recebe "/buscar sênior Python" como mensagem normal
```

Para adicionar um novo comando:
1. Adicione ao dict `TEAMS_SLASH_COMMANDS` em `teams_simple.py:24` (atualiza o manifesto)
2. Não precisa de handler novo — a LIA lida pelo texto

---

## 8. Arquitetura do fluxo

```
Teams User
    │ envia mensagem / anexo
    ▼
Bot Framework Service (Microsoft hospedado)
    │ POST /api/v1/teams/webhook
    │ JWT: validate_token(MICROSOFT_APP_ID)
    ▼
teams.py webhook handler
    ├── type="message" + texto → TeamsOrchestratorBridge.process_message()
    ├── type="message" + anexo → dispatch por MIME type:
    │     application/pdf    → process_cv_attachment()       [extrai CV]
    │     image/*            → process_image_attachment()    [Gemini Vision]
    │     audio/* video/*   → process_voice_attachment()    [Gemini STT → texto]
    │     text/plain csv     → process_general_document()   [extrai texto → orquestrador]
    │     .docx .xlsx etc    → process_general_document()   [redireciona para web]
    └── type="conversationUpdate" (bot adicionado ao grupo) → _store_channel_conversation_reference()

TeamsOrchestratorBridge.process_message()
    │ resolve company_id (via TeamsConversation.company_id → User lookup)
    │ W7.2: PromptInjectionGuard — bloqueia injeção de prompt
    ▼
LIA Orchestrator (MainOrchestrator)
    │ CascadedRouter: memory → redis → vector → fast → LLM (W7.1: PII strip) → autonomous
    ▼
Domain Agent (recruiter_assistant, vacancy_manager, etc.)
    ▼
simple_teams_bot.send_message() / send_adaptive_card()
    ▼
Teams User recebe resposta
```

---

## 9. Serviço canônico: simple_teams_bot

**Sempre use** `simple_teams_bot` de `app/domains/communication/services/teams_simple.py`:

```python
from app.domains.communication.services.teams_simple import simple_teams_bot

await simple_teams_bot.send_message(service_url, conversation_id, text)
await simple_teams_bot.send_adaptive_card(service_url, conversation_id, card_payload)
token = await simple_teams_bot.get_access_token()  # para download de anexos
```

**Paths legados — não use em código novo:**
- `app/domains/communication/services/teams_bot.py`
- `app/domains/communication/services/teams_service.py`
- `libs/messaging/lia_messaging/teams.py`

> **Nota:** `WeeklyDigestService` usa internamente `TeamsService` para envio do digest. Isso é um resíduo que deve ser migrado para `simple_teams_bot` numa próxima sprint, mas não quebra nada agora. Não confunda com código novo — em novo código, sempre use `simple_teams_bot`.

---

## 10. Troubleshooting

| Sintoma | Causa provável | Fix |
|---|---|---|
| `403 Forbidden` no POST /webhook | Validação de token falhou | Confira `MICROSOFT_APP_ID` no Azure Bot Service e no env var |
| `403 Teams Bot not configured` | `MICROSOFT_APP_ID` ou `MICROSOFT_APP_PASSWORD` não setados | Adicionar env vars |
| Bot recebe webhook mas não responde | `company_id = None` — usuário sem conta na plataforma | Criar usuário na plataforma com email Microsoft correto; ver Seção 3 |
| `could not resolve company_id` nos logs | Primeira mensagem de usuário sem conta | Provisionar usuário; ver Seção 3 |
| "Unknown table teams_conversations" na startup | Migration 097 não foi rodada | `alembic upgrade head` antes de subir |
| `TEAMS_APP_ID` muda a cada deploy | Variável não fixada | Defina `TEAMS_APP_ID=<uuid-fixo>` em produção |
| Tab mostra tela em branco / 404 | `WEDOTALENT_PLATFORM_URL` não configurado | Setar a URL base correta da plataforma |
| Tab mostra "Error getting token" (SSO) | OBO exchange falhou | Confira `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`; verifique scope `access_as_user` exposto |
| Calendar scheduling falha | Permissão Graph ausente | `Calendars.ReadWrite` delegated + usuário consentiu |
| Imagem retorna apenas tamanho, sem descrição | Gemini Vision falhou | Confira `AI_INTEGRATIONS_GEMINI_API_KEY`; fallback de tamanho é comportamento esperado |
| Áudio retorna "não disponível" | Código antigo (antes do W9.2) | Confirme que o branch `feat/orch-migration-sprint-I` foi deployado |
| Daily digest não envia de manhã | Scheduler não iniciou ou migration não rodou | Verifique logs de `[AutomationScheduler] Running daily platform digest` |
| Sideloading falha com "App ID already exists" | `TEAMS_APP_ID` colide com app já instalado | Gere um novo UUID e reinstale |

---

## 11. Smoke tests

```bash
# Testes unitários + integração (sempre seguros, sem dependências externas)
pytest tests/integration/test_teams_*.py --no-cov -v

# Smoke E2E (requer ambiente Teams real)
export TEAMS_SMOKE_TEST=1
export PLATFORM_BASE_URL=https://staging.wedotalent.cc
export TEAMS_SMOKE_CONVERSATION_ID=<id-real-de-conversa>
pytest tests/smoke/test_teams_e2e_smoke.py -v -s
```
