# ApplyCollectionChannel - Frontend Integration Guide

## Overview

This document explains how to connect to the `ApplyCollectionChannel` WebSocket from a Vue 3 + Nuxt + Vuetify frontend to track real-time progress when adding candidates to a selective process (kanban column).

## WebSocket Connection

### Base URL

```
ws://localhost:3000/cable?auth_token=<JWT_TOKEN>
# Production:
wss://api.yourdomain.com/cable?auth_token=<JWT_TOKEN>
```

### Authentication

The WebSocket connection requires a valid JWT token passed as `auth_token` query parameter.

## Channel Subscription

### Channel Name: `ApplyCollectionChannel`

### Required Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | Integer | Yes | The job ID where candidates are being added |
| `selective_process_id` | Integer | No | Optional: specific selective process ID for narrower subscription |

### Subscription Message Format

```json
{
  "command": "subscribe",
  "identifier": "{\"channel\":\"ApplyCollectionChannel\",\"job_id\":1827,\"selective_process_id\":21790}"
}
```

## Event Types

The channel broadcasts the following event types:

### 1. `started`

Broadcast when the collection process begins.

```typescript
interface StartedEvent {
  type: 'started';
  timestamp: string; // ISO8601
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  total: number;
  message: string;
}
```

**Example:**
```json
{
  "type": "started",
  "timestamp": "2026-02-17T19:45:00.000Z",
  "job_id": 1827,
  "selective_process_id": 21790,
  "selective_process_name": "Rejected by Client",
  "selective_process_status": "Rejected by Client",
  "total": 7,
  "message": "Iniciando processamento de 7 candidatos"
}
```

### 2. `processing_item`

Broadcast when starting to process each item.

```typescript
interface ProcessingItemEvent {
  type: 'processing_item';
  timestamp: string;
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  current: number;
  total: number;
  percent: number;
  reference_type: string;
  reference_id: string;
  message: string;
}
```

**Example:**
```json
{
  "type": "processing_item",
  "timestamp": "2026-02-17T19:45:01.000Z",
  "job_id": 1827,
  "selective_process_id": 21790,
  "selective_process_name": "Rejected by Client",
  "selective_process_status": "Rejected by Client",
  "current": 3,
  "total": 7,
  "percent": 43,
  "reference_type": "SourcedProfileSourcing",
  "reference_id": "3872",
  "message": "Processando item 3 de 7..."
}
```

### 3. `item_completed`

Broadcast when a candidate is successfully added.

```typescript
interface ItemCompletedEvent {
  type: 'item_completed';
  timestamp: string;
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  current: number;
  total: number;
  created: number;
  skipped: number;
  percent: number;
  apply_id: number;
  candidate_id: number;
  candidate_name: string;
  message: string;
  apply: ApplyAttributes; // Full apply object with all attributes
}

interface ApplyAttributes {
  id: number;
  candidate_id: number;
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  name: string;
  email: string;
  phone: string;
  avatar_url: string;
  // ... all other apply attributes
}
```

**Example:**
```json
{
  "type": "item_completed",
  "timestamp": "2026-02-17T19:45:02.000Z",
  "job_id": 1827,
  "selective_process_id": 21790,
  "selective_process_name": "Rejected by Client",
  "selective_process_status": "Rejected by Client",
  "current": 3,
  "total": 7,
  "created": 3,
  "skipped": 0,
  "percent": 43,
  "apply_id": 12149,
  "candidate_id": 8770,
  "candidate_name": "João Silva",
  "message": "Candidato João Silva adicionado",
  "apply": {
    "id": 12149,
    "candidate_id": 8770,
    "job_id": 1827,
    "selective_process_id": 21790,
    "selective_process_name": "Rejected by Client",
    "selective_process_status": "Rejected by Client",
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "+55 11 99999-9999"
    // ... more attributes
  }
}
```

### 4. `item_skipped`

Broadcast when an item is skipped (e.g., candidate not found).

```typescript
interface ItemSkippedEvent {
  type: 'item_skipped';
  timestamp: string;
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  current: number;
  total: number;
  created: number;
  skipped: number;
  percent: number;
  reason: string;
  message: string;
}
```

### 5. `completed`

Broadcast when all items have been processed.

```typescript
interface CompletedEvent {
  type: 'completed';
  timestamp: string;
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  total: number;
  created: number;
  skipped: number;
  failed: number;
  percent: 100;
  message: string;
  applies: ApplyAttributes[]; // All created applies
}
```

**Example:**
```json
{
  "type": "completed",
  "timestamp": "2026-02-17T19:45:06.000Z",
  "job_id": 1827,
  "selective_process_id": 21790,
  "selective_process_name": "Rejected by Client",
  "selective_process_status": "Rejected by Client",
  "total": 7,
  "created": 7,
  "skipped": 0,
  "failed": 0,
  "percent": 100,
  "message": "Processamento concluído: 7 candidatos adicionados",
  "applies": [ /* array of apply objects */ ]
}
```

### 6. `error`

Broadcast if a fatal error occurs.

```typescript
interface ErrorEvent {
  type: 'error';
  timestamp: string;
  job_id: number;
  selective_process_id: number;
  selective_process_name: string;
  selective_process_status: string;
  message: string;
}
```

---

## Vue 3 + Nuxt Implementation

### 1. Install ActionCable Client

```bash
npm install @rails/actioncable
# or
yarn add @rails/actioncable
```

### 2. Create Composable: `useApplyCollectionChannel.ts`

```typescript
// composables/useApplyCollectionChannel.ts
import { ref, onUnmounted } from 'vue'
import { createConsumer, Subscription } from '@rails/actioncable'

interface ApplyCollectionEvent {
  type: 'started' | 'processing_item' | 'item_completed' | 'item_skipped' | 'completed' | 'error'
  timestamp: string
  job_id: number
  selective_process_id: number
  selective_process_name: string
  selective_process_status: string
  total?: number
  current?: number
  created?: number
  skipped?: number
  failed?: number
  percent?: number
  apply_id?: number
  candidate_id?: number
  candidate_name?: string
  message?: string
  apply?: Record<string, any>
  applies?: Record<string, any>[]
}

interface UseApplyCollectionChannelOptions {
  jobId: number
  selectiveProcessId?: number
  onStarted?: (event: ApplyCollectionEvent) => void
  onProcessingItem?: (event: ApplyCollectionEvent) => void
  onItemCompleted?: (event: ApplyCollectionEvent) => void
  onItemSkipped?: (event: ApplyCollectionEvent) => void
  onCompleted?: (event: ApplyCollectionEvent) => void
  onError?: (event: ApplyCollectionEvent) => void
}

export function useApplyCollectionChannel(options: UseApplyCollectionChannelOptions) {
  const isConnected = ref(false)
  const isProcessing = ref(false)
  const progress = ref(0)
  const currentMessage = ref('')
  const totalItems = ref(0)
  const processedItems = ref(0)
  const createdCount = ref(0)
  const skippedCount = ref(0)
  const failedCount = ref(0)
  
  let subscription: Subscription | null = null
  let consumer: ReturnType<typeof createConsumer> | null = null

  const connect = (authToken: string) => {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:3000'}/cable?auth_token=${authToken}`
    consumer = createConsumer(wsUrl)
    
    const channelParams: Record<string, any> = {
      channel: 'ApplyCollectionChannel',
      job_id: options.jobId
    }
    
    if (options.selectiveProcessId) {
      channelParams.selective_process_id = options.selectiveProcessId
    }

    subscription = consumer.subscriptions.create(channelParams, {
      connected() {
        console.log('[ApplyCollectionChannel] Connected')
        isConnected.value = true
      },

      disconnected() {
        console.log('[ApplyCollectionChannel] Disconnected')
        isConnected.value = false
      },

      rejected() {
        console.error('[ApplyCollectionChannel] Subscription rejected')
        isConnected.value = false
      },

      received(data: ApplyCollectionEvent) {
        console.log('[ApplyCollectionChannel] Received:', data)
        handleEvent(data)
      }
    })
  }

  const handleEvent = (event: ApplyCollectionEvent) => {
    currentMessage.value = event.message || ''
    
    switch (event.type) {
      case 'started':
        isProcessing.value = true
        totalItems.value = event.total || 0
        processedItems.value = 0
        createdCount.value = 0
        skippedCount.value = 0
        failedCount.value = 0
        progress.value = 0
        options.onStarted?.(event)
        break

      case 'processing_item':
        processedItems.value = event.current || 0
        progress.value = event.percent || 0
        options.onProcessingItem?.(event)
        break

      case 'item_completed':
        processedItems.value = event.current || 0
        createdCount.value = event.created || 0
        skippedCount.value = event.skipped || 0
        progress.value = event.percent || 0
        options.onItemCompleted?.(event)
        break

      case 'item_skipped':
        processedItems.value = event.current || 0
        skippedCount.value = event.skipped || 0
        progress.value = event.percent || 0
        options.onItemSkipped?.(event)
        break

      case 'completed':
        isProcessing.value = false
        progress.value = 100
        createdCount.value = event.created || 0
        skippedCount.value = event.skipped || 0
        failedCount.value = event.failed || 0
        options.onCompleted?.(event)
        break

      case 'error':
        isProcessing.value = false
        options.onError?.(event)
        break
    }
  }

  const disconnect = () => {
    if (subscription) {
      subscription.unsubscribe()
      subscription = null
    }
    if (consumer) {
      consumer.disconnect()
      consumer = null
    }
    isConnected.value = false
    isProcessing.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    // State
    isConnected,
    isProcessing,
    progress,
    currentMessage,
    totalItems,
    processedItems,
    createdCount,
    skippedCount,
    failedCount,
    
    // Methods
    connect,
    disconnect
  }
}
```

### 3. Kanban Component with Loading Spinner

```vue
<!-- components/KanbanColumn.vue -->
<template>
  <v-card class="kanban-column" :loading="isLoading">
    <v-card-title class="d-flex align-center">
      <span>{{ column.name }}</span>
      <v-spacer />
      <v-badge v-if="!isLoading" :content="candidates.length" color="primary" />
      
      <!-- Loading Spinner -->
      <v-progress-circular
        v-if="isLoading"
        :model-value="progress"
        :size="32"
        :width="3"
        color="primary"
      >
        <span class="text-caption">{{ progress }}%</span>
      </v-progress-circular>
    </v-card-title>

    <!-- Progress Bar during processing -->
    <v-progress-linear
      v-if="isLoading"
      :model-value="progress"
      color="primary"
      height="4"
    />
    
    <!-- Status Message -->
    <v-alert
      v-if="isLoading && statusMessage"
      type="info"
      density="compact"
      class="ma-2"
    >
      {{ statusMessage }}
    </v-alert>

    <v-card-text class="pa-2">
      <draggable
        v-model="candidates"
        :group="{ name: 'candidates', pull: true, put: true }"
        item-key="id"
        class="kanban-items"
        @end="onDragEnd"
      >
        <template #item="{ element }">
          <CandidateCard
            :candidate="element"
            :key="element.id"
            :class="{ 'newly-added': newlyAddedIds.includes(element.id) }"
          />
        </template>
      </draggable>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useApplyCollectionChannel } from '~/composables/useApplyCollectionChannel'
import { useAuthStore } from '~/stores/auth'

const props = defineProps<{
  column: {
    id: number
    name: string
    status: string
  }
  jobId: number
  initialCandidates: any[]
}>()

const emit = defineEmits<{
  (e: 'candidate-added', apply: any): void
  (e: 'candidates-updated', candidates: any[]): void
}>()

const authStore = useAuthStore()
const candidates = ref([...props.initialCandidates])
const newlyAddedIds = ref<number[]>([])
const statusMessage = ref('')

// Setup WebSocket channel
const {
  isConnected,
  isProcessing: isLoading,
  progress,
  currentMessage,
  createdCount,
  connect,
  disconnect
} = useApplyCollectionChannel({
  jobId: props.jobId,
  selectiveProcessId: props.column.id,
  
  onStarted(event) {
    statusMessage.value = event.message || 'Iniciando...'
  },
  
  onProcessingItem(event) {
    statusMessage.value = event.message || `Processando ${event.current}/${event.total}...`
  },
  
  onItemCompleted(event) {
    // Check if this apply belongs to this column
    if (event.selective_process_id === props.column.id && event.apply) {
      // Add to candidates list if not already present
      const exists = candidates.value.some(c => c.id === event.apply_id)
      if (!exists) {
        candidates.value.push(event.apply)
        newlyAddedIds.value.push(event.apply_id!)
        
        // Remove highlight after 3 seconds
        setTimeout(() => {
          newlyAddedIds.value = newlyAddedIds.value.filter(id => id !== event.apply_id)
        }, 3000)
        
        emit('candidate-added', event.apply)
      }
    }
    statusMessage.value = event.message || ''
  },
  
  onCompleted(event) {
    statusMessage.value = event.message || 'Concluído!'
    
    // Clear status message after 3 seconds
    setTimeout(() => {
      statusMessage.value = ''
    }, 3000)
    
    emit('candidates-updated', candidates.value)
  },
  
  onError(event) {
    statusMessage.value = `Erro: ${event.message}`
  }
})

// Connect on mount
onMounted(() => {
  if (authStore.token) {
    connect(authStore.token)
  }
})

// Disconnect on unmount
onUnmounted(() => {
  disconnect()
})

// Watch for auth token changes
watch(() => authStore.token, (newToken) => {
  if (newToken) {
    disconnect()
    connect(newToken)
  }
})

// Drag and drop handler
const onDragEnd = (event: any) => {
  // Handle drag end - update candidate position
}
</script>

<style scoped>
.kanban-column {
  min-height: 400px;
  background: #f5f5f5;
}

.kanban-items {
  min-height: 300px;
}

.newly-added {
  animation: highlight 3s ease-out;
}

@keyframes highlight {
  0% {
    background-color: rgba(76, 175, 80, 0.3);
    transform: scale(1.02);
  }
  100% {
    background-color: transparent;
    transform: scale(1);
  }
}
</style>
```

### 4. Kanban Board with Multiple Columns

```vue
<!-- components/KanbanBoard.vue -->
<template>
  <v-container fluid>
    <!-- Global Processing Indicator -->
    <v-snackbar
      v-model="showGlobalProgress"
      :timeout="-1"
      location="bottom"
      color="primary"
    >
      <div class="d-flex align-center">
        <v-progress-circular
          :model-value="globalProgress"
          :size="24"
          :width="2"
          class="mr-3"
        />
        <span>{{ globalMessage }}</span>
      </div>
    </v-snackbar>

    <v-row>
      <v-col
        v-for="column in selectiveProcesses"
        :key="column.id"
        cols="12"
        md="3"
      >
        <KanbanColumn
          :column="column"
          :job-id="jobId"
          :initial-candidates="getCandidatesForColumn(column.id)"
          @candidate-added="onCandidateAdded"
          @candidates-updated="onCandidatesUpdated"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  jobId: number
  selectiveProcesses: Array<{
    id: number
    name: string
    status: string
  }>
  applies: any[]
}>()

const showGlobalProgress = ref(false)
const globalProgress = ref(0)
const globalMessage = ref('')

const getCandidatesForColumn = (selectiveProcessId: number) => {
  return props.applies.filter(a => a.selective_process_id === selectiveProcessId)
}

const onCandidateAdded = (apply: any) => {
  console.log('Candidate added:', apply)
}

const onCandidatesUpdated = (candidates: any[]) => {
  console.log('Candidates updated:', candidates)
}
</script>
```

### 5. Alternative: Using Pinia Store for Global State

```typescript
// stores/applyCollection.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createConsumer, Subscription } from '@rails/actioncable'

export const useApplyCollectionStore = defineStore('applyCollection', () => {
  const isConnected = ref(false)
  const isProcessing = ref(false)
  const progress = ref(0)
  const message = ref('')
  const pendingApplies = ref<Map<number, any[]>>(new Map()) // key: selective_process_id
  
  let subscription: Subscription | null = null
  let consumer: ReturnType<typeof createConsumer> | null = null

  function connect(authToken: string, jobId: number, selectiveProcessId?: number) {
    if (consumer) {
      disconnect()
    }

    const wsUrl = `${import.meta.env.VITE_WS_URL}/cable?auth_token=${authToken}`
    consumer = createConsumer(wsUrl)

    const params: Record<string, any> = {
      channel: 'ApplyCollectionChannel',
      job_id: jobId
    }
    
    if (selectiveProcessId) {
      params.selective_process_id = selectiveProcessId
    }

    subscription = consumer.subscriptions.create(params, {
      connected() {
        isConnected.value = true
      },
      disconnected() {
        isConnected.value = false
      },
      received(data: any) {
        handleMessage(data)
      }
    })
  }

  function handleMessage(data: any) {
    progress.value = data.percent || 0
    message.value = data.message || ''

    switch (data.type) {
      case 'started':
        isProcessing.value = true
        break
        
      case 'item_completed':
        if (data.apply && data.selective_process_id) {
          const spId = data.selective_process_id
          if (!pendingApplies.value.has(spId)) {
            pendingApplies.value.set(spId, [])
          }
          pendingApplies.value.get(spId)!.push(data.apply)
        }
        break
        
      case 'completed':
        isProcessing.value = false
        break
        
      case 'error':
        isProcessing.value = false
        break
    }
  }

  function getNewAppliesForProcess(selectiveProcessId: number): any[] {
    return pendingApplies.value.get(selectiveProcessId) || []
  }

  function clearPendingApplies(selectiveProcessId: number) {
    pendingApplies.value.delete(selectiveProcessId)
  }

  function disconnect() {
    subscription?.unsubscribe()
    consumer?.disconnect()
    subscription = null
    consumer = null
    isConnected.value = false
    isProcessing.value = false
  }

  return {
    isConnected,
    isProcessing,
    progress,
    message,
    connect,
    disconnect,
    getNewAppliesForProcess,
    clearPendingApplies
  }
})
```

---

## Testing the Connection

### 1. Browser Console Test

```javascript
// Test in browser console
import { createConsumer } from '@rails/actioncable'

const token = 'YOUR_JWT_TOKEN'
const consumer = createConsumer(`ws://localhost:3000/cable?auth_token=${token}`)

const subscription = consumer.subscriptions.create(
  { channel: 'ApplyCollectionChannel', job_id: 1827, selective_process_id: 21790 },
  {
    connected() { console.log('Connected!') },
    disconnected() { console.log('Disconnected!') },
    rejected() { console.log('Rejected!') },
    received(data) { console.log('Received:', data) }
  }
)
```

### 2. Check Backend Logs

When connected, you should see in Rails logs:

```
[ApplyCollectionChannel] User#1 subscribed to 1_apply_collection_1827_21790
```

When processing:

```
[CreateCollectionFromListJob] Starting processing 7 items for SP#21790 (Rejected by Client)
[CreateCollectionFromListJob] Processing 1/7: SourcedProfileSourcing#3870
```

---

## Troubleshooting

### Connection Issues

1. **Rejected subscription**: Check that `auth_token` is valid and `job_id` is provided
2. **No messages received**: Verify the stream identifier matches between channel and job:
   - Channel: `{user_id}_apply_collection_{job_id}_{selective_process_id?}`
   - Job uses same format
3. **CORS errors**: Ensure ActionCable allowed origins in `config/cable.yml`

### Common Fixes

```yaml
# config/cable.yml
development:
  adapter: redis
  url: redis://localhost:6379/1
  allowed_request_origins:
    - http://localhost:3000
    - http://localhost:8080
    - /http:\/\/localhost:.*/
```

### Debug Mode

Add to your Vue component:

```typescript
const DEBUG = true

function logEvent(event: string, data: any) {
  if (DEBUG) {
    console.log(`[ApplyCollectionChannel] ${event}:`, data)
  }
}
```

---

## Summary

| Event | When | Key Data |
|-------|------|----------|
| `started` | Process begins | `total`, `selective_process_name` |
| `processing_item` | Each item starts | `current`, `percent`, `message` |
| `item_completed` | Candidate added | `apply`, `candidate_name` |
| `item_skipped` | Item skipped | `reason`, `message` |
| `completed` | All done | `created`, `skipped`, `applies[]` |
| `error` | Fatal error | `message` |

The `selective_process_id`, `selective_process_name`, and `job_id` are included in **every event** for easy filtering and routing to the correct kanban column.
