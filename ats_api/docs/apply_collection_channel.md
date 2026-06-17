# ApplyCollectionChannel - Frontend Integration (Vue 3 / Nuxt 3)

## Overview

The `ApplyCollectionChannel` provides real-time WebSocket updates when candidates are being added to a job/selective process via the `create_collection` endpoint. It broadcasts granular events so the frontend can show spinners, progress bars, and per-item feedback.

## Channel Subscription Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | Integer | Yes | The Job ID being applied to |
| `selective_process_id` | Integer | No | The Selective Process ID (if applicable) |

The channel is automatically scoped to the authenticated user via ActionCable connection.

## Event Types

| Event | When | Key Fields |
|-------|------|------------|
| `started` | Job begins processing | `total`, `job_id`, `selective_process_id` |
| `processing_item` | Before each item is processed | `current`, `total`, `percent`, `reference_type` |
| `item_completed` | After each apply is created | `current`, `total`, `created`, `skipped`, `percent`, `apply_id`, `candidate_id`, `apply` |
| `item_skipped` | When a candidate can't be resolved | `current`, `total`, `created`, `skipped`, `percent` |
| `completed` | All items finished | `total`, `created`, `skipped`, `percent`, `applies` |
| `error` | If the job fails | `message` |

Every event includes `type` (string) and `timestamp` (ISO 8601).

## WebSocket Connection

```
ws://YOUR_API_HOST/cable?auth_token=JWT_TOKEN
```

## Nuxt 3 Implementation

### 1. Install ActionCable

```bash
npm install @rails/actioncable
```

### 2. Create the composable

```typescript
// composables/useApplyCollectionChannel.ts
import { ref, onBeforeUnmount } from 'vue'
import { createConsumer, type Subscription } from '@rails/actioncable'

export interface ApplyCollectionEvent {
  type: 'started' | 'processing_item' | 'item_completed' | 'item_skipped' | 'completed' | 'error'
  timestamp: string
  total?: number
  current?: number
  created?: number
  skipped?: number
  percent?: number
  job_id?: number
  selective_process_id?: number
  apply_id?: number
  candidate_id?: number
  reference_type?: string
  reference_id?: number
  message?: string
  apply?: ApplyData
  applies?: ApplyData[]
}

export interface ApplyData {
  id: number
  candidate_id: number
  job_id: number
  selective_process_id: number | null
  selective_process_status: string | null
  name: string | null
  email: string | null
  phone: string | null
  avatar_url: string | null
  linkedin: string | null
  current_company: string | null
  role_name: string | null
  position_level: string | null
  city: string | null
  state: string | null
  created_at: string
  updated_at: string
}

export type ApplyCollectionStatus = 'idle' | 'started' | 'processing' | 'completed' | 'error'

export function useApplyCollectionChannel() {
  const status = ref<ApplyCollectionStatus>('idle')
  const percent = ref(0)
  const total = ref(0)
  const created = ref(0)
  const skipped = ref(0)
  const currentItem = ref(0)
  const errorMessage = ref<string | null>(null)
  const lastEvent = ref<ApplyCollectionEvent | null>(null)
  const completedApplies = ref<ApplyData[]>([])

  let subscription: Subscription | null = null
  let consumer: ReturnType<typeof createConsumer> | null = null

  function subscribe(
    authToken: string,
    jobId: number,
    selectiveProcessId?: number,
    apiWsUrl?: string
  ) {
    const wsUrl = apiWsUrl || useRuntimeConfig().public.apiWsUrl || 'ws://localhost:8080/cable'
    consumer = createConsumer(`${wsUrl}?auth_token=${authToken}`)

    const params: Record<string, any> = {
      channel: 'ApplyCollectionChannel',
      job_id: jobId,
    }
    if (selectiveProcessId) {
      params.selective_process_id = selectiveProcessId
    }

    subscription = consumer.subscriptions.create(params, {
      connected() {
        console.log('[ApplyCollectionChannel] Connected')
      },

      disconnected() {
        console.log('[ApplyCollectionChannel] Disconnected')
      },

      received(data: ApplyCollectionEvent) {
        lastEvent.value = data
        handleEvent(data)
      },
    })
  }

  function handleEvent(event: ApplyCollectionEvent) {
    switch (event.type) {
      case 'started':
        status.value = 'started'
        total.value = event.total ?? 0
        percent.value = 0
        created.value = 0
        skipped.value = 0
        completedApplies.value = []
        errorMessage.value = null
        break

      case 'processing_item':
        status.value = 'processing'
        currentItem.value = event.current ?? 0
        percent.value = event.percent ?? 0
        break

      case 'item_completed':
        status.value = 'processing'
        currentItem.value = event.current ?? 0
        created.value = event.created ?? 0
        skipped.value = event.skipped ?? 0
        percent.value = event.percent ?? 0
        if (event.apply) completedApplies.value.push(event.apply)
        break

      case 'item_skipped':
        currentItem.value = event.current ?? 0
        skipped.value = event.skipped ?? 0
        percent.value = event.percent ?? 0
        break

      case 'completed':
        status.value = 'completed'
        created.value = event.created ?? 0
        skipped.value = event.skipped ?? 0
        percent.value = 100
        if (event.applies) completedApplies.value = event.applies
        break

      case 'error':
        status.value = 'error'
        errorMessage.value = event.message ?? 'Unknown error'
        break
    }
  }

  function unsubscribe() {
    subscription?.unsubscribe()
    consumer?.disconnect()
    subscription = null
    consumer = null
  }

  function reset() {
    status.value = 'idle'
    percent.value = 0
    total.value = 0
    created.value = 0
    skipped.value = 0
    currentItem.value = 0
    errorMessage.value = null
    lastEvent.value = null
    completedApplies.value = []
  }

  onBeforeUnmount(() => {
    unsubscribe()
  })

  return {
    // State
    status,
    percent,
    total,
    created,
    skipped,
    currentItem,
    errorMessage,
    lastEvent,
    completedApplies,

    // Methods
    subscribe,
    unsubscribe,
    reset,
  }
}
```

### 3. Use in a component

```vue
<!-- components/ApplyCollectionProgress.vue -->
<script setup lang="ts">
import { useApplyCollectionChannel } from '~/composables/useApplyCollectionChannel'

const props = defineProps<{
  jobId: number
  selectiveProcessId?: number
}>()

const emit = defineEmits<{
  completed: [applies: ApplyData[], skipped: number]
}>()

const {
  status,
  percent,
  total,
  created,
  skipped,
  currentItem,
  errorMessage,
  completedApplies,
  subscribe,
  unsubscribe,
  reset,
} = useApplyCollectionChannel()

const authStore = useAuthStore() // your auth store

function startListening() {
  reset()
  subscribe(
    authStore.token,
    props.jobId,
    props.selectiveProcessId
  )
}

watch(status, (newStatus) => {
  if (newStatus === 'completed') {
    emit('completed', completedApplies.value, skipped.value)
    setTimeout(() => unsubscribe(), 3000)
  }
})

defineExpose({ startListening, unsubscribe, reset })
</script>

<template>
  <!-- Idle: nothing shown -->
  <div v-if="status !== 'idle'">
    <!-- Started: spinner -->
    <div v-if="status === 'started'" class="flex items-center gap-2">
      <SpinnerIcon class="animate-spin" />
      <span>Preparing to process {{ total }} candidates...</span>
    </div>

    <!-- Processing: progress bar -->
    <div v-if="status === 'processing'" class="space-y-2">
      <div class="flex justify-between text-sm">
        <span>Processing candidate {{ currentItem }} of {{ total }}</span>
        <span>{{ percent }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all duration-300"
          :style="{ width: `${percent}%` }"
        />
      </div>
      <div class="text-xs text-gray-500">
        {{ created }} added · {{ skipped }} skipped
      </div>
    </div>

    <!-- Completed: success message -->
    <div v-if="status === 'completed'" class="text-green-600 flex items-center gap-2">
      <CheckIcon />
      <span>
        Done! {{ created }} candidates added
        <span v-if="skipped > 0">({{ skipped }} skipped)</span>
      </span>
    </div>

    <!-- Error -->
    <div v-if="status === 'error'" class="text-red-600 flex items-center gap-2">
      <AlertIcon />
      <span>Error: {{ errorMessage }}</span>
    </div>
  </div>
</template>
```

### 4. Full page usage example

```vue
<!-- pages/jobs/[id]/add-candidates.vue -->
<script setup lang="ts">
const route = useRoute()
const jobId = Number(route.params.id)
const selectiveProcessId = ref<number | undefined>()

const progressRef = ref<InstanceType<typeof ApplyCollectionProgress>>()
const isSubmitting = ref(false)

async function handleAddCandidates(candidateIds: number[], processId: number, processStatus: string) {
  isSubmitting.value = true
  selectiveProcessId.value = processId

  // 1. Start listening BEFORE making the API call
  progressRef.value?.startListening()

  // 2. Fire the API request
  try {
    await api.post('/v1/users/applies/create_collection', {
      collections: candidateIds.map(id => ({
        candidate_id: id,
        reference_type: 'Candidate',
        reference_id: id,
      })),
      apply: {
        job_id: jobId,
        selective_process_id: processId,
        selective_process_status: processStatus,
      },
    })
  } catch (error) {
    console.error('Failed to start collection:', error)
    isSubmitting.value = false
  }
}

function onCompleted(applies: ApplyData[], skipped: number) {
  isSubmitting.value = false
  // applies contains full serialized apply objects with candidate data
  // You can use them to update the UI immediately without refetching
  console.log(`Added ${applies.length} candidates, ${skipped} skipped`)
}
</script>

<template>
  <div>
    <ApplyCollectionProgress
      ref="progressRef"
      :job-id="jobId"
      :selective-process-id="selectiveProcessId"
      @completed="onCompleted"
    />

    <button
      :disabled="isSubmitting"
      @click="handleAddCandidates(selectedIds, processId, 'Submission')"
    >
      Add {{ selectedIds.length }} Candidates
    </button>
  </div>
</template>
```

### 5. Using with SourcedProfileSourcing (from Sourcing results)

When adding candidates from sourcing results, use `reference_type: 'SourcedProfileSourcing'`:

```typescript
async function addSourcingCandidatesToJob(
  sourcedProfileSourcingIds: number[],
  jobId: number,
  selectiveProcessId: number,
  status: string = 'Submission'
) {
  progressRef.value?.startListening()

  await api.post('/v1/users/applies/create_collection', {
    collections: sourcedProfileSourcingIds.map(id => ({
      reference_type: 'SourcedProfileSourcing',
      reference_id: id,
    })),
    apply: {
      job_id: jobId,
      selective_process_id: selectiveProcessId,
      selective_process_status: status,
    },
  })
}
```

The backend will automatically convert `SourcedProfile` to `Candidate` if needed, and the channel will broadcast each conversion + apply creation step by step.

## Event Flow Diagram

```
Frontend                          Backend (Sidekiq)                    Frontend
   |                                    |                                 |
   |-- POST /create_collection -------->|                                 |
   |<-- { status: "processing" } -------|                                 |
   |                                    |                                 |
   |   subscribe(ApplyCollectionChannel)|                                 |
   |                                    |-- broadcast: started ---------->|
   |                                    |   { type: "started",            |
   |                                    |     total: 10 }                 |
   |                                    |                                 |
   |                                    |-- broadcast: processing_item -->|
   |                                    |   { current: 1, percent: 10 }   |
   |                                    |                                 |
   |                                    |-- broadcast: item_completed --->|
   |                                    |   { current: 1, created: 1,     |
   |                                    |     apply_id: 123 }             |
   |                                    |                                 |
   |                                    |   ... repeats for each item ... |
   |                                    |                                 |
   |                                    |-- broadcast: completed -------->|
   |                                    |   { created: 8, skipped: 2,     |
   |                                    |     percent: 100 }              |
   |                                    |                                 |
```

## Nuxt 3 Config

Add the WebSocket URL to your `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiWsUrl: process.env.API_WS_URL || 'ws://localhost:8080/cable',
    },
  },
})
```

## Important Notes

1. **Subscribe BEFORE the API call** — The job starts immediately after the HTTP response. Subscribe first to avoid missing the `started` event.
2. **Auto-cleanup** — The composable automatically unsubscribes on component unmount via `onBeforeUnmount`.
3. **Backward compatible** — The old `CollectionChannel` broadcasts are still emitted for existing consumers.
4. **Stream identifier** — The stream is `{user_id}_apply_collection_{job_id}_{selective_process_id}`. If no `selective_process_id` is provided, it's `{user_id}_apply_collection_{job_id}`.
