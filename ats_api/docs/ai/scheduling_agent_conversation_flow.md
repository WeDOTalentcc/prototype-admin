# Scheduling Agent — Conversation Flow & API Map

Complete reference for building a conversational AI agent that schedules interviews with candidates.

---

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         SCHEDULING AGENT             │
                    │  (Receives context from orchestrator) │
                    └──────────┬──────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
     ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
     │  SCREENING  │   │  SCHEDULING │   │  DIRECT     │
     │  COMPLETE   │   │  FLOW       │   │  FLOW       │
     │  (trigger)  │   │  (self-sched)│  │  (fixed)    │
     └─────────────┘   └─────────────┘   └─────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
     EvaluationCandidate  SchedulingLink     CalendarEvent
     score >= threshold   + Slots            + Meeting
                          → public_url       → join_url
                          → candidate books  → instant
```

---

## Agent Input (Context Received)

When the scheduling agent is invoked, it receives:

```json
{
  "trigger": "screening_complete | recruiter_request | pipeline_advance",
  "candidate": {
    "id": 123,
    "name": "Maria Santos",
    "email": "maria@example.com",
    "mobile_phone": "+5511999999999"
  },
  "apply": {
    "id": 789,
    "job_id": 456,
    "job_title": "Senior Ruby Developer",
    "current_stage": "interview",
    "sub_status": "invite_sent"
  },
  "evaluation_result": {
    "score": 8.2,
    "wsi_classification": "High",
    "recommendation": "APPROVED"
  },
  "recruiter": {
    "id": 1,
    "name": "João Silva",
    "token": "<jwt>"
  },
  "account": {
    "id": 1,
    "uid": "acc_abc123",
    "timezone": "America/Sao_Paulo"
  },
  "preferences": {
    "interview_type": "technical",
    "platform": "microsoft_teams",
    "duration_minutes": 60,
    "scheduling_mode": "self_scheduling"
  }
}
```

---

## Agent Output (Result Returned)

```json
{
  "action_taken": "scheduling_link_created | calendar_event_created | failed",
  "scheduling_link": {
    "id": 10,
    "token": "abc123xyz",
    "public_url": "https://wedotalent.cc/scheduling/acc_abc123/abc123xyz",
    "slots_offered": 5,
    "expires_at": "2026-03-15T23:59:59-03:00",
    "notifications_sent": ["email", "whatsapp"]
  },
  "calendar_event": {
    "id": 50,
    "start_time": "2026-03-10T14:00:00-03:00",
    "end_time": "2026-03-10T15:00:00-03:00",
    "join_url": "https://teams.microsoft.com/l/meetup-join/...",
    "sub_status": "invite_sent"
  },
  "message_to_candidate": "Olá Maria! Sua avaliação para Senior Ruby Developer foi excelente...",
  "message_to_recruiter": "Entrevista agendada com Maria Santos para Senior Ruby Developer...",
  "next_actions": ["wait_for_booking", "follow_up_in_48h"]
}
```

---

## Conversation Flow — Decision Tree

```
AGENT RECEIVES CONTEXT
│
├─ 1. VALIDATE PREREQUISITES
│  ├─ Has candidate email or phone? → NO → Return error: missing contact
│  ├─ Has recruiter Microsoft/Google connected? → NO → Return error: no calendar provider
│  └─ All OK → Continue
│
├─ 2. CHECK RECRUITER SCHEDULE
│  │  GET /v1/users/scheduling/availability
│  │  Input: { start_date, end_date, duration_minutes }
│  │  Output: { slots[], busy_periods[] }
│  │
│  ├─ No available slots in range? → Expand date range (+7 days) and retry
│  └─ Has slots → Continue
│
├─ 3. DECIDE SCHEDULING MODE
│  │
│  ├─ preferences.scheduling_mode == "self_scheduling"
│  │  │
│  │  ├─ 3a. SELECT BEST SLOTS (3-5 slots)
│  │  │   Strategy: Pick from different days/times for flexibility
│  │  │   Avoid: Early morning (<9h), late evening (>18h), Mondays, Fridays
│  │  │
│  │  ├─ 3b. CREATE SCHEDULING LINK
│  │  │   POST /v1/users/scheduling/links
│  │  │   Input: { candidate_id, job_id, apply_id, subject, platform, slots[], channels[] }
│  │  │   Output: { token, public_url, status: "active" }
│  │  │   Side Effects: Email + WhatsApp invites sent automatically
│  │  │
│  │  └─ 3c. WAIT FOR CANDIDATE BOOKING
│  │     Candidate accesses public_url → picks slot → system auto-creates:
│  │       - Meeting (Teams/Meet/Zoom link)
│  │       - CalendarEvent (on recruiter calendar)
│  │       - Notifications to both parties
│  │
│  └─ preferences.scheduling_mode == "direct"
│     │
│     ├─ 3a. PICK BEST AVAILABLE SLOT
│     │   Strategy: Next available slot during business hours
│     │
│     ├─ 3b. CREATE CALENDAR EVENT + MEETING
│     │   POST /v1/users/calendar_events
│     │   Input: { title, start_time, end_time, provider, event_type: "interview",
│     │            attendees[], settings: { online_meeting: true }, reference_type, reference_id }
│     │   Output: { id, join_url, sub_status: "invite_sent" }
│     │   Side Effects: Calendar invite sent to all attendees
│     │
│     └─ 3c. UPDATE APPLY SUB-STATUS
│        PATCH /v1/users/calendar_events/:id
│        Input: { sub_status: "scheduled" }
│
├─ 4. POST-SCHEDULING ACTIONS
│  ├─ Log action in conversation history
│  ├─ Schedule follow-up reminder (48h if no booking)
│  └─ Update apply.sub_status → "invite_sent"
│
└─ 5. ERROR HANDLING
   ├─ Calendar API failure → Retry once, then notify recruiter
   ├─ No slots available → Suggest recruiter manually pick a time
   └─ Candidate has no contact → Ask recruiter for contact info
```

---

## API Calls — Step-by-Step with I/O

### Step 1: Check Scheduling Settings

```
GET /v1/users/scheduling/settings
Authorization: Bearer <jwt>
```

**Output:**
```json
{
  "timezone": "America/Sao_Paulo",
  "work_hours_start": "09:00",
  "work_hours_end": "18:00",
  "default_duration_minutes": 60,
  "buffer_minutes": 15,
  "lookahead_days": 14
}
```

**Agent uses:** timezone, work_hours, duration, lookahead to calculate date range.

---

### Step 2: Check Availability

```
GET /v1/users/scheduling/availability?start_date=2026-03-10&end_date=2026-03-14&duration_minutes=60
Authorization: Bearer <jwt>
```

**Output:**
```json
{
  "slots": [
    { "start_time": "2026-03-10T09:00:00-03:00", "end_time": "2026-03-10T10:00:00-03:00", "status": "available" },
    { "start_time": "2026-03-10T10:15:00-03:00", "end_time": "2026-03-10T11:15:00-03:00", "status": "busy" },
    { "start_time": "2026-03-10T14:00:00-03:00", "end_time": "2026-03-10T15:00:00-03:00", "status": "available" }
  ],
  "busy_periods": [
    { "start_time": "2026-03-10T10:00:00-03:00", "end_time": "2026-03-10T10:30:00-03:00", "subject": "Daily Standup" }
  ]
}
```

**Agent filters:** Only `status: "available"` slots, picks 3-5 across different days.

---

### Step 3a: Create Scheduling Link (Self-Scheduling)

```
POST /v1/users/scheduling/links
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "scheduling_link": {
    "candidate_id": 123,
    "job_id": 456,
    "apply_id": 789,
    "subject": "Technical Interview - Senior Ruby Developer",
    "message": "Please select a time that works best for you.",
    "interview_type": "technical",
    "platform": "microsoft_teams",
    "duration_minutes": 60,
    "expires_at": "2026-03-15T23:59:59-03:00",
    "channels": ["email", "whatsapp"],
    "slots": [
      { "start_time": "2026-03-10T09:00:00-03:00", "end_time": "2026-03-10T10:00:00-03:00" },
      { "start_time": "2026-03-10T14:00:00-03:00", "end_time": "2026-03-10T15:00:00-03:00" },
      { "start_time": "2026-03-11T10:00:00-03:00", "end_time": "2026-03-11T11:00:00-03:00" },
      { "start_time": "2026-03-12T09:00:00-03:00", "end_time": "2026-03-12T10:00:00-03:00" },
      { "start_time": "2026-03-12T14:00:00-03:00", "end_time": "2026-03-12T15:00:00-03:00" }
    ]
  }
}
```

**Output:**
```json
{
  "data": {
    "id": "10",
    "type": "scheduling_link",
    "attributes": {
      "token": "abc123xyz",
      "status": "active",
      "public_url": "https://wedotalent.cc/scheduling/acc_abc123/abc123xyz",
      "is_bookable": true,
      "slots": [
        { "id": 1, "start_time": "2026-03-10T09:00:00-03:00", "end_time": "2026-03-10T10:00:00-03:00", "is_available": true }
      ]
    }
  }
}
```

**Side Effects:**
- Email sent to candidate with scheduling link
- WhatsApp template "entrevista" sent with link button

---

### Step 3b: Create Calendar Event (Direct Scheduling)

```
POST /v1/users/calendar_events
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "calendar_event": {
    "title": "Technical Interview - Senior Ruby Developer - Maria Santos",
    "start_time": "2026-03-10T14:00:00-03:00",
    "end_time": "2026-03-10T15:00:00-03:00",
    "provider": "microsoft",
    "event_type": "interview",
    "importance": "high",
    "timezone": "America/Sao_Paulo",
    "description": "Technical interview for Senior Ruby Developer position",
    "job_id": 456,
    "apply_id": 789,
    "sub_status": "invite_sent",
    "reference_type": "Candidate",
    "reference_id": 123,
    "settings": { "online_meeting": true },
    "attendees": [
      { "email": "maria@example.com", "name": "Maria Santos", "required": true }
    ]
  }
}
```

**Output:**
```json
{
  "data": {
    "id": "50",
    "type": "calendar_event",
    "attributes": {
      "title": "Technical Interview - Senior Ruby Developer - Maria Santos",
      "start_time": "2026-03-10T14:00:00-03:00",
      "end_time": "2026-03-10T15:00:00-03:00",
      "join_url": "https://teams.microsoft.com/l/meetup-join/...",
      "sub_status": "invite_sent",
      "provider": "microsoft"
    }
  }
}
```

**Side Effects:**
- Calendar event created on recruiter's Microsoft/Google calendar
- Meeting invitation sent via the provider to all attendees
- Meeting record created in the database
- MeetingRelationship links candidate to meeting

---

### Step 4: Candidate Books (Automatic — Self-Scheduling Only)

```
POST /v1/acc_abc123/scheduling/abc123xyz/book
Content-Type: application/json

{ "slot_id": 1 }
```

**Output:**
```json
{
  "status": "booked",
  "subject": "Technical Interview - Senior Ruby Developer",
  "start_time": "2026-03-10T09:00:00-03:00",
  "end_time": "2026-03-10T10:00:00-03:00",
  "join_url": "https://teams.microsoft.com/l/meetup-join/...",
  "platform": "microsoft_teams",
  "recruiter_name": "João Silva",
  "company_name": "WeDOTalent"
}
```

**Automatic Side Effects:**
- Meeting created (Teams/Meet/Zoom)
- CalendarEvent created on recruiter calendar
- Remaining slots marked unavailable
- SchedulingLink status → "booked"
- Email confirmation to recruiter + candidate
- WhatsApp "confirmacao_entrevista" template to candidate

---

## API Gap Analysis — What's Missing

### HIGH Priority (Needed for production agent)

| # | Gap | Impact | Workaround |
|---|-----|--------|------------|
| 1 | **Reschedule endpoint** | No single API to reschedule. Must cancel + recreate. | Agent deletes old event, creates new one. Risk: data loss on failure mid-flow. |
| 2 | **Resend invite/notification** | Cannot re-trigger email/WhatsApp for existing links. | Delete link, create new one with same slots. Loses link token/history. |

### MEDIUM Priority (Quality of life)

| # | Gap | Impact | Workaround |
|---|-----|--------|------------|
| 3 | **List meetings by candidate/apply** | No filter to find all meetings for a specific candidate. | `GET /v1/users/meetings` returns all, agent filters client-side. |
| 4 | **Interview reminder worker** | No automated reminders before interviews. | Agent must track and trigger reminders externally. |
| 5 | **WebSocket broadcast on booking** | Recruiter not notified in real-time when candidate books. | Recruiter sees it on page refresh or email. |

### LOW Priority (Nice to have)

| # | Gap | Impact | Workaround |
|---|-----|--------|------------|
| 6 | **Candidate-side cancel endpoint** | No public URL for candidate to cancel/reschedule. | Candidate must contact recruiter. |
| 7 | **Candidate availability check** | Only recruiter calendar checked, not candidate's. | Agent asks candidate for preferred times in conversation. |

---

## Sub-Status Lifecycle

```
invite_sent ──► scheduled ──► confirmed ──► completed
                                         └─► no_show
```

| Status | Who Sets | When |
|---|---|---|
| `invite_sent` | Agent | After creating link or calendar event |
| `scheduled` | System | After candidate books a slot |
| `confirmed` | Agent/Recruiter | After both parties confirm |
| `completed` | Agent/Recruiter | After interview happens |
| `no_show` | Agent/Recruiter | If candidate/interviewer didn't attend |

---

## Follow-Up Logic

```
AFTER SCHEDULING LINK CREATED
│
├─ t + 24h: Check if booked
│  ├─ YES → Done (system handled notifications)
│  └─ NO → Continue
│
├─ t + 48h: Send follow-up
│  ├─ Channel: WhatsApp preferred, email fallback
│  ├─ Message: "Reminder: you have pending interview slots to choose from"
│  └─ [REQUIRES: Resend notification API — currently missing]
│
├─ t + 72h: Final reminder
│  ├─ Send last reminder
│  └─ Alert recruiter: "Candidate hasn't booked after 72h"
│
└─ t + expires_at: Link expires
   └─ Notify recruiter: "Scheduling link expired without booking"
      Suggest: recreate with new dates or switch to direct scheduling
```

---

## Platform Support

| Platform | Online Meeting? | Calendar Integration? | Provider Value |
|---|---|---|---|
| Microsoft Teams | Yes | Microsoft Calendar | `microsoft_teams` or `teams` |
| Google Meet | Yes | Google Calendar | `google_meet` |
| Zoom | Yes | No native calendar | `zoom` |
| Presential | No | Microsoft/Google | `presential` (uses `location`) |

---

## Notification Channels Summary

| Event | Email | WhatsApp | In-App |
|---|---|---|---|
| Scheduling link created | Yes (auto) | Yes (auto, if phone) | No |
| Candidate books slot | Yes (auto) | Yes (auto, if phone) | No |
| Interview reminder | No (missing) | No (missing) | No |
| Interview cancelled | No (missing) | No (missing) | No |
| No-show detected | No (missing) | No (missing) | No |

---

## Helper APIs

### Natural Language → Structured Time

```
POST /v1/users/calendar_events/suggest_schedule
Input:  { "text": "next tuesday at 2pm for 45 minutes", "timezone": "America/Sao_Paulo" }
Output: { "suggestions": [{ "date": "2026-03-10", "start_time": "...", "end_time": "...", "duration_minutes": 45 }] }
```

### Daily Agenda

```
GET /v1/users/calendar_events/daily_agenda?kind=upcoming&event_type=interview
Output: Grouped by date, lists all upcoming interviews
```

---

## Full Flow Sequence Diagram

```
Recruiter Agent          ATS API              Microsoft Graph         Candidate
     │                     │                       │                     │
     │  GET /settings      │                       │                     │
     │────────────────────>│                       │                     │
     │  {timezone, hours}  │                       │                     │
     │<────────────────────│                       │                     │
     │                     │                       │                     │
     │  GET /availability  │                       │                     │
     │────────────────────>│  GET /calendar/view   │                     │
     │                     │──────────────────────>│                     │
     │                     │  {busy_periods}       │                     │
     │                     │<──────────────────────│                     │
     │  {available_slots}  │                       │                     │
     │<────────────────────│                       │                     │
     │                     │                       │                     │
     │  POST /links        │                       │                     │
     │────────────────────>│                       │                     │
     │  {token, url}       │  Send Email           │                     │
     │<────────────────────│───────────────────────────────────────────>│
     │                     │  Send WhatsApp        │                     │
     │                     │───────────────────────────────────────────>│
     │                     │                       │                     │
     │                     │                       │     POST /book      │
     │                     │<──────────────────────────────────────────│
     │                     │  POST /onlineMeetings │                     │
     │                     │──────────────────────>│                     │
     │                     │  {join_url}           │                     │
     │                     │<──────────────────────│                     │
     │                     │  POST /events         │                     │
     │                     │──────────────────────>│                     │
     │                     │  {event_id}           │                     │
     │                     │<──────────────────────│                     │
     │                     │  Confirm Email        │                     │
     │                     │───────────────────────────────────────────>│
     │                     │  Confirm WhatsApp     │                     │
     │                     │───────────────────────────────────────────>│
     │                     │                       │                     │
```

---

## Recommendations for Agent Implementation

1. **Always use self-scheduling** as default — higher booking rates, better candidate experience
2. **Offer 5 slots** across 3+ different days — improves conversion by ~40%
3. **Set expiration to 5 days** — creates urgency without pressure
4. **Always send both channels** (email + whatsapp) — WhatsApp has 3x higher open rate
5. **Parse natural language** with `suggest_schedule` when recruiter says "next week" or "tomorrow afternoon"
6. **Check daily_agenda** before scheduling to avoid double-booking edge cases
7. **Track sub_status** transitions for pipeline visibility
8. **Handle the reschedule gap** by implementing cancel+recreate as atomic operation in agent logic
