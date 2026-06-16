# API Documentation — Jobs, Selective Processes & LinkedIn Imports

Base URL: `https://<host>/v1/users`

All endpoints require JWT authentication via `Authorization: Bearer <token>`.

---

## Table of Contents

1. [Jobs](#jobs)
   - [List Jobs (Search)](#list-jobs-search)
   - [Show Job](#show-job)
   - [Create Job](#create-job)
   - [Update Job](#update-job)
   - [Delete Job](#delete-job)
   - [Publish / Unpublish](#publish--unpublish)
   - [Change Status](#change-status)
   - [Copy Job](#copy-job)
   - [Bulk Actions](#bulk-actions)
   - [Enum Endpoints](#enum-endpoints)
2. [Selective Processes](#selective-processes)
   - [List Selective Processes (Search)](#list-selective-processes-search)
   - [Show / Create / Update / Delete](#selective-process-crud)
   - [Reorder](#reorder-selective-processes)
3. [LinkedIn Imports](#linkedin-imports)
4. [Search System — How it Works](#search-system)
   - [Params: search, where, order, filter, page, per_page](#search-params)
   - [Where Operators](#where-operators)

---

## Jobs

### List Jobs (Search)

```
GET /v1/users/jobs
```

Uses Searchkick full-text search. Returns JSON:API format.

#### Query Params

| Param | Type | Description |
|---|---|---|
| `search` | string | Full-text search term. Default: `"*"` (all) |
| `where` | JSON string | Structured filters (see [Where Filters](#job-where-filters)) |
| `order` | JSON string | Sort order. Default: `{"created_at": "desc"}` |
| `filter` | JSON string | Alternative filter syntax with `like` support |
| `page` | integer | Page number (1-based). Default: `1` |
| `per_page` | integer | Results per page. Max: `30`. Default: `30` |
| `compact` | string | Comma-separated fields for lightweight response |
| `includes` | string | Comma-separated relationships to include |

#### Example: Basic search

```bash
curl -X GET "https://<host>/v1/users/jobs?search=developer" \
  -H "Authorization: Bearer <token>"
```

#### Example: With where filters

```bash
curl -X GET 'https://<host>/v1/users/jobs?where={"is_active":true,"city":"São Paulo"}' \
  -H "Authorization: Bearer <token>"
```

#### Example: With ordering

```bash
curl -X GET 'https://<host>/v1/users/jobs?order={"published_date":"desc"}' \
  -H "Authorization: Bearer <token>"
```

#### Example: Compact mode (lightweight response)

```bash
curl -X GET "https://<host>/v1/users/jobs?compact=id,title,city,is_active" \
  -H "Authorization: Bearer <token>"
```

#### Job Where Filters

All fields indexed in `search_data` can be used as filters in the `where` param:

| Field | Type | Example | Description |
|---|---|---|---|
| `is_active` | boolean | `true` / `false` | Active/paused status |
| `is_deleted` | boolean | `false` | Soft-delete filter (auto-set to `false`) |
| `is_published` | boolean | `true` | Published status |
| `is_archived` | boolean | `false` | Archived status |
| `is_remote` | boolean | `true` | Remote job |
| `is_urgent` | boolean | `true` | Urgent flag |
| `is_pcd` | boolean | `true` | PCD (disabilities) position |
| `is_screening_active` | boolean | `true` | AI screening enabled |
| `city` | string | `"são paulo"` | City (lowercase) |
| `state` | string | `"sp"` | State (lowercase) |
| `country` | string | `"brazil"` | Country (lowercase) |
| `title` | string | `"developer"` | Job title (lowercase) |
| `user_id` | integer | `42` | Recruiter/owner ID |
| `user_name` | string | `"maria"` | Recruiter name (lowercase) |
| `company_id` | integer | `5` | Company ID |
| `company_name` | string | `"acme"` | Company name (lowercase) |
| `job_status_id` | integer | `1` | Job status ID |
| `job_status_name` | string | `"Em andamento"` | Job status name |
| `department_id` | integer | `3` | Department ID |
| `department_name` | string | `"engineering"` | Department name |
| `seniority` | integer | `0`-`7` | Seniority index (see enum below) |
| `seniority_text` | string | `"Pleno"` | Seniority label |
| `employment_type` | integer | `0`-`5` | Employment type index (see enum below) |
| `employment_type_text` | string | `"CLT"` | Employment type label |
| `workplace_type` | integer | `1`-`3` | Workplace type (see enum below) |
| `priority` | integer | `1`-`3` | Priority level |
| `urgency_level` | integer | `1`-`5` | Urgency level |
| `salary_from` | number | `5000` | Minimum salary (numeric range) |
| `salary_to` | number | `10000` | Maximum salary (numeric range) |
| `provider` | string | `"linkedin"` | External provider source |
| `external_id` | string | `"EXT-123"` | External system ID |
| `workflow_template_id` | integer | `2` | Workflow template ID |
| `hiring_manager_id` | integer | `7` | Hiring manager user ID |
| `confidential_type` | integer | | Confidential type |
| `has_linkedin_post` | boolean | `true` | Published on LinkedIn |
| `has_website_post` | boolean | `true` | Published on website |
| `has_indeed_post` | boolean | `true` | Published on Indeed |
| `total_applies` | integer | `10` | Total apply count |
| `has_deadline` | boolean | `true` | Has application deadline |
| `is_deadline_expired` | boolean | `true` | Deadline has passed |
| `published_date` | date | `"2025-01-01"` | Publication date (ranges supported) |
| `created_at` | datetime | | Creation date (ranges supported) |
| `closing_deadline` | date | | Closing deadline (ranges supported) |

#### Seniority Enum

| Index | Value |
|---|---|
| 0 | Júnior |
| 1 | Pleno |
| 2 | Sênior |
| 3 | Especialista |
| 4 | Estágio |
| 5 | Lead |
| 6 | Gerente |
| 7 | Diretor |

#### Employment Type Enum

| Index | Value |
|---|---|
| 0 | CLT |
| 1 | PJ |
| 2 | Estágio |
| 3 | Temporário |
| 4 | Freelancer |
| 5 | Aprendiz |

#### Workplace Type Enum

| ID | Value |
|---|---|
| 1 | Remoto |
| 2 | Híbrido |
| 3 | Presencial |

#### Priority Enum

| ID | Value |
|---|---|
| 1 | Alta |
| 2 | Média |
| 3 | Baixa |

#### Urgency Level Enum

| ID | Value |
|---|---|
| 1 | Baixa |
| 2 | Moderada |
| 3 | Média |
| 4 | Alta |
| 5 | Crítica |

---

### Show Job

```
GET /v1/users/jobs/:id
```

Returns a single job in JSON:API format with all attributes and relationships.

---

### Create Job

```
POST /v1/users/jobs
```

#### Body

```json
{
  "job": {
    "title": "Backend Developer",
    "description": "<p>Job description HTML</p>",
    "city": "São Paulo",
    "state": "SP",
    "seniority": 2,
    "employment_type": 0,
    "workplace_type": 1,
    "is_remote": true,
    "department_id": 3,
    "hiring_manager_id": 7,
    "responsibilities": ["Develop APIs", "Code reviews"],
    "skills": [
      { "name": "Ruby on Rails" },
      { "name": "PostgreSQL" }
    ],
    "benefits": [
      { "name": "Vale Refeição" },
      { "name": "Plano de Saúde" }
    ],
    "selective_processes_attributes": [
      { "name": "Funil", "status": 0, "position": 0 },
      { "name": "Triagem", "status": 1, "position": 1 },
      { "name": "Entrevista", "status": 2, "position": 2 }
    ]
  }
}
```

If `selective_processes_attributes` is omitted, default selective processes are created automatically (Funil, Triagem, Entrevista, Reprovados).

**Response:** `201 Created` with the job in JSON:API format.

---

### Update Job

```
PUT /v1/users/jobs/:id
```

Same body structure as create. Only send fields you want to update.

**Response:** `200 OK` with updated job.

---

### Delete Job

```
DELETE /v1/users/jobs/:id
```

Soft-deletes the job (`is_deleted: true`).

**Response:** `200 OK`

---

### Publish / Unpublish

```
POST /v1/users/jobs/:id/publish
POST /v1/users/jobs/:id/unpublish
```

Publish validates required fields. If fields are missing, returns `422` with `missing_fields` array.

**Response:** `200 OK` with updated job, or `422` with errors.

---

### Change Status

```
POST /v1/users/jobs/:id/change_status
```

```json
{
  "job_status_id": 3,
  "reason": "Position filled"
}
```

**Response:** `200 OK` or `422` with `allowed_transitions`.

---

### Copy Job

```
POST /v1/users/jobs/:id/copy
```

```json
{
  "job": {
    "user_id": 5,
    "entities": ["skills", "benefits", "selective_processes"]
  }
}
```

**Bulk copy:**

```
POST /v1/users/jobs/:id/copy_job_by_amount
```

```json
{
  "amount": 3,
  "job": {
    "entities": ["skills", "benefits"]
  }
}
```

---

### Bulk Actions

#### Archive / Unarchive / Activate / Pause (collection)

```
POST /v1/users/jobs/archive
POST /v1/users/jobs/unarchive
POST /v1/users/jobs/activate
POST /v1/users/jobs/pause
```

```json
{
  "select_all_params": {
    "where": { "is_active": true },
    "search": "*"
  },
  "reason": "Budget constraints"
}
```

#### Bulk Update

```
POST /v1/users/jobs/bulk_update
```

```json
{
  "job_ids": [1, 2, 3],
  "fields": {
    "is_active": false,
    "reason_for_pause": "On hold"
  }
}
```

---

### Enum Endpoints

These return plain JSON (not JSON:API).

```
GET /v1/users/jobs/priorities
GET /v1/users/jobs/urgency_levels
GET /v1/users/jobs/workplace_types
GET /v1/users/jobs/employment_types
GET /v1/users/jobs/seniorities
GET /v1/users/jobs/pcd_categories
GET /v1/users/jobs/confidential_types
```

**Response format:**

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Júnior", "id": 0 } },
    { "id": "1", "attributes": { "name": "Pleno", "id": 1 } }
  ]
}
```

---

### Other Job Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/jobs/:id/analytics` | Job analytics dashboard |
| GET | `/jobs/:id/matching_candidates` | AI-matched candidates |
| GET | `/jobs/:id/context_for_ai` | AI context data |
| GET | `/jobs/:id/activity_log` | Activity log |
| GET | `/jobs/:id/evaluations` | Linked evaluations |
| GET | `/jobs/:id/export` | Export job data (CSV) |
| POST | `/jobs/:id/add_candidates_from_list` | Add candidates from a list |
| POST | `/jobs/:id/duplicate_selective_processes` | Copy SP from another job |
| POST | `/jobs/:id/auto_source` | Start AI auto-sourcing |
| GET | `/jobs/stats` | Global stats (with date range) |
| GET | `/jobs/alerts` | Job alerts |
| GET | `/jobs/pipeline_health` | Pipeline health metrics |

---

## Selective Processes

### List Selective Processes (Search)

```
GET /v1/users/selective_processes
```

Uses Searchkick search. **Requires `job_id` in `where` param.**

#### Query Params

| Param | Type | Description |
|---|---|---|
| `search` | string | Full-text search. Default: `"*"` |
| `where` | JSON string | Must include `job_id` |
| `order` | JSON string | Sort order |
| `page` | integer | Page number |
| `per_page` | integer | Max `30` |

#### Example: List all selective processes for a job

```bash
curl -X GET 'https://<host>/v1/users/selective_processes?where={"job_id":1590}' \
  -H "Authorization: Bearer <token>"
```

#### Example: Filter by status

```bash
curl -X GET 'https://<host>/v1/users/selective_processes?where={"job_id":1590,"status":"web_submission"}' \
  -H "Authorization: Bearer <token>"
```

#### Selective Process Where Filters

| Field | Type | Example | Description |
|---|---|---|---|
| `job_id` | integer | `1590` | **Required.** Filter by job |
| `id` | integer | `123` | Selective process ID |
| `name` | string | `"Funil"` | Process name |
| `status` | string | `"web_submission"` | Status enum value |
| `position` | integer | `0` | Display position |
| `workflow_template_id` | integer | `2` | Workflow template ID |
| `account_id` | integer | `1` | Account ID |

#### Status Enum

| Value | Integer | Color | Description |
|---|---|---|---|
| `web_submission` | 0 | `#a8ced5` | Entry funnel (default first step) |
| `screening` | 1 | `#d5bfa8` | Screening phase |
| `interview` | 2 | `#a8d5b7` | Interview phase |
| `rejected` | 3 | `#FCA5A5` | Rejected |
| `hired` | 4 | `#bfa8d5` | Hired |

#### Response Attributes

| Attribute | Description |
|---|---|
| `id` | Selective process ID |
| `name` | Display name |
| `position` | Sort order |
| `job_id` | Associated job ID |
| `status` | Status string (e.g. `"web_submission"`) |
| `status_code` | Status integer |
| `status_label` | Translated label |
| `color` | Hex color |
| `color_with_fallback` | Color with default fallback |
| `sub_status` | Array of sub-status codes |
| `sub_status_options` | Available sub-statuses for this status |
| `action_behavior` | Action type for this status |
| `duration` | Duration configuration |
| `approved_process_id` | Next process on approval |
| `rejected_process_id` | Next process on rejection |

---

### Selective Process CRUD

#### Show

```
GET /v1/users/selective_processes/:id
```

#### Create

```
POST /v1/users/selective_processes
```

```json
{
  "selective_process": {
    "name": "Technical Interview",
    "status": 2,
    "position": 3,
    "job_id": 1590,
    "color": "#a8d5b7"
  }
}
```

**Response:** `201 Created`

#### Update

```
PUT /v1/users/selective_processes/:id
```

```json
{
  "selective_process": {
    "name": "Final Interview",
    "position": 4
  }
}
```

#### Delete

```
DELETE /v1/users/selective_processes/:id
```

Soft-delete (`is_deleted: true`).

---

### Reorder Selective Processes

```
POST /v1/users/selective_processes/order
```

```json
{
  "selective_processes": [
    { "id": 100, "position": 0 },
    { "id": 101, "position": 1 },
    { "id": 102, "position": 2 }
  ]
}
```

---

## LinkedIn Imports

### Import Candidates from LinkedIn URLs

```
POST /v1/users/linkedin_imports
```

Parses LinkedIn profiles via Apify, creates candidates with full data (experiences, skills, educations, languages), and creates applies linking them to the job.

**Runs asynchronously via Sidekiq.** Returns immediately with `202 Accepted`.

#### Body

```json
{
  "linkedin_import": {
    "job_id": 1590,
    "selective_process_id": 17513,
    "linkedin_urls": [
      "https://www.linkedin.com/in/john-doe",
      "https://www.linkedin.com/in/jane-smith",
      "https://www.linkedin.com/in/carlos-silva"
    ]
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `job_id` | integer | Yes | Target job ID |
| `selective_process_id` | integer | Yes | Target selective process ID (must belong to the job) |
| `linkedin_urls` | array of strings | Yes | LinkedIn profile URLs to import |

#### Success Response — `202 Accepted`

```json
{
  "status": "processing",
  "message": "3 LinkedIn profiles are being imported in background",
  "job_id": 1590,
  "selective_process_id": 17513,
  "total_urls": 3
}
```

#### Error Responses

**Missing/Invalid Job — `404 Not Found`**

```json
{
  "errors": ["Job não encontrado"]
}
```

**Missing/Invalid Selective Process — `404 Not Found`**

```json
{
  "errors": ["SelectiveProcess não encontrado"]
}
```

**Empty URLs — `400 Bad Request`**

```json
{
  "errors": ["linkedin_urls is required"]
}
```

#### What Happens in Background

For each LinkedIn URL:

1. **Profile parsing** — Apify fetches the LinkedIn profile data (name, headline, about, experiences, skills, educations, languages, avatar)
2. **Candidate deduplication** — Finds existing candidate by email or LinkedIn slug, or creates new
3. **Data enrichment** — Populates skills, experiences (with company/occupation), educations (with institution/study area), languages, avatar, curriculum text
4. **Apply creation** — Creates an apply linking candidate to the job at the specified selective process step (idempotent — won't duplicate existing applies)

---

## Search System

All list endpoints use Searchkick (Elasticsearch) for full-text search with structured filtering.

### Search Params

| Param | Type | Description |
|---|---|---|
| `search` | string | Full-text query. `"*"` returns all records. Searches across configured fields with weighted relevance. |
| `where` | JSON string | Exact-match filters on indexed fields. Example: `{"is_active": true, "city": "são paulo"}` |
| `filter` | JSON string | Alternative filter with `like` support for partial matching |
| `order` | JSON string | Sort fields. Example: `{"created_at": "desc"}`. Use `"score"` for relevance. |
| `page` | integer | Page number (1-based) |
| `per_page` | integer | Items per page (max 30) |

### Where Operators

The `where` param supports Searchkick operators:

#### Exact match

```json
{ "is_active": true }
{ "user_id": 42 }
{ "status": "web_submission" }
```

#### Array (IN / any of)

```json
{ "seniority": [0, 1, 2] }
{ "city": ["são paulo", "rio de janeiro"] }
```

#### Range (gt, gte, lt, lte)

```json
{ "salary_from": { "gte": 5000 } }
{ "created_at": { "gte": "2025-01-01", "lte": "2025-12-31" } }
{ "total_applies": { "gt": 10 } }
```

#### Null check

```json
{ "hiring_manager_id": null }
{ "hiring_manager_id": [null] }
```

#### NOT (exclude)

```json
{ "city": { "not": "são paulo" } }
{ "job_status_id": { "not": [3, 4] } }
```

#### OR conditions

Use the `filter` param for OR logic. Each array value creates an OR condition:

```json
// filter param:
{ "city": ["São Paulo", "Rio de Janeiro"] }
```

This creates: `city = "São Paulo" OR city = "Rio de Janeiro"` with `like` matching.

#### Combined Example

```bash
curl -X GET 'https://<host>/v1/users/jobs?search=backend&where={"is_active":true,"seniority":[1,2],"city":"são paulo","salary_from":{"gte":8000}}&order={"published_date":"desc"}&per_page=10&page=1' \
  -H "Authorization: Bearer <token>"
```

This searches for "backend" jobs that are active, Pleno or Sênior, in São Paulo, with salary >= 8000, sorted by publication date.

### Response Format (JSON:API)

```json
{
  "data": [
    {
      "id": "1590",
      "type": "job",
      "attributes": {
        "title": "Backend Developer",
        "city": "São Paulo",
        "is_active": true
      }
    }
  ],
  "meta": {
    "total": 42,
    "where": { "is_active": true }
  }
}
```

The `meta.total` field contains the total count of matching records (not just the current page).
