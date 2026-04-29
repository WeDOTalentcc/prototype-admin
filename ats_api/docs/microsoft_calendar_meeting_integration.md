# Microsoft Calendar & Meeting Integration

## Overview

The ATS integrates with **Microsoft Graph API** to provide:

- **OAuth 2.0 Authentication** — Connect Microsoft accounts via popup flow
- **Online Meetings** — Create/update/delete Microsoft Teams meetings
- **Calendar Events** — Full CRUD synced with Outlook Calendar
- **Email** — Send emails via Microsoft Graph (single & bulk)
- **Teams Messaging** — Send messages to chats & channels
- **Daily Agenda** — Aggregated view of calendar events
- **Schedule Suggestions** — AI-powered scheduling from natural language

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CONTROLLERS                                │
│                                                                     │
│  MicrosoftAuthsController     ← OAuth flow (login + integration)    │
│  MeetingsController           ← CRUD meetings (provider-agnostic)   │
│  CalendarEventsController     ← CRUD calendar events                │
│  Integrations::Microsoft::                                          │
│    ProfilesController         ← GET /me profile                     │
│    EmailsController           ← Send single email                   │
│    BulkEmailsController       ← Send bulk emails                    │
│    TeamsController             ← Send Teams messages                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                      SERVICE LAYER                                  │
│                                                                     │
│  MeetingService          ← Strategy dispatcher (Teams/Meet/Zoom)    │
│  CalendarService         ← Strategy dispatcher (Microsoft/Google)   │
│                                                                     │
│  Meetings::MicrosoftTeamsStrategy   ← Graph /me/onlineMeetings      │
│  Calendars::MicrosoftCalendarStrategy ← Graph /me/events            │
│                                                                     │
│  CalendarEvents::DailyAgendaService     ← Agenda grouping           │
│  CalendarEvents::ScheduleSuggestionService ← AI schedule parse      │
│                                                                     │
│  MicrosoftService::Api   ← HTTP client (Faraday, auto-refresh)      │
│  MicrosoftService::Auth  ← OAuth token exchange & refresh            │
│  MicrosoftService::Mailer ← Graph /me/sendMail                      │
│  MicrosoftService::Teams  ← Graph /chats & /teams messages          │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                         MODELS                                      │
│                                                                     │
│  Meeting                 ← providers: microsoft_teams, google_meet, │
│                             zoom, presential                        │
│  CalendarEvent           ← providers: microsoft, google             │
│  CalendarEventAttendee   ← attendees with response tracking         │
│  MeetingRelationship     ← polymorphic link to candidates/applies   │
│  User (ms_access_token, ms_refresh_token, ms_expires_at)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Authentication (OAuth 2.0)

### Flow

1. Frontend opens popup → `GET /v1/users/microsoft_graph_auth/url`
2. User consents on Microsoft login page
3. Microsoft redirects to `GET /v1/auth/microsoft_graph_auth/callback`
4. Backend exchanges code for tokens, stores on User record
5. Popup closes, frontend receives success signal

### Microsoft Graph Scopes

```
openid, profile, email, offline_access,
User.Read, Mail.Read, Mail.ReadWrite, Mail.Send,
MailboxSettings.Read, Calendars.ReadWrite,
OnlineMeetings.ReadWrite, Tasks.ReadWrite,
Chat.ReadWrite, Chat.Create
```

### Token Management

- Tokens stored on `User`: `ms_access_token`, `ms_refresh_token`, `ms_expires_at`
- `MicrosoftService::Api.ensure_user_token` auto-refreshes 5 minutes before expiration
- Retry with exponential backoff on transient errors (max 3 retries)
- If refresh token is expired/revoked → clears tokens, user must re-authenticate

### Environment Variables

| Variable | Description |
|---|---|
| `AZURE_APP_ID` | Azure App Registration Client ID |
| `AZURE_APP_SECRET` | Azure App Registration Client Secret |
| `APP_HOST` | Production domain for callback URL |
| `FRONT_URL` | Frontend URL for post-auth redirect |

---

## API Endpoints

### 1. Authentication

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/users/microsoft_graph_auth/url` | Get OAuth consent URL (authenticated user integration) |
| `GET` | `/v1/users/microsoft_graph_auth/login_url` | Get OAuth URL for direct Microsoft login |
| `GET` | `/v1/users/microsoft_graph_auth/status` | Check Microsoft connection status |
| `GET` | `/v1/auth/microsoft_graph_auth/callback` | OAuth callback (handles code exchange) |

#### `GET /v1/users/microsoft_graph_auth/status`

**Response:**
```json
{
  "connected": true,
  "status": "active",
  "expires_at": "2026-02-28T10:30:00Z",
  "auth_url": null
}
```

---

### 2. Meetings (Online & Presential)

Base: `/v1/users/meetings`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/users/meetings` | List meetings (searchable) |
| `GET` | `/v1/users/meetings/:id` | Show meeting details |
| `POST` | `/v1/users/meetings` | Create meeting |
| `PUT` | `/v1/users/meetings/:id` | Update meeting |
| `DELETE` | `/v1/users/meetings/:id` | Delete meeting (soft delete) |

#### `POST /v1/users/meetings` — Create Meeting

**Request Body:**
```json
{
  "meeting": {
    "subject": "Technical Interview - Senior Dev",
    "start_time": "2026-03-01T14:00:00-03:00",
    "end_time": "2026-03-01T15:00:00-03:00",
    "provider": "microsoft_teams",
    "location": "Online",
    "sub_status": "invite_sent",
    "job_id": 123,
    "apply_id": 456,
    "reference_type": "Candidate",
    "reference_id": 789,
    "role": "candidate",
    "settings": {
      "lobby_bypass_scope": "organization",
      "dial_in_bypass": false,
      "allow_chat": "enabled",
      "allow_reactions": true,
      "allowed_presenters": "everyone",
      "record_automatically": false,
      "allow_attendee_mic": true,
      "allow_attendee_camera": true
    }
  }
}
```

**Providers:** `microsoft_teams`, `google_meet`, `zoom`, `presential`

If `provider` is omitted, auto-detection runs:
1. Microsoft SSO enabled + user connected → `microsoft_teams`
2. Google SSO enabled + user connected → `google_meet`
3. Neither → `ProviderNotAvailable` error

**Sub-statuses:** `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show`

**Response (201 Created):**
```json
{
  "data": {
    "id": "1",
    "type": "meeting",
    "attributes": {
      "id": 1,
      "subject": "Technical Interview - Senior Dev",
      "provider": "microsoft_teams",
      "status": "upcoming",
      "sub_status": "invite_sent",
      "sub_status_text": "Convite Enviado",
      "join_url": "https://teams.microsoft.com/l/meetup-join/...",
      "location": "Online",
      "job_id": 123,
      "apply_id": 456,
      "start_time": "2026-03-01T14:00:00-03:00",
      "end_time": "2026-03-01T15:00:00-03:00",
      "settings": { ... },
      "organizer_name": "John Recruiter",
      "organizer_email": "john@company.com",
      "duration_minutes": 60,
      "is_active": true,
      "created_at": "2026-02-27T10:00:00Z",
      "updated_at": "2026-02-27T10:00:00Z"
    }
  }
}
```

**Error Responses:**
- `422 PROVIDER_NOT_AVAILABLE` — No provider connected for the user
- `422 MEETING_CREATION_FAILED` — Microsoft Graph API error

#### `PUT /v1/users/meetings/:id` — Update Meeting

```json
{
  "meeting": {
    "subject": "Updated Subject",
    "start_time": "2026-03-01T15:00:00-03:00",
    "end_time": "2026-03-01T16:00:00-03:00",
    "sub_status": "confirmed"
  }
}
```

Updates are synced to Microsoft Graph (updates the Teams meeting remotely).

---

### 3. Calendar Events

Base: `/v1/users/calendar_events`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/users/calendar_events` | List events (searchable) |
| `GET` | `/v1/users/calendar_events/:id` | Show event details |
| `POST` | `/v1/users/calendar_events` | Create event (syncs with Outlook) |
| `PUT` | `/v1/users/calendar_events/:id` | Update event |
| `DELETE` | `/v1/users/calendar_events/:id` | Cancel event |
| `POST` | `/v1/users/calendar_events/:id/sync` | Sync event from Microsoft Graph |
| `GET` | `/v1/users/calendar_events/daily_agenda` | Aggregated daily agenda |
| `POST` | `/v1/users/calendar_events/suggest_schedule` | AI schedule suggestion |

#### `POST /v1/users/calendar_events` — Create Calendar Event

**Request Body:**
```json
{
  "calendar_event": {
    "title": "Interview - Maria Silva",
    "start_time": "2026-03-01T14:00:00-03:00",
    "end_time": "2026-03-01T15:00:00-03:00",
    "provider": "microsoft",
    "description": "<p>Technical interview for Senior Developer position</p>",
    "location": "Meeting Room 3",
    "event_type": "interview",
    "importance": "high",
    "timezone": "America/Sao_Paulo",
    "is_all_day": false,
    "meeting_id": 1,
    "job_id": 123,
    "apply_id": 456,
    "sub_status": "invite_sent",
    "reference_type": "Candidate",
    "reference_id": 789,
    "role": "candidate",
    "settings": {
      "online_meeting": true
    },
    "attendees": [
      { "email": "maria@email.com", "name": "Maria Silva", "required": true },
      { "email": "tech-lead@company.com", "name": "Tech Lead", "required": true },
      { "email": "hr@company.com", "name": "HR Manager", "required": false }
    ]
  }
}
```

**Providers:** `microsoft`, `google` (auto-detected if omitted)

**Event Types:** `generic`, `interview`, `document_delivery`, `feedback`, `onboarding`

**Importance Levels:** `low`, `normal`, `high`

**Response (201 Created):**
```json
{
  "data": {
    "id": "1",
    "type": "calendar_event",
    "attributes": {
      "id": 1,
      "provider": "microsoft",
      "provider_text": "Microsoft",
      "external_id": "AAMkAGE...",
      "external_uid": "040000008...",
      "title": "Interview - Maria Silva",
      "description": "<p>Technical interview...</p>",
      "location": "Meeting Room 3",
      "event_type": "interview",
      "event_type_text": "Interview",
      "importance": "high",
      "start_time": "2026-03-01T14:00:00-03:00",
      "end_time": "2026-03-01T15:00:00-03:00",
      "timezone": "America/Sao_Paulo",
      "is_all_day": false,
      "is_cancelled": false,
      "is_deleted": false,
      "status": "upcoming",
      "sub_status": "invite_sent",
      "sub_status_text": "Convite Enviado",
      "meeting_id": 1,
      "job_id": 123,
      "apply_id": 456,
      "organizer_id": 10,
      "organizer_name": "John Recruiter",
      "organizer_email": "john@company.com",
      "duration_minutes": 60,
      "has_online_meeting": true,
      "join_url": "https://teams.microsoft.com/l/meetup-join/...",
      "attendees": [
        {
          "id": 1,
          "email": "maria@email.com",
          "name": "Maria Silva",
          "response_status": "not_responded",
          "is_organizer": false,
          "responded_at": null
        }
      ],
      "settings": { "online_meeting": true },
      "metadata": { ... },
      "created_at": "2026-02-27T10:00:00Z",
      "updated_at": "2026-02-27T10:00:00Z"
    }
  }
}
```

#### `POST /v1/users/calendar_events/:id/sync`

Re-fetches event details from Microsoft Graph and updates local record (title, cancellation status, metadata).

#### `GET /v1/users/calendar_events/daily_agenda`

**Query Params:**

| Param | Type | Description |
|---|---|---|
| `kind` | string | `upcoming` (default) or `history` |
| `search` | string | Search in title, description, location, attendee names/emails |
| `from` | datetime | Start of date range |
| `to` | datetime | End of date range |
| `event_type` | string | Filter by event type |
| `provider` | string | Filter by provider |
| `is_cancelled` | boolean | Filter cancelled events |
| `organizer_id` | integer | Filter by organizer |
| `page` | integer | Pagination page |
| `per_page` | integer | Items per page (max 50) |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-03-01",
      "events": [
        {
          "id": 1,
          "title": "Interview - Maria Silva",
          "start_time": "14:00",
          "end_time": "15:00",
          "event_type": "interview",
          "provider": "microsoft",
          "candidate": { "id": 789, "name": "Maria Silva" },
          "job": { "id": 123, "title": "Senior Developer" }
        }
      ]
    }
  ],
  "meta": { "total": 5, "page": 1, "per_page": 20 }
}
```

#### `POST /v1/users/calendar_events/suggest_schedule`

Uses Gemini AI to parse natural language into structured schedule suggestions.

**Request Body:**
```json
{
  "text": "Schedule an interview next Tuesday at 2pm for 1 hour",
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
        "label": "Next Tuesday",
        "day_of_week": "Tuesday",
        "day_of_week_pt": "Terça-feira",
        "date": "2026-03-03",
        "start_time": "2026-03-03T14:00:00-03:00",
        "end_time": "2026-03-03T15:00:00-03:00",
        "duration_minutes": 60,
        "human_readable": "Tuesday, March 3rd at 2:00 PM"
      }
    ]
  }
}
```

---

### 4. Microsoft Integrations

Base: `/v1/users/integrations/microsoft`

All require `MicrosoftLinked` — returns `400` if user has no Microsoft tokens.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/users/integrations/microsoft/me` | Get Microsoft profile + photo |
| `POST` | `/v1/users/integrations/microsoft/email` | Send single email |
| `POST` | `/v1/users/integrations/microsoft/email/bulk` | Send bulk emails with pacing |
| `POST` | `/v1/users/integrations/microsoft/teams/message` | Send Teams message |

#### `GET /v1/users/integrations/microsoft/me`

**Response:**
```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "display_name": "John Recruiter",
  "given_name": "John",
  "surname": "Recruiter",
  "user_principal_name": "john@company.com",
  "mail": "john@company.com",
  "photo": {
    "content_type": "image/jpeg",
    "data_url": "data:image/jpeg;base64,/9j/4AAQ..."
  }
}
```

#### `POST /v1/users/integrations/microsoft/email`

**Request Body:**
```json
{
  "email": {
    "subject": "Interview Invitation",
    "html": "<p>Dear Maria, you've been invited to an interview...</p>",
    "to": "maria@email.com",
    "recipients": ["maria@email.com", "backup@email.com"],
    "reply_to": "hr@company.com",
    "save_to_sent": true,
    "scheduled_for": "2026-03-01T09:00:00-03:00",
    "name": "Interview Invitation Email"
  }
}
```

**Response (202 Accepted):**
```json
{
  "ok": true,
  "dispatch_id": 1,
  "recipients_count": 2
}
```

Emails are queued via `MsGraphEmailWorker` (Sidekiq) and sent through Microsoft Graph `/me/sendMail`.

#### `POST /v1/users/integrations/microsoft/email/bulk`

**Request Body:**
```json
{
  "email": {
    "subject": "Bulk Interview Invitations",
    "html": "<p>Dear candidate...</p>",
    "recipients": ["candidate1@email.com", "candidate2@email.com", "candidate3@email.com"],
    "start_at": "2026-03-01T09:00:00-03:00",
    "delay_seconds": 180,
    "save_to_sent": true,
    "reply_to": "hr@company.com",
    "name": "Bulk Invitation Campaign"
  }
}
```

- Default delay between emails: **180 seconds** (3 minutes)
- Each email is scheduled with `MsGraphEmailWorker.perform_in(offset)`

**Response (202 Accepted):**
```json
{
  "ok": true,
  "dispatch_id": 1,
  "messages_count": 3,
  "scheduled_start_at": "2026-03-01T09:00:00-03:00",
  "delay_seconds": 180
}
```

#### `POST /v1/users/integrations/microsoft/teams/message`

**Request Body — Direct Message:**
```json
{
  "to": "colleague@company.com",
  "content": "<p>The candidate has been approved!</p>",
  "content_type": "html"
}
```

**Request Body — Channel Message:**
```json
{
  "team_name": "Recruiting",
  "channel_name": "General",
  "content": "New candidate approved for Senior Dev position",
  "content_type": "text"
}
```

**Request Body — By IDs:**
```json
{
  "chat_id": "19:meeting_abc123...",
  "content": "<p>Message content</p>"
}
```
or
```json
{
  "team_id": "team-guid",
  "channel_id": "channel-guid",
  "content": "Message content"
}
```

**Response (202 Accepted):**
```json
{
  "ok": true,
  "id": "1234567890"
}
```

---

## Models

### Meeting

| Field | Type | Description |
|---|---|---|
| `id` | integer | Primary key |
| `account_id` | integer | Tenant |
| `organizer_id` | integer | FK → User |
| `provider` | string | `microsoft_teams`, `google_meet`, `zoom`, `presential` |
| `external_id` | string | Microsoft Graph meeting ID |
| `join_url` | string | Teams join URL |
| `subject` | string | Meeting subject |
| `start_time` | datetime | Start |
| `end_time` | datetime | End |
| `location` | string | Physical location (optional) |
| `sub_status` | string | `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show` |
| `job_id` | integer | FK → Job (optional) |
| `apply_id` | integer | FK → Apply (optional) |
| `settings` | jsonb | Teams settings (lobby, chat, recording, etc.) |
| `metadata` | jsonb | Raw Microsoft Graph response |
| `is_deleted` | boolean | Soft delete flag |

### CalendarEvent

| Field | Type | Description |
|---|---|---|
| `id` | integer | Primary key |
| `account_id` | integer | Tenant |
| `organizer_id` | integer | FK → User |
| `provider` | string | `microsoft`, `google` |
| `external_id` | string | Microsoft Graph event ID |
| `external_uid` | string | iCalUId |
| `title` | string | Event title |
| `description` | text | HTML body |
| `location` | string | Location |
| `event_type` | string | `generic`, `interview`, `document_delivery`, `feedback`, `onboarding` |
| `importance` | string | `low`, `normal`, `high` |
| `start_time` | datetime | Start |
| `end_time` | datetime | End |
| `timezone` | string | IANA timezone |
| `is_all_day` | boolean | All day event |
| `is_cancelled` | boolean | Cancelled flag |
| `is_deleted` | boolean | Soft delete flag |
| `sub_status` | string | `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show` |
| `meeting_id` | integer | FK → Meeting (optional, links to online meeting) |
| `job_id` | integer | FK → Job (optional) |
| `apply_id` | integer | FK → Apply (optional) |
| `settings` | jsonb | Custom settings |
| `metadata` | jsonb | Raw Microsoft Graph event response |

### CalendarEventAttendee

| Field | Type | Description |
|---|---|---|
| `id` | integer | Primary key |
| `calendar_event_id` | integer | FK → CalendarEvent |
| `user_id` | integer | FK → User (auto-linked by email) |
| `email` | string | Attendee email |
| `name` | string | Attendee name |
| `is_organizer` | boolean | Whether this is the organizer |
| `response_status` | string | `not_responded`, `accepted`, `declined`, `tentative`, `organizer` |
| `responded_at` | datetime | When they responded |

### MeetingRelationship

| Field | Type | Description |
|---|---|---|
| `id` | integer | Primary key |
| `account_id` | integer | Tenant |
| `reference_type` | string | Polymorphic type (e.g., `Candidate`) |
| `reference_id` | integer | Polymorphic ID |
| `apply_id` | integer | FK → Apply (optional) |
| `meeting_id` | integer | FK → Meeting (optional) |
| `calendar_event_id` | integer | FK → CalendarEvent (optional) |
| `role` | string | `candidate`, `recruiter`, `interviewer`, `client`, `observer` |

---

## Strategy Pattern

Both `MeetingService` and `CalendarService` use the Strategy Pattern to support multiple providers:

### Meeting Strategies

```
MeetingService.create(user:, subject:, ...)
  ├── determine_provider(user)
  │     ├── microsoft_sso + user.microsoft_connected? → MicrosoftTeamsStrategy
  │     ├── google_sso + user.google_connected?       → GoogleMeetStrategy
  │     └── explicit provider                          → direct mapping
  │
  ├── Meetings::MicrosoftTeamsStrategy  → POST /me/onlineMeetings
  ├── Meetings::GoogleMeetStrategy      → Google Calendar API
  ├── Meetings::PresentialStrategy      → Local record only
  └── Meetings::ZoomStrategy            → Zoom API
```

### Calendar Strategies

```
CalendarService.create(user:, title:, ...)
  ├── detect_strategy(user)
  │     ├── microsoft_sso + user.microsoft_connected? → MicrosoftCalendarStrategy
  │     └── google_sso + user.google_connected?       → GoogleCalendarStrategy
  │
  ├── Calendars::MicrosoftCalendarStrategy  → POST /me/events
  └── Calendars::GoogleCalendarStrategy     → Google Calendar API
```

---

## Microsoft Graph API Endpoints Used

| Graph Endpoint | Method | Usage |
|---|---|---|
| `/me` | GET | Get user profile |
| `/me/photo/$value` | GET | Get user photo |
| `/me/sendMail` | POST | Send email |
| `/me/onlineMeetings` | POST | Create Teams meeting |
| `/me/onlineMeetings/:id` | GET/PATCH/DELETE | Manage Teams meeting |
| `/me/events` | GET/POST | List/create calendar events |
| `/me/events/:id` | GET/PATCH/DELETE | Manage calendar event |
| `/me/calendarView` | GET | Get free/busy schedule |
| `/me/joinedTeams` | GET | List Teams |
| `/teams/:id/channels` | GET | List channels |
| `/chats` | POST | Create 1:1 chat |
| `/chats/:id/messages` | POST | Send chat message |
| `/teams/:id/channels/:id/messages` | POST | Send channel message |

---

## MicrosoftLinked Concern

Controllers under `Integrations::Microsoft::*` include the `MicrosoftLinked` concern which:

- Runs `before_action :require_microsoft_linked`
- Returns `400 Bad Request` if user has no `ms_access_token` or `ms_refresh_token`
- Ensures the user has connected their Microsoft account before making Graph API calls

---

## Token Auto-Refresh Flow

```
Request → MicrosoftService::Api.get/post/patch/delete
  └── ensure_user_token(user)
        ├── Token valid? → proceed
        └── Token expired or within 5 min of expiry?
              └── refresh_expires_at(user)
                    ├── POST /oauth2/v2.0/token (grant_type=refresh_token)
                    ├── Success → update user tokens → proceed
                    └── AADSTS700082 / invalid_grant?
                          ├── Clear all tokens
                          └── Raise "User needs to re-authenticate"
```

---

## Typical Usage Flows

### 1. Schedule an Interview

```
1. POST /v1/users/meetings          → Creates Teams meeting (join_url)
2. POST /v1/users/calendar_events   → Creates Outlook event with attendees
   (meeting_id links to step 1)
3. MeetingRelationship created       → Links candidate to both
4. Candidate receives Outlook invite with Teams link
```

### 2. Send Interview Invitation Email

```
1. POST /v1/users/integrations/microsoft/email
   (subject, html body, recipient = candidate email)
2. MsGraphEmailWorker queued (Sidekiq)
3. Worker calls MicrosoftService::Mailer.send_to_address
4. Graph /me/sendMail sends from user's Outlook
```

### 3. Notify Team via Teams

```
1. POST /v1/users/integrations/microsoft/teams/message
   (team_name: "Recruiting", channel_name: "General", content: "Candidate approved!")
2. MicrosoftService::Teams resolves team/channel IDs
3. POST /teams/:id/channels/:id/messages
```

### 4. AI Schedule Suggestion

```
1. POST /v1/users/calendar_events/suggest_schedule
   (text: "entrevista sexta às 14h por 1 hora")
2. ScheduleSuggestionService → Gemini AI parses text
3. Returns structured suggestions with dates/times
4. Frontend uses suggestion to pre-fill calendar event form
```
