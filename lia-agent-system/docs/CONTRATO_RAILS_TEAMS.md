# Teams ↔ Rails Contract

> Maps which Postgres tables, Rails endpoints, and webhooks the Teams integration depends on.
> Updated: 2026-04-27 — post Wave 5–9 implementation.

---

## 1. Postgres Tables Used by Teams

All tables live in the FastAPI service's Postgres DB (not Rails). Rails has its own separate DB (`ats-api-copia`).

### `teams_conversations` (canonical)

Primary store for Teams conversation references (1:1 and group/channel).

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `conversation_id` | VARCHAR | Teams conversation ID (e.g. `19:xxx@thread.v2`) |
| `service_url` | VARCHAR | Bot Framework service URL for proactive messaging |
| `tenant_id` | VARCHAR | Azure AD tenant ID — used for multi-tenancy isolation |
| `channel_id` | VARCHAR | `msteams` |
| `user_id` | VARCHAR | `aad:<object-id>` for 1:1; `channel:<team-id>` for group (W9.1) |
| `user_name` | VARCHAR | Display name |
| `user_aad_object_id` | VARCHAR | AAD object ID (from OBO flow) |
| `conversation_reference` | JSONB | Full activity JSON for proactive re-send |
| `company_id` | UUID FK → companies | Set at write-time via user lookup |
| `last_message_at` | TIMESTAMP | Updated on each message |
| `created_at` | TIMESTAMP | |

**Indexes:** `(conversation_id)` unique, `(company_id, tenant_id)` composite for proactive broadcast.

**Used by:** `TeamsRepository.upsert_conversation()`, `TeamsProactivityEngine._get_channel_refs_for_company()`

---

### `users` (shared with main platform)

Teams uses this to resolve `company_id` from `user_aad_object_id` or Teams user_id.

| Column | Used for |
|---|---|
| `id` | FK in teams_conversations.user_id resolution |
| `company_id` | Injected into TeamsOrchestratorBridge for multi-tenancy |
| `email` | Matched against Azure AD email in SSO flow |
| `role` | Digest sends only to `recruiter`, `admin`, `manager` roles |
| `notification_preferences` | JSONB — `weekly_report_enabled` flag for digest opt-out |

---

### `job_vacancies` (read-only for digest)

`WeeklyDigestService` reads open vacancies count, candidates in screening, etc. to build the morning brief.

| Column | Used for |
|---|---|
| `company_id` | Filter by tenant |
| `status` | Filter `open` vacancies |
| `created_at`, `updated_at` | Period calculations |

---

### `vacancy_candidates` (read-only for digest + pipeline monitor)

| Column | Used for |
|---|---|
| `vacancy_id`, `candidate_id` | Join for pipeline state |
| `stage`, `status` | Pipeline position |
| `updated_at` | Inactive detection (7+ days) |

---

## 2. Rails Endpoints Consumed by Teams

**Teams does NOT call Rails endpoints directly.** The integration is:

```
Teams webhook → FastAPI Teams handler
                     ↓
               FastAPI LIA orchestrator
                     ↓
               Rails (ats-api-copia) via internal HTTP
               (existing recruiter/vacancy REST API)
```

The Teams integration is a **presentation layer** on top of the existing FastAPI orchestrator. Any Rails calls happen through the same service layer used by the web frontend, not through direct Teams integration code.

**Rails endpoints called indirectly (via orchestrator agents):**

| Rails Endpoint | Agent | Purpose |
|---|---|---|
| `GET /api/v1/job_vacancies` | VacancyManagerAgent | List vacancies for recruiter |
| `POST /api/v1/vacancy_candidates` | VacancyManagerAgent | Add candidate to vacancy |
| `GET /api/v1/candidates/:id` | RecruiterAssistantAgent | Candidate profile lookup |
| `POST /api/v1/hiring_stages` | RecruiterAssistantAgent | Move candidate to next stage |

---

## 3. Webhook Map

### Incoming (Teams → WeDOTalent FastAPI)

| Endpoint | Activity Type | Handler |
|---|---|---|
| `POST /api/v1/teams/webhook` | `message` | Text + attachment processing |
| `POST /api/v1/teams/webhook` | `conversationUpdate` | Bot added to 1:1 or group |
| `POST /api/v1/teams/webhook` | `invoke` (SSO) | OBO token exchange |

**Authentication:** Bot Framework JWT token validation (`MICROSOFT_APP_ID`).

### Outgoing (WeDOTalent FastAPI → Teams)

All outgoing calls go through `simple_teams_bot` (canonical) to:
`POST {service_url}/v3/conversations/{conversation_id}/activities`

| Trigger | Method | Content |
|---|---|---|
| Text response | `send_message()` | Plain text |
| Rich response | `send_adaptive_card()` | Adaptive Card JSON |
| Proactive digest | `TeamsProactivityEngine._send_card_to_ref()` | Adaptive Card |
| Group broadcast | `TeamsProactivityEngine.broadcast_to_channels()` | Adaptive Card |

---

## 4. Data Flow: CV Processing (PDF attachment)

```
Teams → webhook → teams.py (MIME dispatch: application/pdf)
                    ↓
              TeamsOrchestratorBridge.process_cv_attachment()
                    ↓
              Downloads PDF via httpx + bot token
                    ↓
              Calls FastAPI CV parsing service (existing)
                    ↓
              Returns structured candidate profile
                    ↓
              TeamsCardRenderer.render() → Adaptive Card
                    ↓
              simple_teams_bot.send_adaptive_card()
```

---

## 5. Multi-Tenancy Contract

The Teams integration is fully multi-tenant. Isolation is enforced at two levels:

1. **`tenant_id`** (Azure AD) — stored in `teams_conversations.tenant_id`. Used by `TeamsProactivityEngine` to filter channel refs for a specific tenant.

2. **`company_id`** (WeDOTalent) — resolved from `users.company_id` via the AAD object ID. Injected into every orchestrator call. Never trusted from the Teams payload.

**Key invariant:** `company_id` is ALWAYS resolved from DB (via user lookup), NEVER from the Teams activity payload.
