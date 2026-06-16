# Sourcing Pagination — Load More API

## Overview

The search system now uses **page-based pagination**. On the first search, a pool of ~150 candidates is fetched and ranked, but only the first page (30) is processed (profiles created + AI analysis). Subsequent pages are loaded on demand via `POST /load_more`.

---

## Flow

```
1. POST /v1/users/sourcings          → Creates Sourcing → LocalSearchJob
2. LocalSearchJob                    → HybridSearch(limit: 150) → processes page 1 (30) → caches full pool in Redis (TTL 30min)
3. POST /v1/users/sourcings/:id/load_more { page: 2 }  → LoadMoreCandidatesJob → processes page 2 (30) from cache
4. Repeat step 3 for page 3, 4, 5...
```

---

## Endpoints

### 1. `POST /v1/users/sourcings` (existing — unchanged request)

Response now includes **pagination** in `GET /show` (see below).

### 2. `GET /v1/users/sourcings/:id` (show — updated response)

```json
{
  "data": {
    "id": "123",
    "type": "sourcing",
    "attributes": {
      "uid": "abc-123",
      "query": "ruby developer",
      "status": "done",
      "results_count": 150,
      "processed_count": 30
    }
  },
  "meta": {
    "pagination": {
      "current_page": 1,
      "page_size": 30,
      "total_pages": 5,
      "total_in_pool": 150,
      "loaded_count": 30,
      "has_more": true,
      "pool_available": true,
      "pool_expires_at": "2026-02-18T12:30:00Z"
    }
  }
}
```

#### Pagination Fields

| Field             | Type      | Description                                                        |
|-------------------|-----------|--------------------------------------------------------------------|
| `current_page`    | `integer` | Current page based on loaded profiles                              |
| `page_size`       | `integer` | Number of profiles per page (default: 30)                          |
| `total_pages`     | `integer` | Total number of pages available                                    |
| `total_in_pool`   | `integer` | Total candidates found in the search pool                          |
| `loaded_count`    | `integer` | Number of profiles already processed (with AI analysis)            |
| `has_more`        | `boolean` | Whether more pages are available to load                           |
| `pool_available`  | `boolean` | Whether the Redis cache pool is still alive (TTL 30min)            |
| `pool_expires_at` | `string`  | ISO 8601 timestamp when the pool expires. `null` if no pool exists |

### 3. `POST /v1/users/sourcings/:id/load_more` (NEW)

Loads the next page of candidates from the cached pool.

#### Request

```
POST /v1/users/sourcings/:id/load_more
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "page": 2,
  "page_size": 30
}
```

| Parameter   | Type      | Required | Default | Description                        |
|-------------|-----------|----------|---------|------------------------------------|
| `page`      | `integer` | No       | 2       | Page number to load                |
| `page_size` | `integer` | No       | 30      | Profiles per page (max: 100)       |

#### Response — `202 Accepted`

```json
{
  "sourcing_id": 123,
  "status": "processing",
  "page": 2,
  "page_size": 30,
  "pagination": {
    "current_page": 1,
    "page_size": 30,
    "total_pages": 5,
    "total_in_pool": 150,
    "loaded_count": 30,
    "has_more": true,
    "pool_available": true,
    "pool_expires_at": "2026-02-18T12:30:00Z"
  }
}
```

Processing happens asynchronously via `LoadMoreCandidatesJob`. Use the existing WebSocket channel to receive progress events.

---

## WebSocket Events

Subscribe to the channel: `sourcing_<sourcing_id>`

All existing events (`profiles_processing_started`, `profile_analyzed`, `sourcing_progress`, etc.) work identically for loaded pages. The following **new events** are added:

### `load_more_completed`

Sent when a `load_more` page finishes processing.

```json
{
  "type": "load_more_completed",
  "sourcing_id": 123,
  "loaded": 30,
  "page": 2,
  "total_pages": 5,
  "total_in_pool": 150,
  "has_more": true
}
```

| Field          | Type      | Description                             |
|----------------|-----------|-----------------------------------------|
| `loaded`       | `integer` | Number of profiles loaded in this batch |
| `page`         | `integer` | Page that was just loaded               |
| `total_pages`  | `integer` | Total pages in the pool                 |
| `total_in_pool`| `integer` | Total candidates in the pool            |
| `has_more`     | `boolean` | Whether more pages remain               |

### `sourcing_pool_expired`

Sent when `load_more` is called but the Redis cache has expired (TTL: 30 minutes).

```json
{
  "type": "sourcing_pool_expired",
  "sourcing_id": 123
}
```

**Frontend action:** When receiving this event, show a message like "Search results expired. Please run a new search." and disable the "Load More" button.

### `load_more_failed`

Sent when an error occurs during `load_more` processing.

```json
{
  "type": "load_more_failed",
  "sourcing_id": 123,
  "error": "Error description"
}
```

---

## Frontend Integration Guide

### 1. Initial Search

No changes needed. After `POST /sourcings`, subscribe to the WebSocket channel and wait for the results as before.

### 2. Display "Load More" Button

After the initial search completes, check `meta.pagination` from `GET /sourcings/:id`:

```javascript
const response = await fetch(`/v1/users/sourcings/${sourcingId}`);
const data = await response.json();

const { has_more, pool_available, total_in_pool, loaded_count, total_pages, current_page } = data.meta.pagination;

// Show "Load More" button if:
const showLoadMore = has_more && pool_available;

// Display progress info:
// "Showing 30 of 150 candidates (Page 1 of 5)"
```

### 3. Load More Action

```javascript
async function loadMore(sourcingId, page) {
  const response = await fetch(`/v1/users/sourcings/${sourcingId}/load_more`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ page, page_size: 30 })
  });

  // Response is 202 — processing happens async
  // Wait for WebSocket events for the new profiles
}
```

### 4. WebSocket Event Handling

```javascript
channel.received = (data) => {
  switch (data.type) {
    case 'profiles_processing_started':
      // Show loading spinner for the new batch
      break;

    case 'profile_analyzed':
      // Append the analyzed profile to the list (same as initial search)
      break;

    case 'profiles_processing_completed':
      // Hide loading spinner
      break;

    case 'load_more_completed':
      // Update pagination state
      // data.has_more → show/hide "Load More" button
      // data.page → current page number
      // data.total_pages → total pages
      break;

    case 'sourcing_pool_expired':
      // Disable "Load More" button
      // Show message: "Search results expired. Run a new search."
      break;

    case 'load_more_failed':
      // Show error message: data.error
      break;
  }
};
```

### 5. Edge Cases

| Scenario                        | Behavior                                                    |
|---------------------------------|-------------------------------------------------------------|
| Pool expired (>30 min)          | `sourcing_pool_expired` event via WebSocket                 |
| Double click "Load More"        | Safe — same page will find already-created profiles (idempotent) |
| Page out of range               | `sourcing_pool_expired` event                               |
| Less than page_size remaining   | `has_more: false` in `load_more_completed`                  |
| Search returned < 30 results    | `has_more: false` from the start, no "Load More"            |

---

## Configuration

| Constant                            | Value | Location                          |
|-------------------------------------|-------|-----------------------------------|
| `Candidates::LocalSearchJob::POOL_SIZE` | 150   | Pool size — total candidates fetched  |
| `Candidates::LocalSearchJob::PAGE_SIZE` | 30    | Candidates per page               |
| `Candidates::LocalSearchJob::POOL_TTL`  | 30min | Redis cache TTL                   |
