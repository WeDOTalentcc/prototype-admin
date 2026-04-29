# Agent-Optimized API Endpoints — Uncommitted Changes

> APIs criadas/aprimoradas para reduzir chamadas N+1 do agente de recrutamento.

---

## 1. `GET /v1/users/calendar_events/daily_agenda` — Enriched with `has_feedback`

**File changed:** `app/services/calendar_events/daily_agenda_service.rb`

**What changed:** Each event in the daily agenda response now includes a `has_feedback` boolean field indicating whether a `CandidateFeedback` (like/dislike) already exists for that event's apply or candidate.

**How it works:** During `preload_associations`, the service batch-loads all `CandidateFeedback.active` records matching the event apply_ids and candidate_ids, building a lookup set. The `enrich_with_references` method then resolves `has_feedback` per event using `resolve_has_feedback`.

**New response field per event:**
```json
{
  "has_feedback": true
}
```

**Params:** Same as before (no new params required).

---

## 2. `GET /v1/users/calendar_events/missing_feedback` — NEW

**Files created:**
- `app/services/calendar_events/missing_feedback_service.rb`
- Route added in `config/routes.rb` under `calendar_events` collection

**Controller action added:** `CalendarEventsController#missing_feedback`

**Purpose:** Returns past interview events where the current user has NOT given feedback (CandidateFeedback). Helps the agent identify interviews that need follow-up.

**Params:**
| Param | Type | Description |
|-------|------|-------------|
| `from` | datetime string | Filter events ending after this date |
| `to` | datetime string | Filter events ending before this date |
| `organizer_id` | integer | Filter by organizer user ID |
| `job_id` | integer | Filter by job ID |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Results per page (default: 20, max: 50) |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "title": "Interview - John Doe",
      "event_type": "interview",
      "start_time": "2025-01-15T10:00:00-03:00",
      "end_time": "2025-01-15T11:00:00-03:00",
      "duration_minutes": 60,
      "candidate": { "id": 1, "name": "John Doe", "email": "john@example.com" },
      "job": { "id": 5, "title": "Senior Developer" },
      "apply_id": 42,
      "days_since_interview": 3
    }
  ],
  "meta": { "total": 5, "page": 1, "per_page": 20, "total_pages": 1 }
}
```

**Logic:**
1. Finds all past interview events (`end_time < now`, `is_cancelled: false`)
2. Excludes events whose apply_id has a feedback from the current user
3. Excludes events whose candidate (via MeetingRelationship) has a feedback from the current user
4. Enriches with candidate/job/apply data using batch preloading

---

## 3. `GET /v1/users/evaluations/response_rates` — NEW

**Files created:**
- `app/services/evaluations/response_rates_service.rb`
- `app/controllers/v1/users/evaluations/response_rates_controller.rb`
- Route added in `config/routes.rb` under `evaluations` collection

**Purpose:** Returns evaluation response/completion rate statistics with optional pending candidates list. Richer than the existing `bulk_stats` endpoint — includes completion_rate, avg_score, and inline pending_candidates.

**Params:**
| Param | Type | Description |
|-------|------|-------------|
| `evaluation_ids` | comma-separated IDs | Filter by specific evaluation IDs |
| `job_ids` | comma-separated IDs | Filter by job IDs |
| `min_rate` | float | Minimum response rate filter (0-100) |
| `max_rate` | float | Maximum response rate filter (0-100) |
| `include_pending` | boolean | Include list of pending candidates inline |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "evaluation_id": 10,
      "evaluation_name": "Technical Assessment",
      "job_id": 5,
      "job_title": "Senior Developer",
      "is_active": true,
      "is_screening": false,
      "total_sent": 20,
      "total_completed": 15,
      "total_pending": 5,
      "response_rate": 75.0,
      "completion_rate": 60.0,
      "avg_score": 7.5,
      "pending_candidates": [
        {
          "evaluation_candidate_id": 101,
          "candidate_id": 42,
          "candidate_name": "Jane Smith",
          "candidate_email": "jane@example.com",
          "sent_at": "2025-01-10T14:00:00-03:00",
          "is_expired": false
        }
      ]
    }
  ],
  "meta": {
    "total_evaluations": 3,
    "filtered_count": 2,
    "overall_response_rate": 68.5,
    "overall_total_sent": 50,
    "overall_total_completed": 34,
    "computed_at": "2025-01-20T10:00:00-03:00"
  }
}
```

---

## 4. `GET /v1/users/jobs/pipeline_health` — ENHANCED

**Files changed:**
- `app/services/jobs/pipeline_health_service.rb`
- `app/controllers/v1/users/jobs/pipeline_health_controller.rb`

**What changed:**
- Added `aging_threshold_days` param — configurable threshold for bottleneck detection (default: 5 days)
- Added `limit` param — limits number of jobs analyzed
- Service now returns structured `{ success, data, meta }` hash instead of raw array
- Meta includes `aging_threshold_days` and `computed_at`

**New params:**
| Param | Type | Description |
|-------|------|-------------|
| `aging_threshold_days` | integer | Days threshold for bottleneck detection (default: 5) |
| `limit` | integer | Max number of jobs to include |

**Response format change:** Now wrapped in `{ success: true, data: [...], meta: {...} }`.

---

## 5. `POST /v1/users/jobs/bulk_analytics` — ENHANCED

**Files changed:**
- `app/services/jobs/bulk_analytics_service.rb`
- `app/controllers/v1/users/jobs/bulk_analytics_controller.rb`

**What changed:**
- Added `where` filter mode — agent can now request analytics for all active jobs without needing to know specific IDs
- Added `limit` param (max: 50)
- `job_ids` is now optional when `where` is provided

**New params:**
| Param | Type | Description |
|-------|------|-------------|
| `where` | JSON object | Filter jobs: `{ "is_active": true, "user_id": 5, "company_id": 1, "department_id": 2 }` |
| `limit` | integer | Max jobs to analyze (default/max: 50) |

**Example request body:**
```json
{
  "where": { "is_active": true, "user_id": 5 },
  "limit": 10
}
```

---

## 6. `POST /v1/users/sourcings/bulk_stats` — ENHANCED

**File changed:** `app/services/sourcings/bulk_stats_service.rb`

**What changed:** Each sourcing in the response now includes:
- `import_stats` — breakdown of imported profiles: `total_imported`, `imported_with_apply` (candidate created AND has at least one Apply), `imported_without_apply`
- `score_distribution` — `avg`, `min`, `max`, `count` of scores from sourced_profile_sourcings

**New fields in response per sourcing:**
```json
{
  "import_stats": {
    "total_imported": 15,
    "imported_with_apply": 8,
    "imported_without_apply": 7
  },
  "score_distribution": {
    "avg": 7.2,
    "min": 3.5,
    "max": 9.8,
    "count": 25
  }
}
```

---

## 7. Searchkick Index Fields — ENHANCED

### Job (`app/models/job.rb`)
- **`last_activity_at`** (datetime) — Timestamp of the most recent apply `updated_at` for the job, or the job's own `updated_at` if no applies exist. Enables sorting/filtering jobs by recent activity.
- *`applies_count` already existed in the index.*

### EvaluationCandidate (`app/models/evaluation_candidate.rb`)
- **`is_expired`** (boolean) — `true` when `date_expiration` is set and in the past. Enables filtering expired evaluation candidates via Searchkick.

### SourcedProfile (`app/models/sourced_profile.rb`)
- **`has_candidate`** (boolean) — `true` when `candidate_id` is present (profile was imported as a candidate). Alias for the existing `imported` field with clearer naming for agent queries.

---

## Dica: Buscar applies de um candidato via `GET /v1/users/applies`

Não é necessário um endpoint dedicado para buscar applies por candidato. O index padrão de applies já suporta filtro via `where`:

```
GET /v1/users/applies?where={"candidate_id": 42, "is_deleted": false}
```

Isso retorna todos os applies do candidato 42, com paginação, ordenação e aggregations padrão do Searchkick. Também funciona com múltiplos filtros combinados:

```
GET /v1/users/applies?where={"candidate_id": 42, "is_deleted": false, "job_id": 10}
```

Campos disponíveis para filtro no `where` do applies: `candidate_id`, `job_id`, `user_id`, `selective_process_id`, `evaluation_candidate_status`, `is_deleted`, `source`, entre outros campos do `search_data` do model Apply.

---

## Summary of Files Changed

| File | Action |
|------|--------|
| `app/services/calendar_events/daily_agenda_service.rb` | Modified — added `has_feedback` enrichment |
| `app/services/calendar_events/missing_feedback_service.rb` | **Created** |
| `app/services/evaluations/response_rates_service.rb` | **Created** |
| `app/controllers/v1/users/evaluations/response_rates_controller.rb` | **Created** |
| `app/controllers/v1/users/calendar_events_controller.rb` | Modified — added `missing_feedback` action |
| `app/services/jobs/pipeline_health_service.rb` | Modified — added `aging_threshold_days`, `limit`, structured response |
| `app/controllers/v1/users/jobs/pipeline_health_controller.rb` | Modified — passes new params |
| `app/services/jobs/bulk_analytics_service.rb` | Modified — added `where` filter mode, `limit` |
| `app/controllers/v1/users/jobs/bulk_analytics_controller.rb` | Modified — accepts `where` and `limit` |
| `app/services/sourcings/bulk_stats_service.rb` | Modified — added `import_stats`, `score_distribution` |
| `app/models/job.rb` | Modified — added `last_activity_at` to `search_data` |
| `app/models/evaluation_candidate.rb` | Modified — added `is_expired` to `search_data` |
| `app/models/sourced_profile.rb` | Modified — added `has_candidate` to `search_data` |
| `config/routes.rb` | Modified — added `missing_feedback` and `response_rates` routes |
