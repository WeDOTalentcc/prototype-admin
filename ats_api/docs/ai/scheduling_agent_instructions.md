# Scheduling & Interview Agent Instructions

Guide for an AI recruitment agent to schedule interviews with candidates using the ATS calendar and scheduling APIs.

---

## Overview

The system has two approaches to schedule interviews:

| Approach | Description | Best For |
|---|---|---|
| **Direct** | Create a CalendarEvent + Meeting directly at a fixed date/time | When the recruiter already knows the exact time |
| **Self-scheduling** | Create a SchedulingLink with available slots so the candidate picks | When you want the candidate to choose their preferred time |

---

## Authentication

All **authenticated** endpoints require the header:

```
Authorization: Bearer <jwt_token>
```

Base URL: `{API_HOST}/v1/users`

---

## Complete Scheduling Flow (Self-Scheduling — Recommended)

### Step 1: Check Recruiter Availability

```
GET /v1/users/scheduling/availability?start_date=2026-03-10&end_date=2026-03-14&duration_minutes=60
```

**Auth:** Required  
**Params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `date` | string | * | Single date (`YYYY-MM-DD`). Use this OR `start_date`/`end_date` |
| `start_date` | string | * | Range start (`YYYY-MM-DD`). Use with `end_date` |
| `end_date` | string | * | Range end (`YYYY-MM-DD`). Use with `start_date` |
| `duration_minutes` | integer | No | Slot duration (default: from recruiter settings, usually 60) |

**Response:**
```json
{
  "slots": [
    {
      "start_time": "2026-03-10T09:00:00-03:00",
      "end_time": "2026-03-10T10:00:00-03:00",
      "status": "available",
      "date": "2026-03-10"
    },
    {
      "start_time": "2026-03-10T10:15:00-03:00",
      "end_time": "2026-03-10T11:15:00-03:00",
      "status": "busy",
      "date": "2026-03-10"
    }
  ],
  "busy_periods": [
    {
      "start_time": "2026-03-10T10:00:00-03:00",
      "end_time": "2026-03-10T10:30:00-03:00",
      "subject": "Daily Standup",
      "date": "2026-03-10"
    }
  ]
}
```

The service integrates with Microsoft Calendar to fetch real busy periods. Slots are generated respecting the recruiter's `SchedulingSetting` (work hours, buffer, timezone, lookahead).

---

### Step 2: Create a Scheduling Link

Send available time slots to the candidate so they can pick.

```
POST /v1/users/scheduling/links
```

**Auth:** Required  
**Body:**

```json
{
  "scheduling_link": {
    "candidate_id": 123,
    "job_id": 456,
    "apply_id": 789,
    "subject": "Technical Interview - Senior Ruby Developer",
    "message": "Please select a time that works best for you.",
    "interview_type": "online",
    "platform": "microsoft_teams",
    "duration_minutes": 60,
    "expires_at": "2026-03-15T23:59:59-03:00",
    "channels": ["email", "whatsapp"],
    "slots": [
      { "start_time": "2026-03-10T09:00:00-03:00", "end_time": "2026-03-10T10:00:00-03:00" },
      { "start_time": "2026-03-10T14:00:00-03:00", "end_time": "2026-03-10T15:00:00-03:00" },
      { "start_time": "2026-03-11T10:00:00-03:00", "end_time": "2026-03-11T11:00:00-03:00" }
    ]
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|---|---|---|---|
| `candidate_id` | integer | Yes | Candidate to invite |
| `job_id` | integer | No | Related job |
| `apply_id` | integer | No | Related application |
| `subject` | string | No | Interview title |
| `message` | string | No | Message shown to candidate |
| `interview_type` | string | No | `technical`, `behavioral`, `cultural_fit`, `case_study`, `online`, `presential` |
| `platform` | string | No | `microsoft_teams`, `google_meet`, `zoom`, `teams` |
| `duration_minutes` | integer | No | Duration in minutes (default: 60) |
| `location` | string | No | Physical address (for presential) |
| `expires_at` | datetime | No | Link expiration |
| `channels` | array | No | Notification channels: `["email"]`, `["whatsapp"]`, `["email", "whatsapp"]` |
| `slots` | array | Yes | Available time slots (array of `{start_time, end_time}`) |

**Response (201 Created):**

```json
{
  "data": {
    "id": "10",
    "type": "scheduling_link",
    "attributes": {
      "token": "abc123xyz",
      "status": "active",
      "interview_type": "online",
      "platform": "microsoft_teams",
      "duration_minutes": 60,
      "subject": "Technical Interview - Senior Ruby Developer",
      "public_url": "https://wedotalent.cc/scheduling/ACCOUNT_UID/abc123xyz",
      "is_bookable": true,
      "slots": [
        { "id": 1, "start_time": "2026-03-10T09:00:00-03:00", "end_time": "2026-03-10T10:00:00-03:00", "is_available": true }
      ]
    }
  }
}
```

**Side effects:**
- If `candidate_id` is present and `channels` includes `"email"`, an email invite is sent automatically
- If `channels` includes `"whatsapp"` and the candidate has `mobile_phone`, a WhatsApp message with the scheduling link is sent

---

### Step 3: Candidate Books a Slot (PUBLIC — No Auth)

The candidate accesses the `public_url` and the frontend calls:

#### View Available Slots

```
GET /v1/:account_uid/scheduling/:token
```

**Auth:** Not required (public)  
**Response:**

```json
{
  "token": "abc123xyz",
  "status": "active",
  "subject": "Technical Interview - Senior Ruby Developer",
  "platform": "microsoft_teams",
  "platform_label": "Microsoft Teams",
  "duration_minutes": 60,
  "recruiter_name": "João Silva",
  "company_name": "WeDOTalent",
  "job_title": "Senior Ruby Developer",
  "candidate_name": "Maria Santos",
  "slots": [
    {
      "id": 1,
      "start_time": "2026-03-10T09:00:00-03:00",
      "end_time": "2026-03-10T10:00:00-03:00",
      "date": "2026-03-10",
      "day_of_week": "terça-feira",
      "start_hour": "09:00",
      "end_hour": "10:00"
    }
  ]
}
```

**Possible `status` values:** `active`, `booked`, `expired`, `cancelled`

#### Book a Slot

```
POST /v1/:account_uid/scheduling/:token/book
```

**Auth:** Not required (public)  
**Body:**

```json
{
  "slot_id": 1
}
```

**Response (200):**

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

**Side effects (automatic):**
- A `Meeting` is created with the chosen provider (Teams/Meet/Zoom/Presential)
- A `CalendarEvent` is created on the recruiter's calendar with the candidate as attendee
- Remaining slots are marked unavailable
- The link status changes to `booked`
- Email notification sent to both recruiter and candidate
- WhatsApp confirmation sent to candidate (if phone available)

---

## Direct Scheduling Flow (Recruiter Chooses Time)

### Create Calendar Event with Interview

```
POST /v1/users/calendar_events
```

**Auth:** Required  
**Body:**

```json
{
  "calendar_event": {
    "title": "Interview - Senior Ruby Developer - Maria Santos",
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
      { "email": "maria@example.com", "name": "Maria Santos", "required": true },
      { "email": "tech-lead@company.com", "name": "Tech Lead", "required": false }
    ]
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Event title |
| `start_time` | datetime | Yes | Start time (ISO 8601) |
| `end_time` | datetime | Yes | End time (ISO 8601) |
| `provider` | string | Yes | `microsoft` or `google` |
| `event_type` | string | No | `generic`, `interview`, `document_delivery`, `feedback`, `onboarding` |
| `importance` | string | No | `low`, `normal`, `high` |
| `timezone` | string | No | Default: `America/Sao_Paulo` |
| `description` | text | No | Event description/body |
| `location` | string | No | Physical address |
| `job_id` | integer | No | Related job |
| `apply_id` | integer | No | Related application |
| `sub_status` | string | No | `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show` |
| `reference_type` | string | No | `Candidate` for MeetingRelationship |
| `reference_id` | integer | No | Candidate ID for MeetingRelationship |
| `role` | string | No | Relationship role: `candidate`, `recruiter`, `interviewer`, `client`, `observer` |
| `is_all_day` | boolean | No | Default: false |
| `meeting_id` | integer | No | Link to existing meeting |
| `settings` | object | No | `{ "online_meeting": true }` creates a Teams/Meet meeting link |
| `attendees` | array | No | `[{ "email": "...", "name": "...", "required": true/false }]` |

**Response (201):** Full CalendarEvent with `join_url` if online meeting was created.

---

### Create Online Meeting Only (Without Calendar Event)

```
POST /v1/users/meetings
```

**Auth:** Required  
**Body:**

```json
{
  "meeting": {
    "subject": "Interview - Maria Santos",
    "start_time": "2026-03-10T14:00:00-03:00",
    "end_time": "2026-03-10T15:00:00-03:00",
    "provider": "microsoft_teams",
    "sub_status": "invite_sent",
    "job_id": 456,
    "apply_id": 789,
    "reference_type": "Candidate",
    "reference_id": 123,
    "role": "candidate",
    "settings": {
      "lobby_bypass_scope": true,
      "allow_chat": true,
      "allow_reactions": true,
      "record_automatically": false
    }
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|---|---|---|---|
| `subject` | string | Yes | Meeting title |
| `start_time` | datetime | Yes | Start time (ISO 8601) |
| `end_time` | datetime | Yes | End time (ISO 8601) |
| `provider` | string | Yes | `microsoft_teams`, `google_meet`, `zoom`, `presential` |
| `location` | string | No | Physical address |
| `sub_status` | string | No | `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show` |
| `job_id` | integer | No | Related job |
| `apply_id` | integer | No | Related application |
| `reference_type` | string | No | `Candidate` for MeetingRelationship |
| `reference_id` | integer | No | Candidate ID |
| `role` | string | No | `candidate`, `recruiter`, `interviewer` |
| `settings` | object | No | Meeting provider settings (lobby, chat, recording) |

**Response (201):** Meeting with `join_url` for the online meeting.

---

## Helper Endpoints

### Natural Language Schedule Suggestion

Parse natural language text into structured date/time suggestions using AI.

```
POST /v1/users/calendar_events/suggest_schedule
```

**Auth:** Required  
**Body:**

```json
{
  "text": "next tuesday at 2pm for 45 minutes",
  "timezone": "America/Sao_Paulo"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "is_primary": true,
        "label": "Terça-feira, 10 de Março",
        "day_of_week": "Tuesday",
        "date": "2026-03-10",
        "start_time": "2026-03-10T14:00:00-03:00",
        "end_time": "2026-03-10T14:45:00-03:00",
        "duration_minutes": 45,
        "human_readable": "Terça-feira, 10/03 às 14:00 - 14:45"
      }
    ]
  }
}
```

---

### Daily Agenda

```
GET /v1/users/calendar_events/daily_agenda
```

**Auth:** Required  
**Params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `kind` | string | `upcoming` | `upcoming` or `history` |
| `from` | date | today | Start date |
| `to` | date | +7 days | End date |
| `event_type` | string | - | Filter: `interview`, `generic`, `feedback`, etc. |
| `provider` | string | - | Filter: `microsoft`, `google` |
| `organizer_id` | integer | - | Filter by organizer user |
| `search` | string | - | Search in title |
| `timezone` | string | `America/Sao_Paulo` | Timezone for grouping |
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page (max 50) |

---

### Scheduling Settings

Configure the recruiter's scheduling preferences.

```
GET /v1/users/scheduling/settings
```
```
PATCH /v1/users/scheduling/settings
```

**Auth:** Required  
**Body (PATCH):**

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

| Field | Type | Default | Description |
|---|---|---|---|
| `timezone` | string | `America/Sao_Paulo` | Recruiter timezone |
| `work_hours_start` | time | `09:00` | Work day start |
| `work_hours_end` | time | `18:00` | Work day end |
| `default_duration_minutes` | integer | `60` | Default slot duration. Valid: 15, 30, 45, 60, 90, 120 |
| `buffer_minutes` | integer | `15` | Buffer between meetings |
| `lookahead_days` | integer | `14` | How many days ahead to show (1-60) |

---

## CRUD Operations

### Scheduling Links Management

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/users/scheduling/links` | Yes | List recruiter's scheduling links |
| `GET` | `/v1/users/scheduling/links/:id` | Yes | Show link details |
| `POST` | `/v1/users/scheduling/links` | Yes | Create scheduling link with slots |
| `PATCH` | `/v1/users/scheduling/links/:id` | Yes | Update active link |
| `DELETE` | `/v1/users/scheduling/links/:id` | Yes | Cancel link |

**List filters:** `?status=active`, `?job_id=123`, `?apply_id=456`

### Calendar Events Management

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/users/calendar_events` | Yes | List events (Searchkick) |
| `GET` | `/v1/users/calendar_events/:id` | Yes | Show event details |
| `POST` | `/v1/users/calendar_events` | Yes | Create event |
| `PATCH` | `/v1/users/calendar_events/:id` | Yes | Update event |
| `DELETE` | `/v1/users/calendar_events/:id` | Yes | Cancel event |
| `POST` | `/v1/users/calendar_events/:id/sync` | Yes | Sync event with provider |

### Meetings Management

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/users/meetings` | Yes | List meetings (Searchkick) |
| `GET` | `/v1/users/meetings/:id` | Yes | Show meeting details |
| `POST` | `/v1/users/meetings` | Yes | Create meeting |
| `PATCH` | `/v1/users/meetings/:id` | Yes | Update meeting |
| `DELETE` | `/v1/users/meetings/:id` | Yes | Soft-delete meeting |

---

## Routes Summary

### Authenticated Routes (require JWT)

| Route | Method | Controller |
|---|---|---|
| `/v1/users/calendar_events` | GET | CalendarEventsController#index |
| `/v1/users/calendar_events/:id` | GET | CalendarEventsController#show |
| `/v1/users/calendar_events` | POST | CalendarEventsController#create |
| `/v1/users/calendar_events/:id` | PATCH | CalendarEventsController#update |
| `/v1/users/calendar_events/:id` | DELETE | CalendarEventsController#destroy |
| `/v1/users/calendar_events/:id/sync` | POST | CalendarEventsController#sync |
| `/v1/users/calendar_events/suggest_schedule` | POST | CalendarEventsController#suggest_schedule |
| `/v1/users/calendar_events/daily_agenda` | GET | CalendarEventsController#daily_agenda |
| `/v1/users/meetings` | GET | MeetingsController#index |
| `/v1/users/meetings/:id` | GET | MeetingsController#show |
| `/v1/users/meetings` | POST | MeetingsController#create |
| `/v1/users/meetings/:id` | PATCH | MeetingsController#update |
| `/v1/users/meetings/:id` | DELETE | MeetingsController#destroy |
| `/v1/users/scheduling/settings` | GET | Scheduling::SettingsController#show |
| `/v1/users/scheduling/settings` | PATCH | Scheduling::SettingsController#update |
| `/v1/users/scheduling/availability` | GET | Scheduling::AvailabilityController#index |
| `/v1/users/scheduling/links` | GET | Scheduling::LinksController#index |
| `/v1/users/scheduling/links/:id` | GET | Scheduling::LinksController#show |
| `/v1/users/scheduling/links` | POST | Scheduling::LinksController#create |
| `/v1/users/scheduling/links/:id` | PATCH | Scheduling::LinksController#update |
| `/v1/users/scheduling/links/:id` | DELETE | Scheduling::LinksController#destroy |

### Public Routes (no auth — candidate-facing)

| Route | Method | Controller |
|---|---|---|
| `/v1/:account_uid/scheduling/:token` | GET | SchedulingController#show |
| `/v1/:account_uid/scheduling/:token/book` | POST | SchedulingController#book |

---

## Agent Decision Tree

```
Want to schedule an interview?
│
├─ Does the recruiter already know the exact date/time?
│  ├─ YES → Use Direct Flow
│  │  └─ POST /v1/users/calendar_events (with event_type: "interview", attendees, settings.online_meeting: true)
│  │
│  └─ NO → Use Self-Scheduling Flow
│     ├─ 1. GET /v1/users/scheduling/availability (check recruiter calendar)
│     ├─ 2. Select 3-5 available slots
│     ├─ 3. POST /v1/users/scheduling/links (with slots, candidate_id, channels)
│     └─ 4. Candidate picks a slot via public URL → booking auto-creates meeting + calendar event
│
├─ Need to parse a natural language time?
│  └─ POST /v1/users/calendar_events/suggest_schedule
│     Body: { "text": "amanhã às 14h por 45 minutos" }
│
├─ Need to check today's schedule?
│  └─ GET /v1/users/calendar_events/daily_agenda?kind=upcoming
│
└─ Need to update interview status?
   └─ PATCH /v1/users/calendar_events/:id
      Body: { "calendar_event": { "sub_status": "confirmed" } }
```

---

## Sub-status Lifecycle

```
invite_sent → scheduled → confirmed → completed
                                    → no_show
```

| Status | Meaning |
|---|---|
| `invite_sent` | Invite was sent, awaiting response |
| `scheduled` | Candidate confirmed the slot (booked) |
| `confirmed` | Both parties confirmed attendance |
| `completed` | Interview happened successfully |
| `no_show` | Candidate or interviewer did not attend |

---

## Notification Channels

When creating a scheduling link with `channels`:

| Channel | Trigger | Content |
|---|---|---|
| `email` | On link creation | Sends email with scheduling link to candidate |
| `whatsapp` | On link creation | Sends WhatsApp template "entrevista" + link button |
| `email` | On booking | Confirmation email to both recruiter and candidate |
| `whatsapp` | On booking | WhatsApp template "confirmacao_entrevista" with date/time/link |

---

## Supported Platforms

| Platform Value | Label | Creates Online Meeting? |
|---|---|---|
| `microsoft_teams` | Microsoft Teams | Yes |
| `teams` | Microsoft Teams | Yes |
| `google_meet` | Google Meet | Yes |
| `zoom` | Zoom | Yes |
| `presential` | Presencial | No (uses `location` field) |

---

## Important Notes for the Agent

1. Always check availability before offering slots — never suggest times when the recruiter is busy
2. Offer 3-5 slots across different days/times to maximize candidate flexibility
3. Set `channels: ["email", "whatsapp"]` to maximize delivery probability
4. Always include `candidate_id`, `job_id`, and `apply_id` for proper tracking
5. Use `interview_type` to categorize: `technical`, `behavioral`, `cultural_fit`, `online`, `presential`
6. Set `expires_at` to 3-5 days from now to create urgency
7. The `public_url` in the response is the link to send/share with the candidate
8. After booking, the system automatically creates the meeting and calendar event — no additional API calls needed
9. Use `suggest_schedule` to parse recruiter's natural language time preferences
10. Use `daily_agenda` with `event_type=interview` to check existing interviews before scheduling
