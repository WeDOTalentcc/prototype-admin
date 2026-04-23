# Interview Scheduling Agent — Blueprint

Blueprint for building a conversational agent (via Microsoft Teams chat) that schedules interviews end-to-end. Documents what already exists in the codebase, what's missing, and the exact input/output of every API call the agent needs to make.

---

## Status: What We Already Have

| Capability | Status | Service/Endpoint |
|---|---|---|
| Receive Teams messages (webhooks) | ✅ Ready | `POST /v1/webhooks/teams_chat` |
| Send Teams messages | ✅ Ready | `MicrosoftService::Teams.send_message` |
| Parse natural language date/time | ✅ Ready | `POST /v1/users/calendar_events/suggest_schedule` |
| Check single-user availability | ✅ Ready | `GET /v1/users/scheduling/availability` |
| Create calendar event + meeting | ✅ Ready | `POST /v1/users/calendar_events` |
| Self-scheduling link (candidate picks slot) | ✅ Ready | `POST /v1/users/scheduling/links` |
| Notify candidate (email + WhatsApp) | ✅ Ready | Built into scheduling link creation |
| Check today's interviews | ✅ Ready | `GET /v1/users/calendar_events/daily_agenda` |
| **Multi-user availability (find common slots)** | ❌ Missing | Need new endpoint |
| **Job interviewers list** | ❌ Missing | Need new endpoint |
| **Agent session/state management** | ❌ Missing | Need new service |
| **Agent message processor** | ❌ Missing | Need new service |

---

## What Needs to Be Built

### 1. Multi-user availability endpoint

The `AvailabilityService` uses `/me/calendar/getSchedule` which already supports multiple emails in the `schedules` array — it just isn't exposed yet.

```
GET /v1/users/scheduling/availability/multi
```

**Params:**
```
attendee_emails[]=paula@company.com&attendee_emails[]=paulo@company.com
&start_date=2026-03-10&end_date=2026-03-14&duration_minutes=60
```

**Response:**
```json
{
  "common_slots": [
    {
      "start_time": "2026-03-10T14:00:00-03:00",
      "end_time": "2026-03-10T15:00:00-03:00",
      "date": "2026-03-10",
      "status": "available"
    }
  ],
  "per_user": {
    "paula@company.com": { "busy_periods": [...] },
    "paulo@company.com": { "busy_periods": [...] }
  }
}
```

The Graph API call to implement this:
```
POST /me/calendar/getSchedule
{
  "schedules": ["paula@company.com", "paulo@company.com", "recruiter@company.com"],
  "startTime": { "dateTime": "2026-03-10T00:00:00", "timeZone": "UTC" },
  "endTime": { "dateTime": "2026-03-14T23:59:59", "timeZone": "UTC" },
  "availabilityViewInterval": 60
}
```

Then intersect the `scheduleItems` of all users to find common free windows.

---

### 2. Job interviewers endpoint

```
GET /v1/users/jobs/:id/interviewers
```

**Response:**
```json
{
  "data": [
    {
      "id": 42,
      "name": "Paulo Moraes",
      "email": "paulo@company.com",
      "role": "Tech Lead",
      "interview_count": 12
    }
  ]
}
```

This should return the users who are members/collaborators of the job and have participated in interviews before (historical context helps the agent suggest them).

---

### 3. Agent session service

Tracks the conversation state across multiple Teams messages for a single scheduling request.

**State machine:**

```
:idle
  → :identifying_candidate  (triggered by "agendar entrevista")
  → :selecting_interview_type
  → :selecting_interviewers
  → :checking_availability
  → :slot_selected
  → :confirming
  → :done
```

**State payload (stored in Redis or DB per chat_id):**
```json
{
  "session_id": "uuid",
  "chat_id": "19:abc...",
  "recruiter_user_id": 1,
  "state": "selecting_interviewers",
  "data": {
    "apply_id": 789,
    "candidate_id": 123,
    "candidate_name": "Ana Oliveira",
    "job_id": 456,
    "job_title": "Desenvolvedor Python Sênior",
    "interview_type": "technical",
    "interviewers": [],
    "slot": null,
    "platform": null
  },
  "expires_at": "2026-03-07T12:00:00Z"
}
```

---

### 4. Agent message processor

The entry point that receives the parsed Teams webhook and routes to the right handler based on the current session state.

```ruby
# app/services/agents/interview_scheduling_agent.rb
module Agents
  class InterviewSchedulingAgent
    def self.process(chat_id:, message:, recruiter_user:)
      new(chat_id, message, recruiter_user).call
    end

    def call
      session = load_or_create_session
      handler = handler_for(session.state)
      result = handler.call(session, @message)
      save_session(result.next_session)
      send_reply(result.reply)
    end
  end
end
```

---

## Complete Agent Flow

### Flow A: Self-scheduling (recommended — candidate picks the slot)

```
Recruiter message
      │
      ▼
[1] Parse intent + extract candidate/job context
      │ POST /v1/users/calendar_events/suggest_schedule (if time was mentioned)
      │ GET  /v1/users/jobs/:id/interviewers
      ▼
[2] Confirm interview type + interviewers
      │ (conversation turn if not inferred)
      ▼
[3] Check availability for all participants
      │ GET /v1/users/scheduling/availability/multi
      │   attendee_emails[]=recruiter@co.com&attendee_emails[]=interviewer@co.com
      │   start_date=today&end_date=+7days&duration_minutes=60
      ▼
[4] Create scheduling link with 3-5 best slots
      │ POST /v1/users/scheduling/links
      │ Body: { candidate_id, job_id, apply_id, slots: [...], channels: ["email","whatsapp"] }
      ▼
[5] Confirm to recruiter + show public_url
      │ MicrosoftService::Teams.send_message(reply with link + summary)
      ▼
[Candidate receives email/WhatsApp, picks slot]
      ▼
[6] Booking happens automatically (no agent action needed)
      │ System creates CalendarEvent + Meeting + notifies both parties
      ▼
[7] Agent notifies recruiter in Teams that booking was confirmed
      │ Triggered by SchedulingLink webhook/job after booking
      │ MicrosoftService::Teams.send_message("Ana Oliveira confirmou: Ter 11/03 10:00")
```

### Flow B: Direct scheduling (recruiter fixes the slot)

```
Recruiter message with explicit date/time
      │
      ▼
[1] Parse date/time from natural language
      │ POST /v1/users/calendar_events/suggest_schedule
      │ Body: { "text": "terça às 10h", "timezone": "America/Sao_Paulo" }
      │ → { suggestions: [{ start_time: "2026-03-11T10:00:00-03:00", end_time: "..." }] }
      ▼
[2] Validate no conflicts for all participants
      │ GET /v1/users/scheduling/availability/multi
      │ Check that proposed slot is free for everyone
      ▼
[3] Create calendar event directly
      │ POST /v1/users/calendar_events
      │ Body: { title, start_time, end_time, event_type: "interview",
      │         settings: { online_meeting: true }, attendees: [...], apply_id }
      │ → { data: { join_url: "https://teams.microsoft.com/...", id: 99 } }
      ▼
[4] Confirm to recruiter + show join_url
      │ MicrosoftService::Teams.send_message(summary + Teams link)
```

---

## API Reference — Agent Calls

### Step 1a: Parse natural language time

```
POST /v1/users/calendar_events/suggest_schedule
Authorization: Bearer <jwt>

{
  "text": "terça às 10h por 1 hora",
  "timezone": "America/Sao_Paulo"
}
```

**Success response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "is_primary": true,
        "label": "Terça-feira, 10 de Março",
        "date": "2026-03-11",
        "start_time": "2026-03-11T10:00:00-03:00",
        "end_time": "2026-03-11T11:00:00-03:00",
        "duration_minutes": 60,
        "human_readable": "Terça-feira, 11/03 às 10:00 - 11:00"
      }
    ]
  }
}
```

**When to use:** Whenever the recruiter mentions a time in natural language.

---

### Step 1b: Get job interviewers (to be built)

```
GET /v1/users/jobs/456/interviewers
Authorization: Bearer <jwt>
```

**Success response:**
```json
{
  "data": [
    { "id": 42, "name": "Paulo Moraes", "email": "paulo@company.com", "role": "Tech Lead" },
    { "id": 43, "name": "Fernanda Costa", "email": "fernanda@company.com", "role": "Manager" }
  ]
}
```

**When to use:** When the agent needs to suggest interviewers or the recruiter says "sugere aí".

---

### Step 2a: Check single-user availability

```
GET /v1/users/scheduling/availability?start_date=2026-03-10&end_date=2026-03-14&duration_minutes=60
Authorization: Bearer <jwt>
```

**Success response:**
```json
{
  "slots": [
    { "start_time": "2026-03-10T09:00:00-03:00", "end_time": "2026-03-10T10:00:00-03:00", "status": "available", "date": "2026-03-10" },
    { "start_time": "2026-03-10T10:15:00-03:00", "end_time": "2026-03-10T11:15:00-03:00", "status": "busy", "date": "2026-03-10" }
  ],
  "busy_periods": [
    { "start_time": "2026-03-10T10:00:00-03:00", "end_time": "2026-03-10T10:30:00-03:00", "subject": "Daily", "date": "2026-03-10" }
  ]
}
```

**When to use:** When only the recruiter's availability matters (no interviewers).

---

### Step 2b: Check multi-user availability (to be built)

```
GET /v1/users/scheduling/availability/multi
  ?attendee_emails[]=paulo@company.com
  &attendee_emails[]=recruiter@company.com
  &start_date=2026-03-10&end_date=2026-03-14&duration_minutes=60
Authorization: Bearer <jwt>
```

**Success response:**
```json
{
  "common_slots": [
    { "start_time": "2026-03-11T10:00:00-03:00", "end_time": "2026-03-11T11:00:00-03:00", "date": "2026-03-11", "status": "available" },
    { "start_time": "2026-03-12T14:00:00-03:00", "end_time": "2026-03-12T15:00:00-03:00", "date": "2026-03-12", "status": "available" }
  ],
  "per_user": {
    "paulo@company.com": { "busy_count": 3 },
    "recruiter@company.com": { "busy_count": 5 }
  }
}
```

**When to use:** When there are interviewers to coordinate. Filter `common_slots` for `status: "available"` and pick the best 3-5.

---

### Step 3: Create scheduling link (self-scheduling flow)

```
POST /v1/users/scheduling/links
Authorization: Bearer <jwt>

{
  "scheduling_link": {
    "candidate_id": 123,
    "job_id": 456,
    "apply_id": 789,
    "subject": "Entrevista Técnica — Desenvolvedor Python Sênior",
    "interview_type": "technical",
    "platform": "microsoft_teams",
    "duration_minutes": 60,
    "expires_at": "2026-03-13T23:59:59-03:00",
    "channels": ["email", "whatsapp"],
    "slots": [
      { "start_time": "2026-03-10T14:00:00-03:00", "end_time": "2026-03-10T15:00:00-03:00" },
      { "start_time": "2026-03-11T10:00:00-03:00", "end_time": "2026-03-11T11:00:00-03:00" },
      { "start_time": "2026-03-12T09:00:00-03:00", "end_time": "2026-03-12T10:00:00-03:00" }
    ]
  }
}
```

**Success response (201):**
```json
{
  "data": {
    "id": "10",
    "type": "scheduling_link",
    "attributes": {
      "token": "abc123xyz",
      "status": "active",
      "public_url": "https://wedotalent.cc/scheduling/ACCOUNT_UID/abc123xyz",
      "is_bookable": true,
      "slots": [
        { "id": 1, "start_time": "2026-03-10T14:00:00-03:00", "end_time": "2026-03-10T15:00:00-03:00", "is_available": true }
      ]
    }
  }
}
```

**Side effects (automatic):** Email + WhatsApp sent to candidate with `public_url`.

**When to use:** When you want the candidate to pick the time. Preferred flow.

---

### Step 3 (alt): Create calendar event directly (direct scheduling flow)

```
POST /v1/users/calendar_events
Authorization: Bearer <jwt>

{
  "calendar_event": {
    "title": "Entrevista Técnica — Ana Oliveira",
    "start_time": "2026-03-11T10:00:00-03:00",
    "end_time": "2026-03-11T11:00:00-03:00",
    "provider": "microsoft",
    "event_type": "interview",
    "importance": "high",
    "timezone": "America/Sao_Paulo",
    "job_id": 456,
    "apply_id": 789,
    "sub_status": "invite_sent",
    "reference_type": "Candidate",
    "reference_id": 123,
    "role": "candidate",
    "settings": { "online_meeting": true },
    "attendees": [
      { "email": "ana@email.com", "name": "Ana Oliveira", "required": true },
      { "email": "paulo@company.com", "name": "Paulo Moraes", "required": true }
    ]
  }
}
```

**Success response (201):**
```json
{
  "data": {
    "id": "99",
    "type": "calendar_event",
    "attributes": {
      "title": "Entrevista Técnica — Ana Oliveira",
      "start_time": "2026-03-11T10:00:00-03:00",
      "end_time": "2026-03-11T11:00:00-03:00",
      "sub_status": "invite_sent",
      "join_url": "https://teams.microsoft.com/l/meetup-join/...",
      "external_id": "AAMkADI...",
      "attendees": [
        { "email": "ana@email.com", "name": "Ana Oliveira", "response_status": "not_responded" },
        { "email": "paulo@company.com", "name": "Paulo Moraes", "response_status": "not_responded" }
      ]
    }
  }
}
```

**When to use:** When the recruiter fixes the time directly and you want to create the event immediately (calendar invite goes to all attendees automatically via Outlook).

---

### Step 4: Update interview status

```
PATCH /v1/users/calendar_events/99
Authorization: Bearer <jwt>

{
  "calendar_event": {
    "sub_status": "confirmed"
  }
}
```

**Sub-status lifecycle:**
```
invite_sent → scheduled → confirmed → completed
                                    → no_show
```

---

### Helper: Check existing interviews before scheduling

```
GET /v1/users/calendar_events/daily_agenda?event_type=interview&from=2026-03-10&to=2026-03-14
Authorization: Bearer <jwt>
```

**When to use:** Before offering slots, verify no interview for this candidate/job already exists in the window.

---

## Agent Message Templates (Teams replies)

### Asking for interview type
```
Encontrei {candidate_name} na vaga {job_title}.

Que tipo de entrevista?
1. RH
2. Técnica
3. Entrevista com Gestor
4. Case Técnico

(ou me diga o tipo)
```

### Showing common slots
```
Horários livres para {interviewer_names} nos próximos 5 dias:

1. Seg 10/03 — 14:00-15:00
2. Ter 11/03 — 10:00-11:00
3. Qua 12/03 — 09:00-10:00

Qual prefere? (ou me diga outro horário)
```

### Conflict detected
```
{interviewer_name} tem conflito em {requested_time} ({conflict_subject}).

Alternativas:
1. {alternative_1}
2. {alternative_2}
3. Manter o horário mesmo assim
```

### Confirmation before sending
```
Resumo antes de enviar:

Entrevista {interview_type} — {candidate_name}
{date_formatted} | {start_time} - {end_time} | {platform}
Entrevistadores: {interviewer_names}

Candidato será notificado por {channels}.

Confirma? (sim/nao)
```

### Success (self-scheduling)
```
Link de agendamento enviado para {candidate_name}!

{email_sent ? "E-mail enviado." : ""}
{whatsapp_sent ? "WhatsApp enviado." : ""}

URL: {public_url}
Expira em: {expires_at_formatted}

Aguardando o candidato escolher o horário.
```

### Success (direct scheduling)
```
Entrevista agendada!

{candidate_name} — {date_formatted} {start_time}-{end_time}
Link Teams: {join_url}

Convite enviado para todos os participantes.
```

### Booking confirmed (async notification to recruiter)
```
{candidate_name} escolheu o horario!

{date_formatted} | {start_time} - {end_time}
Link Teams: {join_url}

Evento criado no seu calendario.
```

---

## Decision Logic for the Agent

```
Recruiter sends message
        │
        ├─ Contains candidate name/reference + "agenda/entrevista/schedule"?
        │    YES → Start scheduling session
        │    NO  → Pass to other agent or respond "nao entendi"
        │
        ▼
Does message contain explicit date/time?
        ├─ YES → POST suggest_schedule → propose Direct Flow
        └─ NO  → Propose Self-Scheduling Flow (candidate picks)
        │
        ▼
Does message specify interviewers?
        ├─ YES → Use mentioned users
        └─ NO  → GET /jobs/:id/interviewers → suggest top candidates
        │
        ▼
Are there multiple interviewers?
        ├─ YES → GET /scheduling/availability/multi (find common slots)
        └─ NO  → GET /scheduling/availability (single user)
        │
        ▼
Recruiter confirms slot/approach
        │
        ├─ Self-scheduling → POST /scheduling/links (candidate picks) → send link
        └─ Direct          → POST /calendar_events (fixed time)       → send confirmation
```

---

## Context the Agent Needs in Every Session

| Field | Source | How to get it |
|---|---|---|
| `recruiter_user_id` | JWT token | From auth context |
| `apply_id` | Message context or search | From previous agent turn or `GET /applies?candidate_name=...` |
| `candidate_id` | From apply | `apply.candidate_id` |
| `candidate_name` | From apply | `apply.candidate.name` |
| `job_id` | From apply | `apply.job_id` |
| `job_title` | From job | `apply.job.title` |
| `interview_type` | Extracted from message or asked | NLU or menu |
| `interviewers` | Mentioned or suggested | Message NLU or GET /jobs/:id/interviewers |
| `slot` | Offered by agent, chosen by recruiter | From availability check |
| `platform` | Mentioned or from settings | Default: `microsoft_teams` |

---

## Summary: Build Order

1. **`GET /v1/users/scheduling/availability/multi`** — extend `AvailabilityService` to accept multiple emails (the Graph API already supports it, just pass multiple values in the `schedules` array). This unblocks the agent from checking conflicts for multiple interviewers.

2. **`GET /v1/users/jobs/:id/interviewers`** — expose job team members so the agent can suggest interviewers instead of asking.

3. **Agent session store** — Redis-backed session per `chat_id` tracking state + collected data across multiple Teams messages.

4. **Agent message processor** — the orchestration service that receives the parsed Teams webhook message, calls the APIs above in the right order, and sends the formatted Teams reply.

5. **Post-booking notifier** — a job triggered when a `SchedulingLink` is booked that finds the recruiter's Teams chat and sends the confirmation message.
