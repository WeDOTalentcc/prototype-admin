# Auto Source - Real-Time Progress Implementation

## 🎯 Overview

This document summarizes the implementation of **real-time progress broadcasting** for the Auto Source feature, enabling the frontend to display live status updates during the candidate search and analysis process.

---

## ✨ What Was Implemented

### 1. Backend Broadcasts

Added WebSocket broadcasts at key stages of the Auto Source process:

| Stage | Event | Description |
|-------|-------|-------------|
| **Start** | `auto_source_started` | Immediately when search begins |
| **Analysis** | `profile_analyzed` | Each candidate that gets added to job |
| **Batch Done** | `auto_source_batch_completed` | After processing X pages |
| **Finished** | `auto_source_finished` | When max pages reached |

### 2. Modified Files

#### [AutoSourcePaginationService](../app/services/jobs/auto_source_pagination_service.rb)
- ✅ Added `broadcast_auto_source_started` method
- ✅ Broadcasts initial progress (page 0, target X)
- ✅ Includes job title, target count, pagination info

#### [AutoSourceMetadataUpdateService](../app/services/jobs/auto_source_metadata_update_service.rb)
- ✅ Added `broadcast_batch_completed` method
- ✅ Broadcasts after each batch with:
  - Total candidates searched/added
  - Percentage complete
  - Whether continuing automatically
  - Whether user can request more

#### [AutoSourceContinuationJob](../app/jobs/jobs/auto_source_continuation_job.rb)
- ✅ Added `broadcast_auto_source_finished` method
- ✅ Broadcasts when max pages reached
- ✅ Includes completion reason and final stats

#### [AutoSourceController](../app/controllers/v1/users/jobs/auto_source_controller.rb)
- ✅ Updated response to include WebSocket subscription info
- ✅ Lists all event types frontend should handle

---

## 📡 Broadcast Flow

```
User → POST /v1/users/jobs/:id/auto_source
         ↓
Controller returns subscription info
         ↓
Frontend subscribes to SourcingChannel
         ↓
Backend broadcasts:

1. auto_source_started
   {
     phase: "search",
     progress: { candidates_added: 0, target: 30 },
     message: "Searching for qualified candidates..."
   }

2. profile_analyzed (repeated for each candidate)
   {
     candidate_name: "João Silva",
     score: 85.5,
     processed: 5
   }

3. auto_source_batch_completed
   {
     status: "continuing",
     progress: { candidates_added: 15, target: 30 },
     completion: { will_continue: true }
   }

4. auto_source_started (next batch if needed)
   ... repeat 2-3 ...

5. auto_source_batch_completed
   {
     status: "completed",
     progress: { candidates_added: 30, target: 30, percentage: 100 },
     completion: { target_reached: true }
   }
```

---

## 🎨 Frontend Implementation

### Response Structure

```json
{
  "success": true,
  "sourcing_id": 789,
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

### Recommended UI States

| Phase | Icon | Message | Action |
|-------|------|---------|--------|
| `searching` | 🔍 | "Searching candidates..." | Show spinner |
| `analyzing` | 🧠 | "Analyzing João Silva (85%)" | Update progress bar |
| `continuing` | 🔄 | "Found 15/30, continuing..." | Keep loader open |
| `completed` | ✅ | "Added 30 candidates!" | Close after 2s |
| `completed_partial` | ⚠️ | "Added 18 of 30 (max reached)" | Show options |

---

## 📊 Progress Information

### Fields Available in Events

```typescript
progress: {
  // Current batch (auto_source_started)
  current_page: number,          // e.g., 1
  pages_this_batch: number,      // e.g., 3
  max_page: number,              // e.g., 3

  // Candidates (all events)
  candidates_found: number,      // Total found (raw)
  candidates_added: number,      // Qualified & added
  target: number,                // User's requested count
  remaining: number,             // target - candidates_added
  percentage: number,            // (candidates_added / target) * 100

  // Pages (batch_completed)
  candidates_searched: number,   // Total profiles analyzed
  last_page: number,             // Cumulative page count
  max_pages: 10                  // Hard limit
}
```

### Completion Status

```typescript
completion: {
  target_reached: boolean,       // true if >= target
  max_pages_reached: boolean,    // true if last_page >= 10
  will_continue: boolean,        // true if auto-continuing
  can_request_more: boolean      // true if user can request more
}
```

---

## 🔄 Automatic Continuation

The system **automatically** searches more pages if:
- ✅ Target not yet reached (`candidates_added < target`)
- ✅ Max pages not reached (`last_page < 10`)
- ✅ Remaining candidates needed

**No user action required!**

When continuing:
```json
{
  "status": "continuing",
  "message": "🔄 Batch complete. Found 15/30, continuing search...",
  "completion": {
    "will_continue": true
  }
}
```

Frontend should:
- Keep loader open
- Show "Continuing search..." message
- Wait for next `auto_source_started` event

---

## 🎯 Requesting More Pages

If search stops before target (max pages reached), user can manually request more:

```typescript
// Simply call the endpoint again
await fetch(`/v1/users/jobs/${jobId}/auto_source`, {
  method: 'POST',
  body: JSON.stringify({
    limit: 30,      // Can request more
    min_score: 70
  })
})
```

**Backend automatically:**
- Checks `auto_source_metadata.last_page`
- Continues from next page
- Respects 10-page limit

**Frontend shows button when:**
```typescript
if (event.completion.can_request_more) {
  showButton("🔄 Search More Pages")
}
```

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Start Auto Source
curl -X POST http://localhost:3000/v1/users/jobs/123/auto_source \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "limit": 10, "min_score": 70 }'

# 2. Subscribe to WebSocket in browser console
cable.subscriptions.create(
  { channel: 'SourcingChannel', sourcing_id: 789 },
  {
    received(data) {
      console.log('[Event]', data.type, data)
    }
  }
)

# 3. Watch events in console:
# - auto_source_started
# - profile_analyzed (multiple)
# - auto_source_batch_completed
```

### Expected Console Output

```
[Event] auto_source_started {
  phase: "search",
  progress: { candidates_added: 0, target: 10 }
}

[Event] profile_analyzed {
  candidate_name: "João Silva",
  score: 85.5,
  processed: 1
}

[Event] profile_analyzed {
  candidate_name: "Maria Santos",
  score: 78.2,
  processed: 2
}

... (8 more) ...

[Event] auto_source_batch_completed {
  status: "completed",
  progress: { candidates_added: 10, target: 10, percentage: 100 },
  completion: { target_reached: true }
}
```

### Backend Logs

```bash
docker logs -f ats_api | grep AutoSource

# You should see:
🚀 [AutoSourcePagination] Starting paginated search
   Job: 123 - Senior Ruby Developer
   Pages: 1 to 3
   Target: 10 candidates
📢 [AutoSourcePagination] Broadcasted 'auto_source_started'
✅ [AutoSourceMetadataUpdate] Updated job metadata
📢 [AutoSourceMetadataUpdate] Broadcasted 'batch_completed' - status: completed
```

---

## 📚 Documentation Files

### Created Documents

1. **[auto_source_frontend_implementation.md](./auto_source_frontend_implementation.md)**
   - Complete guide for frontend developers
   - Vue 3 example implementation
   - UI/UX recommendations
   - Error handling
   - Mobile considerations

2. **[auto_source_events_reference.md](./auto_source_events_reference.md)**
   - Quick reference for all events
   - Full event payload schemas
   - Flow examples
   - Decision tree
   - Testing guide

3. **[auto_source_real_time_implementation.md](./auto_source_real_time_implementation.md)** (this file)
   - Implementation summary
   - Backend changes
   - Integration guide

### Existing Documents (Updated)

- [auto_source_pagination.md](./auto_source_pagination.md) - Backend pagination logic
- [auto_source_kanban_websocket_integration.md](./auto_source_kanban_websocket_integration.md) - Kanban integration

---

## 🔍 How It Works

### 1. User Triggers Auto Source

```javascript
POST /v1/users/jobs/123/auto_source
{
  "limit": 30,
  "min_score": 70
}
```

Response includes subscription info.

### 2. Frontend Subscribes

```javascript
cable.subscriptions.create(
  { channel: 'SourcingChannel', sourcing_id: 789 },
  { received: handleEvent }
)
```

### 3. Backend Processes

```
AutoSourcePaginationService
  ↓ broadcast: auto_source_started
LocalSearchJob (pages 1-3)
  ↓
AiAnalysisJob (for each profile)
  ↓ broadcast: profile_analyzed (if qualified)
AutoSourceMetadataUpdateService
  ↓ broadcast: auto_source_batch_completed
  ↓ (if needed)
AutoSourceContinuationJob
  ↓ (repeat from step 1)
```

### 4. Frontend Updates UI

```javascript
const handleEvent = (data) => {
  switch (data.type) {
    case 'auto_source_started':
      showLoader()
      break
    case 'profile_analyzed':
      updateProgress(data.progress)
      break
    case 'auto_source_batch_completed':
      if (data.status === 'completed') {
        showSuccess()
        closeLoader()
      } else {
        showContinuing()
      }
      break
  }
}
```

---

## 🎉 Benefits

### Before

- ❌ No feedback during process
- ❌ User doesn't know if it's working
- ❌ Need to refresh page to see results
- ❌ Don't know when to request more

### After

- ✅ Real-time progress updates
- ✅ Live candidate counter
- ✅ Phase indicators (searching → analyzing → done)
- ✅ Automatic continuation
- ✅ Clear completion status
- ✅ Option to request more when available

---

## 🚀 Next Steps

### For Frontend Developers

1. Read [auto_source_frontend_implementation.md](./auto_source_frontend_implementation.md)
2. Implement WebSocket subscription
3. Create loader component with progress bar
4. Handle 4 event types
5. Test with real data

**Estimated Time:** 2-4 hours

### For Backend Developers

✅ **Already done!** Just monitor logs and adjust broadcast frequency if needed.

### Optional Enhancements

- [ ] Add estimated time remaining
- [ ] Show candidate avatars in loader
- [ ] Add sound/notification when completed
- [ ] Allow canceling in-progress search
- [ ] Show detailed breakdown per page

---

## 📊 Performance Considerations

### Broadcast Frequency

| Event | Frequency | Impact |
|-------|-----------|--------|
| `auto_source_started` | Once per batch | Low |
| `profile_analyzed` | 10-30 per batch | Medium |
| `auto_source_batch_completed` | Once per batch | Low |

**Total per batch:** ~12-32 events

**Recommendation:** If receiving too many `profile_analyzed` events, debounce UI updates:

```typescript
const debouncedUpdate = useDebounceFn((event) => {
  updateProgress(event.progress)
}, 300)
```

### Memory Usage

- WebSocket connection: ~50KB RAM
- Event payloads: ~1-2KB each
- Total per session: ~100-200KB

**Safe for mobile devices!**

---

## 🐛 Troubleshooting

### No Events Received

**Check:**
1. WebSocket connection established?
2. Correct channel/stream format?
3. Authorization header included?

**Debug:**
```ruby
# Rails console
SourcingChannel.broadcast_to(
  "42_sourcing_789",
  { type: "test", message: "Hello" }
)
```

### Events Out of Order

**Rare, but possible with network issues.**

**Solution:** Include timestamp in all events, order by timestamp in frontend.

### Loader Stuck

**If loader doesn't close:**

**Check:**
- Did `batch_completed` event arrive?
- Is `status: "completed"`?
- Timeout after 10 minutes and show error

---

## 📝 Summary

**What Changed:**
- ✅ Added 4 broadcast events to Auto Source flow
- ✅ Real-time progress updates
- ✅ Completion status with options
- ✅ Updated API response with subscription info
- ✅ Created comprehensive documentation

**What's Required (Frontend):**
- Subscribe to `SourcingChannel`
- Handle 4 event types
- Update loader UI based on events
- Show completion status

**Expected Result:**
A smooth, real-time experience that keeps users informed throughout the Auto Source process! 🎉

---

## 🔗 Quick Links

- [Frontend Implementation Guide](./auto_source_frontend_implementation.md)
- [Events Reference](./auto_source_events_reference.md)
- [Backend Pagination Logic](./auto_source_pagination.md)
- [Controller Code](../app/controllers/v1/users/jobs/auto_source_controller.rb)
- [Service Code](../app/services/jobs/auto_source_pagination_service.rb)
