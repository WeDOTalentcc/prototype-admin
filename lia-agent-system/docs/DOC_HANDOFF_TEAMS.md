# Teams Integration — Developer Handoff

> Status: Production-ready. All waves W5–W9 completed 2026-04-27 on branch `feat/orch-migration-sprint-I`.

---

## 1. Environment Variables (15 catalogadas)

### Required — Bot Framework (message receive + token validation)

| Variable | Description | Example |
|---|---|---|
| `MICROSOFT_APP_ID` | Azure AD app registration client ID (GUID) | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `MICROSOFT_APP_PASSWORD` | Bot Framework client secret (from Azure portal) | `~abc123...` |
| `TEAMS_WEBHOOK_SECRET` | HMAC secret for webhook signature validation (32+ chars) | `python -c "import secrets; print(secrets.token_hex(32))"` |

### Required — SSO Tab (OBO flow)

| Variable | Description | Notes |
|---|---|---|
| `AZURE_CLIENT_ID` | Azure AD app registration client ID for SSO | Same app or different from bot |
| `AZURE_TENANT_ID` | Azure AD directory (tenant) ID | Use `common` for multi-tenant |

### Required — Calendar Integration (interview scheduling)

| Variable | Description |
|---|---|
| `AZURE_CLIENT_SECRET` | Service account secret for Calendar API |
| `MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI` | Must match redirect URI in Azure portal |
| `MICROSOFT_CALENDAR_DEFAULT_TIMEZONE` | Default: `America/Sao_Paulo` |

### Optional — Manifest + Proactive

| Variable | Description |
|---|---|
| `TEAMS_APP_ID` | UUID for the Teams manifest app (auto-generated if not set) |
| `TEAMS_BOT_APP_ID` | Alias for `MICROSOFT_APP_ID` used in manifest generator |
| `TEAMS_APP_TENANT_ID` | Separate tenant ID for bot registration (if differs from SSO) |
| `TEAMS_WEBHOOK_URL` | Outgoing webhook URL (if Teams calls a separate endpoint) |
| `ENABLE_MICROSOFT_GRAPH` | Default: `true`. Set `false` to disable Graph integrations. |

### Service config

| Variable | Description |
|---|---|
| `PLATFORM_DOMAIN` | Used in SSO resource URI: `api://{PLATFORM_DOMAIN}/{AZURE_CLIENT_ID}` |
| `APP_ENV` | `production` enforces TEAMS_WEBHOOK_SECRET validation |

---

## 2. Azure AD App Registration — Required Steps

### 2.1 Bot Framework Registration

1. Go to Azure Portal → App Registrations → New Registration
2. Name: `WeDOTalent LIA Bot`
3. Supported account types: "Accounts in any organizational directory" (multi-tenant)
4. No redirect URI needed for bot (Bot Framework handles auth)
5. After creation:
   - Copy **Application (client) ID** → `MICROSOFT_APP_ID`
   - Certificates & Secrets → New client secret → copy **Value** → `MICROSOFT_APP_PASSWORD`
6. Register the bot in Azure Bot Services, pointing to: `https://{platform-domain}/api/v1/teams/webhook`

### 2.2 SSO App Registration (Tab auth)

1. New Registration (can be same app or separate)
2. Redirect URIs → Add: `https://{platform-domain}/api/v1/teams/auth/callback`
3. Expose an API:
   - Application ID URI: `api://{platform-domain}/{AZURE_CLIENT_ID}`
   - Add scope: `access_as_user` (Admin + User consent)
   - Authorized client applications: add Teams client IDs (`1fec8e78-bce4-4aaf-ab1b-5451cc387264` and `5e3ce6c0-2b1f-4285-8d4b-75ee78787346`)
4. API Permissions: `User.Read`, `openid`, `profile`, `email`
5. Copy client ID → `AZURE_CLIENT_ID`; copy tenant ID → `AZURE_TENANT_ID`

### 2.3 Calendar Permissions (if using interview scheduling)

1. On the SSO app (or a dedicated daemon app):
2. API Permissions → Add `Calendars.ReadWrite` (Delegated)
3. Add `offline_access` (for refresh tokens)
4. Create a new client secret → `AZURE_CLIENT_SECRET`
5. Set `MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI` in Azure portal Redirect URIs

---

## 3. Manifest Deployment

### Quick deploy (sideloading)

```bash
# 1. Get manifest ZIP
GET /api/v1/teams/manifest-zip

# 2. In Teams Admin Center (or Teams Desktop):
#    Apps → Manage Apps → Upload a custom app → upload the ZIP

# Or via Teams app store (for org-wide):
#    Teams Admin Center → Teams apps → Manage apps → Upload
```

### Manifest endpoint (inspect before deploy)

```bash
GET /api/v1/teams/manifest
# Returns JSON manifest. Verify botId, validDomains, webApplicationInfo.
```

### Required: Tab URLs must be whitelisted

In `validDomains` in manifest, add your `PLATFORM_DOMAIN`. Also ensure the domain is registered in Azure Bot Service "Messaging endpoint" field.

---

## 4. Architecture Overview

```
Teams User
    │ sends message / attachment
    ▼
Bot Framework Service (Microsoft hosted)
    │ POST /api/v1/teams/webhook
    ▼
teams.py webhook handler
    │ validates token (MICROSOFT_APP_ID)
    │ routes by activity.type:
    │  • "message" → TeamsOrchestratorBridge.process_message()
    │  • "conversationUpdate" (bot added to group) → _store_channel_conversation_reference()
    │  • attachment dispatch (W9.3+W9.2):
    │     PDF → process_cv_attachment()
    │     image/* → process_image_attachment() [Gemini Vision]
    │     audio/video/* → process_voice_attachment() [Gemini STT]
    │     other → process_general_document()
    ▼
TeamsOrchestratorBridge
    │ resolves company_id from TeamsConversation DB record
    │ W7.2: PromptInjectionGuard (blocks injection attempts)
    │ W7.3: LGPD consent gate (WhatsApp screening only)
    ▼
LIA Orchestrator (MainOrchestrator)
    │ CascadedRouter: memory → redis → vector → fast → LLM → autonomous
    ▼
Domain Agent (recruiter_assistant, vacancy_manager, etc.)
    ▼
Response → simple_teams_bot.send_message() / send_adaptive_card()
    ▼
Teams User receives response
```

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `403 Forbidden` on POST /webhook | Token validation failed | Check `MICROSOFT_APP_ID` matches the bot registration |
| `403 Teams Bot not configured` | `MICROSOFT_APP_ID` or `MICROSOFT_APP_PASSWORD` not set | Add to env vars |
| Webhook returns 200 but no bot response | `company_id` resolution failed | Ensure user has run `/agendar` or chatted once to populate TeamsConversation |
| SSO Tab shows "Error getting token" | OBO exchange failed | Check `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`; verify scope `access_as_user` is exposed |
| Calendar scheduling fails | Graph permissions | Ensure `Calendars.ReadWrite` delegated permission + user has consented |
| Daily digest not sending | Cron not running | Check AutomationScheduler is started; verify `daily_platform_digest` job in scheduler |
| Audio attachment returns "not available" | Old placeholder | Ensure W9.2 commit is deployed (`process_voice_attachment` in bridge) |
| Image attachment fails | Gemini Vision error | Check `AI_INTEGRATIONS_GEMINI_API_KEY` is set; graceful fallback returns size message |

---

## 6. Canonical Service: simple_teams_bot

The canonical Teams bot instance is `simple_teams_bot` in:
`app/domains/communication/services/teams_simple.py`

**Always use this for:**
- `send_message(service_url, conversation_id, text)`
- `send_adaptive_card(service_url, conversation_id, card_payload)`
- `get_access_token()` (for downloading attachments)

**Deprecated paths (do not use):**
- `app/domains/communication/services/teams_bot.py` — legacy
- `app/domains/communication/services/teams_service.py` — legacy
- `libs/messaging/lia_messaging/teams.py` — legacy

---

## 7. Running the smoke tests

```bash
# Unit + integration (always safe)
pytest tests/integration/test_teams_*.py --no-cov -v

# E2E smoke (needs live Teams environment)
export TEAMS_SMOKE_TEST=1
export PLATFORM_BASE_URL=https://staging.wedotalent.cc
export TEAMS_SMOKE_CONVERSATION_ID=<real-conv-id>
pytest tests/smoke/test_teams_e2e_smoke.py -v -s
```
