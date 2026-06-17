# Background Agent — Real-time Dashboard (Frontend Integration)

## Overview

The background agent executes search cycles asynchronously. During execution, progress updates are broadcast via **ActionCable WebSocket** so the frontend can show real-time status to the user.

## Architecture

```
Python Worker → POST /report_progress → Rails → ActionCable broadcast → Frontend WebSocket
```

## 1. WebSocket Connection

### Connect to ActionCable

```ts
// composables/useBackgroundAgentChannel.ts
import { createConsumer } from '@rails/actioncable'

const CABLE_URL = `${API_BASE_URL}/cable?auth_token=${jwtToken}`

export function useBackgroundAgentChannel(agentId: number) {
  const consumer = createConsumer(CABLE_URL)
  const progress = ref<AgentProgress | null>(null)
  const isRunning = ref(false)
  let subscription: any = null

  function subscribe() {
    subscription = consumer.subscriptions.create(
      { channel: 'BackgroundAgentChannel', agent_id: agentId },
      {
        received(data: WebSocketMessage) {
          handleMessage(data)
        },
        connected() {
          console.log(`[Agent:${agentId}] WebSocket connected`)
        },
        disconnected() {
          console.log(`[Agent:${agentId}] WebSocket disconnected`)
        },
      }
    )
  }

  function handleMessage(data: WebSocketMessage) {
    switch (data.type) {
      case 'progress':
        progress.value = data as AgentProgress
        isRunning.value = data.status !== 'completed' && data.status !== 'error'
        break
      case 'cycle_delivered':
        isRunning.value = false
        // Refresh agent data from API
        break
    }
  }

  function unsubscribe() {
    subscription?.unsubscribe()
    consumer.disconnect()
  }

  onMounted(subscribe)
  onUnmounted(unsubscribe)

  return { progress, isRunning }
}
```

### TypeScript Types

```ts
interface WebSocketMessage {
  type: 'progress' | 'cycle_delivered'
}

interface AgentProgress extends WebSocketMessage {
  type: 'progress'
  agent_id: number
  cycle_id: number
  step: AgentStep
  status: 'running' | 'completed' | 'error'
  message: string
  details?: Record<string, any>
  timestamp: string // ISO 8601
}

interface CycleDelivered extends WebSocketMessage {
  type: 'cycle_delivered'
  cycle_id: number
  cycle_number: number
}

type AgentStep =
  | 'load_context'
  | 'generate_queries'
  | 'search_iteration'
  | 'deduplicate'
  | 'evaluate_results'
  | 'reformulate_queries'
  | 'score_final'
  | 'select_batch'
  | 'deliver'
  | 'completed'
  | 'error'
```

## 2. Progress Steps (execution order)

| Step | Message | Details | Description |
|------|---------|---------|-------------|
| `load_context` | Loading job context and agent configuration | — | Loads job data, criteria, feedback history |
| `generate_queries` | Generating search queries with AI | — | LLM generates diversified search queries |
| `search_iteration` | Searching for candidates | `{ iteration: 1, provider: "local" }` | Executes queries against provider |
| `deduplicate` | Removing duplicates | — | Removes already-presented and duplicate candidates |
| `evaluate_results` | Evaluating search results quality | `{ candidates_so_far: 15 }` | Quality scoring to decide next action |
| `reformulate_queries` | Refining search strategy | — | LLM generates new queries (loops back to search_iteration) |
| `score_final` | Scoring candidates with AI | `{ candidates_to_score: 20 }` | LLM scores each candidate 0-100 |
| `select_batch` | Selecting best candidates | — | Picks top candidates up to daily_limit |
| `deliver` | Delivering results | — | Sends results back to Rails |
| `completed` | Cycle completed — N candidates delivered | `{ duration_ms, iterations, candidates_delivered }` | Final event |
| `error` | Error: ... | — | Something failed |

### Flow Diagram

```
load_context → generate_queries → search_iteration → deduplicate → evaluate_results
                                        ↑                                ↓
                                        ├──────── reformulate_queries ←──┤ (NEEDS_IMPROVEMENT)
                                        │                               ↓
                                        └──────── paginate ←────────────┤ (PAGINATE_MORE)
                                                                        ↓
                                                    score_final → select_batch → deliver → completed
```

The loop (search_iteration → evaluate → reformulate → search_iteration) can repeat up to 3 times (configurable via `max_search_iterations`).

## 3. Dashboard Component Example

```vue
<!-- components/BackgroundAgentProgress.vue -->
<template>
  <v-card v-if="isRunning || progress" variant="outlined" class="mb-4">
    <v-card-title class="d-flex align-center">
      <v-icon :color="statusColor" class="mr-2">{{ statusIcon }}</v-icon>
      Agent Execution
    </v-card-title>

    <v-card-text>
      <!-- Progress Stepper -->
      <v-stepper
        :model-value="currentStepIndex"
        alt-labels
        flat
        non-linear
      >
        <v-stepper-header>
          <template v-for="(step, i) in visibleSteps" :key="step.key">
            <v-stepper-item
              :value="i"
              :complete="isStepComplete(step.key)"
              :color="getStepColor(step.key)"
              :icon="getStepIcon(step.key)"
              :title="step.label"
            />
            <v-divider v-if="i < visibleSteps.length - 1" />
          </template>
        </v-stepper-header>
      </v-stepper>

      <!-- Current Status -->
      <div class="text-center mt-4">
        <p class="text-body-1">{{ progress?.message }}</p>

        <!-- Iteration indicator -->
        <v-chip
          v-if="progress?.details?.iteration"
          size="small"
          color="primary"
          variant="tonal"
          class="mr-2"
        >
          Iteration {{ progress.details.iteration }}
        </v-chip>

        <!-- Provider -->
        <v-chip
          v-if="progress?.details?.provider"
          size="small"
          variant="tonal"
        >
          {{ progress.details.provider }}
        </v-chip>

        <!-- Candidates count -->
        <v-chip
          v-if="progress?.details?.candidates_so_far != null"
          size="small"
          color="success"
          variant="tonal"
        >
          {{ progress.details.candidates_so_far }} candidates found
        </v-chip>
      </div>

      <!-- Completion Summary -->
      <v-alert
        v-if="progress?.step === 'completed'"
        type="success"
        variant="tonal"
        class="mt-4"
      >
        Delivered {{ progress.details?.candidates_delivered || 0 }} candidates
        in {{ formatDuration(progress.details?.duration_ms) }}
        ({{ progress.details?.iterations }} iterations)
      </v-alert>

      <!-- Error -->
      <v-alert
        v-if="progress?.step === 'error'"
        type="error"
        variant="tonal"
        class="mt-4"
      >
        {{ progress.message }}
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useBackgroundAgentChannel } from '~/composables/useBackgroundAgentChannel'

const props = defineProps<{ agentId: number }>()

const { progress, isRunning } = useBackgroundAgentChannel(props.agentId)

const STEP_ORDER: { key: AgentStep; label: string }[] = [
  { key: 'load_context', label: 'Loading' },
  { key: 'generate_queries', label: 'Queries' },
  { key: 'search_iteration', label: 'Searching' },
  { key: 'evaluate_results', label: 'Evaluating' },
  { key: 'score_final', label: 'Scoring' },
  { key: 'deliver', label: 'Delivering' },
]

const visibleSteps = STEP_ORDER

const currentStepIndex = computed(() => {
  if (!progress.value) return -1
  return STEP_ORDER.findIndex((s) => s.key === progress.value?.step)
})

function isStepComplete(step: AgentStep): boolean {
  if (!progress.value) return false
  if (progress.value.step === 'completed') return true
  const current = STEP_ORDER.findIndex((s) => s.key === progress.value?.step)
  const target = STEP_ORDER.findIndex((s) => s.key === step)
  return target < current
}

function getStepColor(step: AgentStep): string {
  if (progress.value?.step === 'error') return 'error'
  if (progress.value?.step === step) return 'primary'
  if (isStepComplete(step)) return 'success'
  return 'grey'
}

function getStepIcon(step: AgentStep): string {
  if (isStepComplete(step)) return 'mdi-check'
  if (progress.value?.step === step) return 'mdi-loading mdi-spin'
  return ''
}

const statusColor = computed(() => {
  if (progress.value?.step === 'completed') return 'success'
  if (progress.value?.step === 'error') return 'error'
  return 'primary'
})

const statusIcon = computed(() => {
  if (progress.value?.step === 'completed') return 'mdi-check-circle'
  if (progress.value?.step === 'error') return 'mdi-alert-circle'
  return 'mdi-robot'
})

function formatDuration(ms?: number): string {
  if (!ms) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
</script>
```

## 4. Using the Component

```vue
<!-- pages/jobs/[id]/agent.vue -->
<template>
  <div>
    <!-- Show progress when agent has a running cycle -->
    <BackgroundAgentProgress :agent-id="agent.id" />

    <!-- Agent details card -->
    <v-card>
      <v-card-title>{{ agent.name }}</v-card-title>
      <v-card-text>
        Status: {{ agent.status }}
        Delivered today: {{ agent.total_delivered - agent.remaining_today }} / {{ agent.daily_limit }}
      </v-card-text>
    </v-card>
  </div>
</template>
```

## 5. REST API Endpoints

### GET /v1/users/background_agents

List agents. Supports `where` filter:

```ts
const { data } = await api.get('/v1/users/background_agents', {
  params: {
    where: JSON.stringify({ job_id: jobId, is_deleted: false }),
    order: JSON.stringify({ created_at: 'desc' }),
  },
})
```

### GET /v1/users/background_agents/:id

Single agent with relationships.

### POST /v1/users/background_agents

Create agent:

```ts
await api.post('/v1/users/background_agents', {
  background_agent: {
    job_id: jobId,
    criteria_text: 'Senior Ruby on Rails developer...',
    mode: 'review',       // "review" | "auto_add"
    daily_limit: 25,
    sources: ['local'],
    min_score_threshold: 60,
  },
})
```

### POST /v1/users/background_agents/:id/pause

### POST /v1/users/background_agents/:id/resume

### POST /v1/users/background_agents/:id/stop

### GET /v1/users/background_agents/:id/cycles

List execution cycles with status and results.

## 6. Agent Attributes (from serializer)

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Agent display name |
| `criteria_text` | string | Search criteria text |
| `calibration_state` | string | Calibration status |
| `mode` | string | `"review"` or `"auto_add"` |
| `status` | string | `"active"`, `"paused"`, `"stopped"` |
| `daily_limit` | integer | Max candidates per day |
| `total_delivered` | integer | All-time delivered candidates |
| `total_approved` | integer | Approved by recruiter |
| `total_rejected` | integer | Rejected by recruiter |
| `sources` | string[] | `["local"]`, `["local", "pearch"]` |
| `min_score_threshold` | integer | Minimum score (0-100) |
| `auto_pause_days` | integer | Auto-pause after N inactive days |
| `last_run_at` | datetime | Last cycle execution |
| `remaining_today` | integer | Remaining daily quota |
| `current_cycle_number` | integer | Currently running cycle number |
| `cycles_count` | integer | Total cycles executed |
| `approval_rate` | float | Approval percentage |

## 7. WebSocket Events Summary

### `progress` — Sent during cycle execution

```json
{
  "type": "progress",
  "agent_id": 1,
  "cycle_id": 4,
  "step": "search_iteration",
  "status": "running",
  "message": "Searching for candidates",
  "details": { "iteration": 2, "provider": "local" },
  "timestamp": "2026-04-01T14:30:00Z"
}
```

### `cycle_delivered` — Sent when cycle finishes delivering

```json
{
  "type": "cycle_delivered",
  "cycle_id": 4,
  "cycle_number": 2
}
```

On `cycle_delivered`, refresh the agent data via REST API to get updated `total_delivered`, `remaining_today`, etc.

## 8. Reactive State Management (Pinia)

```ts
// stores/backgroundAgent.ts
export const useBackgroundAgentStore = defineStore('backgroundAgent', () => {
  const agents = ref<BackgroundAgent[]>([])
  const progressMap = ref<Record<number, AgentProgress>>({})

  function updateProgress(agentId: number, data: AgentProgress) {
    progressMap.value[agentId] = data

    if (data.step === 'completed' || data.step === 'error') {
      setTimeout(() => {
        delete progressMap.value[agentId]
      }, 10000)
    }
  }

  function getProgress(agentId: number): AgentProgress | undefined {
    return progressMap.value[agentId]
  }

  async function fetchAgents(jobId: number) {
    const { data } = await api.get('/v1/users/background_agents', {
      params: { where: JSON.stringify({ job_id: jobId }) },
    })
    agents.value = data.data.map(deserialize)
  }

  async function refreshAgent(agentId: number) {
    const { data } = await api.get(`/v1/users/background_agents/${agentId}`)
    const index = agents.value.findIndex((a) => a.id === agentId)
    if (index >= 0) agents.value[index] = deserialize(data.data)
  }

  return { agents, progressMap, updateProgress, getProgress, fetchAgents, refreshAgent }
})
```
