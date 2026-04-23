# WeDO Talent ATS — API Documentation (Users Namespace)

> **Base URL:** `/v1/users`
> **Authentication:** Bearer JWT token in `Authorization` header
> **Response Format:** JSON:API (`jsonapi-serializer`)
> **Content-Type:** `application/json`

---

## Table of Contents

- [Authentication](#authentication)
- [Search System (Global)](#search-system-global)
- [Jobs](#jobs)
- [Candidates](#candidates)
- [Applies (Applications)](#applies-applications)
- [Selective Processes](#selective-processes)
- [Evaluations](#evaluations)
- [Evaluation Candidates](#evaluation-candidates)
- [Messages](#messages)
- [Workspaces](#workspaces)
- [Sourcings](#sourcings)
- [Sourced Profiles](#sourced-profiles)
- [Sourced Profile Sourcings](#sourced-profile-sourcings)
- [Search Archetypes](#search-archetypes)
- [Lists](#lists)
- [List Relationships](#list-relationships)
- [Skills](#skills)
- [Skill Relationships](#skill-relationships)
- [Behavioral Skills](#behavioral-skills)
- [Behavioral Skill Relationships](#behavioral-skill-relationships)
- [Benefits](#benefits)
- [Benefit Relationships](#benefit-relationships)
- [Remunerations](#remunerations)
- [Remuneration Relationships](#remuneration-relationships)
- [Languages](#languages)
- [Language Relationships](#language-relationships)
- [Experiences](#experiences)
- [Educations](#educations)
- [Companies](#companies)
- [Occupations](#occupations)
- [Institutions](#institutions)
- [Study Areas](#study-areas)
- [Departments](#departments)
- [Department Relationships](#department-relationships)
- [Teams](#teams)
- [Team Members](#team-members)
- [Organizational Positions](#organizational-positions)
- [Position Assignments](#position-assignments)
- [Approvers](#approvers)
- [Approval Requests](#approval-requests)
- [Businesses](#businesses)
- [Meetings](#meetings)
- [Calendar Events](#calendar-events)
- [Scheduling](#scheduling)
- [Interview Sessions](#interview-sessions)
- [Notifications](#notifications)
- [Notification Preferences](#notification-preferences)
- [Email Templates](#email-templates)
- [Data Files](#data-files)
- [Activity Logs](#activity-logs)
- [Feedbacks](#feedbacks)
- [Candidate Feedbacks](#candidate-feedbacks)
- [Workflow Templates](#workflow-templates)
- [Job Statuses](#job-statuses)
- [Job Users](#job-users)
- [Job Journeys](#job-journeys)
- [Job Field Templates](#job-field-templates)
- [Apply Statuses](#apply-statuses)
- [Entity Columns](#entity-columns)
- [Entity Pages](#entity-pages)
- [Sectors](#sectors)
- [Sector Relationships](#sector-relationships)
- [Issues](#issues)
- [Dispatches](#dispatches)
- [Answers](#answers)
- [Audio Messages](#audio-messages)
- [Dashboard](#dashboard)
- [Productivity](#productivity)
- [Aggregators](#aggregators)
- [Account](#account)
- [LLM Usages](#llm-usages)
- [LLM Quotas](#llm-quotas)
- [Addresses](#addresses)
- [Address Relationships](#address-relationships)
- [Bulk Imports](#bulk-imports)
- [Candidate Imports](#candidate-imports)
- [Lookups (Cities, States, Countries, etc.)](#lookups)
- [Microsoft Integration](#microsoft-integration)
- [Admin Namespace](#admin-namespace)

---

## Authentication

All endpoints under `/v1/users` require a valid JWT token:

```
Authorization: Bearer <jwt_token>
```

The token is obtained from `POST /v1/sessions` and contains `user_id` and `account_id`. The API automatically switches to the correct tenant schema based on the token.

---

## Search System (Global)

Most `index` endpoints use **Searchkick** (Elasticsearch) for search, filtering, ordering, and pagination. The following query parameters are available on **all searchable index endpoints**:

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | `string` | `"*"` (all) | Full-text search term. Use `*` for all records |
| `term` | `string` | — | Alternative search term (takes priority over `search`) |
| `where` | `JSON string` or `object` | `{}` | Structured Elasticsearch filters (exact match, range, etc.) |
| `filter` | `JSON string` or `object` | `{}` | High-level filters — arrays become `_or` with `like` matching |
| `order` | `JSON string` or `object` | `{"created_at":"desc"}` | Sort order |
| `page` | `integer` | `1` | Page number (1-based) |
| `per_page` / `limit` | `integer` | `30` | Results per page (max 30) |
| `boost_where` | `JSON string` | — | Additional boost conditions |
| `compact` | `string` | — | Comma-separated attribute names to return raw (bypasses serializer) |
| `preset` | `string` | — | AI sparse-fieldset preset (`list`, `minimal`, `contact`) |
| `fields` | `string` or `object` | — | Comma-separated attribute whitelist for serializer |
| `includes` | `string` | — | Relationship inclusion hints for serializer |
| `extra_params` | `string` | — | Semicolon-separated model scope calls (e.g., `"with_applies(true);active"`) |
| `entity_column_id` | `integer` | — | EntityColumn ID for dynamic aggregation filtering |

### Where Filter Operators

The `where` parameter supports Searchkick operators:

```json
// Exact match
{ "where": { "status": "active" } }

// Range
{ "where": { "created_at": { "gte": "2024-01-01", "lte": "2024-12-31" } } }

// Greater than / Less than
{ "where": { "score": { "gt": 80 } } }

// NOT
{ "where": { "status": { "not": "archived" } } }

// LIKE (fuzzy)
{ "where": { "name": { "like": "%john%" } } }

// OR conditions
{ "where": { "_or": [{ "status": "active" }, { "status": "pending" }] } }

// AND conditions
{ "where": { "_and": [{ "status": "active" }, { "priority": "high" }] } }

// Array (IN)
{ "where": { "status": ["active", "pending"] } }

// NULL check
{ "where": { "field": null } }

// Boolean
{ "where": { "is_deleted": false } }
```

### Filter Parameter

The `filter` parameter provides a higher-level filtering interface:

```json
// Fuzzy match (uses LIKE %value%)
{ "filter": { "name": "john" } }

// Array values create OR conditions with LIKE matching
{ "filter": { "city": ["São Paulo", "Rio de Janeiro"] } }

// ID fields (id, external_id) use exact match
{ "filter": { "id": "123" } }

// Special: favorited filter
{ "filter": { "is_favorited": ["Favoritado"] } }
```

### Pin & Confidential System

Endpoints that use `search_with_pin` automatically:
- **Boost pinned items** to the top of results
- **Filter confidential** records (only visible to assigned users)

### Response Format

```json
{
  "data": [
    {
      "id": "1",
      "type": "resource",
      "attributes": { ... },
      "relationships": { ... }
    }
  ],
  "meta": {
    "total": 100,
    "where": { ... },
    "search": "keyword"
  }
}
```

### Compact Mode

When `compact` is passed, the response bypasses JSON:API format:

```json
// GET /v1/users/jobs?compact=id,title,city
{
  "data": [
    { "id": 1, "title": "Developer", "city": "SP" }
  ],
  "meta": { "total": 50 }
}
```

---

## Jobs

### `GET /v1/users/jobs`
Search jobs with pin/confidential filtering.

**Query params:** [Search System params](#search-system-global) + `compact`

### `GET /v1/users/jobs/:id`
Show a single job.

### `POST /v1/users/jobs`
Create a new job.

**Body:**
```json
{
  "job": {
    "title": "Software Engineer",
    "description": "Job description...",
    "user_id": 1,
    "department_id": 5,
    "city": "São Paulo",
    "state": "SP",
    "employment_type": 0,
    "workplace_type": 0,
    "seniority": 2,
    "salary_from": 8000,
    "salary_to": 12000,
    "salary_currency": "BRL",
    "salary_period": "monthly",
    "is_active": true,
    "responsibilities": ["Code review", "Development"],
    "selective_processes_attributes": [
      { "name": "Applied", "position": 0, "color": "#ccc" }
    ]
  }
}
```

**Full field list:** `title`, `description`, `user_id`, `account_id`, `job_status_id`, `published_date`, `application_deadline`, `is_remote`, `company_id`, `friendly_badge`, `disabilities`, `workplace_type`, `city`, `state`, `pin`, `confidential`, `provider`, `provider_job_id`, `external_id`, `job_url`, `department`, `employment_type`, `salary_from`, `salary_to`, `salary_currency`, `salary_period`, `salary_contract_type`, `commission_from`, `commission_to`, `commission_currency`, `commission_period`, `bonus_from`, `bonus_to`, `bonus_currency`, `bonus_period`, `seniority`, `is_urgent`, `is_deleted`, `is_active`, `reason_for_pause`, `screening_deadline`, `shortlist_deadline`, `closing_deadline`, `priority`, `urgency_level`, `is_screening_active`, `department_id`, `required_pcd_files`, `main_pcd_category`, `secondary_pcd_category`, `pcd_description`, `pcd_files_description`, `sector`, `segment`, `target_audience`, `has_linkedin_post`, `has_website_post`, `has_indeed_post`, `confidential_type`, `confidential_company_name`, `hiring_manager_id`, `use_whatsapp_channel`, `use_webchat_channel`, `use_call_channel`, `minimum_screening_score`, `screening_timeout`, `screening_max_attempts`, `screening_approve_limit`, `interview_minimum_score`, `has_automatic_interview`, `interview_calendar_type`, `interview_hours_range`, `interview_duration`, `responsibilities[]`, `selective_processes_attributes[]`

### `PUT /v1/users/jobs/:id`
Update a job.

### `DELETE /v1/users/jobs/:id`
Destroy a job (hard delete).

### `POST /v1/users/jobs/:id/copy`
Copy a job via `Jobs::CopyService`.

**Body:**
```json
{
  "job": {
    "user_id": 1,
    "entities": ["selective_processes", "skills", "benefits"]
  }
}
```

### `POST /v1/users/jobs/:id/copy_job_by_amount`
Bulk copy a job (async via Sidekiq).

**Body:**
```json
{ "amount": 5, "job": { "user_id": 1, "entities": ["selective_processes"] } }
```

### `POST /v1/users/jobs/:id/change_status`
Change job status.

**Body:** `{ "job_status_id": 3, "reason": "Filled" }`

### `POST /v1/users/jobs/:id/publish`
Publish a job.

### `POST /v1/users/jobs/:id/unpublish`
Unpublish a job.

### `POST /v1/users/jobs/:id/duplicate_selective_processes`
Duplicate selective processes from another job.

**Body:** `{ "source_job_id": 10, "replace": true }`

### `POST /v1/users/jobs/:id/add_candidates_from_list`
Add candidates from a list to a job (async).

**Body:** `{ "list_id": 5, "selective_process_id": 3 }`

### `GET /v1/users/jobs/:id/export`
Export job data. **Query:** `format=csv`

### `POST /v1/users/jobs/bulk_update`
Bulk update multiple jobs.

**Body:** `{ "job_ids": [1, 2, 3], "fields": { "is_active": false } }`

### `POST /v1/users/jobs/archive`
Bulk archive jobs.

**Body:** `{ "select_all_params": { ... }, "is_archived": true }`

### `POST /v1/users/jobs/unarchive`
Bulk unarchive jobs.

### `POST /v1/users/jobs/activate`
Bulk activate jobs.

**Body:** `{ "select_all_params": { ... }, "reason": "Re-opening" }`

### `POST /v1/users/jobs/pause`
Bulk pause jobs.

### `POST /v1/users/jobs/boolean_search`
Generate LinkedIn boolean search string from job.

**Body:** `{ "job_id": 5 }`

### `GET /v1/users/jobs/stats`
Job statistics.

**Query:** `start_date`, `end_date`

### `GET /v1/users/jobs/alerts`
Job alerts.

### `GET /v1/users/jobs/data_for_description`
Get job data for description generation (includes remunerations, benefits, skills, languages).

### Enum Lookups

| Endpoint | Returns |
|----------|---------|
| `GET /v1/users/jobs/priorities` | Priority options |
| `GET /v1/users/jobs/urgency_levels` | Urgency level options |
| `GET /v1/users/jobs/workplace_types` | Workplace type options |
| `GET /v1/users/jobs/employment_types` | Employment type options |
| `GET /v1/users/jobs/seniorities` | Seniority options |
| `GET /v1/users/jobs/pcd_categories` | PCD category options |
| `GET /v1/users/jobs/confidential_types` | Confidential type options |

### Job Sub-Resources

#### `GET /v1/users/jobs/:job_id/kanban`
Returns kanban board data (columns + applies per selective process stage).

**Query:** `term`, `page`, `selective_process_id`, `where` filters

#### `GET /v1/users/jobs/:job_id/analytics`
Returns job analytics data.

**Query:** `force_refresh=true` to bypass cache

#### `GET /v1/users/jobs/:job_id/context_for_ai`
Returns structured job context for AI consumption.

**Query:** `tier=1` (basic) or `tier=2` (with analytics + activity)

#### `GET /v1/users/jobs/:job_id/matching_candidates`
Find matching candidates via embedding similarity.

**Query:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_k` | integer | 500 | Max candidates to evaluate (max 2000) |
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Results per page (max 100) |
| `min_score` | float | — | Minimum similarity score (0-1.0) |
| `max_score` | float | — | Maximum similarity score (0-1.0) |
| `filters` | object | — | Additional filters |
| `include` | string | — | Comma-separated includes |

#### `GET /v1/users/jobs/:job_id/evaluations`
Returns evaluations linked to a job.

#### `GET /v1/users/jobs/:job_id/activity_log`
Returns activity log for a job.

#### `POST /v1/users/jobs/:job_id/auto_source`
Start auto-sourcing for a job (returns WebSocket subscription).

**Query:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 30 | Number of candidates (1-100) |
| `min_score` | integer | 70 | Minimum score (0-100) |
| `sources` | array | — | `["local"]`, `["global"]`, or both |
| `reset` | boolean | false | Reset existing results |

#### `POST /v1/users/jobs/:job_id/applies/approve_collection`
Bulk approve applies for a job.

**Body:** `{ "select_all_params": { ... } }`

#### `POST /v1/users/jobs/:job_id/applies/reject_collection`
Bulk reject applies for a job.

**Body:** `{ "select_all_params": { ... } }`

#### `POST /v1/users/jobs/:job_id/suggestion`
Generate AI suggestion for a job.

**Body:**
```json
{
  "type": "description",
  "job": {
    "id": 1,
    "title": "Dev",
    "description": "...",
    "responsibilities": [],
    "skills": [],
    "behavioral_skills": []
  }
}
```

#### `POST /v1/users/jobs/:job_id/suggestion/questions`
Generate evaluation questions.

**Body:** `{ "type": "wsi", "evaluation_id": 5, "query": "..." }`

#### `POST /v1/users/jobs/generate_query_from_job`
Generate search queries from recent jobs.

#### `GET /v1/users/jobs/matches/candidates`
Find candidate matches across all jobs.

---

## Candidates

### `GET /v1/users/candidates`
Search candidates with pin support. Default filter: `is_deleted: false`.

### `GET /v1/users/candidates/:id`
Show a candidate.

### `POST /v1/users/candidates`
Create a candidate.

**Body:**
```json
{
  "candidate": {
    "name": "João Silva",
    "email": "joao@email.com",
    "mobile_phone": "+5511999999999",
    "role_name": "Software Engineer",
    "city": "São Paulo",
    "state": "SP",
    "source": "linkedin",
    "curriculum_text": "Resume text..."
  }
}
```

**Full field list:** `name`, `email`, `secondary_email`, `mobile_phone`, `phone`, `secondary_phone`, `linkedin`, `github`, `portfolio`, `current_company`, `role_name`, `position_level`, `self_introduction`, `curriculum_text`, `date_birth`, `gender`, `nationality`, `marital_status`, `cpf`, `street`, `number`, `district`, `zip`, `city`, `state`, `country`, `complement`, `clt_expectation`, `pj_expectation`, `freelance_expectation`, `current_salary`, `desired_salary`, `currency`, `remote_work`, `mobility`, `interests`, `comments`, `source`, `curriculum_pdf_url`, `completed_register`, `account_id`, `accept_terms`, `avatar` (file), `pin`, `confidential`, `favorite`, `external_id`, `external_provider`

### `PUT /v1/users/candidates/:id`
Update a candidate (supports `favorite: true/false` toggle).

### `DELETE /v1/users/candidates/:id`
Soft-delete candidate (`is_deleted: true`).

### `GET /v1/users/candidates/stats`
Candidate statistics.

**Query:** `start_date`, `end_date`, `source`

### `GET /v1/users/candidates/:id/calculate_remunerations`
Returns salary/remuneration breakdown with annual calculations.

### `GET /v1/users/candidates/:id/calculate_benefits`
Returns benefits breakdown with annual values.

### `GET /v1/users/candidates/:id/communications`
Returns candidate communication history.

### `GET /v1/users/candidates/suggestions`
AI text suggestions.

**Query:** `text` or `query`

### `GET /v1/users/candidates/prompt_search`
AI-powered natural language search.

**Query:** `search`, `where`, `filter`, `order`

### `POST /v1/users/candidates/generate_query`
Generate search query from filters.

### `POST /v1/users/candidates/upload_resume`
Upload and parse a resume.

**Body (multipart):** `resume_file` (file) or `resume_text` (string), `ai_provider`

---

## Applies (Applications)

### `GET /v1/users/applies`
Search applies with pin support. Default filter: `is_deleted: false`.

### `GET /v1/users/applies/:id`
Show an apply.

### `GET /v1/users/applies/:id/timeline`
Returns apply timeline history.

### `POST /v1/users/applies`
Create an apply (supports external ID resolution).

**Body:**
```json
{
  "apply": {
    "candidate_id": 1,
    "job_id": 5,
    "selective_process_id": 3,
    "selective_process_status": "applied"
  }
}
```

**Full field list:** `candidate_id`, `job_id`, `selective_process_id`, `is_deleted`, `account_id`, `selective_process_status`, `pin`, `confidential`, `external_candidate_id`, `external_job_id`, `external_id`, `updated_at`, `sub_status`, `reason_for_reject`, `reason_code`, `reason_category`, `internal_comment`

### `PUT /v1/users/applies/:id`
Update an apply.

### `DELETE /v1/users/applies/:id`
Soft-delete an apply.

### `POST /v1/users/applies/create_collection`
Bulk create applies.

**Body:** `{ "select_all_params": { ... } }` or `{ "collections": [{ "candidate_id": 1, "job_id": 5 }] }`

### `PUT /v1/users/applies/update_collection`
Bulk update applies (async).

### `DELETE /v1/users/applies/delete_collection`
Bulk delete applies (async).

### `GET /v1/users/applies/stats`
Apply statistics.

**Query:** `start_date`, `end_date`, `job_id`, `user_id`

### `GET /v1/users/applies/aging`
Applies aging report.

**Query:** `days`, `status`, `job_id`, `page`, `per_page`

---

## Selective Processes

### `GET /v1/users/selective_processes`
Search selective processes.

### `GET /v1/users/selective_processes/:id`
Show a selective process.

### `POST /v1/users/selective_processes`
Create a selective process.

**Body:**
```json
{
  "selective_process": {
    "name": "Phone Screen",
    "position": 1,
    "job_id": 5,
    "color": "#4CAF50",
    "sub_status": ["Scheduled", "Completed"]
  }
}
```

**Full field list:** `name`, `position`, `user_id`, `status`, `job_id`, `uid`, `account_id`, `duration`, `workflow_template_id`, `position_x`, `position_y`, `external_id`, `color`, `is_deleted`, `approved_process_id`, `rejected_process_id`, `sub_status[]`, `childrens[]`

### `PUT /v1/users/selective_processes/:id`
Update a selective process.

### `POST /v1/users/selective_processes/order`
Bulk update position ordering.

### `DELETE /v1/users/selective_processes/:id`
Soft-delete selective process.

---

## Evaluations

### `GET /v1/users/evaluations`
Search evaluations.

### `GET /v1/users/evaluations/:id`
Show an evaluation.

### `POST /v1/users/evaluations`
Create an evaluation.

**Body:**
```json
{
  "evaluation": {
    "name": "Technical Assessment",
    "job_id": 5,
    "selective_process_id": 3,
    "status": "active",
    "time": 30,
    "ai_enabled": true,
    "is_chatbot": true
  }
}
```

**Full field list:** `name`, `job_id`, `selective_process_id`, `user_id`, `account_id`, `status`, `position`, `sub_status`, `description`, `is_main`, `time`, `uid`, `is_chatbot`, `ai_enabled`, `report_date`, `chatbot_channel`, `is_trigger`, `notification_enabled`, `notification_type`, `notification_hour`, `approved_selective_process_id`, `rejected_selective_process_id`, `is_screening`, `introduction_details`, `notification_days[]`

### `PUT /v1/users/evaluations/:id`
Update an evaluation.

### `DELETE /v1/users/evaluations/:id`
Soft-delete evaluation.

### `GET /v1/users/evaluations/:id/dashboard_stats`
Returns evaluation dashboard statistics.

### `POST /v1/users/evaluations/:evaluation_id/:job_id/generate_report`
Generate evaluation report.

### Evaluation Questions

#### `GET /v1/users/evaluations/:evaluation_id/questions`
List questions for an evaluation.

#### `GET /v1/users/evaluations/:evaluation_id/questions/:id`
Show a question.

#### `POST /v1/users/evaluations/:evaluation_id/questions`
Create a question.

**Body:**
```json
{
  "question": {
    "title": "What is polymorphism?",
    "description": "Explain OOP concept",
    "response_type": "text",
    "position": 1,
    "time": 120,
    "is_required": true,
    "expected_response": "...",
    "category": "technical",
    "competence_type": "hard_skill"
  }
}
```

**Full field list:** `title`, `description`, `details`, `number_retakers`, `time`, `evaluation_id`, `response_type`, `position`, `deleted`, `selective_process_id`, `expected_response`, `is_required`, `parent_question_id`, `choices`, `value_father`, `extra_params`, `category`, `competence_type`, `framework`, `bloom_level`, `dreyfus_target`, `ocean_trait`, `validation_type_weight`, `framework_weights{}`

#### `PUT /v1/users/evaluations/:evaluation_id/questions/:id`
Update a question.

#### `DELETE /v1/users/evaluations/:evaluation_id/questions/:id`
Delete a question.

---

## Evaluation Candidates

### `GET /v1/users/evaluation_candidates`
Search evaluation candidates.

### `GET /v1/users/evaluation_candidates/:id`
Show an evaluation candidate.

### `POST /v1/users/evaluation_candidates`
Create an evaluation candidate.

**Body:**
```json
{
  "evaluation_candidate": {
    "candidate_id": 1,
    "evaluation_id": 5,
    "apply_id": 10,
    "job_id": 3,
    "date_expiration": "2025-12-31"
  }
}
```

### `PUT /v1/users/evaluation_candidates/:id`
Update an evaluation candidate.

### `DELETE /v1/users/evaluation_candidates/:id`
Delete an evaluation candidate.

### `POST /v1/users/evaluation_candidates/create_collection`
Bulk create evaluation candidates.

**Body:** `{ "select_all_params": { ... } }`

### `GET /v1/users/evaluation_candidates/stats`
Evaluation candidate statistics.

---

## Messages

### `GET /v1/users/messages`
Search messages (scoped to current user).

### `GET /v1/users/messages/:id`
Show a message.

### `POST /v1/users/messages`
Create a message (auto-creates workspace if needed).

**Body:**
```json
{
  "message": {
    "content": "Hello, I need help with...",
    "workspace_id": 834,
    "domain": "sourcing",
    "domain_reference_id": "123",
    "entity": 0,
    "metadata": { "key": "value" }
  }
}
```

**Full field list:** `content`, `content_format` (default: `plain_text`), `user_context_id`, `type`, `is_deleted`, `status`, `parent_message_id`, `reference_type`, `reference_id`, `entity`, `workspace_id`, `no_reply`, `domain`, `domain_reference_id`, `audio_file` (file), `data_file_ids[]`, `file_urls[]`, `metadata{}`

### `PUT /v1/users/messages/:id`
Update a message (owner only).

### `DELETE /v1/users/messages/:id`
Delete a message (owner only). Returns 204.

---

## Workspaces

### `GET /v1/users/workspaces`
Search workspaces.

### `GET /v1/users/workspaces/:id`
Show a workspace.

### `POST /v1/users/workspaces`
Create a workspace.

**Body:** `{ "workspace": { "name": "My Workspace" } }`

### `PUT /v1/users/workspaces/:id`
Update a workspace.

**Body:** `{ "workspace": { "name": "New Name" } }`

### `DELETE /v1/users/workspaces/:id`
Soft-delete a workspace.

---

## Sourcings

### `GET /v1/users/sourcings`
Search sourcings.

### `GET /v1/users/sourcings/:id`
Show a sourcing with pool pagination info.

### `POST /v1/users/sourcings`
Create a new sourcing (triggers candidate search).

**Body:**
```json
{
  "sourcing": {
    "query": "Senior Ruby Developer São Paulo",
    "sources": ["local", "global"],
    "limit": 50
  }
}
```

Supports: `query`, `sources[]`, `files` (upload), `is_linkedin_parse`, `linkedin_profile_urls`, `limit`

### `PUT /v1/users/sourcings/:id`
Update a sourcing.

**Body:** `{ "sourcing": { "saved": true, "notes": "Good results", "status": "completed" } }`

### `POST /v1/users/sourcings/:id/load_more`
Load more candidates from pool.

**Body:** `{ "page": 2, "page_size": 20 }`

### `GET /v1/users/sourcings/:id/stats`
Returns sourcing stats, score distribution, ROI metrics.

### `GET /v1/users/sourcings/:id/context_for_ai`
Returns sourcing data formatted for AI.

**Query:** `page`, `per_page`, `selected_ids`

### `POST /v1/users/sourcings/:id/recalculate_stats`
Enqueue stats recalculation.

### `POST /v1/users/sourcings/:id/refine`
Refine sourcing results (deprecated).

**Body:**
```json
{
  "liked_candidate_ids": [1, 2, 3],
  "disliked_feedbacks": [{ ... }],
  "sources": ["local"],
  "limit": 30
}
```

### `POST /v1/users/sourcings/:sourcing_id/refinements`
Create a refinement for a sourcing.

### `GET /v1/users/sourcings/history`
Returns sourcing history grouped by date.

### `GET /v1/users/sourcings/credits`
Returns credit statistics.

**Query:** `start_date`, `end_date`

### `GET /v1/users/sourcings/transactions`
Returns credit transactions.

### `POST /v1/users/sourcings/search_profiles`
Returns search profile definitions and current balance.

### `POST /v1/users/sourcings/find_similar_candidates`
Find similar candidates via embeddings.

**Body:**
```json
{
  "candidate_ids": [1, 2],
  "job_id": 5,
  "limit": 20,
  "threshold": 0.7,
  "exclude_ids": [3, 4],
  "sources": ["local"],
  "skip_cache": false
}
```

---

## Sourced Profiles

### `GET /v1/users/sourced_profiles`
Search sourced profiles.

### `GET /v1/users/sourced_profiles/:id`
Show a profile (marks as viewed).

### `PUT /v1/users/sourced_profiles/:id`
Update a profile.

**Body:**
```json
{
  "sourced_profile": {
    "status": "approved",
    "rating": 5,
    "internal_notes": "Great candidate",
    "tags": ["senior", "ruby"]
  }
}
```

### `POST /v1/users/sourced_profiles/:id/import`
Import sourced profile as a candidate (creates or updates).

### `GET /v1/users/sourced_profiles/:id/similar`
Returns similar profiles.

**Query:** `limit`

### `POST /v1/users/sourced_profiles/:id/enrich_emails`
Enrich profile with email contacts.

### `POST /v1/users/sourced_profiles/:id/enrich_phones`
Enrich profile with phone contacts.

### `POST /v1/users/sourced_profiles/:id/enrich_contacts`
Enrich profile with both email and phone contacts.

### `POST /v1/users/sourced_profiles/convert_to_candidates`
Bulk convert sourced profiles to candidates.

**Body:** `{ "sourced_profile_ids": [1, 2, 3] }` or `{ "select_all_params": { ... } }`

### `GET /v1/users/sourced_profiles/stats`
Sourced profile statistics.

**Query:** `start_date`, `end_date`

---

## Sourced Profile Sourcings

### `GET /v1/users/sourced_profile_sourcings`
Search sourced profile sourcings.

### `GET /v1/users/sourced_profile_sourcings/:id`
Show a sourced profile sourcing.

### `POST /v1/users/sourced_profile_sourcings`
Create a sourced profile sourcing.

**Body:**
```json
{
  "sourced_profile_sourcing": {
    "sourced_profile_id": 1,
    "sourcing_id": 5,
    "analysis": "Good match",
    "score": 85.5,
    "saved": true
  }
}
```

### `PUT /v1/users/sourced_profile_sourcings/:id`
Update a sourced profile sourcing.

### `DELETE /v1/users/sourced_profile_sourcings/:id`
Soft-delete.

### `GET /v1/users/sourced_profile_sourcings/:id/similar_candidates`
Find matching candidates via embedding similarity.

**Query:** `top_k`, `page`, `per_page`, `min_score`, `max_score`, `filters`, `compact`, `include`

---

## Search Archetypes

### `GET /v1/users/search_archetypes`
Search archetypes (own, public, or default).

### `GET /v1/users/search_archetypes/defaults`
Returns default archetypes ordered by usage count.

### `GET /v1/users/search_archetypes/enums`
Returns seniority/work_model/contract_type options.

### `GET /v1/users/search_archetypes/:uid`
Show an archetype (by `uid`).

### `POST /v1/users/search_archetypes`
Create an archetype.

**Body:**
```json
{
  "search_archetype": {
    "name": "Senior Backend",
    "emoji": "🚀",
    "description": "Senior backend developers",
    "query": "senior backend ruby python",
    "seniority": "senior",
    "min_experience_years": 5,
    "location": "São Paulo",
    "work_model": "remote",
    "contract_type": "clt",
    "skills": ["Ruby", "Python"],
    "tags": ["backend"],
    "languages": ["English"],
    "is_public": true
  }
}
```

**Full field list:** `name`, `emoji`, `description`, `query`, `seniority`, `min_experience_years`, `industry`, `location`, `work_model`, `contract_type`, `is_public`, `skills[]`, `tags[]`, `languages[]`, `local_filters{}`, `global_filters{}`

### `PUT /v1/users/search_archetypes/:uid`
Update an archetype (owner or admin only).

### `DELETE /v1/users/search_archetypes/:uid`
Soft-delete an archetype.

### `POST /v1/users/search_archetypes/:uid/search`
Execute search from archetype.

**Body:** `{ "sources": ["local", "global"] }`

### `POST /v1/users/search_archetypes/:uid/duplicate`
Duplicate an archetype for the current user.

---

## Lists

### `GET /v1/users/lists`
Search lists (Pundit authorized).

### `GET /v1/users/lists/:id`
Show a list.

### `POST /v1/users/lists`
Create a list.

**Body:** `{ "list": { "name": "Shortlist", "is_public": true, "color": "#FF5733", "description": "Top candidates" } }`

### `PUT /v1/users/lists/:id`
Update a list.

### `DELETE /v1/users/lists/:id`
Soft-delete a list.

---

## List Relationships

### `GET /v1/users/lists/:list_id/relationships/:reference_type`
List items in a list filtered by reference type (redirects to entity index with list filter).

### `GET /v1/users/lists/:list_id/relationships_by_reference/:reference_type`
Search list relationships by reference type.

### `GET /v1/users/lists/:list_id/relationships/:relationship_id`
Show a list relationship.

### `POST /v1/users/lists/:list_id/relationships`
Add item to a list.

**Body:**
```json
{
  "list_relationship": {
    "reference_type": "Candidate",
    "reference_id": 1,
    "general_comments": "Top pick",
    "score": 95
  }
}
```

### `PUT /v1/users/lists/:list_id/relationships/:relationship_id`
Update a list relationship.

### `DELETE /v1/users/lists/:list_id/relationships/:relationship_id`
Soft-delete from list.

### `POST /v1/users/lists/:list_id/relationships/sort`
Bulk update position ordering.

### `POST /v1/users/lists/:list_id/relationships/collection`
Bulk add references to a list (async).

**Body:**
```json
{
  "collections": [
    { "reference_type": "Candidate", "reference_id": 1 },
    { "reference_type": "Candidate", "reference_id": 2 }
  ]
}
```

### `DELETE /v1/users/lists/:list_id/relationships/delete_collection`
Bulk remove from list (async).

---

## Skills

### `GET /v1/users/skills`
Search skills.

### `GET /v1/users/skills/:id`
Show a skill.

### `POST /v1/users/skills`
Create a skill (find-or-create by name).

**Body:** `{ "skill": { "name": "Ruby", "skill_category_id": 3 } }`

### `PUT /v1/users/skills/:id`
Update a skill.

### `DELETE /v1/users/skills/:id`
Delete a skill.

---

## Skill Relationships

### `GET /v1/users/skill_relationships`
Search skill relationships.

### `GET /v1/users/skill_relationships/:id`
Show a skill relationship.

### `POST /v1/users/skill_relationships`
Create a skill relationship (auto find-or-create skill by `skill_name`).

**Body:**
```json
{
  "skill_relationship": {
    "skill_id": 1,
    "skill_name": "Ruby",
    "reference_type": "Job",
    "reference_id": 5,
    "priority": 1,
    "min_value": 3,
    "max_value": 5,
    "experience_time": 2,
    "level_skill": "advanced",
    "main": true
  }
}
```

### `PUT /v1/users/skill_relationships/:id`
Update a skill relationship.

### `DELETE /v1/users/skill_relationships/:id`
Soft-delete.

### `GET /v1/users/skill_relationships/experience_times`
List experience time options.

### `GET /v1/users/skill_relationships/skill_levels`
List skill level options.

---

## Behavioral Skills

### `GET /v1/users/behavioral_skills`
Search behavioral skills. Standard CRUD.

### `POST /v1/users/behavioral_skills`
**Body:** `{ "behavioral_skill": { "name": "Leadership" } }`

---

## Behavioral Skill Relationships

### Standard CRUD at `/v1/users/behavioral_skill_relationships`

**Body:**
```json
{
  "behavioral_skill_relationship": {
    "behavioral_skill_id": 1,
    "reference_type": "Job",
    "reference_id": 5,
    "priority": 1,
    "experience_time": 2,
    "level_skill": "advanced"
  }
}
```

### `GET /v1/users/behavioral_skill_relationships/experience_times`
### `GET /v1/users/behavioral_skill_relationships/skill_levels`

---

## Benefits

### Standard CRUD at `/v1/users/benefits`

**Body:**
```json
{
  "benefit": {
    "name": "Health Insurance",
    "category": "health",
    "types": ["VIP", "Standard"],
    "is_possible_extend_to_dependents": true,
    "is_per_day": false
  }
}
```

### `GET /v1/users/benefits/grouped_by_category`
Returns benefits grouped by category.

---

## Benefit Relationships

### Standard CRUD at `/v1/users/benefit_relationships`

**Body:**
```json
{
  "benefit_relationship": {
    "benefit_id": 1,
    "reference_type": "Job",
    "reference_id": 5,
    "value": 500.00,
    "category": "health",
    "description": "Full coverage"
  }
}
```

### `POST /v1/users/benefit_relationships/create_collection`
Bulk create benefit relationships.

### `POST /v1/users/benefit_relationships/bulk_upsert`
Bulk create/update/delete benefit relationships.

---

## Remunerations

### Standard CRUD at `/v1/users/remunerations`

**Body:** `{ "remuneration": { "name": "Base Salary", "description": "Monthly base" } }`

---

## Remuneration Relationships

### Standard CRUD at `/v1/users/remuneration_relationships`

**Body:**
```json
{
  "remuneration_relationship": {
    "remuneration_id": 1,
    "reference_type": "Job",
    "reference_id": 5,
    "currency": "BRL",
    "period": "monthly",
    "value": 8000,
    "contract_type": ["CLT"]
  }
}
```

### `POST /v1/users/remuneration_relationships/bulk_upsert`
Bulk create/update remuneration relationships.

### `GET /v1/users/remuneration_relationships/currencies`
List available currencies.

### `GET /v1/users/remuneration_relationships/contract_types`
List contract type options.

---

## Languages

### Standard CRUD at `/v1/users/languages`

---

## Language Relationships

### Standard CRUD at `/v1/users/language_relationships`

**Body:**
```json
{
  "language_relationship": {
    "language_id": 1,
    "reference_type": "Job",
    "reference_id": 5,
    "level": "fluent",
    "is_required": true,
    "priority": 1
  }
}
```

### `GET /v1/users/language_relationships/levels`
List language level options.

---

## Experiences

### Standard CRUD at `/v1/users/experiences`

**Body:**
```json
{
  "experience": {
    "candidate_id": 1,
    "company_name": "Acme Corp",
    "occupation_name": "Software Engineer",
    "start_date": "2020-01-01",
    "end_date": "2023-06-30",
    "work_here": false,
    "description": "Developed...",
    "contract_type": "clt"
  }
}
```

**Full field list:** `work_here`, `start_date`, `end_date`, `candidate_id`, `occupation_id`, `company_id`, `city_id`, `description`, `reasons_leaving`, `contract_type`, `parse_language`, `is_deleted`, `company_name`, `occupation_name`

---

## Educations

### Standard CRUD at `/v1/users/educations`

**Body:**
```json
{
  "education": {
    "candidate_id": 1,
    "institution_name": "USP",
    "study_area_name": "Computer Science",
    "formation_type": "bachelor",
    "start_date": "2016-01-01",
    "end_date": "2020-12-31",
    "study_here": false
  }
}
```

---

## Companies

### Standard CRUD at `/v1/users/companies`

---

## Occupations

### Standard CRUD at `/v1/users/occupations`

---

## Institutions

### Standard CRUD at `/v1/users/institutions`

---

## Study Areas

### Standard CRUD at `/v1/users/study_areas`

---

## Departments

### `GET /v1/users/departments`
Search departments.

### `GET /v1/users/departments/:id`
Show a department.

### `POST /v1/users/departments`
Create a department.

**Body:**
```json
{
  "department": {
    "name": "Engineering",
    "description": "Tech team",
    "parent_department_id": 1,
    "color": "#2196F3",
    "managers": [
      { "id": 1, "name": "John", "email": "john@co.com", "title": "VP", "is_primary": true }
    ]
  }
}
```

### `PUT /v1/users/departments/:id`
Update a department.

### `DELETE /v1/users/departments/:id`
Soft-delete.

### `GET /v1/users/departments/tree`
Returns department tree hierarchy.

### `POST /v1/users/departments/reorder`
Reorder departments.

**Body:** `{ "items": [{ "id": 1, ... }] }`

### `POST /v1/users/departments/import`
Import departments from file.

**Body (multipart):** `file` or `data_file_id`, `async` (boolean)

### `GET /v1/users/departments/:id/ancestors`
Returns ancestors.

### `GET /v1/users/departments/:id/descendants`
Returns descendants.

### `GET /v1/users/departments/:id/organization_chart`
Returns org chart with positions and teams.

---

## Department Relationships

### Standard CRUD at `/v1/users/department_relationships`

---

## Teams

### Standard CRUD at `/v1/users/teams`

**Body:**
```json
{
  "team": {
    "name": "Backend Squad",
    "description": "Backend development team",
    "department_id": 5,
    "team_lead_id": 1,
    "is_active": true
  }
}
```

### `GET /v1/users/teams/:id/composition`
Returns team's current composition.

---

## Team Members

### `GET /v1/users/teams/:team_id/team_members`
List team members (active by default).

### `POST /v1/users/teams/:team_id/team_members`
Add a team member.

**Body:**
```json
{
  "team_member": {
    "user_id": 1,
    "role": "developer",
    "joined_at": "2024-01-01"
  }
}
```

### `DELETE /v1/users/teams/:team_id/team_members/:id`
Soft-deactivate member.

---

## Organizational Positions

### Standard CRUD at `/v1/users/organizational_positions`

**Body:**
```json
{
  "organizational_position": {
    "title": "Engineering Manager",
    "department_id": 5,
    "reports_to_id": 1,
    "level": 3,
    "position_type": "management",
    "is_active": true
  }
}
```

### `GET /v1/users/organizational_positions/:id/reporting_chain`
Returns reporting chain upward.

### `GET /v1/users/organizational_positions/:id/direct_reports`
Returns direct report positions.

---

## Position Assignments

### Standard CRUD at `/v1/users/position_assignments`

**Body:**
```json
{
  "position_assignment": {
    "user_id": 1,
    "organizational_position_id": 5,
    "start_date": "2024-01-01",
    "is_current": true,
    "employment_type": "full_time"
  }
}
```

---

## Approvers

### Standard CRUD at `/v1/users/approvers`

**Body:**
```json
{
  "approver": {
    "user_id": 1,
    "department_id": 5,
    "approval_type": "job_creation",
    "approval_level": 1,
    "limit_value": 50000,
    "is_active": true
  }
}
```

### `POST /v1/users/approvers/reorder`
Reorder approval levels.

### `GET /v1/users/approvers/by_type`
List approvers by `approval_type`.

### `GET /v1/users/approvers/approval_types`
List available approval types.

---

## Approval Requests

### `GET /v1/users/approval_requests`
Search approval requests.

### `GET /v1/users/approval_requests/:id`
Show an approval request.

### `POST /v1/users/approval_requests`
Create an approval request.

**Body:**
```json
{
  "approval_request": {
    "approver_id": 1,
    "reference_type": "Job",
    "reference_id": 5,
    "approval_level": 1,
    "comments": "Please review",
    "expires_at": "2025-12-31"
  }
}
```

### `POST /v1/users/approval_requests/:id/approve`
Approve a request.

### `POST /v1/users/approval_requests/:id/reject`
Reject a request.

**Body:** `{ "comments": "Reason for rejection" }`

### `POST /v1/users/approval_requests/:id/cancel`
Cancel a request.

### `GET /v1/users/approval_requests/pending`
List pending approvals for current user.

### `GET /v1/users/approval_requests/my_requests`
List requests made by current user.

### `GET /v1/users/approval_requests/by_reference`
List by reference.

**Query:** `reference_type`, `reference_id`

### `POST /v1/users/approval_requests/create_chain`
Create full approval chain.

**Body:** `{ "reference_type": "Job", "reference_id": 5, "approval_type": "job_creation", "department_id": 3 }`

---

## Businesses

### Standard CRUD at `/v1/users/businesses`

Supports `logo` and `cover_image` file uploads (multipart).

**Body:**
```json
{
  "business": {
    "name": "Acme Corp",
    "cnpj": "12345678000199",
    "email": "contact@acme.com",
    "industry": "Technology",
    "size": "medium",
    "about": "We build...",
    "culture_values": ["Innovation", "Teamwork"],
    "soft_skills": ["Communication"]
  }
}
```

### `POST /v1/users/businesses/:id/generate_big_five`
Generate AI Big Five personality profile for the business.

---

## Meetings

### Standard CRUD at `/v1/users/meetings`

**Body:**
```json
{
  "meeting": {
    "subject": "Interview with John",
    "start_time": "2025-01-15T10:00:00Z",
    "end_time": "2025-01-15T11:00:00Z",
    "provider": "teams",
    "location": "Online",
    "job_id": 5,
    "reference_type": "Candidate",
    "reference_id": 1,
    "settings": {
      "record_automatically": true,
      "allow_chat": true
    }
  }
}
```

### `GET /v1/users/meetings/stats`
Meeting statistics.

**Query:** `start_date`, `end_date`, `job_id`, `organizer_id`

---

## Calendar Events

### Standard CRUD at `/v1/users/calendar_events`

**Body:**
```json
{
  "calendar_event": {
    "title": "Phone Screen - John",
    "start_time": "2025-01-15T10:00:00Z",
    "end_time": "2025-01-15T10:30:00Z",
    "timezone": "America/Sao_Paulo",
    "provider": "teams",
    "event_type": "interview",
    "job_id": 5,
    "reference_type": "Candidate",
    "reference_id": 1,
    "attendees": [
      { "email": "john@email.com", "name": "John", "required": true }
    ]
  }
}
```

### `GET /v1/users/calendar_events/daily_agenda`
Returns daily agenda.

**Query:** `kind`, `search`, `from`, `to`, `timezone`, `event_type`, `provider`, `is_cancelled`, `organizer_id`, `page`, `per_page`

### `POST /v1/users/calendar_events/suggest_schedule`
AI-suggested schedule.

**Body:** `{ "text": "Schedule interview next week", "timezone": "America/Sao_Paulo" }`

### `POST /v1/users/calendar_events/:id/sync`
Sync event with external provider.

---

## Scheduling

### Settings

#### `GET /v1/users/scheduling/settings`
Show scheduling settings (auto-created for current user).

#### `PATCH /v1/users/scheduling/settings`
Update scheduling settings.

**Body:**
```json
{
  "settings": {
    "timezone": "America/Sao_Paulo",
    "work_hours_start": "09:00",
    "work_hours_end": "18:00",
    "default_duration_minutes": 30,
    "buffer_minutes": 15,
    "lookahead_days": 14
  }
}
```

### Availability

#### `GET /v1/users/scheduling/availability`
Returns available scheduling slots.

**Query:** `date` (single day) or `start_date` + `end_date` (range), `duration_minutes`

### Links

#### Standard CRUD at `/v1/users/scheduling/links`

**Body:**
```json
{
  "link": {
    "duration_minutes": 30,
    "interview_type": "technical",
    "platform": "teams",
    "subject": "Technical Interview",
    "message": "Please select a time",
    "apply_id": 10,
    "candidate_id": 1,
    "job_id": 5,
    "slots": [
      { "start_time": "2025-01-15T10:00:00Z", "end_time": "2025-01-15T10:30:00Z" }
    ],
    "channels": ["email"]
  }
}
```

**Filter query:** `status`, `job_id`, `apply_id`

---

## Interview Sessions

### `GET /v1/users/interview_sessions`
List interview sessions.

**Query:** `job_id`, `status`, `candidate_id`

### `GET /v1/users/interview_sessions/:id`
Show an interview session.

### `POST /v1/users/interview_sessions`
Create an interview session.

**Body:**
```json
{
  "interview_session": {
    "evaluation_id": 5,
    "candidate_id": 1,
    "job_id": 3,
    "apply_id": 10,
    "interview_type": "technical",
    "duration_minutes": 30,
    "language": "pt-BR",
    "channels": ["webchat"]
  }
}
```

---

## Notifications

### `GET /v1/users/notifications`
List notifications with custom pagination.

**Query:** `notification_type`, `status`, `since`, `page`, `per_page`

### `GET /v1/users/notifications/:id`
Show a notification.

### `PUT /v1/users/notifications/:id/read`
Mark as read.

### `POST /v1/users/notifications/mark_all_read`
Mark all unread notifications as read.

### `GET /v1/users/notifications/unread_count`
Returns unread count.

### `POST /v1/users/notifications/send_push`
Send push notification (requires service token).

**Body:**
```json
{
  "user_id": 1,
  "notification_type": "alert",
  "content": "New candidate applied",
  "channel": "push",
  "reference_type": "Apply",
  "reference_id": 10,
  "metadata": {}
}
```

---

## Notification Preferences

### `GET /v1/users/notification_preferences`
Show current user's notification preferences.

### `PUT /v1/users/notification_preferences`
Update preferences.

**Body:**
```json
{
  "notification_preferences": {
    "briefing_enabled": true,
    "briefing_time": "08:00",
    "briefing_channel": "email",
    "alert_aging_enabled": true,
    "alert_deadline_enabled": true,
    "aging_threshold_days": 7,
    "timezone": "America/Sao_Paulo",
    "alert_channels": ["push", "email"]
  }
}
```

---

## Email Templates

### Standard CRUD at `/v1/users/email_templates`

**Body:**
```json
{
  "email_template": {
    "name": "Interview Invitation",
    "subject": "Interview for {{job_title}}",
    "content": "Dear {{candidate_name}}, ...",
    "category_id": 1,
    "is_automated": false
  }
}
```

### `GET /v1/users/email_templates/categories`
Returns template categories.

### `GET /v1/users/email_templates/tags`
Returns available template tags.

**Query:** `reference_types` (array)

### `POST /v1/users/email_templates/generate_suggestion`
AI-generated template suggestion.

**Body:**
```json
{
  "text": "rejection email, polite tone",
  "reference_types": ["Candidate", "Job"],
  "subject": "Application Update",
  "extra_params": {}
}
```

### `POST /v1/users/email_templates/:id/duplicate`
Duplicate a template.

### `POST /v1/users/email_templates/render`
Render template with tag replacement.

**Body:** `{ "content": "Hello {{name}}", "template_id": 1, "context": { "candidate_id": 5, "job_id": 3 } }`

### `POST /v1/users/email_templates/render_for_candidate`
Render for a specific candidate.

**Body:** `{ "template_id": 1, "candidate_id": 5, "job_id": 3, "apply_id": 10 }`

### `POST /v1/users/email_templates/send`
Send emails via Microsoft Graph.

**Body:**
```json
{
  "template_id": 1,
  "subject": "Interview Invitation",
  "content": "<rendered html>",
  "job_id": 5,
  "selective_process_id": 3,
  "collections": [
    { "reference_type": "Candidate", "reference_id": 1, "email": "john@email.com" }
  ]
}
```

---

## Data Files

### Standard CRUD at `/v1/users/data_files`

**Body (multipart):**
```
file: <binary>
name: "resume.pdf"
reference_type: "Candidate"
reference_id: 1
file_type: "resume"
avoid_duplicate: true
```

---

## Activity Logs

### Standard CRUD at `/v1/users/activity_logs`

### `POST /v1/users/activity_logs/:id/rollback`
Revert the changes recorded in an activity log.

---

## Feedbacks

### Standard CRUD at `/v1/users/feedbacks`

**Body:**
```json
{
  "feedback": {
    "title": "Positive Feedback",
    "description": "Great candidate...",
    "name": "Technical Interview",
    "job_id": 5,
    "selective_process_id": 3
  }
}
```

---

## Candidate Feedbacks

### `GET /v1/users/candidate_feedbacks`
List candidate feedbacks.

### `POST /v1/users/candidate_feedbacks`
Create/upsert feedback.

**Body:**
```json
{
  "candidate_feedback": {
    "sourcing_id": 1,
    "candidate_id": 5,
    "reference_type": "SourcingProfile",
    "reference_id": 10,
    "reason": "Not relevant",
    "feedback_type": "dislike",
    "job_id": 3
  }
}
```

### `DELETE /v1/users/candidate_feedbacks/:id`
Soft-delete feedback.

### `DELETE /v1/users/candidate_feedbacks`
Bulk delete feedbacks.

---

## Workflow Templates

### Standard CRUD at `/v1/users/workflow_templates`

**Body:** `{ "workflow_template": { "name": "Standard Hiring Flow" } }`

---

## Job Statuses

### Standard CRUD at `/v1/users/job_statuses`

**Body:** `{ "job_status": { "name": "Open", "color": "#4CAF50" } }`

---

## Job Users

### Standard CRUD at `/v1/users/job_users`

**Body:**
```json
{
  "job_user": {
    "user_id": 1,
    "job_id": 5,
    "person_function": "recruiter",
    "split": 50
  }
}
```

---

## Job Journeys

### Standard CRUD at `/v1/users/job_journeys`

**Body:**
```json
{
  "job_journey": {
    "name": "Resume Review",
    "description": "Initial resume screening",
    "position": 1,
    "active": true,
    "required": true,
    "job_id": 5
  }
}
```

### `PUT /v1/users/job_journeys/update_positions`
Bulk update journey positions.

---

## Job Field Templates

### Standard CRUD at `/v1/users/job_field_templates`

**Body:**
```json
{
  "job_field_template": {
    "name": "Standard Template",
    "is_default": true,
    "fields": [
      { "label": "Title", "category": "basic", "priority": 1, "field_name": "title", "is_required": true }
    ]
  }
}
```

### `GET /v1/users/job_field_templates/default_fields`
Returns default field definitions.

---

## Apply Statuses

### Standard CRUD at `/v1/users/apply_statuses`

**Body:**
```json
{
  "apply_status": {
    "apply_id": 10,
    "selective_process_id": 3,
    "status_name": "Interview Scheduled"
  }
}
```

---

## Entity Columns

### `GET /v1/users/entity_columns`
Search entity columns.

### `GET /v1/users/entity_columns/:entity/structure`
Returns default column structure for an entity.

### `POST /v1/users/entity_columns/:entity/save`
Create or update entity column configuration.

### `PUT /v1/users/entity_columns/:entity/update_view`
Update main view for an entity.

### `POST /v1/users/entity_columns/views`
Create a named view.

### `DELETE /v1/users/entity_columns/:id/view`
Delete a view.

### `DELETE /v1/users/entity_columns/:entity/delete`
Delete entity column by entity name.

---

## Entity Pages

### Standard CRUD at `/v1/users/entity_pages`
Create does upsert by `entity` + `user` + `type_view` + `job_id`.

---

## Sectors

### Standard CRUD at `/v1/users/sectors`

### `GET /v1/users/sectors/tree`
Returns sector tree hierarchy.

### `GET /v1/users/sectors/autocomplete`
Autocomplete search for sectors.

---

## Sector Relationships

### Standard CRUD at `/v1/users/sector_relationships`

---

## Issues

### Standard CRUD at `/v1/users/issues`

---

## Dispatches

### `GET /v1/users/dispatches`
### `GET /v1/users/dispatches/:id`
### `POST /v1/users/dispatches`

---

## Answers

### Standard CRUD at `/v1/users/answers`

---

## Audio Messages

### `POST /v1/users/audio_messages`
Create an audio message.

### `GET /v1/users/audio_messages/:id`
Show an audio message.

### `GET /v1/users/audio_messages/:id/audio`
Get audio file.

---

## Dashboard

### `GET /v1/users/dashboard/briefing`
Returns daily briefing (cached 5min).

**Query:** `since` (date), `timezone`

---

## Productivity

### `GET /v1/users/me/productivity`
Returns user productivity metrics (cached 10min).

**Query:** `start_date`, `end_date`

---

## Aggregators

### `GET /v1/users/aggregators/:entity`
### `POST /v1/users/aggregators/:entity`
Returns Searchkick aggregations for a given entity (model name).

Supports full search params: `where`, `filter`, `order`, `aggs`.

**Example:** `GET /v1/users/aggregators/candidates?where={"is_deleted":false}&aggs=["city","source"]`

---

## Account

### `GET /v1/users/account`
Returns current user's account data.

---

## LLM Usages

### `GET /v1/users/llm_usages`
Search LLM usage records.

### `GET /v1/users/llm_usages/:id`
Show a single LLM usage record.

### `POST /v1/users/llm_usages`
Create an LLM usage record.

**Body:**
```json
{
  "llm_usage": {
    "model": "gemini-2.0-flash",
    "operation": "evaluation",
    "input_tokens": 500,
    "output_tokens": 200,
    "total_tokens": 700,
    "cost_usd": 0.001,
    "latency_ms": 450,
    "success": true,
    "context": { "service": "EvaluationService" }
  }
}
```

### `GET /v1/users/llm_usages/stats`
Aggregated stats (today, this week, this month, last 30 days).

### `GET /v1/users/llm_usages/by_model`
Usage breakdown by LLM model.

### `GET /v1/users/llm_usages/by_operation`
Usage breakdown by operation type.

### `GET /v1/users/llm_usages/by_service`
Usage breakdown by service name.

### `GET /v1/users/llm_usages/daily_trend`
Daily usage trend (up to 90 days).

### `GET /v1/users/llm_usages/failures`
List recent failed LLM calls.

### `GET /v1/users/llm_usages/recent`
List recent LLM usage records.

### `GET /v1/users/llm_usages/top_consumers`
Top users by LLM cost.

---

## LLM Quotas

### `GET /v1/users/llm_quotas/current`
Show current LLM quota + usage + summary for the account.

### `PATCH /v1/users/llm_quotas/update_current`
Update quota settings (admin-only).

**Body:** `{ "notify_at_percentage": 80, "hard_limit": true }`

---

## Addresses

### Standard CRUD at `/v1/users/addresses`

**Body:**
```json
{
  "address": {
    "street": "Av. Paulista",
    "number": "1000",
    "complement": "Suite 500",
    "neighborhood": "Bela Vista",
    "zip_code": "01310-100",
    "city_id": 1,
    "address_type": "office",
    "title": "HQ"
  }
}
```

### `GET /v1/users/addresses/:entity/:id`
Returns addresses linked to a given entity/id.

---

## Address Relationships

### Standard CRUD at `/v1/users/address_relationships`

---

## Bulk Imports

### `POST /v1/users/bulk_imports/:entity_type`
Start a bulk import.

### `POST /v1/users/bulk_imports/:entity_type/preview`
Preview bulk import data.

---

## Candidate Imports

### `POST /v1/users/candidate_imports_preview`
Preview candidate import.

### `POST /v1/users/candidate_imports`
Execute candidate import.

---

## Lookups

### `GET /v1/users/cities`
Search cities.

### `GET /v1/users/countries`
List countries.

### `GET /v1/users/countries/:id`
Show a country.

### `GET /v1/users/states`
List states.

### `GET /v1/users/states/:id`
Show a state.

### `GET /v1/users/genders`
List gender options.

### `GET /v1/users/marital_statuses`
List marital status options.

### `GET /v1/users/role_names`
Search role names.

### `GET /v1/users/role_names/suggestions`
Role name suggestions.

### `GET /v1/users/position_levels`
List position level options.

### `GET /v1/users/replace_tags`
List available replacement tags.

---

## Microsoft Integration

### `GET /v1/users/microsoft_graph_auth/url`
Get Microsoft Graph OAuth URL.

### `GET /v1/users/microsoft_graph_auth/login_url`
Get Microsoft login URL.

### `GET /v1/users/microsoft_graph_auth/status`
Check Microsoft Graph auth status.

### `GET /v1/users/integrations/microsoft/me`
Get Microsoft profile.

### `POST /v1/users/integrations/microsoft/email`
Send email via Microsoft Graph.

### `POST /v1/users/integrations/microsoft/email/bulk`
Bulk send emails via Microsoft Graph.

### `POST /v1/users/integrations/microsoft/teams/message`
Send Teams message.

---

## Admin Namespace

All admin endpoints require admin-level privileges.

**Base:** `/v1/users/admin`

### Accounts
Standard CRUD at `/v1/users/admin/accounts`

### Users
Standard CRUD at `/v1/users/admin/users`

### Roles
Standard CRUD at `/v1/users/admin/roles`

### Permissions
`GET /v1/users/admin/permissions` and `GET /v1/users/admin/permissions/:id`

### LLM Costs
`GET /v1/users/admin/llm_costs/overview` — System-wide LLM cost overview.

### Search Credits

| Endpoint | Description |
|----------|-------------|
| `GET /v1/users/admin/search_credits/list_accounts` | List accounts with credit info |
| `POST /v1/users/admin/search_credits/:id/add` | Add credits |
| `POST /v1/users/admin/search_credits/:id/remove` | Remove credits |
| `GET /v1/users/admin/search_credits/:id/show` | Show credit details |
| `GET /v1/users/admin/search_credits/:id/transactions` | Credit transactions |

### LLM Quotas

| Endpoint | Description |
|----------|-------------|
| `GET /v1/users/admin/llm_quotas` | List all quotas |
| `GET /v1/users/admin/llm_quotas/:id` | Show quota |
| `PUT /v1/users/admin/llm_quotas/:id` | Update quota |
| `POST /v1/users/admin/llm_quotas/:id/grant_extra` | Grant extra quota |
| `POST /v1/users/admin/llm_quotas/:id/reset_usage` | Reset usage |

### Job Field Templates
Standard CRUD at `/v1/users/admin/job_field_templates`

### WhatsApp Configurations

| Endpoint | Description |
|----------|-------------|
| Standard CRUD | `/v1/users/admin/whatsapp_configurations` |
| `POST /v1/users/admin/whatsapp_configurations/:id/restore` | Restore config |
| `POST /v1/users/admin/whatsapp_configurations/quick_update_url` | Quick update URL |
