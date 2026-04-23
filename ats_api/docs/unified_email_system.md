# Sistema Unificado de Email — Guia para o Frontend

## Resumo da Mudança

O backend agora possui um **sistema unificado de disparo de email** para candidatos. Antes, existiam 3 fluxos separados com templates diferentes. Agora, tudo passa por um único serviço (`UnifiedInviteService`) que renderiza um email bonito com **N botões dinâmicos** baseado nos canais configurados na Evaluation.

### Campo Novo: `notification_channels` (Evaluation)

A Evaluation agora possui um campo `notification_channels` (array de strings) que define **quais opções o candidato terá no email**. Isso substitui a lógica antiga que dependia apenas do `chatbot_channel` (enum: `internal` / `whatsapp`).

**Valores válidos:** `"internal"`, `"voice"`, `"phone"`, `"whatsapp"`

**Exemplos:**

```json
// Só chat
{ "notification_channels": ["internal"] }

// Chat + entrevista por voz (2 botões no email)
{ "notification_channels": ["internal", "voice"] }

// Só entrevista por ligação
{ "notification_channels": ["phone"] }

// Chat + voz + ligação (3 botões no email)
{ "notification_channels": ["internal", "voice", "phone"] }

// WhatsApp (envia via WhatsApp, sem email)
{ "notification_channels": ["whatsapp"] }
```

**Retrocompatibilidade:** Se `notification_channels` estiver vazio/null, o backend usa o `chatbot_channel` como fallback (comportamento antigo).

---

## O Que Mudou

### ANTES

| Cenário | Como funcionava | Template |
|---------|----------------|----------|
| **Avaliação por Chat** | `CreateCollectionJob` renderizava email a partir de `chatbot_channel: internal` | `invitation.html.erb` — botão fixo "Iniciar Conversa" + "Não Tenho Interesse" |
| **Entrevista por Voz** | Frontend chamava `POST /v1/users/email_templates/send` com body de texto puro | Texto puro (sem template HTML bonito) |
| **Entrevista por Ligação** | Igual ao de voz — frontend mandava texto puro via `email_templates/send` | Texto puro (sem template HTML bonito) |
| **Nenhum controle** | Não existia forma de definir quais canais o candidato teria no email | - |

### DEPOIS

| Cenário | Como funciona agora | Template |
|---------|-------------------|----------|
| **`notification_channels: ["internal"]`** | Email com 1 botão: "Iniciar Conversa por Chat" | `unified_invitation.html.erb` |
| **`notification_channels: ["voice"]`** | Email com 1 botão: "Entrevista por Voz" | `unified_invitation.html.erb` |
| **`notification_channels: ["internal", "voice"]`** | Email com 2 botões + seção "Escolha como participar" | `unified_invitation.html.erb` |
| **`notification_channels: ["internal", "voice", "phone"]`** | Email com 3 botões | `unified_invitation.html.erb` |
| **`notification_channels: ["whatsapp"]`** | WhatsApp via Meta API (sem email) | - |

---

## APIs que o Frontend Precisa Usar

### 1. Configurar Canais na Evaluation — `PUT /v1/users/evaluations/:id`

**⚠️ NOVO E IMPORTANTE:** O frontend precisa enviar `notification_channels` ao criar/editar uma Evaluation.

#### Request

```http
PUT /v1/users/evaluations/170
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "evaluation": {
    "notification_channels": ["internal", "voice"]
  }
}
```

#### Valores válidos para `notification_channels`

| Valor | Significado | Botão no Email | URL |
|-------|-------------|---------------|-----|
| `"internal"` | Chat na web | "Iniciar Conversa por Chat" | `/evaluations/{account_uid}/{ec_uid}` |
| `"voice"` | Entrevista por voz (IA) | "Entrevista por Voz" | `/interviews/{account_uid}/{token}` |
| `"phone"` | Entrevista por ligação | "Entrevista por Ligação" | `/interviews/{account_uid}/{token}` |
| `"whatsapp"` | Notificação via WhatsApp | (sem email — dispara WhatsApp) | - |

#### Response (Evaluation serializada)

```json
{
  "data": {
    "id": "170",
    "type": "evaluation",
    "attributes": {
      "name": "Avaliação Inicial",
      "chatbot_channel": "internal",
      "notification_channels": ["internal", "voice"],
      "is_chatbot": true,
      "ai_enabled": true,
      "...": "..."
    }
  }
}
```

#### Combinações típicas

```javascript
// Evaluation só com chat (padrão atual)
await api.put(`/evaluations/${id}`, {
  evaluation: { notification_channels: ['internal'] }
})

// Evaluation com chat + entrevista por voz automática
await api.put(`/evaluations/${id}`, {
  evaluation: { notification_channels: ['internal', 'voice'] }
})

// Evaluation com entrevista por voz apenas
await api.put(`/evaluations/${id}`, {
  evaluation: { notification_channels: ['voice'] }
})

// Evaluation por WhatsApp
await api.put(`/evaluations/${id}`, {
  evaluation: { notification_channels: ['whatsapp'] }
})
```

---

### 2. Disparo de Avaliação — `POST /v1/users/evaluation_candidates/create_collection`

**Sem mudança na chamada.** O backend lê os canais direto do campo `notification_channels` da Evaluation.

#### Request (igual ao antes)

```http
POST /v1/users/evaluation_candidates/create_collection
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "select_all_params": {
    "model": "Apply",
    "where": { "job_id": 7144 },
    "ids": [15473, 15474, 15475]
  },
  "evaluation_candidate": {
    "evaluation_id": 170,
    "job_id": 7144
  }
}
```

#### O que acontece no backend

1. `CreateCollectionJob` é enfileirado no Sidekiq
2. Para cada candidato, cria/encontra `EvaluationCandidate`
3. Lê `evaluation.notification_channels`:
   - `["internal"]` → email com botão "Iniciar Conversa por Chat"
   - `["internal", "voice"]` → email com 2 botões (Chat + Voz)
   - `["whatsapp"]` → dispara WhatsApp (sem email)
   - `[]` ou `null` → fallback para `chatbot_channel` antigo
4. Chama `UnifiedInviteService` que envia email com o template bonito
5. Broadcast de progresso via WebSocket `EvaluationCandidateCollectionChannel`

#### WebSocket — Canal de Progresso

```javascript
cable.subscriptions.create("EvaluationCandidateCollectionChannel", {
  received(data) {
    // data.status: "loading" | "completed" | "error"
    // data.percent: 0-100
    // data.errors: string[]
    // data.sent_evaluation_candidate_ids: number[] (quando completed)
  }
})
```

**Payloads:**

```json
// Progresso
{ "status": "loading", "percent": 33.33, "errors": [] }

// Concluído
{ "status": "completed", "percent": 100, "sent_evaluation_candidate_ids": [832, 833], "errors": [] }

// Erro
{ "status": "error", "percent": 100, "errors": ["Erro ao processar envio de provas: ..."] }
```

---

### 3. Entrevista por Voz/Ligação — `POST /v1/users/interview_sessions`

**⚠️ MUDANÇA IMPORTANTE: O frontend NÃO precisa mais chamar `POST /v1/users/email_templates/send`.** O backend envia o email automaticamente ao criar a InterviewSession.

O backend agora lê os `notification_channels` da Evaluation vinculada e usa todos os canais configurados no email. Se a Evaluation tiver `["internal", "voice"]`, o email terá 2 botões.

#### Request

```http
POST /v1/users/interview_sessions
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "evaluation_id": 170,
  "candidate_id": 17485,
  "job_id": 7144,
  "apply_id": 15473,
  "interview_type": "voice",
  "duration_minutes": 30,
  "language": "pt-BR",
  "channels": ["email"]
}
```

#### Parâmetros

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `evaluation_id` | integer | ✅ | ID da avaliação (que tem `notification_channels` configurado) |
| `candidate_id` | integer | ✅ | ID do candidato |
| `job_id` | integer | ✅ | ID da vaga |
| `apply_id` | integer | ❌ | ID da candidatura |
| `interview_type` | string | ❌ | `"voice"` (padrão), `"video"`, `"phone"` |
| `duration_minutes` | integer | ❌ | Duração em minutos (padrão: 30) |
| `language` | string | ❌ | Idioma (padrão: `"pt-BR"`) |
| `channels` | string[] | ❌ | Canais de envio: `["email"]`, `["whatsapp"]`, `["email", "whatsapp"]` |

> **Nota:** O `channels` aqui define o **meio de envio** (email ou whatsapp). Os **botões dentro do email** vêm do `notification_channels` da Evaluation.

#### O que acontece no backend

1. Cria `InterviewSession` com token único e validade de 7 dias
2. Cria/encontra `EvaluationCandidate` associado
3. Se `channels` incluir `"email"`:
   - Lê `evaluation.notification_channels` → determina quais botões colocar no email
   - Se `notification_channels` está vazio → fallback: botão baseado no `interview_type` (`voice` ou `phone`)
   - Chama `UnifiedInviteService` → email HTML bonito com os botões dinâmicos
4. Se `channels` incluir `"whatsapp"`:
   - Envia template WhatsApp via Meta API + link da entrevista

#### Response (201 Created)

```json
{
  "data": {
    "id": "42",
    "type": "interview_session",
    "attributes": {
      "token": "abc123-unique-token",
      "status": "pending",
      "interview_type": "voice",
      "duration_minutes": 30,
      "language": "pt-BR",
      "expires_at": "2026-03-24T18:00:00Z",
      "public_url": "http://localhost:3000/interviews/{account_uid}/{token}"
    },
    "relationships": {
      "candidate": { "data": { "id": "17485", "type": "candidate" } },
      "job": { "data": { "id": "7144", "type": "job" } },
      "evaluation": { "data": { "id": "170", "type": "evaluation" } }
    }
  }
}
```

#### Erros

```json
{ "errors": ["Evaluation not found"] }
{ "errors": ["Candidate not found"] }
{ "errors": ["Job not found"] }
```

---

### 4. ❌ NÃO USAR MAIS — `POST /v1/users/email_templates/send`

**O frontend NÃO deve mais usar esta rota para enviar emails de entrevista.** O disparo agora é automático via `channels: ["email"]` no `POST /v1/users/interview_sessions`.

A rota `email_templates/send` continua existindo para outros usos (emails manuais, templates customizados), mas **não deve ser usada para convites de entrevista**.

---

## URLs das Páginas do Candidato

O email enviado ao candidato contém botões com URLs que apontam para páginas do frontend:

| Canal | URL Pattern | Exemplo |
|-------|-------------|---------|
| **Chat (internal)** | `{FRONT_URL}/evaluations/{account_uid}/{evaluation_candidate_uid}` | `https://app.wedotalent.cc/evaluations/6b61fa80-xxxx/5961d96d-yyyy` |
| **Voz (voice)** | `{FRONT_URL}/interviews/{account_uid}/{token}` | `https://app.wedotalent.cc/interviews/6b61fa80-xxxx/abc123-token` |
| **Ligação (phone)** | `{FRONT_URL}/interviews/{account_uid}/{token}` | `https://app.wedotalent.cc/interviews/6b61fa80-xxxx/abc123-token` |
| **Declinar** | `{FRONT_URL}/evaluations/{account_uid}/{evaluation_candidate_uid}?action=decline` | `https://app.wedotalent.cc/evaluations/6b61fa80-xxxx/5961d96d-yyyy?action=decline` |

---

## Como o Email Fica

### Email com 1 canal — `notification_channels: ["internal"]`

```
┌─────────────────────────────────────┐
│          Company Name •             │
├─────────────────────────────────────┤
│                                     │
│  OPORTUNIDADE — Company Name        │
│                                     │
│  Olá, [Nome]. Meu nome é [Recruiter]│
│  e faço parte do time de            │
│  recrutamento da [Company].         │
│  Identificamos seu perfil e         │
│  gostaríamos de conversar sobre     │
│  a vaga de [Job Title].             │
│                                     │
│  DETALHES DA VAGA                   │
│  Vaga    │ Job Title                │
│  Empresa │ Company Name             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Iniciar Conversa por Chat   │    │ ← Botão escuro (primário)
│  └─────────────────────────────┘    │
│                                     │
│      Não tenho interesse            │ ← Link de declinar
│                                     │
│  [Recruiter Name]                   │
│  Recrutador(a) · Company Name       │
│                                     │
├─────────────────────────────────────┤
│  WeDO Talent • Privacidade • Termos │
└─────────────────────────────────────┘
```

### Email com 2 canais — `notification_channels: ["internal", "voice"]`

```
┌─────────────────────────────────────┐
│          Company Name •             │
├─────────────────────────────────────┤
│                                     │
│  OPORTUNIDADE — Company Name        │
│                                     │
│  Olá, [Nome]. Meu nome é [Recruiter]│
│  ... (mesma mensagem de intro) ...  │
│                                     │
│  DETALHES DA VAGA                   │
│  Vaga    │ Job Title                │
│  Empresa │ Company Name             │
│                                     │
│  ESCOLHA COMO PARTICIPAR            │ ← Aparece quando há 2+ canais
│  Você pode participar de uma das    │
│  seguintes formas:                  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Iniciar Conversa por Chat   │    │ ← Botão escuro (primário)
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │   Entrevista por Voz        │    │ ← Botão outlined (secundário)
│  └─────────────────────────────┘    │
│                                     │
│      Não tenho interesse            │
│                                     │
│  [Recruiter Name]                   │
│  Recrutador(a) · Company Name       │
│                                     │
├─────────────────────────────────────┤
│  WeDO Talent • Privacidade • Termos │
└─────────────────────────────────────┘
```

### Email com 3 canais — `notification_channels: ["internal", "voice", "phone"]`

```
┌─────────────────────────────────────┐
│          Company Name •             │
├─────────────────────────────────────┤
│  ...                                │
│  ESCOLHA COMO PARTICIPAR            │
│  ┌─────────────────────────────┐    │
│  │ Iniciar Conversa por Chat   │    │ ← Primário
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │   Entrevista por Voz        │    │ ← Secundário
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │  Entrevista por Ligação     │    │ ← Secundário
│  └─────────────────────────────┘    │
│      Não tenho interesse            │
│  ...                                │
└─────────────────────────────────────┘
```

---

## Canais Disponíveis

| Valor | Label no Email | URL Destino | Requer InterviewSession? |
|-------|----------------|-------------|--------------------------|
| `"internal"` | "Iniciar Conversa por Chat" | `/evaluations/{account_uid}/{ec_uid}` | Não |
| `"voice"` | "Entrevista por Voz" | `/interviews/{account_uid}/{token}` | Sim |
| `"phone"` | "Entrevista por Ligação" | `/interviews/{account_uid}/{token}` | Sim |
| `"whatsapp"` | (sem email — WhatsApp) | - | Não |

> **Importante:** Os canais `voice` e `phone` precisam de uma `InterviewSession` para gerar a URL. No fluxo de `create_collection`, se o `notification_channels` tiver `voice` ou `phone` mas não existir `InterviewSession`, esses botões serão omitidos do email (só aparecem os que têm URL válida).

---

## Fluxo Completo — Diagramas

### Configuração + Disparo (create_collection)

```
Frontend                          Backend
   │                                │
   │ 1. Configura Evaluation        │
   ├─PUT /evaluations/170 ─────────►│ Salva notification_channels: ["internal", "voice"]
   │  { notification_channels:      │
   │    ["internal", "voice"] }     │
   │                                │
   │ 2. Dispara avaliação           │
   ├─POST /evaluation_candidates/   │
   │  create_collection             │
   │  { select_all_params,          │
   │    evaluation_candidate }      │
   │────────────────────────────────►│
   │                                ├──► CreateCollectionJob (Sidekiq)
   │                                │      │
   │                                │      ├─ Lê evaluation.notification_channels
   │                                │      │   → [:internal, :voice]
   │                                │      │
   │◄─── WebSocket: loading 33% ───┤      ├─ Cria EvaluationCandidate
   │◄─── WebSocket: loading 66% ───┤      │
   │                                │      ├─ UnifiedInviteService
   │                                │      │    channels: [:internal, :voice]
   │                                │      │    │
   │                                │      │    ├─ Renderiza unified_invitation.html.erb
   │                                │      │    │   com botões: "Chat" + "Voz"
   │                                │      │    ├─ Cria Dispatch + DispatchMessage
   │                                │      │    └─ MsGraphEmailWorker → envia email
   │                                │      │
   │◄── WebSocket: completed 100% ─┤      └─ done
   │    { sent_evaluation_          │
   │      candidate_ids: [...] }    │
```

### Entrevista por Voz/Ligação

```
Frontend                          Backend
   │                                │
   ├─POST /interview_sessions      │
   │  { evaluation_id: 170,        │
   │    candidate_id: 17485,       │
   │    job_id: 7144,              │
   │    interview_type: "voice",   │
   │    channels: ["email"] }      │
   │───────────────────────────────►│
   │                                ├─ InterviewSessions::CreateService
   │                                │    │
   │                                │    ├─ Cria InterviewSession (token, public_url)
   │                                │    ├─ Cria/encontra EvaluationCandidate
   │                                │    └─ Enfileira InviteNotificationJob
   │                                │         │
   │◄── 201 { data: session } ─────┤         ├─ Lê evaluation.notification_channels
   │                                │         │   → [:internal, :voice]
   │                                │         │
   │                                │         ├─ UnifiedInviteService
   │                                │         │    channels: [:internal, :voice]
   │                                │         │    interview_session: session
   │                                │         │    │
   │                                │         │    ├─ Renderiza email com:
   │                                │         │    │   "Chat" → /evaluations/{uid}/{ec_uid}
   │                                │         │    │   "Voz"  → /interviews/{uid}/{token}
   │                                │         │    ├─ Cria Dispatch + DispatchMessage
   │                                │         │    └─ MsGraphEmailWorker → envia email
   │                                │         │
   │                                │         └─ done (async)
```

---

## O Que o Frontend Precisa Mudar

### ⚠️ Mudanças obrigatórias

1. **Formulário de Evaluation** — Adicionar campo `notification_channels` (multiselect/checkboxes):
   
   ```javascript
   // Ao criar/editar uma Evaluation, enviar os canais selecionados:
   await api.post('/evaluations', {
     evaluation: {
       name: 'Avaliação Técnica',
       job_id: 7144,
       is_chatbot: true,
       chatbot_channel: 'internal',
       notification_channels: ['internal', 'voice'],  // ← NOVO
       // ... outros campos
     }
   })
   ```

   **UI sugerida:** Checkboxes ou multiselect com as opções:
   - [ ] Chat na web (`internal`)
   - [ ] Entrevista por Voz (`voice`)
   - [ ] Entrevista por Ligação (`phone`)
   - [ ] WhatsApp (`whatsapp`)

2. **`POST /v1/users/interview_sessions`** — Incluir `channels: ["email"]` no body:

   ```javascript
   // ANTES: Frontend criava session + mandava email separado
   const session = await api.post('/interview_sessions', {
     evaluation_id: 170,
     candidate_id: 17485,
     job_id: 7144,
     interview_type: 'voice'
   })
   await api.post('/email_templates/send', {
     subject: 'Convite para Entrevista',
     content: 'Texto puro...',
     collections: [{ email: 'candidato@email.com' }]
   })

   // DEPOIS: Só criar a session com channels
   const session = await api.post('/interview_sessions', {
     evaluation_id: 170,
     candidate_id: 17485,
     job_id: 7144,
     interview_type: 'voice',
     channels: ['email']  // ← Backend cuida do email bonito
   })
   ```

3. **Remover `POST /v1/users/email_templates/send`** para convites de entrevista

### ✅ Manter como está

1. `POST /v1/users/evaluation_candidates/create_collection` — sem mudança na chamada
2. WebSocket `EvaluationCandidateCollectionChannel` — payloads iguais
3. Página do candidato `/evaluations/{account_uid}/{ec_uid}` — sem mudança
4. Página de entrevista `/interviews/{account_uid}/{token}` — sem mudança

### ❌ Não fazer mais

1. Não montar texto de email de entrevista no frontend
2. Não chamar `email_templates/send` para convites de entrevista/avaliação
3. Não se preocupar com template de email — backend renderiza tudo

---

## Retrocompatibilidade

Se `notification_channels` estiver vazio ou null (evaluations antigas): 

| Fluxo | Fallback |
|-------|----------|
| `create_collection` | Usa `chatbot_channel`: `internal` → `[:internal]`, `whatsapp` → WhatsApp |
| `interview_sessions` | Usa `interview_type`: `voice`/`video` → `[:voice]`, `phone` → `[:phone]` |

Evaluations antigas continuam funcionando sem mudança. O frontend pode migrar gradualmente.

---

## Resumo Rápido

| Ação | Endpoint | O que define os botões do email |
|------|----------|---------------------------------|
| Configurar canais | `PUT /evaluations/:id` | `notification_channels: ["internal", "voice"]` |
| Enviar avaliação | `POST /evaluation_candidates/create_collection` | Lê `notification_channels` da Evaluation |
| Criar entrevista + email | `POST /interview_sessions` (com `channels: ["email"]`) | Lê `notification_channels` da Evaluation |
| Criar entrevista + WhatsApp | `POST /interview_sessions` (com `channels: ["whatsapp"]`) | WhatsApp template |
| Criar entrevista sem notificar | `POST /interview_sessions` (sem `channels`) | Nenhum email/whatsapp |
