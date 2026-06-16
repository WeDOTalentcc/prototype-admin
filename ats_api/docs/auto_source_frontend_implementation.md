# Auto Source - Frontend Implementation Guide

## 🎯 Overview

This guide explains how to implement a **real-time loader/progress UI** for the Auto Source feature, which automatically searches and adds qualified candidates to a job in the background.

---

## 🔄 Process Flow

```
User clicks "Auto Source"
         ↓
POST /v1/users/jobs/:id/auto_source
         ↓
Frontend subscribes to SourcingChannel
         ↓
Backend starts searching (broadcasts events):
  1. auto_source_started       → "Searching for candidates..."
  2. profile_analyzed (multiple) → "Analyzing candidate X..."
  3. auto_source_batch_completed → "Batch done, found 10/30..."
  4. [repeat if target not reached]
  5. auto_source_finished       → "Complete! Added 30 candidates."
         ↓
Frontend updates progress bar/loader
         ↓
When finished, frontend can:
  - Request more pages (if max not reached)
  - Close loader and show results
```

---

## 📡 WebSocket Events

### Event Types

| Event | When | Phase |
|-------|------|-------|
| `auto_source_started` | Process begins | `searching` |
| `profile_analyzed` | Each candidate analyzed | `analyzing` |
| `auto_source_batch_completed` | Batch of pages done | `continuing` or `completed` |
| `auto_source_finished` | Max pages reached | `finished` |

---

## 🚀 API Endpoint

### POST `/v1/users/jobs/:id/auto_source`

**Request:**
```json
{
  "limit": 30,
  "min_score": 70
}
```

**Response:**
```json
{
  "success": true,
  "sourcing_id": 789,
  "uid": "abc-123-def",
  "status": "processing",
  "job_id": 456,
  "min_score_threshold": 70.0,
  "target_count": 30,
  "pagination": {
    "current_page": 1,
    "pages_to_search": 3,
    "max_page": 3
  },
  "subscription": {
    "channel": "SourcingChannel",
    "stream": "42_sourcing_789",
    "events": [
      "auto_source_started",
      "profile_analyzed",
      "auto_source_batch_completed",
      "auto_source_finished"
    ]
  },
  "message": "Auto Source started. Subscribe to channel for real-time updates."
}
```

---

## 📨 WebSocket Event Payloads

### 1. `auto_source_started`

Sent **immediately** when search begins.

```typescript
{
  type: "auto_source_started",
  sourcing_id: 789,
  job_id: 456,
  job_title: "Senior Ruby Developer",
  status: "searching",
  phase: "search",
  message: "Searching for qualified candidates...",
  progress: {
    current_page: 1,
    pages_this_batch: 3,
    max_page: 3,
    candidates_found: 0,
    candidates_added: 0,
    target: 30,
    remaining: 30,
    percentage: 0
  },
  timestamp: "2026-03-06T14:30:00.000Z"
}
```

**Frontend Action:**
- Show loader modal
- Display: "Searching for candidates... 0/30"

---

### 2. `profile_analyzed`

Sent for **each candidate** that passes AI analysis and gets added to the job.

```typescript
{
  type: "profile_analyzed",
  sourcing_id: 789,
  profile_id: 123,
  candidate_id: 456,
  candidate_name: "João Silva",
  score: 85.5,
  added_to_job: true,
  processed: 5,
  total: 90,
  percentage: 5,
  timestamp: "2026-03-06T14:30:15.000Z"
}
```

**Frontend Action:**
- Update progress bar
- Display: "Analyzing João Silva... 5/30 added"
- Increment counter

---

### 3. `auto_source_batch_completed`

Sent when a **batch of pages** is fully processed (search + analysis).

#### Scenario A: Target Reached ✅

```typescript
{
  type: "auto_source_batch_completed",
  sourcing_id: 789,
  job_id: 456,
  status: "completed",
  phase: "completed",
  message: "✅ Target reached! Added 30 candidates.",
  progress: {
    candidates_searched: 90,
    candidates_added: 30,
    target: 30,
    remaining: 0,
    percentage: 100,
    last_page: 3,
    max_pages: 10
  },
  completion: {
    target_reached: true,
    max_pages_reached: false,
    will_continue: false,
    can_request_more: false
  },
  timestamp: "2026-03-06T14:32:00.000Z"
}
```

**Frontend Action:**
- Show success message: "✅ Found 30 qualified candidates!"
- Close loader after 2s
- Refresh candidate list

---

#### Scenario B: Continuing Search 🔄

```typescript
{
  type: "auto_source_batch_completed",
  sourcing_id: 789,
  job_id: 456,
  status: "continuing",
  phase: "continuing",
  message: "🔄 Batch complete. Found 15/30, continuing search...",
  progress: {
    candidates_searched: 90,
    candidates_added: 15,
    target: 30,
    remaining: 15,
    percentage: 50,
    last_page: 3,
    max_pages: 10
  },
  completion: {
    target_reached: false,
    max_pages_reached: false,
    will_continue: true,
    can_request_more: true
  },
  timestamp: "2026-03-06T14:32:00.000Z"
}
```

**Frontend Action:**
- Update message: "Continuing search... 15/30 found"
- Keep loader open
- Wait for next batch

---

#### Scenario C: Max Pages Reached ⚠️

```typescript
{
  type: "auto_source_batch_completed",
  sourcing_id: 789,
  job_id: 456,
  status: "completed_partial",
  phase: "completed",
  message: "⚠️ Max pages reached. Added 18 of 30 candidates.",
  progress: {
    candidates_searched: 300,
    candidates_added: 18,
    target: 30,
    remaining: 12,
    percentage: 60,
    last_page: 10,
    max_pages: 10
  },
  completion: {
    target_reached: false,
    max_pages_reached: true,
    will_continue: false,
    can_request_more: false
  },
  timestamp: "2026-03-06T14:35:00.000Z"
}
```

**Frontend Action:**
- Show warning: "Found 18 candidates (target was 30)"
- Option: "Search with broader criteria"
- Close loader

---

### 4. `auto_source_finished`

Sent only if process stops due to max pages reached (fallback event).

```typescript
{
  type: "auto_source_finished",
  sourcing_id: 789,
  job_id: 456,
  status: "completed",
  phase: "finished",
  message: "Auto Source finished. Added 18 of 30 candidates (Max pages reached)",
  progress: {
    candidates_added: 18,
    target: 30,
    percentage: 60
  },
  completion: {
    reason: "Max pages reached",
    can_request_more: false
  },
  timestamp: "2026-03-06T14:35:00.000Z"
}
```

**Frontend Action:**
- Same as `auto_source_batch_completed` with `max_pages_reached: true`

---

## 🎨 Frontend Implementation

### Vue 3 + Composition API Example

```vue
<template>
  <div>
    <!-- Trigger Button -->
    <v-btn @click="startAutoSource" :loading="isProcessing">
      🤖 Auto Source
    </v-btn>

    <!-- Loader Modal -->
    <v-dialog v-model="showLoader" persistent max-width="500">
      <v-card>
        <v-card-title>
          {{ loaderPhase === 'searching' ? '🔍' : '🧠' }}
          {{ loaderTitle }}
        </v-card-title>

        <v-card-text>
          <!-- Progress Bar -->
          <v-progress-linear
            :model-value="progress.percentage"
            height="25"
            rounded
            color="primary"
          >
            <strong>{{ progress.candidates_added }} / {{ progress.target }}</strong>
          </v-progress-linear>

          <!-- Status Message -->
          <div class="mt-4 text-center">
            <v-icon v-if="isCompleted" color="success" size="48">
              mdi-check-circle
            </v-icon>
            <v-progress-circular
              v-else
              indeterminate
              color="primary"
              size="32"
            />
            <p class="mt-2">{{ statusMessage }}</p>
          </div>

          <!-- Details -->
          <v-chip-group class="mt-4">
            <v-chip size="small">
              📄 Searched: {{ progress.candidates_searched }}
            </v-chip>
            <v-chip size="small" color="success">
              ✅ Added: {{ progress.candidates_added }}
            </v-chip>
            <v-chip size="small">
              📊 Page: {{ progress.last_page }}/{{ progress.max_pages }}
            </v-chip>
          </v-chip-group>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            v-if="isCompleted"
            color="primary"
            @click="closeLoader"
          >
            {{ canRequestMore ? 'Done' : 'Close' }}
          </v-btn>
          <v-btn
            v-if="canRequestMore && isCompleted"
            color="secondary"
            @click="requestMoreCandidates"
          >
            🔄 Search More Pages
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAutoSourceChannel } from '@/composables/useAutoSourceChannel'

const props = defineProps({
  jobId: { type: Number, required: true }
})

// State
const isProcessing = ref(false)
const showLoader = ref(false)
const loaderPhase = ref('searching') // 'searching', 'analyzing', 'completed'
const statusMessage = ref('')
const isCompleted = ref(false)
const canRequestMore = ref(false)
const currentSourcingId = ref(null)

const progress = ref({
  candidates_found: 0,
  candidates_added: 0,
  candidates_searched: 0,
  target: 0,
  remaining: 0,
  percentage: 0,
  last_page: 0,
  max_pages: 10
})

// Computed
const loaderTitle = computed(() => {
  if (isCompleted.value) return '✅ Auto Source Complete'
  if (loaderPhase.value === 'searching') return '🔍 Searching Candidates'
  if (loaderPhase.value === 'analyzing') return '🧠 Analyzing Profiles'
  return 'Processing...'
})

// WebSocket Channel
const { subscribe, unsubscribe } = useAutoSourceChannel()

// Event Handlers
const handleAutoSourceStarted = (event) => {
  console.log('[AutoSource] Started:', event)
  loaderPhase.value = 'search'
  statusMessage.value = event.message
  progress.value = event.progress
  showLoader.value = true
  isCompleted.value = false
}

const handleProfileAnalyzed = (event) => {
  console.log('[AutoSource] Profile analyzed:', event)
  loaderPhase.value = 'analyzing'
  statusMessage.value = `Analyzing ${event.candidate_name}...`
  progress.value.candidates_added = event.processed
  progress.value.percentage = event.percentage
}

const handleBatchCompleted = (event) => {
  console.log('[AutoSource] Batch completed:', event)
  
  progress.value = event.progress
  statusMessage.value = event.message
  canRequestMore.value = event.completion.can_request_more

  if (event.completion.target_reached || event.completion.max_pages_reached) {
    isCompleted.value = true
    loaderPhase.value = 'completed'
  } else if (event.completion.will_continue) {
    statusMessage.value += ' ⏳'
  }
}

const handleAutoSourceFinished = (event) => {
  console.log('[AutoSource] Finished:', event)
  progress.value = { ...progress.value, ...event.progress }
  statusMessage.value = event.message
  isCompleted.value = true
  loaderPhase.value = 'completed'
  canRequestMore.value = event.completion.can_request_more
}

// Actions
const startAutoSource = async () => {
  isProcessing.value = true

  try {
    const response = await fetch(`/v1/users/jobs/${props.jobId}/auto_source`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        limit: 30,
        min_score: 70
      })
    })

    const data = await response.json()

    if (!data.success) {
      alert(data.error)
      return
    }

    currentSourcingId.value = data.sourcing_id
    progress.value.target = data.target_count

    // Subscribe to WebSocket
    subscribe(data.sourcing_id, {
      onAutoSourceStarted: handleAutoSourceStarted,
      onProfileAnalyzed: handleProfileAnalyzed,
      onBatchCompleted: handleBatchCompleted,
      onAutoSourceFinished: handleAutoSourceFinished
    })

  } catch (error) {
    console.error('Failed to start Auto Source:', error)
    alert('Failed to start Auto Source')
  } finally {
    isProcessing.value = false
  }
}

const closeLoader = () => {
  showLoader.value = false
  unsubscribe(currentSourcingId.value)
  // Refresh candidate list
  emit('candidatesAdded')
}

const requestMoreCandidates = async () => {
  // Start new Auto Source request
  await startAutoSource()
}

// Cleanup
onUnmounted(() => {
  if (currentSourcingId.value) {
    unsubscribe(currentSourcingId.value)
  }
})
</script>
```

---

### Composable: `useAutoSourceChannel.ts`

```typescript
import { inject } from 'vue'

export function useAutoSourceChannel() {
  const cable = inject('$cable') // ActionCable instance

  let subscription = null

  const subscribe = (sourcingId, callbacks) => {
    const userId = getUserId() // Get from store/auth

    subscription = cable.subscriptions.create(
      {
        channel: 'SourcingChannel',
        sourcing_id: sourcingId
      },
      {
        connected() {
          console.log(`[SourcingChannel] Connected: sourcing_${sourcingId}`)
        },

        received(data) {
          console.log('[SourcingChannel] Received:', data)

          switch (data.type) {
            case 'auto_source_started':
              callbacks.onAutoSourceStarted?.(data)
              break

            case 'profile_analyzed':
              callbacks.onProfileAnalyzed?.(data)
              break

            case 'auto_source_batch_completed':
              callbacks.onBatchCompleted?.(data)
              break

            case 'auto_source_finished':
              callbacks.onAutoSourceFinished?.(data)
              break

            default:
              console.warn('[SourcingChannel] Unknown event:', data.type)
          }
        },

        disconnected() {
          console.log('[SourcingChannel] Disconnected')
        }
      }
    )
  }

  const unsubscribe = (sourcingId) => {
    if (subscription) {
      subscription.unsubscribe()
      subscription = null
      console.log(`[SourcingChannel] Unsubscribed from sourcing_${sourcingId}`)
    }
  }

  return {
    subscribe,
    unsubscribe
  }
}
```

---

## 🎯 Requesting More Pages

If `can_request_more: true` in completion event, user can trigger another search:

```typescript
const requestMorePages = async () => {
  // Simply call the same endpoint again
  const response = await fetch(`/v1/users/jobs/${jobId}/auto_source`, {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      limit: 30,  // Can request more
      min_score: 70
    })
  })

  // Backend automatically continues from last page
  // Metadata tracks progress: last_page, total_added, etc.
}
```

**Backend behavior:**
- Checks `auto_source_metadata.last_page`
- Continues from next page (e.g., page 4-6 if last was 3)
- Respects 10-page total limit

---

## 📊 Loader States

### State Machine

```
IDLE
  ↓ (user clicks "Auto Source")
REQUESTING
  ↓ (API responds)
SEARCHING (auto_source_started)
  ↓ (profiles being found)
ANALYZING (profile_analyzed)
  ↓ (all profiles analyzed)
CONTINUING (auto_source_batch_completed, will_continue: true)
  ↓ (next batch starts)
SEARCHING → ANALYZING → CONTINUING
  ↓ (target reached OR max pages)
COMPLETED (auto_source_batch_completed, status: completed)
  ↓ (user closes or requests more)
IDLE
```

---

## 🎨 UI/UX Recommendations

### Progress Bar

```vue
<!-- Linear with percentage -->
<v-progress-linear
  :model-value="percentage"
  :buffer-value="percentage + 10"
  height="30"
  color="success"
  striped
  rounded
>
  <strong class="text-white">{{ added }}/{{ target }}</strong>
</v-progress-linear>
```

### Status Messages

| Phase | Icon | Message |
|-------|------|---------|
| Starting | 🚀 | "Starting Auto Source..." |
| Searching | 🔍 | "Searching candidates... page 1-3" |
| Analyzing | 🧠 | "Analyzing João Silva (score: 85%)" |
| Continuing | 🔄 | "Found 15/30, searching more pages..." |
| Completed | ✅ | "Added 30 qualified candidates!" |
| Partial | ⚠️ | "Added 18 of 30 (max pages reached)" |

### Animations

```css
/* Pulse animation for loader */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.searching-indicator {
  animation: pulse 1.5s ease-in-out infinite;
}

/* Success animation */
@keyframes checkmark {
  0% { transform: scale(0); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.completed-icon {
  animation: checkmark 0.5s ease-out;
}
```

---

## 🐛 Error Handling

### Scenarios

| Error | When | Frontend Action |
|-------|------|----------------|
| `max_pages_reached` | 10 pages searched | Show partial result, offer to adjust filters |
| WebSocket disconnect | Connection lost | Show "Reconnecting..." or fallback to polling |
| No candidates found | Low match threshold | Suggest lowering min_score |
| API error | 4xx/5xx response | Show error toast, allow retry |

### Example

```typescript
const handleError = (error) => {
  if (error.type === 'max_pages_reached') {
    showDialog({
      title: 'Partial Results',
      message: `Found ${progress.added} of ${progress.target} candidates.`,
      actions: [
        { label: 'Done', action: closeLoader },
        { label: 'Lower Criteria', action: adjustFilters }
      ]
    })
  }
}
```

---

## 📱 Mobile Considerations

- Use bottom sheet instead of modal
- Show simplified progress (percentage only)
- Allow background processing with notification

```vue
<!-- Mobile optimized -->
<v-bottom-sheet v-model="showLoader" persistent>
  <v-card>
    <v-card-title class="text-center">
      🤖 Auto Sourcing
    </v-card-title>
    <v-card-text>
      <v-progress-circular
        :model-value="percentage"
        size="100"
        width="10"
        color="primary"
      >
        {{ percentage }}%
      </v-progress-circular>
      <p class="mt-4">{{ added }} / {{ target }} candidates</p>
    </v-card-text>
  </v-card>
</v-bottom-sheet>
```

---

## 🧪 Testing

### Manual Testing

1. **Start Auto Source** (target: 10, min_score: 70)
2. **Watch events in console**
3. **Verify progress bar updates**
4. **Check completion message**
5. **Test "Request More" button**

### Automated Testing

```typescript
// Vitest + Vue Test Utils
describe('AutoSourceLoader', () => {
  it('shows loader when auto source starts', async () => {
    const wrapper = mount(AutoSourceButton, { props: { jobId: 123 } })
    
    await wrapper.find('button').trigger('click')
    
    // Mock WebSocket event
    emitEvent('auto_source_started', { progress: { target: 30 } })
    
    await nextTick()
    
    expect(wrapper.find('.loader').exists()).toBe(true)
    expect(wrapper.text()).toContain('0 / 30')
  })

  it('updates progress on profile_analyzed', async () => {
    // ... test implementation
  })

  it('closes loader when completed', async () => {
    // ... test implementation
  })
})
```

---

## 🚀 Performance Tips

1. **Debounce UI updates** if receiving many `profile_analyzed` events
2. **Use virtual scrolling** if showing candidate list during process
3. **Lazy load avatar images** in progress cards
4. **Cancel previous subscription** when starting new Auto Source

```typescript
// Debounce progress updates
const debouncedUpdate = useDebounceFn((event) => {
  progress.value = event.progress
}, 300)

const handleProfileAnalyzed = (event) => {
  debouncedUpdate(event)
}
```

---

## 📚 Related Documentation

- [auto_source_pagination.md](./auto_source_pagination.md) - Backend pagination logic
- [auto_source_kanban_websocket_integration.md](./auto_source_kanban_websocket_integration.md) - Kanban integration
- [SourcingChannel API](../app/channels/sourcing_channel.rb) - WebSocket channel

---

## 🎉 Summary

**Checklist for implementation:**

- ✅ API call to `/v1/users/jobs/:id/auto_source`
- ✅ Subscribe to `SourcingChannel` with sourcing_id
- ✅ Handle 4 event types: `started`, `profile_analyzed`, `batch_completed`, `finished`
- ✅ Show progress bar (candidates_added / target)
- ✅ Display status messages per phase
- ✅ Close loader when completed
- ✅ Allow "Request More Pages" if not at max
- ✅ Handle errors gracefully

**Expected result:**
A smooth, real-time UI that keeps users informed throughout the Auto Source process, with clear status messages and the ability to request more candidates if needed. 🚀
