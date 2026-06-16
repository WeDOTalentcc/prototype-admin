# Email Dispatch & Tag Replacer API

## Table of Contents

1. [Email Templates (CRUD)](#1-email-templates-crud)
2. [Available Tags](#2-available-tags)
3. [Render Preview (Tag Replacement)](#3-render-preview-tag-replacement)
4. [Send Email via Template](#4-send-email-via-template)
5. [Microsoft Graph - Single Email](#5-microsoft-graph---single-email)
6. [Microsoft Graph - Bulk Email](#6-microsoft-graph---bulk-email)
7. [Dispatches (Generic)](#7-dispatches-generic)
8. [Tag Replacer System (Internal)](#8-tag-replacer-system-internal)

---

## Authentication

All endpoints (except public) require the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

---

## 1. Email Templates (CRUD)

Base URL: `/v1/users/email_templates`

### 1.1 List Templates

```
GET /v1/users/email_templates
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `where[category_id]` | integer | Filter by category (1-6) |
| `where[is_deleted]` | boolean | Filter deleted (default: `false`) |
| `q` | string | Search by name, subject, content |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "1",
      "type": "email_template",
      "attributes": {
        "id": 1,
        "name": "Welcome Email",
        "subject": "Welcome {{candidate_name}}!",
        "content": "<p>Hello {{candidate_name}}, your application for {{job_title}} was received.</p>",
        "category_id": 6,
        "category": "Contato Inicial",
        "category_color": "#9e9e9e",
        "account_id": 1,
        "user_id": 1,
        "is_deleted": false,
        "user": { "id": 1, "name": "John Doe", "email": "john@example.com" },
        "account": { "id": 1, "name": "Acme Corp" },
        "created_at": "2026-01-15T10:00:00.000Z",
        "updated_at": "2026-01-15T10:00:00.000Z"
      }
    }
  ]
}
```

### 1.2 Show Template

```
GET /v1/users/email_templates/:id
```

**Response:** `200 OK` — Same structure as list item.

### 1.3 Create Template

```
POST /v1/users/email_templates
```

**Body:**
```json
{
  "email_template": {
    "name": "Interview Invitation",
    "subject": "Interview for {{job_title}} - {{candidate_name}}",
    "content": "<p>Dear {{candidate_name}},</p><p>You've been selected for an interview for the position of {{job_title}}.</p><p>Best regards,<br>{{recruiter_name}}</p>",
    "category_id": 3
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Template name |
| `subject` | string | yes | Email subject (supports tags) |
| `content` | string | yes | HTML body (supports tags) |
| `category_id` | integer | yes | Category: 1=Aprovação, 2=Rejeição, 3=Agendamento, 4=Follow-up, 5=Feedback, 6=Contato Inicial |

**Response:** `201 Created`

### 1.4 Update Template

```
PUT /v1/users/email_templates/:id
```

**Body:** Same as create. **Response:** `200 OK`

### 1.5 Delete Template (soft delete)

```
DELETE /v1/users/email_templates/:id
```

**Response:** `200 OK` — Sets `is_deleted: true`.

### 1.6 Duplicate Template

```
POST /v1/users/email_templates/:id/duplicate
```

**Response:** `201 Created` — Creates a copy with name "Original Name (cópia)".

### 1.7 List Categories

```
GET /v1/users/email_templates/categories
```

**Response:** `200 OK`
```json
{
  "categories": [
    { "id": 1, "name": "Aprovação", "color": "#35ab86" },
    { "id": 2, "name": "Rejeição", "color": "#df3939" },
    { "id": 3, "name": "Agendamento", "color": "#3e75ed" },
    { "id": 4, "name": "Follow-up", "color": "#dc8117" },
    { "id": 5, "name": "Feedback", "color": "#1195b5" },
    { "id": 6, "name": "Contato Inicial", "color": "#9e9e9e" }
  ]
}
```

### 1.8 Generate AI Suggestion

```
POST /v1/users/email_templates/generate_suggestion
```

**Body:**
```json
{
  "text": "Create an email to reject a candidate politely",
  "reference_types": ["Candidate"],
  "subject": "Optional existing subject",
  "content": "Optional existing content to modify"
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "name": "Polite Rejection",
    "subject": "Update on your application",
    "content": "<p>Dear {{candidate_name}},</p><p>Thank you for your interest...</p>",
    "category_id": 2
  }
}
```

---

## 2. Available Tags

### 2.1 List Tags

```
GET /v1/users/email_templates/tags
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reference_types[]` | string[] | Filter by entity: `Candidate`, `SourcedProfile`, `User`, `Job` |

**Example:**
```
GET /v1/users/email_templates/tags?reference_types[]=Candidate&reference_types[]=Job
```

**Response:** `200 OK`
```json
{
  "data": [
    { "attributes": { "text": "Candidato - E-mail", "tag": "{{candidate_email}}", "field": "email" } },
    { "attributes": { "text": "Candidato - Nome", "tag": "{{candidate_name}}", "field": "name" } },
    { "attributes": { "text": "Vaga - Título", "tag": "{{job_title}}", "field": "title" } },
    { "attributes": { "text": "Vaga - Descrição", "tag": "{{job_description}}", "field": "description" } }
  ]
}
```

### 2.2 Complete Tag Reference

#### Candidate Tags
| Tag | Description |
|-----|-------------|
| `{{candidate_name}}` | Full candidate name |
| `{{candidate_first_name}}` | Candidate first name |
| `{{candidate_email}}` | Candidate email |
| `{{candidate_phone}}` | Candidate phone |
| `{{candidate_mobile_phone}}` | Candidate mobile phone |
| `{{candidate_access_url}}` | Candidate access URL |

#### User / Recruiter Tags
| Tag | Description |
|-----|-------------|
| `{{user_name}}` | Logged-in user full name |
| `{{user_email}}` | Logged-in user email |
| `{{recruiter_name}}` | Recruiter name |
| `{{recruiter_email}}` | Recruiter email |
| `{{recruiter_phone}}` | Recruiter phone |

#### Job Tags
| Tag | Description |
|-----|-------------|
| `{{job_title}}` | Job title |
| `{{job_description}}` | Job description |
| `{{job_location}}` | Job location |

#### Client Tags
| Tag | Description |
|-----|-------------|
| `{{client_contact_name}}` | Client contact name |
| `{{client_contact_email}}` | Client contact email |
| `{{client_company_name}}` | Client company name |
| `{{client_company_corporate_name}}` | Client company corporate name |

#### Date Tags
| Tag | Description |
|-----|-------------|
| `{{date_today}}` | Current date (EN format) |
| `{{date_br_today}}` | Current date (BR format: dd/mm/yyyy) |

#### Special Tags
| Tag | Description |
|-----|-------------|
| `{{evaluation_candidate_url}}` | Evaluation candidate URL |

#### Legacy Tags (deprecated, still supported)
| Tag | Equivalent |
|-----|-----------|
| `{{nome_do_candidato}}` | `{{candidate_name}}` |
| `{{email_do_candidato}}` | `{{candidate_email}}` |
| `{{nome_do_usuario}}` | `{{user_name}}` |
| `{{email_do_usuario}}` | `{{user_email}}` |

---

## 3. Render Preview (Tag Replacement)

Preview how a template looks with real data, replacing all tags with actual values.

```
POST /v1/users/email_templates/render
```

**Body:**
```json
{
  "content": "<p>Hello {{candidate_name}}, we'd like to invite you for {{job_title}}.</p>",
  "context": {
    "candidate_id": 42,
    "job_id": 7
  }
}
```

Or using an existing template:
```json
{
  "template_id": 15,
  "context": {
    "candidate_id": 42,
    "job_id": 7
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | conditional | HTML content with tags (required if no `template_id`) |
| `template_id` | integer | conditional | Use content from existing template |
| `context.candidate_id` | integer | no | Candidate to resolve candidate tags |
| `context.job_id` | integer | no | Job to resolve job tags |

**Response:** `200 OK`
```json
{
  "rendered_text": "<p>Hello Maria Silva, we'd like to invite you for Senior Developer.</p>",
  "missing_variables": []
}
```

If some tags couldn't be resolved (no context provided):
```json
{
  "rendered_text": "<p>Hello Maria Silva, we'd like to invite you for {{job_title}}.</p>",
  "missing_variables": ["{{job_title}}"]
}
```

---

## 4. Send Email via Template

Send personalized emails to multiple recipients using tag replacement. Uses **Microsoft Graph** to send via the authenticated user's mailbox.

```
POST /v1/users/email_templates/send
```

**Body:**
```json
{
  "template_id": 15,
  "subject": "Optional subject override",
  "content": "Optional content override",
  "job_id": 7,
  "selective_process_id": 3,
  "collections": [
    {
      "reference_type": "Candidate",
      "reference_id": 42,
      "email": "maria@example.com"
    },
    {
      "reference_type": "Candidate",
      "reference_id": 55,
      "email": "joao@example.com"
    },
    {
      "reference_type": "SourcedProfile",
      "reference_id": 10,
      "email": "sourced@example.com"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | integer | conditional | ID of email template (provides subject/content if not overridden) |
| `subject` | string | conditional | Email subject (overrides template subject) |
| `content` | string | conditional | HTML body (overrides template content) |
| `job_id` | integer | no | Job for tag replacement and apply creation |
| `selective_process_id` | integer | no | Selective process for auto-creating applies |
| `collections` | array | yes | Array of recipients |
| `collections[].reference_type` | string | yes | `"Candidate"` or `"SourcedProfile"` |
| `collections[].reference_id` | integer | yes | ID of the candidate or sourced profile |
| `collections[].email` | string | yes | Recipient email address |

**Tag Replacement:** For each recipient, tags like `{{candidate_name}}` are resolved using the referenced entity (`Candidate` or `SourcedProfile`). The `{{user_name}}`, `{{recruiter_name}}` etc. are resolved from the authenticated user. If `job_id` is provided, `{{job_title}}` and similar tags are resolved.

**Auto Apply Creation:** When both `job_id` and `selective_process_id` are provided, an `Apply` record is automatically created (or found) linking the candidate to the job/selective process.

**Response:** `202 Accepted`
```json
{
  "ok": true,
  "dispatch_id": 123,
  "recipients_count": 3,
  "applies_created": 2
}
```

Emails are sent asynchronously via `MsGraphEmailWorker` (Sidekiq).

---

## 5. Microsoft Graph - Single Email

Send a single email (or to multiple recipients) without tag replacement, directly via Microsoft Graph.

```
POST /v1/users/integrations/microsoft/email
```

**Body:**
```json
{
  "email": {
    "subject": "Meeting follow-up",
    "html": "<p>Thanks for the meeting today.</p>",
    "to": "recipient@example.com",
    "recipients": ["extra1@example.com", "extra2@example.com"],
    "save_to_sent": true,
    "reply_to": "custom-reply@example.com",
    "scheduled_for": "2026-03-01T14:00:00Z"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | yes | Email subject |
| `html` | string | conditional | HTML body (required if no `text`) |
| `text` | string | conditional | Plain text body (fallback) |
| `to` | string | no | Single recipient |
| `recipients` | string[] | no | Multiple recipients (combined with `to`) |
| `save_to_sent` | boolean | no | Save to Sent folder (default: `true`) |
| `reply_to` | string | no | Custom reply-to address |
| `scheduled_for` | string (ISO 8601) | no | Schedule send time |

**Response:** `202 Accepted`
```json
{
  "ok": true,
  "dispatch_id": 456,
  "recipients_count": 3
}
```

---

## 6. Microsoft Graph - Bulk Email

Send bulk emails with pacing (delay between sends) via Microsoft Graph.

```
POST /v1/users/integrations/microsoft/email/bulk
```

**Body:**
```json
{
  "email": {
    "name": "Campaign Q1 2026",
    "subject": "Exciting opportunity at Acme!",
    "html": "<p>We have a great role for you.</p>",
    "recipients": [
      "lead1@example.com",
      "lead2@example.com",
      "lead3@example.com"
    ],
    "start_at": "2026-03-01T09:00:00Z",
    "delay_seconds": 180,
    "save_to_sent": true,
    "reply_to": "recruiting@acme.com"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | no | Campaign name (default: "Microsoft Bulk Email") |
| `subject` | string | yes | Email subject |
| `html` | string | conditional | HTML body (required if no `text`) |
| `text` | string | conditional | Plain text body (fallback) |
| `recipients` | string[] | yes | List of email addresses |
| `start_at` | string (ISO 8601) | no | When to start sending (default: now) |
| `delay_seconds` | integer | no | Delay between each email in seconds (default: `180`) |
| `save_to_sent` | boolean | no | Save to Sent folder (default: `true`) |
| `reply_to` | string | no | Custom reply-to address |

**Response:** `202 Accepted`
```json
{
  "ok": true,
  "dispatch_id": 789,
  "messages_count": 3,
  "scheduled_start_at": "2026-03-01T09:00:00.000Z",
  "delay_seconds": 180
}
```

**Pacing:** Each recipient email is scheduled with incremental delay. For 3 recipients with `delay_seconds: 180`:
- Recipient 1: sent at `start_at + 0s`
- Recipient 2: sent at `start_at + 180s`
- Recipient 3: sent at `start_at + 360s`

---

## 7. Dispatches (Generic)

Create a dispatch to send messages to candidates/users via any supported channel.

```
POST /v1/users/dispatches
```

**Body:**
```json
{
  "dispatch": {
    "name": "Follow-up Campaign",
    "channel_type": "microsoft_mail",
    "subject": "Hello {{candidate_name}}",
    "body": "<p>Dear {{candidate_name}}, {{job_title}} update...</p>",
    "target_type": "ids",
    "candidate_ids": [1, 2, 3],
    "scheduled_for": "2026-03-01T14:00:00Z"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | no | Dispatch name |
| `channel_type` | string | yes | Channel: `microsoft_mail` |
| `subject` | string | yes | Email subject (supports tags) |
| `body` | string | yes | HTML body (supports tags) |
| `target_type` | string | yes | `ids`, `reference`, or `search` |
| `candidate_ids` | integer[] | conditional | Required when `target_type: "ids"` |
| `user_ids` | integer[] | conditional | Alternative to `candidate_ids` |
| `reference_type` | string | conditional | Polymorphic reference type (for `target_type: "reference"`) |
| `reference_id` | integer | conditional | Polymorphic reference ID |
| `scheduled_for` | string (ISO 8601) | no | Schedule send time |
| `target_payload` | object | conditional | Search params (for `target_type: "search"`) |

**Target Types:**
- `ids` — Send to specific candidate/user IDs
- `reference` — Send to all candidates/users tied to a polymorphic reference
- `search` — Send to candidates matching a search query

**Tag Replacement:** Tags in both `subject` and `body` are automatically replaced per recipient during async delivery. Each candidate gets their personalized version.

**Response:** `202 Accepted`
```json
{
  "dispatch": {
    "id": 101,
    "status": "pending",
    "channel_type": "microsoft_mail"
  }
}
```

---

## 8. Tag Replacer System (Internal)

### Architecture

The `TagReplacer` module is a standalone tag resolution engine used throughout the email system.

### Flow

```
Template with tags  →  TagReplacer::Service.call(content, record:, recruiter_id:)
                            ↓
                    Registry.tags_in(message)     ← finds which tags exist in the text
                            ↓
                    Context.new(record, recruiter_id) ← loads entities (candidate, job, user...)
                            ↓
                    ResolverFactory.for(tag_def)   ← picks the right resolver
                            ↓
                    Resolver.resolve(context, tag) ← returns the value
                            ↓
                    message.gsub!(tag, value)      ← replaces tag in text
```

### Usage (Ruby)

```ruby
content = "Hello {{candidate_name}}, the position {{job_title}} awaits you!"

rendered = TagReplacer::Service.call(
  content,
  record: {
    candidate: Candidate.find(42),
    job: Job.find(7)
  },
  recruiter_id: current_user.id
)
# => "Hello Maria Silva, the position Senior Developer awaits you!"
```

### Resolver Types

| Type | Description | Example Tags |
|------|-------------|-------------|
| `:attribute` | Direct attribute access on the entity | `{{candidate_name}}`, `{{job_title}}` |
| `:date` | Current date formatting | `{{date_today}}`, `{{date_br_today}}` |
| `:url` | URL generation | `{{candidate_access_url}}` |
| `:method` | Custom method call | `{{evaluation_candidate_url}}` |

### Allowed Entities

`candidate`, `recruiter`, `job`, `client_contact`, `client_company`, `user`, `interview`, `experience`, `education`, `business`, `proposal`, `evaluation_candidate`

### Allowed Attributes

`name`, `first_name`, `last_name`, `email`, `phone`, `mobile_phone`, `title`, `description`, `location`, `occupation_name`, `company_name`, `cpf`, `rg`, `cnpj`, `address`, `city`, `state`, `zip`, `linkedin`, `logo_url`, `corporate_name`

### Safety

The `Sanitizer` whitelist ensures only approved entities and methods can be accessed — arbitrary attribute access is blocked.

### Error Handling

When a tag cannot be resolved (entity not found, attribute missing), the tag is left as-is in the output (e.g., `{{job_title}}` stays if no job provided). The `render_preview` endpoint returns unresolved tags in the `missing_variables` array.

---

## Common Patterns

### Pattern 1: Create template → Preview → Send

```
1. POST /v1/users/email_templates          ← Create template with tags
2. POST /v1/users/email_templates/render    ← Preview with real candidate data
3. POST /v1/users/email_templates/send      ← Send to multiple candidates
```

### Pattern 2: Bulk campaign with pacing

```
1. GET  /v1/users/email_templates/tags      ← Get available tags
2. POST /v1/users/email_templates           ← Create template
3. POST /v1/users/integrations/microsoft/email/bulk  ← Send with delay
```

### Pattern 3: Quick single email

```
POST /v1/users/integrations/microsoft/email  ← Direct send (no template)
```

### Pattern 4: Dispatch to search results

```
POST /v1/users/dispatches
{
  "dispatch": {
    "channel_type": "microsoft_mail",
    "target_type": "search",
    "subject": "New opportunity: {{job_title}}",
    "body": "...",
    "target_payload": {
      "query": "ruby developer",
      "where": { "city": "São Paulo" }
    }
  }
}
```

---

## Error Responses

### Validation Error
```json
{ "error": "subject é obrigatório" }
```
Status: `422 Unprocessable Entity`

### Not Found
```json
{ "error": "Email Template not found" }
```
Status: `404 Not Found`

### Send Failure
```json
{ "error": "Falha ao enviar emails" }
```
Status: `422 Unprocessable Entity`

### Dispatch Validation
```json
{ "errors": ["Sem candidatos ou usuários informados"] }
```
Status: `422 Unprocessable Entity`
