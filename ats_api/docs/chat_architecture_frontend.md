# Chat Architecture — Frontend Implementation Guide

> Como consumir o sistema de mensagens e workspaces para implementar o chat geral e chats contextuais.

---

## Conceitos

### Workspace

Um **Workspace** agrupa mensagens de uma conversa. Cada workspace pertence a um **user** e tem um **domain** opcional.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `integer` | ID interno |
| `uid` | `string` | UUID público (usar para rotas no frontend) |
| `name` | `string` | Nome gerado automaticamente pela IA com base na primeira mensagem |
| `domain` | `string \| null` | Tipo do chat: `null` = chat geral, `"sourcing"`, `"jobs"`, `"teams"`, `"lia_general"` |
| `domain_reference_id` | `integer \| null` | ID do objeto associado (ex: job_id, sourcing_id). `null` para chat geral e `lia_general` |
| `last_message_date` | `datetime` | Timestamp da última mensagem |
| `is_deleted` | `boolean` | Soft delete |

### Categorias de Chat

| Categoria | `domain` | `domain_reference_id` | Descrição |
|-----------|----------|-----------------------|-----------|
| **Chat Geral** | `null` | `null` | Conversas livres com a IA. Cada nova conversa cria um workspace |
| **Lia General** | `"lia_general"` | `null` | Workspace singleton — sempre o mesmo workspace por user |
| **Sourcing** | `"sourcing"` | `sourcing.id` | Chat contextual sobre um sourcing específico |
| **Jobs** | `"jobs"` | `job.id` | Chat contextual sobre uma vaga específica |
| **Teams** | `"teams"` | `teams_chat_id` | Integração Microsoft Teams |

### Message

Cada mensagem pertence a um workspace e a um user (via `reference_type`/`reference_id`).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `integer` | ID da mensagem |
| `content` | `string` | Conteúdo da mensagem |
| `entity` | `integer` | `0` = sistema/IA, `1` = usuário, `2` = candidato |
| `status` | `integer` | `0` = não respondida, `1` = respondida |
| `workspace_id` | `integer` | Workspace ao qual pertence |
| `domain` | `string \| null` | Mesmo domínio do workspace |
| `is_thinking` | `boolean` | `true` enquanto IA está processando |
| `thinking_status` | `string` | Status da execução (`"planning"`, `"searching"`, etc.) |
| `execution_tracking` | `object` | Dados de progresso em tempo real |
| `metadata` | `object` | Dados extras (estado conversacional, etc.) |

---

## Endpoints

### 1. Listar Workspaces (sidebar do chat)

```
GET /v1/users/workspaces
```

**Filtros via query params** (Searchkick):

```javascript
// Todos os workspaces do user (exceto deletados)
GET /v1/users/workspaces

// Apenas chats gerais (sem domain)
GET /v1/users/workspaces?where={"domain": null}

// Apenas chats de sourcing
GET /v1/users/workspaces?where={"domain": "sourcing"}

// Ordenar por última atividade
GET /v1/users/workspaces?order={"last_message_date": "desc"}
```

**Response (JSON:API):**

```json
{
  "data": [
    {
      "id": "101",
      "type": "workspace",
      "attributes": {
        "uid": "a1b2c3d4-...",
        "name": "Análise de vagas abertas",
        "domain": null,
        "domain_reference_id": null,
        "last_message_date": "2026-03-13T14:30:00Z",
        "is_deleted": false,
        "has_messages": true,
        "last_activity": "2026-03-13T14:30:00Z",
        "messages_count": 12
      }
    },
    {
      "id": "102",
      "type": "workspace",
      "attributes": {
        "uid": "e5f6g7h8-...",
        "name": "Sourcing #45",
        "domain": "sourcing",
        "domain_reference_id": 45,
        "last_message_date": "2026-03-13T10:00:00Z",
        "is_deleted": false,
        "has_messages": true,
        "last_activity": "2026-03-13T10:00:00Z",
        "messages_count": 5
      }
    }
  ]
}
```

### 2. Listar Mensagens de um Workspace

```
GET /v1/users/messages?where={"workspace_id": 101}
```

**Filtros comuns:**

```javascript
// Mensagens de um workspace específico
GET /v1/users/messages?where={"workspace_id": 101}

// Com paginação
GET /v1/users/messages?where={"workspace_id": 101}&page=1&per_page=20

// Ordenar por data (mais recente primeiro para load mais recente, mais antigo para scroll infinito)
GET /v1/users/messages?where={"workspace_id": 101}&order={"created_at": "desc"}&per_page=20
```

**Response (JSON:API):**

```json
{
  "data": [
    {
      "id": "3001",
      "type": "message",
      "attributes": {
        "content": "Quais vagas estão abertas?",
        "entity": 1,
        "status": 1,
        "workspace_id": 101,
        "domain": null,
        "is_thinking": false,
        "thinking_status": null,
        "execution_tracking": {},
        "metadata": {},
        "created_at": "2026-03-13T14:28:00Z"
      }
    },
    {
      "id": "3002",
      "type": "message",
      "attributes": {
        "content": "Encontrei 12 vagas ativas...",
        "entity": 0,
        "status": 0,
        "workspace_id": 101,
        "domain": null,
        "is_thinking": false,
        "thinking_status": "completed",
        "execution_tracking": { "plan": [...], "progress": { "done": 3, "total": 3, "percentage": 100 } },
        "metadata": {},
        "created_at": "2026-03-13T14:28:05Z"
      }
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total_count": 12 }
}
```

### 3. Enviar Mensagem (Chat Geral)

```
POST /v1/users/messages
Content-Type: application/json

{
  "message": {
    "content": "Quais vagas estão abertas?",
    "workspace_id": 101
  }
}
```

**Comportamento:**
- Se `workspace_id` é enviado e existe → mensagem vai para esse workspace
- Se `workspace_id` NÃO é enviado → um novo workspace é criado automaticamente, com nome gerado pela IA a partir do conteúdo da primeira mensagem

**Iniciar nova conversa (criar workspace automaticamente):**

```
POST /v1/users/messages
Content-Type: application/json

{
  "message": {
    "content": "Me ajude a analisar as vagas"
  }
}
```

O backend cria um workspace, gera um nome via IA (async via job), e retorna a mensagem com `workspace_id` preenchido.

### 4. Enviar Mensagem (Chat Contextual)

Para chats de domínio (sourcing, jobs), envie `domain` e `domain_reference_id`:

```
POST /v1/users/messages
Content-Type: application/json

{
  "message": {
    "content": "Qual o status desse sourcing?",
    "domain": "sourcing",
    "domain_reference_id": 45
  }
}
```

O backend faz `Workspace.find_or_create_for_domain` — se já existe workspace para este user+domain+reference_id, reutiliza. Caso contrário, cria um novo.

### 5. CRUD de Workspace

```
GET    /v1/users/workspaces/:uid    → Detalhes de um workspace
PUT    /v1/users/workspaces/:uid    → Renomear workspace (params: { workspace: { name: "..." } })
DELETE /v1/users/workspaces/:uid    → Soft delete (is_deleted: true)
```

---

## WebSocket — Tempo Real

### Canal Principal

```javascript
// Stream: messages_user_{userId}
const channel = useChannel('MessageChannel', {
  auth_token: getAuthToken()
})
```

**Eventos recebidos:**

| Evento | Quando |
|--------|--------|
| `message_created` | Nova mensagem da IA (entity = 0) |
| `message_updated` | Mensagem atualizada (conteúdo, status, execution_tracking) |
| `execution_tracking_updated` | Progresso de execução atualizado |
| `workspace_updated` | Nome do workspace gerado/atualizado |

### Canal de Domínio (para chats contextuais)

```javascript
// Stream: domain_messages_user_{userId}_{domain}_{domainReferenceId}
const channel = useChannel('DomainMessageChannel', {
  auth_token: getAuthToken(),
  domain: 'sourcing',
  domain_reference_id: 45
})
```

### Handler de Eventos

```typescript
function handleWebSocketEvent(event: any) {
  switch (event.type) {
    case 'message_created':
      addMessageToWorkspace(event.workspace_id, event)
      break

    case 'message_updated':
      updateMessageInWorkspace(event.workspace_id, event)
      break

    case 'execution_tracking_updated':
      updateExecutionTracking(event.id, event)
      break

    case 'workspace_updated':
      updateWorkspaceName(event.workspace_id, event.name)
      break
  }
}
```

---

## Implementação Frontend — Composables

### `useWorkspaces.ts` — Gerenciamento de Workspaces

```typescript
import { ref, computed } from 'vue'

interface Workspace {
  id: number
  uid: string
  name: string
  domain: string | null
  domainReferenceId: number | null
  lastMessageDate: string | null
  hasMessages: boolean
  messagesCount: number
}

export function useWorkspaces() {
  const workspaces = ref<Workspace[]>([])
  const loading = ref(false)
  const activeWorkspaceId = ref<number | null>(null)

  async function fetchWorkspaces(domain?: string | null) {
    loading.value = true
    const where: Record<string, any> = {}
    if (domain !== undefined) where.domain = domain
    
    const { data } = await api.get('/v1/users/workspaces', {
      params: { where: JSON.stringify(where), order: JSON.stringify({ last_message_date: 'desc' }) }
    })
    workspaces.value = data.data.map(mapWorkspace)
    loading.value = false
  }

  const generalWorkspaces = computed(() =>
    workspaces.value.filter(w => w.domain === null)
  )

  const domainWorkspaces = computed(() =>
    workspaces.value.filter(w => w.domain !== null)
  )

  function groupByDomain() {
    return workspaces.value.reduce((groups, ws) => {
      const key = ws.domain ?? 'general'
      if (!groups[key]) groups[key] = []
      groups[key].push(ws)
      return groups
    }, {} as Record<string, Workspace[]>)
  }

  return {
    workspaces,
    loading,
    activeWorkspaceId,
    generalWorkspaces,
    domainWorkspaces,
    groupByDomain,
    fetchWorkspaces
  }
}
```

### `useChatMessages.ts` — Mensagens de um Workspace

```typescript
import { ref } from 'vue'

interface ChatMessage {
  id: number
  content: string
  entity: number
  status: number
  workspaceId: number
  isThinking: boolean
  thinkingStatus: string | null
  executionTracking: Record<string, any>
  createdAt: string
}

export function useChatMessages(workspaceId: Ref<number | null>) {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const hasMore = ref(true)
  const page = ref(1)

  async function fetchMessages(reset = false) {
    if (!workspaceId.value) return
    if (reset) { page.value = 1; hasMore.value = true }

    loading.value = true
    const { data } = await api.get('/v1/users/messages', {
      params: {
        where: JSON.stringify({ workspace_id: workspaceId.value }),
        order: JSON.stringify({ created_at: 'desc' }),
        page: page.value,
        per_page: 20
      }
    })

    const newMessages = data.data.map(mapMessage)
    if (reset) {
      messages.value = newMessages.reverse()
    } else {
      messages.value = [...newMessages.reverse(), ...messages.value]
    }

    hasMore.value = newMessages.length === 20
    page.value++
    loading.value = false
  }

  async function sendMessage(content: string) {
    const { data } = await api.post('/v1/users/messages', {
      message: { content, workspace_id: workspaceId.value }
    })
    const msg = mapMessage(data.data)
    messages.value.push(msg)
    return msg
  }

  async function startNewConversation(content: string) {
    const { data } = await api.post('/v1/users/messages', {
      message: { content }
    })
    const msg = mapMessage(data.data)
    workspaceId.value = msg.workspaceId
    messages.value = [msg]
    return msg
  }

  function handleIncomingMessage(event: any) {
    if (event.workspace_id !== workspaceId.value) return

    const existing = messages.value.findIndex(m => m.id === event.id)
    const mapped = mapEventToMessage(event)

    if (existing >= 0) {
      messages.value[existing] = mapped
    } else {
      messages.value.push(mapped)
    }
  }

  return {
    messages,
    loading,
    hasMore,
    fetchMessages,
    sendMessage,
    startNewConversation,
    handleIncomingMessage
  }
}
```

---

## Layout Sugerido

```
┌──────────────────────────────────────────────────────────────────┐
│  Sidebar (workspaces)                │  Chat Area               │
│                                      │                          │
│  ┌─ Chat Geral ──────────────────┐   │  ┌──────────────────┐    │
│  │  📝 Análise de vagas abertas  │◀──│──│ [mensagem user]  │    │
│  │     há 5 minutos              │   │  │ [resposta IA]    │    │
│  │  📝 Ajuda com descrição       │   │  │ [mensagem user]  │    │
│  │     há 2 horas                │   │  │ [🔄 thinking...] │    │
│  │  📝 Dashboard RH              │   │  │ [resposta IA]    │    │
│  └───────────────────────────────┘   │  └──────────────────┘    │
│                                      │                          │
│  ┌─ Sourcing ────────────────────┐   │  ┌──────────────────┐    │
│  │  🔍 Sourcing #45             │   │  │ Input box        │    │
│  │  🔍 Sourcing #78             │   │  │ [Enviar]         │    │
│  └───────────────────────────────┘   │  └──────────────────┘    │
│                                      │                          │
│  ┌─ Vagas ───────────────────────┐   │                          │
│  │  💼 Dev Backend Senior        │   │                          │
│  │  💼 Product Manager           │   │                          │
│  └───────────────────────────────┘   │                          │
│                                      │                          │
│  [+ Nova conversa]                   │                          │
└──────────────────────────────────────────────────────────────────┘
```

### Comportamento

1. **Ao abrir o chat geral**: `GET /v1/users/workspaces?where={"domain": null}&order={"last_message_date": "desc"}`
2. **Ao clicar em um workspace**: `GET /v1/users/messages?where={"workspace_id": X}&order={"created_at": "desc"}&per_page=20`
3. **Ao clicar em "+ Nova conversa"**: Envia POST sem `workspace_id` → backend cria workspace automaticamente
4. **Ao abrir chat contextual (ex: dentro de sourcing)**: `GET /v1/users/workspaces?where={"domain": "sourcing", "domain_reference_id": 45}`
5. **Scroll infinito**: Incrementa `page` no `fetchMessages`

---

## Separação de Chats — Como Funciona

A separação é feita pelo campo `domain` do Workspace:

```
┌─────────────────────────────────────────────┐
│                  Workspaces                 │
│                                             │
│  domain = null  → Chat Geral (sidebar)     │
│  domain = "sourcing"  → Chat do Sourcing    │
│  domain = "jobs"      → Chat da Vaga        │
│  domain = "teams"     → Integração Teams    │
│  domain = "lia_general" → Lia (singleton)   │
│                                             │
│  Cada workspace:                            │
│  - Pertence a UM user (user_id)             │
│  - Tem N messages (workspace_id)            │
│  - É isolado por tenant (Apartment)         │
└─────────────────────────────────────────────┘
```

**Segurança:**
- `WorkspacesController#index` filtra automaticamente por `user_id = current_user.id`
- `MessagesController#index` filtra automaticamente por `reference_id = current_user.id` e `reference_type = "User"`
- Cada user vê apenas seus próprios workspaces e mensagens
- Multi-tenancy via Apartment isola dados entre empresas

---

## Novo Workspace vs Workspace Existente

| Cenário | O que enviar | O que acontece |
|---------|--------------|----------------|
| Nova conversa no chat geral | `POST /messages` com `content` apenas | Backend cria workspace com `domain: null`, gera nome via IA |
| Continuar conversa existente | `POST /messages` com `content` + `workspace_id` | Mensagem vai para o workspace existente |
| Chat contextual (sourcing) | `POST /messages` com `content` + `domain: "sourcing"` + `domain_reference_id: 45` | Backend faz `find_or_create_for_domain` — reutiliza se já existe |
| Chat contextual (jobs) | `POST /messages` com `content` + `domain: "jobs"` + `domain_reference_id: 12` | Mesmo comportamento do sourcing |

---

## WebSocket — Atualização do Nome do Workspace

Quando o user cria uma nova conversa, o workspace é criado com um nome temporário. O backend dispara um job async (`WorkspaceNameGenerationJob`) que usa IA para gerar um nome descritivo.

Quando o nome é gerado, o frontend recebe via WebSocket:

```typescript
// Canal: messages_user_{userId}
{
  type: 'workspace_updated',
  workspace_id: 101,
  name: 'Análise de vagas abertas',
  updated_at: '2026-03-13T14:30:00Z'
}
```

O frontend deve atualizar o nome do workspace na sidebar.

---

## Notas

1. **Paginação**: Use `per_page=20` e scroll infinito para carregar mensagens mais antigas
2. **Ordenação**: Workspaces por `last_message_date desc`, mensagens por `created_at desc` (inverter no frontend para exibir cronologicamente)
3. **Nova conversa**: Sempre que a primeira mensagem não tiver `workspace_id`, um workspace novo é criado com nome gerado pela IA
4. **Chats contextuais**: Quando o user está em uma tela de sourcing/vaga e abre o chat, o frontend deve enviar `domain` + `domain_reference_id` no POST. O workspace é reutilizado automaticamente
5. **Domain `null` = chat geral**: Filtrar workspaces com `domain: null` para listar apenas conversas gerais na sidebar
6. **Soft delete**: `DELETE /workspaces/:uid` marca `is_deleted: true`. Workspaces deletados não aparecem nas listagens
7. **Performance**: O `workspace.messages_count` e `workspace.has_messages` evitam ter que carregar mensagens só para saber se o workspace tem conteúdo
