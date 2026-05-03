# Configuration Reference — LIA Agent System

Generated: 2026-05-02

## Feature Flags — Database-Backed (FeatureFlagService)

All flags are stored in the `feature_flags` table (Postgres, per-company scoped or global).
API: `GET/POST /api/v1/flags/{flag_key}` (requires admin role).
Implementation: `app/shared/governance/feature_flag_service.py`

### Default Flags (DEFAULT_FLAGS)

| Flag Key | Category | Default | Description | Impact if enabled |
|----------|----------|---------|-------------|-------------------|
| `learning_hub_enabled` | learning | `True` | Unified learning hub functionality | Enables learning data aggregation across job closures |
| `outcome_learning_enabled` | learning | `True` | Outcome-based learning when jobs close | LIA learns from hire/reject outcomes per job |
| `stage_feedback_enabled` | learning | `True` | Stage-by-stage feedback collection | Feedback collected at each pipeline stage transition |
| `skills_deduplication_enabled` | wizard | `True` | Skills deduplication between wizard stages | Prevents duplicate skill entries in job descriptions |
| `analytics_dashboard_enabled` | analytics | `True` | Learning analytics dashboard | Shows analytics tab in learning hub UI |
| `ai_suggestions_enhanced` | ai | `True` | Enhanced AI suggestions with learning context | LIA uses historical company data for suggestions |
| `empty_field_notifications` | wizard | `True` | Empty field notifications in wizard | Wizard prompts user to fill required empty fields |
| `field_toggles_enabled` | wizard | `True` | LIA field toggles system | Enables per-field LIA assistance toggle in UI |
| `ENABLE_AUTO_SCREENING` | automation | `False` | Automatic candidate screening | LIA auto-screens candidates without recruiter trigger |
| `ENABLE_AUTO_SCHEDULING` | automation | `False` | Automatic interview scheduling | LIA auto-schedules interviews when candidate advances |
| `ENABLE_AUTO_STAGE_ADVANCE` | automation | `False` | Automatic pipeline stage advancement | LIA moves candidates to next stage automatically |
| `CREW_DELEGATION_ENABLED` | agents | `True` | CrewAI-style multi-agent delegation on AgentBus | Enables agent-to-agent task delegation via AgentBus |

### Environment Variable Flags

| Variable | Default | Description | Impact if enabled |
|----------|---------|-------------|-------------------|
| `LIA_V2_USE_PLAN_SERVICE` | `False` | Use new PlanService for orchestration (Sprint III-B rollout) | Routes orchestration through PlanService instead of legacy flow |

**Rollout plan for `LIA_V2_USE_PLAN_SERVICE`:** Canary at 5% → 25% → 100%. See `docs/migrations/SPRINT_III_E_CANARY_PLAN.md`.

### Governance / Automation Flags (set at company onboarding via policy_sync_service)

Controlled via `POST /api/v1/companies/{company_id}/policy` payload `feature_flags` key.
Synced by `app/shared/policy_sync_service.py::_sync_feature_flags`.

---

## Other Runtime Configuration

| Variable | Description |
|----------|-------------|
| `SENIORITY_RESOLVER_ENABLED` | Boolean, enables ML-based seniority inference (see `app/domains/cv_screening/services/seniority_resolver.py`) |

---

## Wizard Feature Gate

Location: `app/domains/job_creation/feature_flag.py`
Function: `is_wizard_enabled(company_id) -> bool`
Used to gate access to the Job Creation Wizard per company.

---

## How to Set a Flag via API

```bash
# Enable auto-screening for a specific company
POST /api/v1/flags/ENABLE_AUTO_SCREENING
{
  "company_id": "<uuid>",
  "is_enabled": true,
  "reason": "Approved by admin on 2026-05-02"
}
```

Requires `Authorization: Bearer <admin-token>`.

---

## Cache TTL Reference (UC-P3-07)

### Embedding Cache

| Layer | TTL | Location |
|-------|-----|----------|
| Response cache (per domain) | 60s – 300s | `app/orchestrator/main_orchestrator._CACHE_TTL_BY_DOMAIN` |
| Semantic cache (exact match) | 300s | `app/orchestrator/semantic_cache.py` |
| Extraction cache | 300s, max 200 entries | `app/orchestrator/` |
| AI-architecture calibration cache | 24h (86400s) | Documented in `docs/ai-architecture-audit.md` |
| Redis sessions | 24h (dump.rdb) | `docs/DISASTER_RECOVERY.md` |

Note: There is **no** 30-day embedding cache TTL in the codebase. All embedding and
response caches use short TTLs (seconds to 24h). The 30-day figure in earlier drafts
was erroneous — the actual TTLs are listed above.

---

## PII Filter Reference (UC-P3-12)

Two PII filter modules exist with distinct responsibilities:

### `app/shared/pii_masking.py`
- **Use when**: sanitizing log messages, exception text, or LLM prompt strings
- **Fields**: CPF, email, phone (BR), RG, CNPJ, graduation year, age, address (regex); PERSON/LOCATION/etc (Presidio NER, opt-in)
- **Mode**: inline synchronous + Python logging middleware (`PIIMaskingFilter`)
- **Key functions**: `mask_pii()`, `strip_pii_for_llm_prompt()`, `install_global_pii_masking()`
- **Env vars**: `LLM_PROMPT_PII_STRIPPING_ENABLED` (default true), `LLM_PROMPT_PRESIDIO_ENABLED` (default false)

### `app/domains/ats_integration/services/ats_clients/ats_pii_filter.py`
- **Use when**: filtering outbound payloads to external ATS (Gupy, Pandape) or sanitizing inbound ATS webhook text
- **Fields**: defined in `lgpd_field_registry.OUTBOUND_SENSITIVE_FIELDS` (social IDs, health, religion, salary, address)
- **Mode**: synchronous dict→dict (filter_outbound), async with consent check (filter_sensitive_outbound), synchronous text (filter_inbound_text)
- **Consent**: checks `ats_sharing` granular consent (D5) via GranularConsentService

---

## SSE Streaming Behavior (UC-P3-06)

Endpoint: `POST /api/v1/chat/{session_id}/stream`
File: `app/api/v1/agent_chat_sse.py`

| Aspect | Behavior |
|--------|----------|
| Token delivery | Token-by-token (one SSE event per token chunk) |
| Event types | `thinking`, `token`, `token_done`, `message`, `panel_update`, `error` |
| Keepalive | Empty `: keepalive` comment every 30s of silence |
| Reconnection | Last-Event-ID accepted; server replay not yet implemented |
| Auth | `Authorization: Bearer <token>` header required |
| Timeout | `LLM_TIMEOUT_SECONDS` env var |
| Configurable | `LIA_WS_TOKEN_STREAMING` controls token streaming on WS transport (sibling) |

Frontend must listen for `"token"` events for incremental rendering and `"message"` event for final assembled response with actions/navigation.