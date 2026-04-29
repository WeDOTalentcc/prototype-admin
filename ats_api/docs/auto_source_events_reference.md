# Auto Source - WebSocket Events Reference

Quick reference guide for all Auto Source broadcast events.

---

## 📡 Channel Information

**Channel:** `SourcingChannel`  
**Stream:** `{user_id}_sourcing_{sourcing_id}`  
**Protocol:** ActionCable (WebSocket)

---

## 📨 Event Types

### 1. `auto_source_started`

**When:** Immediately when Auto Source process begins  
**Sent by:** `AutoSourcePaginationService`

```typescript
{
  type: "auto_source_started",
  sourcing_id: number,
  job_id: number,
  job_title: string,
  status: "searching",
  phase: "search",
  message: "Searching for qualified candidates...",
  progress: {
    current_page: number,        // Starting page (e.g., 1)
    pages_this_batch: number,    // Pages in this batch (1-3)
    max_page: number,             // Last page of batch
    candidates_found: 0,          // Always 0 at start
    candidates_added: number,     // Total added so far
    target: number,               // Target count (from request)
    remaining: number,            // target - candidates_added
    percentage: number            // (candidates_added / target) * 100
  },
  timestamp: string               // ISO 8601
}
```

**Frontend Action:**
- Show loader/modal
- Initialize progress bar
- Display: "Searching for candidates... 0/{target}"

---

### 2. `profile_analyzed`

**When:** Each time a candidate passes AI analysis (score >= threshold)  
**Sent by:** `AiAnalysisJob` (via `AutoAddCandidateService`)  
**Frequency:** Multiple times per sourcing (up to ~90 times for 3 pages)

```typescript
{
  type: "profile_analyzed",
  sourcing_id: number,
  profile_id: number,
  candidate_id: number,
  candidate_name: string,
  score: number,                  // AI match score (0-100)
  added_to_job: boolean,          // true if score >= threshold
  processed: number,              // Total profiles analyzed so far
  total: number,                  // Total profiles to analyze
  percentage: number,             // (processed / total) * 100
  timestamp: string
}
```

**Frontend Action:**
- Update progress bar
- Display: "Analyzing {candidate_name}... {processed}/{target} added"
- Increment counter

---

### 3. `auto_source_batch_completed`

**When:** After a batch of pages is fully processed (search + AI analysis)  
**Sent by:** `AutoSourceMetadataUpdateService`  
**Status Values:**
- `"completed"` - Target reached
- `"completed_partial"` - Max pages reached, target not met
- `"continuing"` - Will automatically search more pages

```typescript
{
  type: "auto_source_batch_completed",
  sourcing_id: number,
  job_id: number,
  status: "completed" | "completed_partial" | "continuing",
  phase: "completed" | "continuing",
  message: string,                // Human-readable status
  progress: {
    candidates_searched: number,  // Total candidates searched (pages * 30)
    candidates_added: number,     // Total qualified candidates added
    target: number,               // Original target
    remaining: number,            // target - candidates_added
    percentage: number,           // (candidates_added / target) * 100
    last_page: number,            // Last page searched (cumulative)
    max_pages: 10                 // Hard limit
  },
  completion: {
    target_reached: boolean,      // true if candidates_added >= target
    max_pages_reached: boolean,   // true if last_page >= 10
    will_continue: boolean,       // true if triggering next batch
    can_request_more: boolean     // true if user can manually request more
  },
  timestamp: string
}
```

**Frontend Action:**

#### If `status: "completed"`
- Show success: "✅ Found {candidates_added} qualified candidates!"
- Close loader after 2s
- Refresh candidate list

#### If `status: "continuing"`
- Update message: "Continuing search... {candidates_added}/{target} found"
- Keep loader open
- Show spinner/pulse animation

#### If `status: "completed_partial"`
- Show warning: "Found {candidates_added} of {target} (max pages reached)"
- Offer to adjust filters or search again
- Show "Close" button

---

### 4. `auto_source_finished`

**When:** Process stops due to max pages reached (fallback event)  
**Sent by:** `AutoSourceContinuationJob`  
**Note:** Usually not needed if `batch_completed` is handled properly

```typescript
{
  type: "auto_source_finished",
  sourcing_id: number,
  job_id: number,
  status: "completed",
  phase: "finished",
  message: "Auto Source finished. Added X of Y candidates (reason)",
  progress: {
    candidates_added: number,
    target: number,
    percentage: number
  },
  completion: {
    reason: "Max pages reached" | "Target reached",
    can_request_more: boolean
  },
  timestamp: string
}
```

**Frontend Action:**
- Same as `auto_source_batch_completed` with appropriate status
- Show final summary

---

## 🔄 Event Flow Examples

### Example 1: Success (Target Reached)

```
1. auto_source_started
   {
     progress: { candidates_added: 0, target: 30, percentage: 0 },
     message: "Searching for qualified candidates..."
   }

2. profile_analyzed (x15)
   {
     candidate_name: "João Silva",
     score: 85.5,
     processed: 1,
     total: 90
   }
   ... (14 more)

3. auto_source_batch_completed
   {
     status: "completed",
     progress: { candidates_added: 30, target: 30, percentage: 100 },
     completion: { target_reached: true, will_continue: false },
     message: "✅ Target reached! Added 30 candidates."
   }
```

**Total Time:** ~2-5 minutes (depends on AI analysis speed)

---

### Example 2: Continuation (Multiple Batches)

```
1. auto_source_started
   {
     progress: { current_page: 1, pages_this_batch: 3, target: 50 }
   }

2. profile_analyzed (x10)
   ... 10 candidates added

3. auto_source_batch_completed
   {
     status: "continuing",
     progress: { candidates_added: 10, target: 50, remaining: 40 },
     completion: { will_continue: true },
     message: "🔄 Batch complete. Found 10/50, continuing search..."
   }

4. auto_source_started (new batch)
   {
     progress: { current_page: 4, pages_this_batch: 3, target: 50 }
   }

5. profile_analyzed (x25)
   ... 25 more candidates

6. auto_source_batch_completed
   {
     status: "continuing",
     progress: { candidates_added: 35, target: 50, remaining: 15 }
   }

7. auto_source_started (3rd batch)
   ...

8. auto_source_batch_completed
   {
     status: "completed",
     progress: { candidates_added: 52, target: 50, percentage: 100 }
   }
```

**Total Time:** ~6-15 minutes (3 batches × 2-5 min each)

---

### Example 3: Partial Result (Max Pages)

```
1. auto_source_started
   {
     progress: { current_page: 1, target: 100 }
   }

2. profile_analyzed (x18)
   ... only 18 qualified candidates in 10 pages

3. auto_source_batch_completed
   {
     status: "completed_partial",
     progress: {
       candidates_added: 18,
       target: 100,
       last_page: 10,
       percentage: 18
     },
     completion: {
       max_pages_reached: true,
       can_request_more: false
     },
     message: "⚠️ Max pages reached. Added 18 of 100 candidates."
   }
```

**Reason:** Either:
- Very high `min_score` threshold (80%+)
- Limited candidate pool
- Specific job requirements

---

## 🎯 Decision Tree

```
Receive Event
  ├─ auto_source_started
  │    └─> Show loader, init progress
  │
  ├─ profile_analyzed
  │    └─> Update progress bar, increment counter
  │
  ├─ auto_source_batch_completed
  │    ├─ status: "completed"
  │    │    └─> Show success, close loader (2s delay)
  │    │
  │    ├─ status: "continuing"
  │    │    └─> Update message, keep loader open
  │    │
  │    └─ status: "completed_partial"
  │         └─> Show warning, offer options
  │
  └─ auto_source_finished
       └─> Fallback: close loader, show summary
```

---

## 📊 Progress Calculation

### Percentage

```typescript
// For batch_completed event:
percentage = (candidates_added / target) * 100

// For profile_analyzed event:
percentage = (processed / total) * 100
```

### Remaining

```typescript
remaining = target - candidates_added
```

### Estimated Time

Not provided by backend. Frontend can estimate:

```typescript
const estimatedTime = (remaining / (candidates_added / elapsedMinutes))
```

---

## 🐛 Error Scenarios

### WebSocket Disconnected

**Detection:**
```typescript
cable.subscriptions.create(
  { channel: 'SourcingChannel', sourcing_id: id },
  {
    disconnected() {
      // Show "Reconnecting..." message
      // Or fallback to polling API
    }
  }
)
```

**Fallback:**
Poll `/v1/users/jobs/:id` to check `auto_source_metadata`:

```typescript
const pollProgress = async () => {
  const job = await fetchJob(jobId)
  const metadata = job.auto_source_metadata
  
  return {
    candidates_added: metadata.total_added,
    last_page: metadata.last_page
  }
}
```

---

### No Events Received

**Possible Causes:**
1. Wrong channel/stream format
2. Authentication issue
3. Backend service down
4. Sourcing already completed

**Debug:**
```typescript
console.log('Subscribed to:', `${userId}_sourcing_${sourcingId}`)
// Check: Does it match backend broadcast?
```

---

### Events Out of Order

**Rare scenario:** Network issues may deliver events out of order.

**Mitigation:**
```typescript
const handleEvent = (event) => {
  // Use timestamp to order events
  if (event.timestamp < lastEventTimestamp) {
    console.warn('Received old event, ignoring')
    return
  }
  lastEventTimestamp = event.timestamp
  // ... process event
}
```

---

## 🧪 Testing Events

### Backend (Rails Console)

```ruby
# Simulate auto_source_started
SourcingChannel.broadcast_to(
  "42_sourcing_789",
  {
    type: "auto_source_started",
    sourcing_id: 789,
    job_id: 456,
    status: "searching",
    message: "Test message",
    progress: { candidates_added: 0, target: 30, percentage: 0 },
    timestamp: Time.current.iso8601
  }
)

# Simulate profile_analyzed
SourcingChannel.broadcast_to(
  "42_sourcing_789",
  {
    type: "profile_analyzed",
    candidate_name: "Test Candidate",
    score: 85.5,
    processed: 5,
    total: 90,
    timestamp: Time.current.iso8601
  }
)
```

### Frontend (Browser Console)

```javascript
// Listen to all events
cable.subscriptions.create(
  { channel: 'SourcingChannel', sourcing_id: 789 },
  {
    received(data) {
      console.log('[TEST]', data.type, data)
    }
  }
)
```

---

## 📚 Related Files

**Backend:**
- [AutoSourcePaginationService](../app/services/jobs/auto_source_pagination_service.rb)
- [AutoSourceMetadataUpdateService](../app/services/jobs/auto_source_metadata_update_service.rb)
- [AutoSourceContinuationJob](../app/jobs/jobs/auto_source_continuation_job.rb)
- [SourcingChannel](../app/channels/sourcing_channel.rb)

**Docs:**
- [Frontend Implementation Guide](./auto_source_frontend_implementation.md)
- [Auto Source Pagination](./auto_source_pagination.md)
- [Kanban WebSocket Integration](./auto_source_kanban_websocket_integration.md)

---

## 🎯 Summary

**4 Event Types:**
1. **started** - Process begins
2. **profile_analyzed** - Each candidate added
3. **batch_completed** - Batch done (+ continuation decision)
4. **finished** - Fallback when max reached

**Key Fields:**
- `status`: current state (`searching`, `completed`, `continuing`)
- `phase`: UI phase (`search`, `analyzing`, `completed`)
- `progress.candidates_added`: main counter
- `completion.can_request_more`: show "Search More" button

**Typical Flow:**
```
started → profile_analyzed (x10-30) → batch_completed (continue) →
started → profile_analyzed (x10-30) → batch_completed (completed)
```

**Implementation Time:** ~2-4 hours for full frontend integration 🚀
