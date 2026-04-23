# Applies API - Complete Documentation

## Base URL

```
/v1/users/applies
```

All endpoints require authentication via Bearer token.

---

## Endpoints

| Method | Path | Action | Description |
|--------|------|--------|-------------|
| `GET` | `/v1/users/applies` | `index` | List/search applies with Searchkick |
| `GET` | `/v1/users/applies/:id` | `show` | Get single apply |
| `POST` | `/v1/users/applies` | `create` | Create apply (candidate + job) |
| `PUT` | `/v1/users/applies/:id` | `update` | Update apply |
| `DELETE` | `/v1/users/applies/:id` | `destroy` | Soft delete apply |
| `POST` | `/v1/users/applies/create_collection` | `create_collection` | Bulk create applies |
| `PUT` | `/v1/users/applies/update_collection` | `update_collection` | Bulk update applies |
| `DELETE` | `/v1/users/applies/delete_collection` | `delete_collection` | Bulk delete applies |
| `POST` | `/v1/users/jobs/:id/applies/approve_collection` | `approve_collection` | Bulk approve applies for a job |
| `POST` | `/v1/users/jobs/:id/applies/reject_collection` | `reject_collection` | Bulk reject applies for a job |

---

## 1. List / Search Applies

```
GET /v1/users/applies
```

Uses **Searchkick** (Elasticsearch) for powerful search, filtering, ordering, and pagination. All fields in `search_data` are searchable via the `where` parameter.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | `*` (all) | Full-text search term |
| `page` | integer | `1` | Page number |
| `per_page` / `limit` | integer | `30` (max: 30) | Results per page |
| `where` | object | `{}` | Elasticsearch filters (see below) |
| `order` | object | `{ created_at: "desc" }` | Sort order |
| `filter` | object | `{}` | Additional filters with LIKE support |
| `compact` | string | - | Comma-separated fields for compact response |
| `boost_where` | JSON string | - | Boost scoring for specific fields |

### `where` Parameter — Searchkick Filtering

The `where` parameter accepts any field from `search_data`. Pass filters as query params:

```
where[field_name]=value
```

#### Available Fields for `where`

##### Apply Fields (direct)

| Field | Type | Example |
|-------|------|---------|
| `id` | integer/array | `where[id]=123` or `where[id][]=1&where[id][]=2` |
| `job_id` | integer/array | `where[job_id]=456` |
| `candidate_id` | integer/array | `where[candidate_id]=789` |
| `selective_process_id` | integer/array | `where[selective_process_id]=10` |
| `selective_process_status` | string | `where[selective_process_status]=Entrevista` |
| `evaluation_candidate_status` | string | `where[evaluation_candidate_status]=sent` |
| `is_deleted` | boolean | `where[is_deleted]=false` (default) |
| `cv_match` | float | `where[cv_match][gte]=80` |
| `total_score` | float | `where[total_score][gte]=70` |
| `sub_status` | string | `where[sub_status]=aguardando` |
| `pin_user_ids` | integer | `where[pin_user_ids]=1` |
| `confidential_user_ids` | integer | `where[confidential_user_ids]=1` |
| `alerts_count` | integer | `where[alerts_count][gte]=1` |
| `created_at` | datetime | `where[created_at][gte]=2026-01-01` |
| `updated_at` | datetime | `where[updated_at][lte]=2026-12-31` |

##### Candidate Fields (from `search_data`)

| Field | Type | Example |
|-------|------|---------|
| `name` | string | `where[name]=joao silva` |
| `email` | string | `where[email]=joao@email.com` |
| `phone` | string | `where[phone]=11999999999` |
| `linkedin` | string | `where[linkedin]=linkedin.com/in/joao` |
| `github` | string | `where[github]=github.com/joao` |
| `portfolio` | string | `where[portfolio]=joao.dev` |
| `role_name` | string | `where[role_name]=desenvolvedor` |
| `current_company` | string | `where[current_company]=acme` |
| `city` | string | `where[city]=são paulo` |
| `state` | string | `where[state]=SP` |
| `country` | string | `where[country]=Brasil` |
| `gender` | string | `where[gender]=Masculino` |
| `nationality` | string | `where[nationality]=brasileiro` |
| `cpf` | string | `where[cpf]=12345678900` |
| `source` | string | `where[source]=linkedin` |
| `remote_work` | string | `where[remote_work]=true` |
| `mobility` | string | `where[mobility]=true` |
| `completed_register` | boolean | `where[completed_register]=true` |
| `accept_terms` | boolean | `where[accept_terms]=true` |
| `date_birth` | date | `where[date_birth][gte]=1990-01-01` |
| `clt_expectation` | float | `where[clt_expectation][gte]=5000` |
| `pj_expectation` | float | `where[pj_expectation][lte]=15000` |
| `current_salary` | float | `where[current_salary][gte]=3000` |
| `desired_salary` | float | `where[desired_salary][lte]=10000` |
| `currency` | string | `where[currency]=BRL` |
| `external_id` | integer | `where[external_id]=999` |

##### Process Fields

| Field | Type | Example |
|-------|------|---------|
| `selective_process_name` | string | `where[selective_process_name]=triagem` |
| `candidate_feedback` | string | `where[candidate_feedback]=positive` |
| `favorite_user_ids` | integer | `where[favorite_user_ids]=1` |

##### Evaluation Fields (dynamic)

Evaluation scores are indexed dynamically based on the evaluations configured for the job. The field name follows the pattern: `{evaluation_name}_{evaluation_id}`.

```
where[english_test_42][gte]=70
```

### Filter Operators

Searchkick supports comparison operators for numeric and date fields:

```javascript
// Exact match
where[job_id] = 123

// Array (IN)
where[id][] = 1
where[id][] = 2
where[id][] = 3

// Greater than or equal
where[cv_match][gte] = 80

// Less than or equal
where[cv_match][lte] = 100

// Greater than
where[created_at][gt] = "2026-01-01"

// Less than
where[updated_at][lt] = "2026-06-01"

// Range (combine gte + lte)
where[cv_match][gte] = 50
where[cv_match][lte] = 100

// Not equal
where[selective_process_status][not] = "Reprovado"

// Boolean
where[is_deleted] = false
```

### `order` Parameter

```javascript
// Single field
order[created_at] = "desc"

// By score (pinned first by default in index)
order[score] = "desc"

// By cv_match
order[cv_match] = "desc"

// Multiple
order[selective_process_status] = "asc"
order[created_at] = "desc"
```

### `filter` Parameter

Works like `where` but applies **LIKE** matching for string fields (case-insensitive partial match):

```javascript
// Partial match on name
filter[name] = "silva"           // matches "João Silva", "Maria da Silva"

// Partial match on email
filter[email] = "@gmail"         // matches all gmail addresses

// Partial match on city
filter[city] = "paulo"           // matches "São Paulo", "Paulópolis"

// Filter by id (exact match, same as where)
filter[id] = 123
```

### `compact` Parameter

Returns only specific fields for lighter responses:

```
GET /v1/users/applies?compact=id,candidate_id,name,email,selective_process_status
```

Response:
```json
{
  "data": [
    { "id": 1, "candidate_id": 10, "name": "João", "email": "joao@email.com", "selective_process_status": "Triagem" },
    { "id": 2, "candidate_id": 11, "name": "Maria", "email": "maria@email.com", "selective_process_status": "Entrevista" }
  ],
  "meta": { "total": 2 }
}
```

### Full Request Examples

#### Basic: List all applies for a job

```
GET /v1/users/applies?where[job_id]=456&where[is_deleted]=false
```

#### Filter by multiple IDs

```
GET /v1/users/applies?where[id][]=1&where[id][]=2&where[id][]=3
```

#### Search by candidate email

```
GET /v1/users/applies?where[email]=joao@email.com
```

#### Search by name (partial, LIKE)

```
GET /v1/users/applies?filter[name]=silva
```

#### Filter by status + order by score

```
GET /v1/users/applies?where[job_id]=456&where[selective_process_status]=Entrevista&order[cv_match]=desc
```

#### Filter by date range

```
GET /v1/users/applies?where[created_at][gte]=2026-01-01&where[created_at][lte]=2026-03-01
```

#### Filter by salary expectation range

```
GET /v1/users/applies?where[clt_expectation][gte]=5000&where[clt_expectation][lte]=15000
```

#### Filter by candidate city + process status

```
GET /v1/users/applies?where[city]=são paulo&where[selective_process_status]=Triagem&where[job_id]=456
```

#### Pinned first + custom order

```
GET /v1/users/applies?where[job_id]=456&order[score]=desc&order[created_at]=desc
```

#### Full-text search

```
GET /v1/users/applies?search=java developer&where[job_id]=456
```

#### Compact response (only IDs and names)

```
GET /v1/users/applies?where[job_id]=456&compact=id,candidate_id,name,selective_process_status,cv_match
```

#### Filter by evaluation status

```
GET /v1/users/applies?where[evaluation_candidate_status]=answered&where[job_id]=456
```

#### Filter by candidate feedback

```
GET /v1/users/applies?where[candidate_feedback]=positive&where[job_id]=456
```

### Response Format

```json
{
  "data": [
    {
      "id": "1",
      "type": "apply",
      "attributes": {
        "id": 1,
        "candidate_id": 10,
        "job_id": 456,
        "selective_process_id": 5,
        "selective_process_name": "Triagem",
        "selective_process_status": "Triagem",
        "evaluation_candidate_status": "pending",
        "name": "João Silva",
        "email": "joao@email.com",
        "phone": "11999999999",
        "secondary_phone": null,
        "linkedin": "linkedin.com/in/joao",
        "github": "github.com/joao",
        "avatar_url": "https://...",
        "curriculum_pdf_url": "https://...",
        "portfolio": null,
        "current_company": "Acme Corp",
        "role_name": "Senior Developer",
        "position_level": "senior",
        "self_introduction": "...",
        "curriculum_text": "...",
        "date_birth": "1990-01-15",
        "gender": "Masculino",
        "nationality": "Brasileiro",
        "marital_status": null,
        "cpf": "12345678900",
        "street": "Rua X",
        "number": "100",
        "district": "Centro",
        "zip": "01001000",
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "complement": "Apto 42",
        "clt_expectation": 12000.0,
        "pj_expectation": 18000.0,
        "freelance_expectation": null,
        "current_salary": 10000.0,
        "desired_salary": 15000.0,
        "currency": "BRL",
        "remote_work": "hybrid",
        "mobility": "yes",
        "interests": null,
        "comments": null,
        "source": "linkedin",
        "completed_register": true,
        "accept_terms": true,
        "is_deleted": false,
        "evaluation_candidate_scores": { "english_test_42": 85.0 },
        "evaluation_candidate_summaries": { "english_test_42": "Good performance" },
        "cv_match": 87.5,
        "total_score": 86.25,
        "alerts": [],
        "color": "#4CAF50",
        "is_candidate_favorite": false,
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-02-20T14:00:00Z",
        "external_id": "EXT-123",
        "sub_status": null,
        "url": "/user/jobs/456/applies/1",
        "pin": true,
        "confidential": false,
        "candidate_feedback": "positive",
        "meetings": [
          {
            "id": 1,
            "reference_type": "CalendarEvent",
            "reference_id": 10,
            "role": "candidate",
            "meeting_id": "meeting_abc",
            "calendar_event_id": 5,
            "join_url": "https://teams.microsoft.com/...",
            "provider_text": "Microsoft Teams"
          }
        ],
        "english_test_42": 85.0,
        "english_test_42_summary": "Good performance"
      }
    }
  ],
  "meta": {
    "total": 150,
    "where": { "job_id": 456, "is_deleted": false }
  }
}
```

---

## 2. Show Apply

```
GET /v1/users/applies/:id
```

Returns a single apply with all attributes.

### Response

Same structure as index, but single `data` object (not array).

---

## 3. Create Apply

```
POST /v1/users/applies
```

### Request Body

```json
{
  "apply": {
    "candidate_id": 10,
    "job_id": 456,
    "selective_process_id": 5,
    "selective_process_status": "Triagem"
  }
}
```

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidate_id` | integer | **Yes*** | Candidate ID |
| `job_id` | integer | **Yes*** | Job ID |
| `selective_process_id` | integer | No | Selective process ID |
| `selective_process_status` | string | No | Auto-filled from process if omitted |
| `account_id` | integer | No | Defaults to current user's account |

*Either `candidate_id` or `external_candidate_id` is required. Same for `job_id`/`external_job_id`.

### External ID Support

You can create applies using external IDs instead of internal IDs:

```json
{
  "apply": {
    "external_candidate_id": "EXT-CAND-123",
    "external_job_id": "EXT-JOB-456",
    "selective_process_status": "Triagem"
  }
}
```

The API will resolve these to internal IDs automatically.

### Behavior

- If an apply already exists (same `candidate_id` + `job_id`, not deleted): **updates** it
- If a deleted apply exists (same candidate + job): **reactivates** it
- Otherwise: **creates** new apply

### Response

```json
{
  "data": {
    "id": "1",
    "type": "apply",
    "attributes": { ... }
  }
}
```

Status: `201 Created`

### Errors

```json
{
  "errors": ["candidate_id e job_id são obrigatórios"]
}
```

Status: `422 Unprocessable Entity`

---

## 4. Update Apply

```
PUT /v1/users/applies/:id
```

### Request Body

```json
{
  "apply": {
    "selective_process_id": 6,
    "selective_process_status": "Entrevista",
    "sub_status": "agendada",
    "pin": true,
    "confidential": false,
    "reason_for_reject": "Não atende requisitos",
    "reason_code": "SKILL_MISMATCH",
    "reason_category": "Técnica",
    "internal_comment": "Candidato não tem experiência suficiente"
  }
}
```

### Updatable Fields

| Field | Type | Description |
|-------|------|-------------|
| `selective_process_id` | integer | Move to different stage |
| `selective_process_status` | string | Update status text |
| `sub_status` | string | Sub-status detail |
| `pin` | boolean | `true` = pin for current user, `false` = unpin |
| `confidential` | boolean | `true` = mark confidential, `false` = remove |
| `is_deleted` | boolean | Soft delete flag |
| `reason_for_reject` | string | Rejection reason text |
| `reason_code` | string | Rejection reason code |
| `reason_category` | string | Rejection category |
| `internal_comment` | string | Internal notes |

### Pin/Confidential Behavior

- `pin: true` → adds current user ID to `pin_user_ids` array
- `pin: false` → removes current user ID from `pin_user_ids`
- `confidential: true` → adds current user ID to `confidential_user_ids`
- `confidential: false` → removes current user ID from `confidential_user_ids`

These are per-user flags — each user manages their own pins independently.

---

## 5. Delete Apply (Soft Delete)

```
DELETE /v1/users/applies/:id
```

Sets `is_deleted: true` on the apply. The apply is not physically removed from the database.

### Response

Returns the updated apply object.

---

## 6. Create Collection (Bulk Create)

```
POST /v1/users/applies/create_collection
```

### Option A: Using `collections` array

```json
{
  "collections": [
    { "candidate_id": 10 },
    { "candidate_id": 11 },
    { "candidate_id": 12 }
  ],
  "apply_collection": {
    "job_id": 456,
    "selective_process_id": 5,
    "selective_process_status": "Triagem"
  }
}
```

### Option B: Using `reference_type` + `reference_id`

Supports creating applies from different entity types:

```json
{
  "collections": [
    { "reference_type": "SourcedProfileSourcing", "reference_id": 100 },
    { "reference_type": "SourcedProfile", "reference_id": 200 },
    { "reference_type": "Candidate", "reference_id": 300 },
    { "reference_type": "Apply", "reference_id": 400 }
  ],
  "apply_collection": {
    "job_id": 456,
    "selective_process_id": 5
  }
}
```

| reference_type | Description |
|----------------|-------------|
| `Candidate` | Uses `reference_id` as `candidate_id` directly |
| `SourcedProfile` | Converts sourced profile to candidate if needed |
| `SourcedProfileSourcing` | Resolves through sourced profile sourcing → sourced profile → candidate |
| `Apply` | Gets `candidate_id` from existing apply |

### Option C: Using `select_all_params` (bulk from search)

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "job_id": 456, "selective_process_status": "Triagem" }
  },
  "apply": {
    "job_id": 789,
    "selective_process_id": 10,
    "selective_process_status": "Triagem"
  }
}
```

### Response

```json
{
  "status": "processing",
  "message": "3 aplicações estão sendo processadas em background"
}
```

Status: `200 OK`

All operations run as background jobs (Sidekiq).

---

## 7. Update Collection (Bulk Update)

```
PUT /v1/users/applies/update_collection
```

### Request Body

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "job_id": 456, "selective_process_status": "Triagem" }
  },
  "apply": {
    "selective_process_id": 6,
    "selective_process_status": "Entrevista"
  }
}
```

Runs in background. Response:

```json
{
  "message": "As aplicações estão sendo atualizadas"
}
```

---

## 8. Delete Collection (Bulk Delete)

```
DELETE /v1/users/applies/delete_collection
```

### Request Body

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "job_id": 456, "selective_process_status": "Reprovado" }
  },
  "apply": {}
}
```

Runs in background. Response:

```json
{
  "message": "As aplicações estão sendo deletadas"
}
```

---

## 9. Approve Collection (Bulk Approve)

```
POST /v1/users/jobs/:job_id/applies/approve_collection
```

### Request Body

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "selective_process_status": "Triagem" }
  }
}
```

### Response

```json
{
  "status": "processing",
  "message": "As candidaturas estão sendo aprovadas em background",
  "job_id": 456
}
```

---

## 10. Reject Collection (Bulk Reject)

```
POST /v1/users/jobs/:job_id/applies/reject_collection
```

### Request Body

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "selective_process_status": "Entrevista" }
  }
}
```

### Response

```json
{
  "status": "processing",
  "message": "As candidaturas estão sendo rejeitadas em background",
  "job_id": 456
}
```

---

## Search Data Reference

All these fields are indexed in Elasticsearch and available for `where` queries:

```ruby
{
  # === Apply Fields ===
  id: 1,
  job_id: 456,
  candidate_id: 10,
  account_id: 1,
  selective_process_id: 5,
  selective_process_status: "Triagem",
  is_deleted: false,
  evaluation_candidate_status: "pending",   # "pending", "sent", "answered"
  cv_match: 87.5,
  total_score: 86.25,
  alerts: [{ type: "new_feedback", timestamp: "2026-01-15T10:00:00Z" }],
  alerts_count: 1,
  sub_status: nil,
  pin_user_ids: [1, 3],
  confidential_user_ids: [1],
  created_at: "2026-01-15T10:30:00Z",
  updated_at: "2026-02-20T14:00:00Z",

  # === Candidate Fields ===
  name: "joão silva",                        # lowercased
  email: "joao@email.com",                   # lowercased
  external_id: 999,
  role_name: "desenvolvedor senior",         # lowercased
  current_company: "acme corp",              # lowercased
  phone: "11999999999",
  linkedin: "linkedin.com/in/joao",
  github: "github.com/joao",
  portfolio: "joao.dev",
  date_birth: "1990-01-15",
  gender: "Masculino",
  nationality: "Brasileiro",
  cpf: "12345678900",
  street: "Rua X",
  number: "100",
  district: "Centro",
  zip: "01001000",
  city: "são paulo",
  state: "SP",
  country: "Brasil",
  complement: "Apto 42",
  clt_expectation: 12000.0,
  pj_expectation: 18000.0,
  freelance_expectation: nil,
  current_salary: 10000.0,
  desired_salary: 15000.0,
  currency: "BRL",
  remote_work: "hybrid",
  mobility: "yes",
  source: "linkedin",
  completed_register: true,
  accept_terms: true,

  # === Process Fields ===
  selective_process_name: "triagem",         # lowercased

  # === Evaluation Fields (dynamic per job) ===
  evaluation_candidate_scores: { "english_test_42": 85.0 },
  evaluation_candidate_summaries: { "english_test_42": "Good performance" },
  english_test_42: 85.0,                    # dynamic field

  # === Favorite/Pin ===
  favorite_user_ids: [1, 3],
  is_candidate_favorite: true,
  candidate_feedback: "positive"             # "positive", "negative", nil
}
```

---

## Common Use Cases

### Kanban: Get applies by job grouped by status

```
GET /v1/users/applies?where[job_id]=456&where[is_deleted]=false&order[selective_process_status]=asc&limit=30
```

### Find apply by candidate email

```
GET /v1/users/applies?where[email]=joao@email.com
```

### Get all pinned applies

```
GET /v1/users/applies?where[pin_user_ids]=CURRENT_USER_ID
```

### Get high-score candidates for a job

```
GET /v1/users/applies?where[job_id]=456&where[cv_match][gte]=80&order[cv_match]=desc
```

### Get applies with evaluation completed

```
GET /v1/users/applies?where[job_id]=456&where[evaluation_candidate_status]=answered
```

### Get applies with alerts

```
GET /v1/users/applies?where[job_id]=456&where[alerts_count][gte]=1
```

### Get applies by salary range

```
GET /v1/users/applies?where[job_id]=456&where[clt_expectation][gte]=5000&where[clt_expectation][lte]=15000
```

### Get applies from specific source

```
GET /v1/users/applies?where[source]=linkedin&where[job_id]=456
```

### Get applies by city

```
GET /v1/users/applies?where[city]=são paulo&where[job_id]=456
```

### Get applies created in date range

```
GET /v1/users/applies?where[created_at][gte]=2026-01-01&where[created_at][lte]=2026-01-31&where[job_id]=456
```

### Move candidate to next stage

```
PUT /v1/users/applies/123
{
  "apply": {
    "selective_process_id": 6,
    "selective_process_status": "Entrevista"
  }
}
```

### Pin a candidate

```
PUT /v1/users/applies/123
{
  "apply": { "pin": true }
}
```

### Reject with reason

```
PUT /v1/users/applies/123
{
  "apply": {
    "selective_process_id": 99,
    "selective_process_status": "Reprovado",
    "reason_for_reject": "Não atende requisitos técnicos",
    "reason_code": "SKILL_MISMATCH",
    "reason_category": "Técnica"
  }
}
```

### Add candidate from sourced profile to job

```
POST /v1/users/applies/create_collection
{
  "collections": [
    { "reference_type": "SourcedProfile", "reference_id": 200 }
  ],
  "apply_collection": {
    "job_id": 456,
    "selective_process_id": 5,
    "selective_process_status": "Triagem"
  }
}
```

### Bulk move all "Triagem" to "Entrevista"

```
PUT /v1/users/applies/update_collection
{
  "select_all_params": {
    "search": "*",
    "where": { "job_id": 456, "selective_process_status": "Triagem" }
  },
  "apply": {
    "selective_process_id": 6,
    "selective_process_status": "Entrevista"
  }
}
```

---

## Aggregations

When called with `include_aggregators=true`, the index returns aggregated counts:

```
GET /v1/users/applies?where[job_id]=456&include_aggregators=true
```

Response includes:

```json
{
  "meta": {
    "total": 150,
    "aggregators": {
      "selective_process_status": {
        "buckets": [
          { "key": "Triagem", "doc_count": 80 },
          { "key": "Entrevista", "doc_count": 45 },
          { "key": "Proposta", "doc_count": 15 },
          { "key": "Reprovado", "doc_count": 10 }
        ]
      },
      "candidate_feedback": {
        "buckets": [
          { "key": "positive", "doc_count": 50 },
          { "key": "negative", "doc_count": 20 }
        ]
      }
    }
  }
}
```

---

## Error Responses

### 400 Bad Request

```json
{ "error": "collections parameter is required" }
```

### 404 Not Found

```json
{ "error": "Apply não encontrado" }
```

### 422 Unprocessable Entity

```json
{ "errors": ["candidate_id e job_id são obrigatórios"] }
```

### 403 Forbidden

```json
{ "error": "Not authorized" }
```
