# Copilot Instructions — Background Agent Frontend (Vue 3 / Nuxt)

## Overview

The background agent executes search cycles asynchronously in a Python worker. Progress updates arrive in real-time via **ActionCable WebSocket** and are also persisted in the Rails API for historical viewing. The frontend must show a live execution timeline with agent "thinking" details.

## Architecture

```
Rails ActionCable WebSocket ──→ useBackgroundAgentChannel composable ──→ Pinia store ──→ UI components
Rails REST API (GET /steps)  ──→ Initial load / page refresh recovery
```

## Data Flow

1. **On page load**: Fetch persisted steps via `GET /v1/users/background_agents/{id}/steps?cycle_id={cycleId}` to recover state
2. **Subscribe** to ActionCable channel `BackgroundAgentChannel` with `{ agent_id }`
3. **On WebSocket message**: Append step to local store, update UI reactively
4. **On disconnect/reconnect**: Re-fetch steps from API to fill any gaps

## REST API: Steps Endpoint

### `GET /v1/users/background_agents/{id}/steps`

Query params:
- `cycle_id` (optional) — filter steps by cycle
- `step` (optional) — filter by step name

Response format: JSON:API via `BackgroundAgentStepSerializer`

```json
{
  "data": [
    {
      "id": "1",
      "type": "background_agent_step",
      "attributes": {
        "step": "search",
        "status": "done",
        "message": "Found 23 candidates in iteration 2",
        "details": {
          "candidates_found": 23,
          "provider": "local",
          "query": "python developer senior"
        },
        "iteration_number": 2,
        "created_at": "2026-04-03T17:00:00Z"
      },
      "relationships": {
        "background_agent": { "data": { "id": "5", "type": "background_agent" } },
        "agent_cycle": { "data": { "id": "42", "type": "agent_cycle" } }
      }
    }
  ]
}
```

## WebSocket Messages

### Channel subscription

```ts
import { createConsumer } from '@rails/actioncable'

const consumer = createConsumer(`${API_WS_URL}/cable?auth_token=${token}`)

const subscription = consumer.subscriptions.create(
  { channel: 'BackgroundAgentChannel', agent_id: agentId },
  {
    received(data: AgentWebSocketMessage) { /* handle */ },
    connected() { /* mark connected */ },
    disconnected() { /* mark disconnected, schedule reconnect */ }
  }
)
```

### Message Types

```ts
type AgentWebSocketMessage = AgentProgressMessage | CycleDeliveredMessage

interface AgentProgressMessage {
  type: 'progress'
  agent_id: number
  cycle_id: number | null
  step_id: number
  step: AgentStepName
  status: 'running' | 'done' | 'error'
  message: string | null
  details: Record<string, any> | null
  iteration_number: number | null
  timestamp: string
}

interface CycleDeliveredMessage {
  type: 'cycle_delivered'
  cycle_id: number
  cycle_number: number
}

type AgentStepName = 'plan' | 'load_context' | 'generate_queries' | 'search' | 'evaluate' | 'score' | 'deliver'
```

## Pinia Store Pattern

```ts
// stores/backgroundAgentProgress.ts
import { defineStore } from 'pinia'

interface StepEntry {
  id: number
  step: AgentStepName
  status: 'running' | 'done' | 'error'
  message: string | null
  details: Record<string, any> | null
  iterationNumber: number | null
  createdAt: string
}

export const useBackgroundAgentProgressStore = defineStore('backgroundAgentProgress', {
  state: () => ({
    steps: [] as StepEntry[],
    currentStep: null as AgentStepName | null,
    isRunning: false,
    isConnected: false,
    agentId: null as number | null,
  }),

  getters: {
    currentStepDetails: (state) => state.steps.filter(s => s.step === state.currentStep),
    completedSteps: (state) => [...new Set(state.steps.filter(s => s.status === 'done').map(s => s.step))],
    planText: (state) => state.steps.find(s => s.step === 'plan' && s.status === 'done')?.details?.plan_text,
    evaluationGaps: (state) => state.steps.filter(s => s.step === 'evaluate').flatMap(s => s.details?.gaps || []),
    searchIterations: (state) => state.steps.filter(s => s.step === 'search'),
    lastError: (state) => state.steps.find(s => s.status === 'error'),
    totalCandidatesFound: (state) => {
      const searchSteps = state.steps.filter(s => s.step === 'search' && s.status === 'done')
      return searchSteps.reduce((sum, s) => sum + (s.details?.candidates_found || 0), 0)
    },
  },

  actions: {
    handleProgressMessage(msg: AgentProgressMessage) {
      this.steps.push({
        id: msg.step_id,
        step: msg.step,
        status: msg.status,
        message: msg.message,
        details: msg.details,
        iterationNumber: msg.iteration_number,
        createdAt: msg.timestamp,
      })
      this.currentStep = msg.step
      this.isRunning = msg.status !== 'error'
    },

    handleCycleDelivered() {
      this.isRunning = false
      this.currentStep = null
    },

    loadStepsFromApi(steps: StepEntry[]) {
      this.steps = steps
      const last = steps[steps.length - 1]
      if (last) {
        this.currentStep = last.step
        this.isRunning = last.status === 'running'
      }
    },

    reset() {
      this.steps = []
      this.currentStep = null
      this.isRunning = false
    },
  },
})
```

## Composable Pattern

```ts
// composables/useBackgroundAgentChannel.ts
export function useBackgroundAgentChannel(agentId: Ref<number>) {
  const store = useBackgroundAgentProgressStore()
  let subscription: any = null
  let consumer: any = null

  async function fetchPersistedSteps(cycleId?: number) {
    const params: Record<string, any> = {}
    if (cycleId) params.cycle_id = cycleId
    const { data } = await api.get(`/v1/users/background_agents/${agentId.value}/steps`, { params })
    store.loadStepsFromApi(deserializeSteps(data))
  }

  function connect() {
    consumer = createConsumer(`${wsUrl}/cable?auth_token=${token}`)
    subscription = consumer.subscriptions.create(
      { channel: 'BackgroundAgentChannel', agent_id: agentId.value },
      {
        connected() {
          store.isConnected = true
          fetchPersistedSteps()
        },
        disconnected() {
          store.isConnected = false
        },
        received(data: AgentWebSocketMessage) {
          if (data.type === 'progress') store.handleProgressMessage(data)
          if (data.type === 'cycle_delivered') store.handleCycleDelivered()
        },
      }
    )
  }

  function disconnect() {
    subscription?.unsubscribe()
    consumer?.disconnect()
    store.reset()
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { store }
}
```

## UI Components to Build

### 1. AgentExecutionTimeline

Shows a vertical timeline of all steps with expandable details. Each step shows:
- Step name with icon
- Status indicator (spinner for running, check for done, X for error)
- Message text
- Expandable details panel (gaps, queries, scores, etc.)
- Timestamp

### 2. AgentThinkingPanel

Shows the agent's "reasoning" in real-time:
- **Plan text** from `plan` step details
- **Search strategy** from `generate_queries` details
- **Evaluation diagnosis** from `evaluate` details (gaps, hypotheses, diagnosis)
- **Score distribution** from `score` details

### 3. AgentProgressStepper

Horizontal stepper showing overall progress through the pipeline:
`Plan → Load → Queries → Search → Evaluate → Score → Deliver`
- Highlights current step
- Shows iteration loops (search → evaluate → search)
- Collapse repeated iterations

### 4. AgentStatsBar

Quick stats bar showing:
- Total candidates found
- Current iteration number
- Quality score (from evaluate)
- Average candidate score (from score)
- Duration elapsed

## Step Icons & Colors

| Step | Icon | Color (running) | Color (done) |
|------|------|-----------------|--------------|
| `plan` | `mdi-lightbulb-outline` | `warning` | `success` |
| `load_context` | `mdi-database-search` | `info` | `success` |
| `generate_queries` | `mdi-brain` | `info` | `success` |
| `search` | `mdi-magnify` | `primary` | `success` |
| `evaluate` | `mdi-chart-bar` | `warning` | `success` |
| `score` | `mdi-star-half-full` | `warning` | `success` |
| `deliver` | `mdi-send` | `primary` | `success` |

## Key Implementation Rules

1. **Always fetch persisted steps on mount** — handles page refresh and late joins
2. **Append WebSocket messages, never replace** — the store accumulates all steps chronologically
3. **Handle reconnection gracefully** — on `connected()` callback, re-fetch steps from API to fill gaps
4. **Show iteration loops** — `search` and `evaluate` steps repeat; group them visually by `iteration_number`
5. **Expand `evaluate` details by default** — gaps, diagnosis, and hypotheses are the most interesting "thinking" data
6. **Show `plan` step prominently** — it's the agent's declared strategy and users want to see it
7. **Auto-scroll timeline** — when new steps arrive, scroll to the latest entry
8. **Animate transitions** — use Vue transitions for new steps appearing
9. **Use `step_id` as unique key** — not array index; steps are persisted with stable IDs
10. **Don't poll** — rely on WebSocket for real-time updates, only use REST API for initial load and reconnection recovery
11. **Show connection status** — a small indicator showing if WebSocket is connected
12. **Handle `error` status** — show error alert prominently, stop the progress stepper
