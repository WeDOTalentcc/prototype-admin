# Microsoft Integration - Guia Completo

**Última Atualização:** 30 Janeiro 2026

## Visão Geral

Este guia consolida todas as integrações Microsoft necessárias para a Plataforma LIA:

- **Azure Bot Service** - Bot para comunicação via Microsoft Teams
- **Microsoft Graph API** - Acesso ao calendário Outlook para agendamento
- **Teams Bot** - Comandos e interação direta no Teams

---

## 1. Visão Geral da Integração Microsoft

### Componentes da Integração

| Componente | Função | Status |
|------------|--------|--------|
| Azure Bot | Canal de comunicação Teams ↔ Backend LIA | 🔴 Configurar |
| Microsoft App Registration | Credenciais OAuth | 🔴 Configurar |
| Microsoft Graph API | Calendário Outlook | 🔴 Configurar |
| Teams Channel | Ativar integração com Teams | 🔴 Configurar |

### Pré-requisitos

- Conta Microsoft Azure (https://portal.azure.com)
- Azure Active Directory tenant
- Admin access to Azure Portal
- Microsoft 365 subscription with Exchange Online
- Permissões para criar aplicações no Azure AD

### Credenciais Necessárias

Ao final da configuração, você terá:

| Secret | Descrição |
|--------|-----------|
| `MICROSOFT_APP_ID` | Application (client) ID do bot |
| `MICROSOFT_APP_PASSWORD` | Client Secret do bot |
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `AZURE_CLIENT_ID` | Client ID para Graph API |
| `AZURE_CLIENT_SECRET` | Client Secret para Graph API |

---

## 2. Azure Bot Setup

### 2.1 Publicar o Backend LIA no Replit

**IMPORTANTE**: O Azure Bot precisa de uma URL pública para enviar mensagens.

1. No Replit, clique no botão **"Deploy"** (ou "Publish")
2. Configure o deployment:
   - **Deployment Target**: `vm` (sempre rodando)
   - **Run Command**: Já configurado automaticamente
3. Clique em **"Deploy"**
4. Anote a **URL pública** do deploy (ex: `https://seu-projeto.repl.co`)

Sua **Messaging Endpoint URL** será:
```
https://SEU-PROJETO.repl.co/api/v1/teams/messages
```

### 2.2 Criar Azure Bot

1. Acesse: https://portal.azure.com
2. No menu de busca (topo), digite **"Azure Bot"**
3. Clique em **"+ Create"** (Criar)
4. Preencha os campos:

| Campo | Valor |
|-------|-------|
| **Subscription** | Sua assinatura Azure |
| **Resource Group** | Criar novo: `lia-bot-resources` |
| **Bot Handle** | `lia-wedotalent` (nome único global) |
| **Pricing Tier** | **F0 (Free)** - 10.000 mensagens/mês |
| **Type of App** | **Multi Tenant** |
| **Creation type** | **Create new Microsoft App ID** |
| **Data residency** | Brazil South (ou região mais próxima) |

5. Clique em **"Review + create"** e depois **"Create"**
6. Aguarde ~2 minutos para o deployment
7. Clique em **"Go to resource"**

### 2.3 Configurar Credenciais

#### Copiar Microsoft App ID
1. Na página do Azure Bot, procure por **"Microsoft App ID"**
2. Copie o valor (formato: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)

#### Criar Client Secret
1. No menu lateral, clique em **"Configuration"**
2. Ao lado de "Microsoft App ID", clique em **"Manage"**
3. Na página do App Registration, vá em **"Certificates & secrets"**
4. Na aba **"Client secrets"**, clique em **"+ New client secret"**
5. Preencha:
   - **Description**: `LIA Teams Bot Secret`
   - **Expires**: **12 months** (recomendado)
6. Clique em **"Add"**
7. **⚠️ MUITO IMPORTANTE**: Copie o **Value** IMEDIATAMENTE
   - Este valor só aparece uma vez!

#### Configurar Messaging Endpoint
1. Volte para a página do **Azure Bot**
2. No menu lateral, clique em **"Configuration"**
3. No campo **"Messaging endpoint"**, cole:
   ```
   https://SEU-PROJETO.repl.co/api/v1/teams/messages
   ```
4. Clique em **"Apply"**

### 2.4 Ativar Canal do Microsoft Teams

1. Na página do Azure Bot, menu lateral, clique em **"Channels"**
2. Clique no ícone do **Microsoft Teams**
3. Confirme que **"Enable this bot on Microsoft Teams"** está marcado
4. Clique em **"Apply"**
5. Clique em **"Agree"** nos termos de serviço

### 2.5 Configurar Secrets no Replit

1. No Replit, clique na aba **"Secrets"**
2. Adicione as seguintes secrets:

```bash
MICROSOFT_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_APP_PASSWORD=aBc123~DeF456.GhI789-JkL012MnO345
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Para obter o Tenant ID:
1. No Azure Portal, vá em **Azure Active Directory**
2. Em **Overview**, copie **Tenant ID**

---

## 3. Microsoft Graph API (Calendar)

### 3.1 Criar Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in the details:
   - **Name**: `LIA Calendar Integration`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave blank
5. Click **Register**

### 3.2 Configurar API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** → **Microsoft Graph** → **Application permissions**
3. Add the following permissions:
   - `Calendars.ReadWrite` - Read and write calendars in all mailboxes
   - `User.Read.All` - Read all users' full profiles
   - `offline_access` - Maintain access to data
4. Click **Grant admin consent** for your organization

### 3.3 Criar Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description: `LIA Backend Secret`
4. Expiration: 6-12 months (recommended)
5. Click **Add**
6. **IMPORTANT**: Copy the secret value immediately

### 3.4 Configurar Environment Variables

Add to Replit Secrets:

```bash
AZURE_CLIENT_ID=<your-application-client-id>
AZURE_CLIENT_SECRET=<your-client-secret-value>
AZURE_TENANT_ID=<your-tenant-id>
```

**Where to find these values:**
- `AZURE_CLIENT_ID`: App registration **Overview** page → Application (client) ID
- `AZURE_CLIENT_SECRET`: The secret value you copied
- `AZURE_TENANT_ID`: App registration **Overview** page → Directory (tenant) ID

### 3.5 Testar a Integração

1. Restart the LIA backend
2. Check the startup logs for:
   ```
   ✅ Microsoft Graph API configured (Outlook Calendar access enabled)
   ```

3. Test the calendar health endpoint:
   ```bash
   curl http://localhost:8000/api/v1/calendar/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "calendar-api",
     "graph_configured": true
   }
   ```

### 3.6 Operações de Calendário

#### Check Availability
```bash
curl -X POST http://localhost:8000/api/v1/calendar/availability \
  -H "Content-Type: application/json" \
  -d '{
    "interviewer_email": "interviewer@company.com",
    "date": "2025-11-25T09:00:00Z",
    "duration_minutes": 60
  }'
```

#### Find Meeting Times
```bash
curl -X POST http://localhost:8000/api/v1/calendar/find-meeting-times \
  -H "Content-Type: application/json" \
  -d '{
    "organizer_email": "hr@company.com",
    "interviewer_emails": ["interviewer1@company.com", "interviewer2@company.com"],
    "candidate_email": "candidate@example.com",
    "duration_minutes": 60,
    "preferred_days": ["Mon", "Tue", "Wed"]
  }'
```

#### Schedule Interview
```bash
curl -X POST http://localhost:8000/api/v1/calendar/schedule-interview \
  -H "Content-Type: application/json" \
  -d '{
    "organizer_email": "hr@company.com",
    "candidate_name": "João Silva",
    "candidate_email": "joao.silva@example.com",
    "interviewer_emails": ["interviewer@company.com"],
    "position": "Desenvolvedor Python Sênior",
    "start_time": "2025-11-25T14:00:00Z",
    "duration_minutes": 60,
    "as_teams_meeting": true,
    "notes": "Primeira entrevista técnica"
  }'
```

### Features do Calendar

#### ✅ Calendar Operations
- **Check Availability**: Find all free slots in business hours (9am-6pm) with 30-min increments
- **Find Meeting Times**: Use Microsoft Graph's intelligent scheduling
- **Schedule Interview**: Create calendar events with Teams meeting links
- **Cancel Interview**: Cancel meetings with notification to all attendees
- **Reschedule Interview**: Update existing meeting times

#### ✅ Timezone Support
- Comprehensive Windows to IANA timezone mapping (~50 common timezones)
- All datetimes converted to UTC internally
- Timezone-aware datetime operations

#### ✅ Security
- Application permissions using client credentials flow
- Token caching with automatic refresh
- Secure secret management via Replit Secrets

### API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/calendar/health` | GET | Health check |
| `/api/v1/calendar/availability` | POST | Check interviewer availability |
| `/api/v1/calendar/find-meeting-times` | POST | Find best meeting times |
| `/api/v1/calendar/schedule-interview` | POST | Schedule interview |
| `/api/v1/calendar/cancel-interview` | POST | Cancel interview |
| `/api/v1/calendar/reschedule-interview` | POST | Reschedule interview |

---

## 4. Teams Bot (Manifest e Comandos)

### 4.0 Setup de Produção (ai.wedotalent.cc) — Checklist Rápido

**App Registration:** `LIA-Teams-Bot` (`246eb1e7-a437-4cb2-a231-0325b567be5f`)

**Variáveis de ambiente obrigatórias no Cloud Run (backend):**

```bash
MICROSOFT_APP_ID=246eb1e7-a437-4cb2-a231-0325b567be5f
MICROSOFT_APP_PASSWORD=<client-secret-do-bot>
TEAMS_APP_TENANT_ID=bd25f438-71ab-4f63-a88f-abc8da37a1f6   # tenant do LIA-Teams-Bot
WEDOTALENT_PLATFORM_URL=https://ai.wedotalent.cc
```

**Messaging Endpoint no Azure Bot:**
```
https://ai.wedotalent.cc/api/v1/teams/messages
```

**Verificar saúde do bot (deve retornar "healthy"):**
```bash
curl https://ai.wedotalent.cc/api/v1/teams/health
# Resposta esperada: {"status":"healthy","service":"teams-bot","bot_configured":true}
```

**Ícones do app (acessíveis publicamente):**
```
https://ai.wedotalent.cc/teams-icons/wedo-color.png
https://ai.wedotalent.cc/teams-icons/wedo-outline.png
```

---

### 4.1 Instalar Bot no Teams

#### Método Rápido: Download ZIP Completo (Recomendado)

O backend gera automaticamente um pacote ZIP pronto para upload:

```
https://ai.wedotalent.cc/api/v1/teams/manifest-zip
```

Este ZIP contém:
- `manifest.json` — gerado dinamicamente com o bot ID, domínio e comandos corretos
- `wedo-color.png` — ícone colorido 192x192
- `wedo-outline.png` — ícone de contorno 32x32

**Como fazer upload no Teams Admin Center:**

1. Acesse: https://admin.teams.microsoft.com
2. No menu esquerdo: **Teams apps** → **Manage apps**
3. Clique em **"Upload new app"** (canto superior direito)
4. Selecione **"Upload an app"** → faça upload do arquivo `wedo-teams-app.zip`
5. O app aparecerá com status **"Custom app"**
6. Clique no app → **"Publish"** para disponibilizá-lo para a organização

**Alternativa: Sideload para testes individuais:**

1. No Microsoft Teams, clique em **"Apps"** (barra lateral esquerda)
2. Clique em **"Manage your apps"** → **"Upload an app"**
3. Selecione **"Upload a custom app"**
4. Faça upload do ZIP baixado
5. O bot WeDO aparecerá para instalação

#### Método Alternativo: Manifest JSON + Ícones Manuais

1. Baixe o manifest: `https://ai.wedotalent.cc/api/v1/teams/manifest`
2. Baixe os ícones de `https://ai.wedotalent.cc/teams-icons/`
3. Crie um ZIP com os 3 arquivos: `manifest.json`, `wedo-color.png`, `wedo-outline.png`
4. Faça upload conforme os passos acima

#### Método Legado: Direct Link do Azure Bot
1. No Azure Bot (`LIA-Teams-Bot`), vá em **"Channels"** → **Microsoft Teams**
2. Copie o link em **"Add to Microsoft Teams"**
3. Abra o link em seu navegador
4. Teams abrirá e solicitará instalação do bot

### 4.2 Teams App Manifest (manifest.json)

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "SEU_MICROSOFT_APP_ID",
  "packageName": "com.wedotalent.lia",
  "developer": {
    "name": "WedoTalent",
    "websiteUrl": "https://wedotalent.com",
    "privacyUrl": "https://wedotalent.com/privacy",
    "termsOfUseUrl": "https://wedotalent.com/terms"
  },
  "name": {
    "short": "LIA",
    "full": "LIA - Learning Intelligence Assistant"
  },
  "description": {
    "short": "Assistente de recrutamento inteligente",
    "full": "LIA é sua assistente de recrutamento que ajuda a criar vagas, buscar candidatos, agendar entrevistas e organizar sua agenda de forma proativa."
  },
  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },
  "accentColor": "#60BED1",
  "bots": [
    {
      "botId": "SEU_MICROSOFT_APP_ID",
      "scopes": ["personal", "team", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["personal", "team", "groupchat"],
          "commands": [
            {
              "title": "Criar Vaga",
              "description": "Iniciar criação de uma nova vaga"
            },
            {
              "title": "Buscar Candidatos",
              "description": "Buscar candidatos para uma vaga"
            },
            {
              "title": "Agendar Entrevista",
              "description": "Agendar entrevista com candidato"
            },
            {
              "title": "Minha Agenda",
              "description": "Ver sua agenda de entrevistas"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["SEU_DOMINIO_REPLIT.replit.app"]
}
```

**Notas:**
- Substitua `SEU_MICROSOFT_APP_ID` pelo App ID
- Substitua `SEU_DOMINIO_REPLIT` pelo domínio do Repl
- Crie 2 ícones:
  - `outline.png`: 32x32px, transparente
  - `color.png`: 192x192px, fundo colorido

**Empacotar App:**
1. Coloque `manifest.json`, `outline.png` e `color.png` em uma pasta
2. Crie um arquivo ZIP com esses 3 arquivos
3. Faça upload no App Studio

### 4.3 Testar o Bot

#### Teste 1: Enviar Mensagem
1. No Teams, abra o chat com a LIA
2. Envie: **"Olá LIA!"**
3. LIA deve responder com mensagem de boas-vindas

#### Teste 2: Verificar Logs
No Replit, veja os logs do backend:
```bash
INFO: Received Teams activity: message
INFO: Received message from João Silva: Olá LIA!
```

#### Teste 3: Health Check
```
https://SEU_DOMINIO_REPLIT/api/v1/teams/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "service": "teams-bot",
  "bot_configured": true
}
```

#### Teste 4: Comandos
Envie mensagens para a LIA:

```
Olá LIA!
```

```
Preciso criar uma vaga para Desenvolvedor Python Sênior
```

```
Agenda uma entrevista com João Silva para segunda-feira
```

---

## 5. Troubleshooting Unificado

### Azure Bot

#### Erro: "Bot not found"
- **Causa**: Microsoft App ID incorreto
- **Solução**: Verifique se copiou o App ID corretamente

#### Erro: "Unauthorized" (401)
- **Causa**: Client Secret incorreto ou expirado
- **Solução**: Crie um novo Client Secret e atualize no Replit

#### Bot não responde
- **Causa**: Messaging endpoint incorreto ou backend não está rodando
- **Solução**: 
  1. Verifique se o backend está publicado (deployed)
  2. Confirme que a URL do messaging endpoint está correta
  3. Teste: `curl https://SEU-PROJETO.repl.co/health`

#### Erro: "Service Unavailable" (503)
- **Causa**: Backend não está rodando ou secrets não configuradas
- **Solução**: Verifique os logs e confirme as secrets

### Microsoft Graph API

#### Error: 503 Service Unavailable
- **Cause**: Azure credentials not configured
- **Solution**: Complete the Graph API setup steps

#### Error: 401 Unauthorized
- **Cause**: Invalid client secret or expired token
- **Solution**: Generate new client secret in Azure Portal

#### Error: 403 Forbidden
- **Cause**: Missing API permissions or admin consent not granted
- **Solution**: Re-check permissions, ensure admin consent is granted

#### Timezone warnings in logs
- **Cause**: Unknown Windows timezone name
- **Solution**: Add mapping to `app/utils/datetime_helpers.py`:
  ```python
  WINDOWS_TO_IANA_TIMEZONES = {
      "XYZ Standard Time": "Region/City",
  }
  ```

### Teams Bot

#### Erro: "Bot not responding"
1. Messaging endpoint incorreto
   - Deve terminar com `/api/v1/teams/messages`
   - HTTPS é obrigatório
2. Secrets não configurados
3. Backend não está rodando

#### Erro: "404 Not Found"
1. Verifique se as rotas do Teams foram registradas no `main.py`
2. Reinicie o backend
3. Teste: `curl https://SEU_DOMINIO/api/v1/teams/health`

---

## 6. Referências

### Azure & Bot Framework
- [Azure Bot Documentation](https://learn.microsoft.com/azure/bot-service/)
- [Bot Framework SDK](https://learn.microsoft.com/azure/bot-service/bot-service-overview)
- [Bot Framework SDK for Python](https://github.com/microsoft/botbuilder-python)

### Microsoft Graph
- [Microsoft Graph Documentation](https://learn.microsoft.com/graph/)
- [Calendar API Reference](https://learn.microsoft.com/graph/api/resources/calendar)

### Teams
- [Teams Bot Messaging](https://learn.microsoft.com/microsoftteams/platform/bots/how-to/conversations/conversation-basics)
- [Teams Bot Development](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)
- [Adaptive Cards Designer](https://adaptivecards.io/designer/)

### Security Best Practices
1. **Rotate client secrets** every 6-12 months
2. **Use separate app registrations** for dev/staging/production
3. **Monitor API permissions** - only grant what's necessary
4. **Review audit logs** regularly in Azure Portal
5. **Never commit secrets** to version control

---

## Próximos Passos

Depois de configurar todas as integrações:

1. **Testar conversas básicas** - LIA responde perguntas e processa intenções
2. **Implementar mensagens proativas** - Notificações de entrevistas agendadas
3. **Adicionar aprovações interativas** - Botões de aprovar/rejeitar
4. **Integrar com frontend Next.js** - Dashboard web + Teams bot funcionando juntos
5. **Implementar reminders** - Lembretes automáticos antes de entrevistas

---

**Mantido por**: Replit Agent  
**Última atualização**: Janeiro 2026
