# Execution Tracking — Frontend Implementation Guide

> Sistema de planejamento e execução em tempo real para o agente de IA.
> O frontend **não interage diretamente** — apenas renderiza os dados enviados via WebSocket.
> O agente de IA é o único responsável por criar mensagens "thinking" e atualizar os steps.

---

## Visão Geral

Quando o agente de IA recebe uma pergunta complexa, ele:

1. Cria uma **mensagem de thinking** com um plano de execução
2. Executa cada step do plano, atualizando via `PUT /v1/users/messages/:id` (rota autenticada por JWT)
3. Cada atualização dispara um evento WebSocket para o frontend em tempo real
4. Ao final, marca a mensagem como `completed` e envia a resposta final

O agente se autentica com JWT (obtido via OTT exchange) e usa as mesmas rotas `v1/users/` do frontend.

O frontend deve escutar esses eventos e exibir uma UI rica com progresso visual.

### Como o Agente Atualiza

O agente pode enviar `is_thinking`, `thinking_status` e `execution_tracking` de **duas formas**:

**1. Diretamente nos campos:**
```json
PUT /v1/users/messages/42
{
  "message": {
    "content": "Buscando...",
    "is_thinking": true,
    "thinking_status": "searching",
    "execution_tracking": { "plan": [...], "progress": {...} }
  }
}
```

**2. Dentro do `metadata` (sync automático):**
```json
PUT /v1/users/messages/42
{
  "message": {
    "content": "Buscando...",
    "metadata": {
      "is_thinking": true,
      "thinking_status": "searching",
      "execution_tracking": { "plan": [...], "progress": {...} }
    }
  }
}
```

No segundo caso, o backend extrai automaticamente esses campos do `metadata` para as colunas dedicadas via `before_save` callback. O `metadata` final fica limpo (sem esses campos duplicados).

---

## Novos Campos na Message

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `is_thinking` | `boolean` | `true` enquanto o agente está pensando/executando |
| `thinking_status` | `string` | Status livre — ex: `"planning"`, `"searching"`, `"executing"`, `"analyzing"`, `"finalizing"`, `"completed"`, `"error"` |
| `execution_tracking` | `object` | Dados completos de progresso (plano, tools, budget) |

### Estrutura do `execution_tracking`

```json
{
  "plan": [
    {
      "step": 1,
      "task": "Buscar vagas ativas",
      "status": "done",
      "tool": "get_jobs_stats",
      "duration_ms": 230
    },
    {
      "step": 2,
      "task": "Verificar pipeline health",
      "status": "in_progress",
      "tool": "get_pipeline_health"
    },
    {
      "step": 3,
      "task": "Analisar candidaturas paradas",
      "status": "pending"
    },
    {
      "step": 4,
      "task": "Sintetizar diagnóstico",
      "status": "pending"
    }
  ],
  "progress": {
    "done": 1,
    "total": 4,
    "percentage": 25
  },
  "tools_executed": [
    {
      "name": "get_jobs_stats",
      "success": true,
      "duration_ms": 230,
      "executed_at": "2026-03-13T14:00:01Z"
    }
  ],
  "started_at": "2026-03-13T14:00:00Z",
  "budget": {
    "used": 1,
    "limit": 40
  }
}
```

### Status dos Steps

| Status | Descrição | Ícone sugerido |
|--------|-----------|----------------|
| `pending` | Ainda não iniciado | `mdi-circle-outline` (cinza) |
| `in_progress` | Em execução agora | `mdi-loading` (animado, azul) |
| `done` | Concluído com sucesso | `mdi-check-circle` (verde) |
| `error` | Falhou | `mdi-alert-circle` (vermelho) |

### Thinking Status (ciclo de vida)

O `thinking_status` é um campo livre (string). O agente pode usar qualquer valor descritivo.
Valores comuns:

```
planning → searching → executing → analyzing → finalizing → completed
                                                           → error
```

---

## WebSocket — Como Consumir

### Conexão

O frontend já deve estar conectado ao ActionCable via:

```javascript
// nuxt.config.ts ou plugin
const cable = createCable(`${API_WS_URL}/cable?auth_token=${token}`)
```

### Canais Disponíveis

#### 1. Canal Geral de Mensagens (recomendado)

```javascript
// composables/useMessageChannel.ts
import { useChannel } from '@/composables/useActionCable'

export function useMessageChannel(userId: number) {
  const channel = useChannel('MessageChannel', {
    auth_token: getAuthToken()
  })

  // Stream: messages_user_{userId}
  // Todos os eventos de mensagem chegam aqui
}
```

#### 2. Canal de Domínio (para chats contextuais — sourcing, jobs, etc.)

```javascript
export function useDomainMessageChannel(userId: number, domain: string, domainReferenceId: number) {
  const channel = useChannel('DomainMessageChannel', {
    auth_token: getAuthToken(),
    domain: domain,
    domain_reference_id: domainReferenceId
  })

  // Stream: domain_messages_user_{userId}_{domain}_{domainReferenceId}
}
```

### Eventos WebSocket

O frontend receberá **3 tipos de eventos** relacionados ao execution tracking:

#### `message_created` — Mensagem de thinking criada

Disparado quando o agente cria a mensagem thinking inicial.

```typescript
interface MessageCreatedEvent {
  type: 'message_created'
  id: number
  content: string | null
  entity: 0  // ROLE_SYSTEM
  status: number
  is_thinking: true
  thinking_status: 'planning'
  execution_tracking: ExecutionTracking
  workspace_id: number
  domain: string | null
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}
```

#### `execution_tracking_updated` — Progresso atualizado (via helper methods)

Disparado quando o backend usa os métodos programáticos (`start_thinking!`, `update_execution_step`, `add_tool_executed`).

```typescript
interface ExecutionTrackingUpdatedEvent {
  type: 'execution_tracking_updated'
  id: number                          // message_id
  workspace_id: number
  domain: string | null
  is_thinking: boolean                // false quando completa
  thinking_status: string             // valor livre: 'planning', 'searching', 'executing', etc.
  execution_tracking: ExecutionTracking
  updated_at: string
}
```

#### `message_updated` — Evento principal (cada PUT do agente)

Disparado a cada `PUT /v1/users/messages/:id` feito pelo agente (via `after_update_commit`).
**Este é o evento mais frequente — use para atualizar a UI a cada mudança.**

```typescript
interface MessageUpdatedEvent {
  type: 'message_updated'
  id: number
  content: string | null              // null enquanto pensando, preenchido na resposta final
  is_thinking: boolean                // true durante execução, false ao completar
  thinking_status: string             // valor livre: 'searching', 'executing', 'completed', etc.
  execution_tracking: ExecutionTracking
  changed_fields: string[]            // ex: ['content', 'is_thinking', 'execution_tracking']
  // ... demais campos de message
}
```

### Handler Completo

```typescript
// composables/useExecutionTracking.ts
import { ref, computed } from 'vue'

interface PlanStep {
  step: number
  task: string
  status: 'pending' | 'in_progress' | 'done' | 'error'
  tool?: string
  duration_ms?: number
}

interface ToolExecution {
  name: string
  success: boolean
  duration_ms?: number
  executed_at: string
}

interface ExecutionTracking {
  plan: PlanStep[]
  progress: { done: number; total: number; percentage: number }
  tools_executed: ToolExecution[]
  started_at: string
  budget: { used: number; limit: number }
}

interface ThinkingMessage {
  id: number
  isThinking: boolean
  thinkingStatus: string
  executionTracking: ExecutionTracking | null
}

export function useExecutionTracking() {
  const thinkingMessages = ref<Map<number, ThinkingMessage>>(new Map())

  function handleWebSocketEvent(event: any) {
    switch (event.type) {
      case 'message_created':
        if (event.is_thinking) {
          thinkingMessages.value.set(event.id, {
            id: event.id,
            isThinking: true,
            thinkingStatus: event.thinking_status,
            executionTracking: event.execution_tracking
          })
        }
        break

      case 'execution_tracking_updated':
        thinkingMessages.value.set(event.id, {
          id: event.id,
          isThinking: event.is_thinking,
          thinkingStatus: event.thinking_status,
          executionTracking: event.execution_tracking
        })

        if (!event.is_thinking) {
          // Aguardar um pouco antes de remover para animação de conclusão
          setTimeout(() => {
            thinkingMessages.value.delete(event.id)
          }, 3000)
        }
        break

      case 'message_updated':
        if (event.is_thinking || event.changed_fields?.includes('is_thinking') || event.changed_fields?.includes('execution_tracking')) {
          thinkingMessages.value.set(event.id, {
            id: event.id,
            isThinking: event.is_thinking,
            thinkingStatus: event.thinking_status,
            executionTracking: event.execution_tracking
          })

          if (!event.is_thinking) {
            setTimeout(() => {
              thinkingMessages.value.delete(event.id)
            }, 3000)
          }
        }
        break
    }
  }

  const activeThinkingMessages = computed(() =>
    Array.from(thinkingMessages.value.values()).filter(m => m.isThinking)
  )

  return {
    thinkingMessages,
    activeThinkingMessages,
    handleWebSocketEvent
  }
}
```

---

## Componentes Vue/Vuetify Sugeridos

### 1. `ExecutionTracker.vue` — Componente Principal

Exibe o plano de execução com animação de progresso.

```vue
<template>
  <v-card
    v-if="tracking"
    variant="outlined"
    class="execution-tracker pa-4 mb-3"
    :class="{ 'thinking-active': isThinking }"
  >
    <!-- Header com status -->
    <div class="d-flex align-center mb-3">
      <v-avatar size="32" :color="statusColor" class="mr-3">
        <v-icon :icon="statusIcon" size="18" color="white" />
      </v-avatar>

      <div class="flex-grow-1">
        <div class="text-subtitle-2 font-weight-bold">
          {{ statusLabel }}
        </div>
        <div class="text-caption text-medium-emphasis">
          {{ tracking.progress.done }}/{{ tracking.progress.total }} etapas
        </div>
      </div>

      <!-- Progress circular -->
      <v-progress-circular
        :model-value="tracking.progress.percentage"
        :size="44"
        :width="4"
        :color="statusColor"
      >
        <span class="text-caption font-weight-bold">
          {{ tracking.progress.percentage }}%
        </span>
      </v-progress-circular>
    </div>

    <!-- Barra de progresso linear -->
    <v-progress-linear
      :model-value="tracking.progress.percentage"
      :color="statusColor"
      height="6"
      rounded
      class="mb-4"
      :indeterminate="thinkingStatus === 'planning'"
    />

    <!-- Lista de steps -->
    <v-timeline density="compact" side="end" class="execution-timeline">
      <v-timeline-item
        v-for="step in tracking.plan"
        :key="step.step"
        :dot-color="stepColor(step.status)"
        :icon="stepIcon(step.status)"
        size="small"
      >
        <div class="d-flex align-center justify-space-between">
          <div>
            <span
              class="text-body-2"
              :class="{
                'text-medium-emphasis': step.status === 'pending',
                'font-weight-medium': step.status === 'in_progress',
                'text-decoration-line-through': step.status === 'done'
              }"
            >
              {{ step.task }}
            </span>
            <div v-if="step.tool" class="text-caption text-medium-emphasis">
              <v-icon icon="mdi-function" size="12" class="mr-1" />
              {{ step.tool }}
              <span v-if="step.duration_ms" class="ml-1">
                ({{ step.duration_ms }}ms)
              </span>
            </div>
          </div>

          <!-- Indicador de loading no step atual -->
          <v-progress-circular
            v-if="step.status === 'in_progress'"
            indeterminate
            size="16"
            width="2"
            color="primary"
          />
          <v-icon
            v-else-if="step.status === 'done'"
            icon="mdi-check"
            size="16"
            color="success"
          />
          <v-icon
            v-else-if="step.status === 'error'"
            icon="mdi-close"
            size="16"
            color="error"
          />
        </div>
      </v-timeline-item>
    </v-timeline>

    <!-- Footer: budget e tempo -->
    <v-divider class="my-3" />
    <div class="d-flex justify-space-between text-caption text-medium-emphasis">
      <span>
        <v-icon icon="mdi-tools" size="14" class="mr-1" />
        {{ tracking.budget.used }}/{{ tracking.budget.limit }} ferramentas
      </span>
      <span>
        <v-icon icon="mdi-clock-outline" size="14" class="mr-1" />
        {{ elapsedTime }}
      </span>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  tracking: ExecutionTracking | null
  isThinking: boolean
  thinkingStatus: string
}

const props = defineProps<Props>()

const STATUS_CONFIG = {
  planning: { color: 'info', icon: 'mdi-brain', label: 'Planejando...' },
  searching: { color: 'primary', icon: 'mdi-magnify', label: 'Buscando...' },
  executing: { color: 'primary', icon: 'mdi-cog-sync', label: 'Executando...' },
  analyzing: { color: 'primary', icon: 'mdi-chart-line', label: 'Analisando...' },
  finalizing: { color: 'primary', icon: 'mdi-text-box-check', label: 'Finalizando...' },
  completed: { color: 'success', icon: 'mdi-check-circle', label: 'Concluído' },
  error: { color: 'error', icon: 'mdi-alert-circle', label: 'Erro' }
} as const

const statusColor = computed(() => STATUS_CONFIG[props.thinkingStatus]?.color ?? 'grey')
const statusIcon = computed(() => STATUS_CONFIG[props.thinkingStatus]?.icon ?? 'mdi-help-circle')
const statusLabel = computed(() => STATUS_CONFIG[props.thinkingStatus]?.label ?? props.thinkingStatus)

function stepColor(status: string) {
  const colors = { pending: 'grey', in_progress: 'primary', done: 'success', error: 'error' }
  return colors[status] ?? 'grey'
}

function stepIcon(status: string) {
  const icons = {
    pending: 'mdi-circle-outline',
    in_progress: 'mdi-loading mdi-spin',
    done: 'mdi-check-circle',
    error: 'mdi-alert-circle'
  }
  return icons[status] ?? 'mdi-circle-outline'
}

const elapsedTime = computed(() => {
  if (!props.tracking?.started_at) return '--'
  const start = new Date(props.tracking.started_at)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - start.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
})
</script>

<style scoped>
.execution-tracker {
  border-color: rgb(var(--v-theme-surface-variant));
  transition: all 0.3s ease;
}

.thinking-active {
  border-color: rgb(var(--v-theme-primary));
  animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: rgb(var(--v-theme-primary)); }
  50% { border-color: rgba(var(--v-theme-primary), 0.3); }
}

.execution-timeline :deep(.v-timeline-item__body) {
  padding-block: 4px;
}
</style>
```

### 2. `ThinkingIndicator.vue` — Indicador Compacto (dentro do chat)

Para exibir inline na lista de mensagens.

```vue
<template>
  <div v-if="message.is_thinking" class="thinking-indicator d-flex align-center pa-3">
    <div class="thinking-dots mr-3">
      <span /><span /><span />
    </div>

    <div class="flex-grow-1">
      <div class="text-body-2 font-weight-medium">
        {{ currentStepLabel }}
      </div>
      <v-progress-linear
        :model-value="message.execution_tracking?.progress?.percentage ?? 0"
        color="primary"
        height="3"
        rounded
        class="mt-1"
      />
    </div>

    <v-btn
      v-if="showDetails"
      icon
      variant="text"
      size="small"
      @click="$emit('toggle-details')"
    >
      <v-icon icon="mdi-chevron-down" />
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  message: any
  showDetails?: boolean
}>()

defineEmits(['toggle-details'])

const currentStepLabel = computed(() => {
  const plan = props.message.execution_tracking?.plan
  if (!plan) return 'Pensando...'
  const current = plan.find((s: any) => s.status === 'in_progress')
  return current?.task ?? 'Processando...'
})
</script>

<style scoped>
.thinking-dots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-primary));
  animation: thinking 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes thinking {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
```

### 3. Integração na Lista de Mensagens

```vue
<!-- MessageList.vue -->
<template>
  <div class="message-list">
    <template v-for="message in messages" :key="message.id">
      <!-- Mensagem normal -->
      <MessageBubble
        v-if="!message.is_thinking"
        :message="message"
      />

      <!-- Mensagem de thinking com execution tracker -->
      <div v-else class="thinking-message-wrapper">
        <ThinkingIndicator
          :message="message"
          :show-details="!expandedTracking.has(message.id)"
          @toggle-details="toggleTracking(message.id)"
        />

        <ExecutionTracker
          v-if="expandedTracking.has(message.id)"
          :tracking="message.execution_tracking"
          :is-thinking="message.is_thinking"
          :thinking-status="message.thinking_status"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const expandedTracking = ref(new Set<number>())

function toggleTracking(messageId: number) {
  if (expandedTracking.value.has(messageId)) {
    expandedTracking.value.delete(messageId)
  } else {
    expandedTracking.value.add(messageId)
  }
}
</script>
```

---

## Fluxo Completo (Sequência)

```
Frontend                    WebSocket                   Backend (AI Agent)
   │                           │                              │
   │  user envia pergunta      │                              │
   │  POST /v1/users/messages  │                              │
   │ ─────────────────────────────────────────────────────────>│
   │                           │                              │
   │                           │  message_created             │
   │                           │  (is_thinking: true,         │
   │                           │   thinking_status: planning) │
   │<──────────────────────────│                              │
   │                           │                              │
   │  Renderiza ThinkingDots   │  PUT /v1/users/messages/:id  │
   │                           │  (thinking_status: searching)│
   │                           │  message_updated             │
   │                           │  (step 1: in_progress)       │
   │<──────────────────────────│                              │
   │                           │                              │
   │  Anima step 1 loading     │  PUT /v1/users/messages/:id  │
   │                           │  (step 1: done, step 2: ...) │
   │                           │  message_updated             │
   │                           │  (step 1: done,              │
   │                           │   step 2: in_progress,       │
   │                           │   percentage: 25)            │
   │<──────────────────────────│                              │
   │                           │                              │
   │  Marca step 1 ✓           │                              │
   │  Anima step 2 loading     │                              │
   │  Atualiza progress 25%    │                              │
   │                           │                              │
   │          ... (repete para cada step) ...                  │
   │                           │                              │
   │                           │  PUT /v1/users/messages/:id  │
   │                           │  (is_thinking: false)        │
   │                           │  message_updated             │
   │                           │  (is_thinking: false,        │
   │                           │   thinking_status: completed │
   │                           │   content: "resposta final") │
   │<──────────────────────────│                              │
   │                           │                              │
   │  Remove ExecutionTracker  │                              │
   │  Renderiza MessageBubble  │                              │
   │  com conteúdo final       │                              │
```

---

## JSON:API Response — GET `/v1/users/messages`

As mensagens retornadas pelo endpoint REST agora incluem os novos campos:

```json
{
  "data": [
    {
      "id": "123",
      "type": "message",
      "attributes": {
        "content": null,
        "content_format": "plain_text",
        "entity": 0,
        "status": 0,
        "is_thinking": true,
        "thinking_status": "executing",
        "execution_tracking": {
          "plan": [
            { "step": 1, "task": "Buscar vagas ativas", "status": "done", "tool": "get_jobs_stats", "duration_ms": 230 },
            { "step": 2, "task": "Verificar pipeline health", "status": "in_progress", "tool": "get_pipeline_health" },
            { "step": 3, "task": "Analisar candidaturas paradas", "status": "pending" },
            { "step": 4, "task": "Sintetizar diagnóstico", "status": "pending" }
          ],
          "progress": { "done": 1, "total": 4, "percentage": 25 },
          "tools_executed": [
            { "name": "get_jobs_stats", "success": true, "duration_ms": 230, "executed_at": "2026-03-13T14:00:01Z" }
          ],
          "started_at": "2026-03-13T14:00:00Z",
          "budget": { "used": 1, "limit": 40 }
        },
        "workspace_id": 45,
        "domain": null,
        "metadata": {},
        "created_at": "2026-03-13T14:00:00Z",
        "updated_at": "2026-03-13T14:00:02Z"
      }
    }
  ]
}
```

---

## Notas Importantes

1. **O frontend NÃO modifica execution tracking** — é responsabilidade exclusiva do agente de IA (via `PUT /v1/users/messages/:id` autenticado)
2. **Performance**: Os eventos `execution_tracking_updated` podem chegar em rajadas (1 por segundo). Use `requestAnimationFrame` ou `throttle` para animações suaves
3. **Reconexão**: Se o WebSocket reconectar, busque as mensagens do workspace via `GET /v1/users/messages` com `where={"workspace_id": X}` para recuperar o estado atual
4. **Mensagens antigas**: Quando `is_thinking: false` e `thinking_status: "completed"`, o `execution_tracking` permanece para histórico — pode ser útil mostrar um "ver plano de execução" colapsável
5. **Budget**: O campo `budget.limit` indica o máximo de ferramentas que o agente pode usar. Pode ser exibido como um indicador de consumo de recursos
6. **Auto-expand**: Considere expandir automaticamente o `ExecutionTracker` para a mensagem thinking mais recente

---

## Dicas de UX

- Use `v-fade-transition` do Vuetify para transições suaves entre steps
- O `VProgressLinear` com `indeterminate` durante `planning` dá feedback visual imediato
- Cores consistentes: azul (executando), verde (concluído), vermelho (erro), cinza (pendente)
- O timer `elapsedTime` no footer mostra ao usuário quanto tempo está demorando
- Considere um efeito de "shimmer" ou "pulse" no card enquanto `is_thinking === true`
- Sound feedback sutil ao completar todos os steps pode melhorar a experiência
