# ADR-031 — Canonical Domain Architecture: Structure, Agent Studio Registration & Governance

**Status:** ACCEPTED  
**Date:** 2026-06-13  
**Authors:** Paulo Moraes (WeDOTalent)  
**Supersedes:** AI_LAYER_TREE.md (descriptive), IMPLEMENTATION_ROADMAP.md (partial)  
**Enforced by:** `tests/contract/test_domain_structure_conformance.py` (245 passed, CI blocking)

---

## 1. Context

The `lia-agent-system` grew organically to 35 domain directories with no enforced structure. An architectural audit in June 2026 identified:

- **No canonical 4-file contract** for agentic domains — some had `domain.py`, many didn't, none had conformance tests.
- **3 separate Python dicts** for Agent Studio tool registration (`PLATFORM_TOOLS_REGISTRY`, `HITL_REQUIRED_TOOLS`, `domain_tool_loaders`) maintained inline in `custom_agent_runtime.py`.
- **4 new domains** (interview_intelligence, talent_intelligence, workforce, automation) wired to Agent Studio loaders but with no registered conformance.
- **~30 repository stubs** scattered at domain top-level instead of `repositories/`.
- **Ghost actions** — `DomainAction` declarations with no handler.

This ADR documents the decisions made to address those gaps, the canonical pattern that now applies, and the accepted exceptions + deferred items.

---

## 2. Domain Inventory (current state — 2026-06-13)

**Total domains: 35**

### 2.1 Registered Agentic Domains (22)

These domains participate in the intent-routing system and Agent Studio. All must satisfy the canonical contract (§3).

| Domain | caps.yaml | agents/ | actions.py | Notes |
|---|---|---|---|---|
| agent_studio | ✅ | — | ✅ | Orchestration hub; top-level exception files documented in §5.1 |
| analytics | ✅ | ✅ | ✅ | |
| ats_integration | ✅ | ✅ | ✅ | |
| automation | ✅ | ✅ | ✅ | |
| candidate_self_service | ✅ | ✅ | — | Actions inline in domain.py (§5.3) |
| communication | ✅ | ✅ | ✅ | |
| company_settings | ✅ | ✅ | — | Actions inline in domain.py (§5.3) |
| cv_screening | ✅ | ✅ | ✅ | |
| digital_twin | ✅ | — | ✅ | |
| hiring_policy | ✅ | ✅ | — | Actions inline in domain.py (§5.3) |
| interview_intelligence | ✅ | — | ✅ | tools/ instead of agents/ (§5.4) |
| interview_scheduling | ✅ | ✅ | ✅ | |
| job_creation | — | — | — | LangGraph wizard exception (§5.2) |
| job_management | ✅ | ✅ | ✅ | |
| offer | ✅ | ✅ | — | Actions inline in domain.py (§5.3) |
| pipeline | ✅ | ✅ | — | Actions inline in domain.py (§5.3) |
| recruiter_assistant | ✅ | ✅ | ✅ | |
| recruitment_campaign | ✅ | — | ✅ | |
| sourcing | ✅ | ✅ | ✅ | |
| talent_intelligence | ✅ | — | ✅ | tools/ instead of agents/ (§5.4) |
| talent_pool | ✅ | ✅ | ✅ | |
| workforce | ✅ | ✅ | ✅ | |

### 2.2 Service Domains (13)

Pure service layer — no intent routing, no Agent Studio participation. Only `services/`, `repositories/`, `schemas/`.

`ai`, `billing`, `candidates`, `company`, `compliance`, `consent`, `credits`, `integrations_hub`, `lgpd`, `persona`, `policy`, `recruitment`, `voice`

---

## 3. Canonical Domain Contract (Registered Agentic Domains)

Every domain in `_REGISTERED_DOMAINS` MUST have:

```
app/domains/<domain>/
├── __init__.py              # exports Domain class; __domain_type__ recommended (§6.1)
├── domain.py                # registers via @register_domain; inherits ComplianceDomainPrompt
├── actions.py               # DomainAction list (OR inline in domain.py — §5.3)
├── config/
│   └── capabilities.yaml    # intent_keywords → action mapping (§3.2)
└── agents/ OR tools/        # tool registry (agents/ canonical; tools/ accepted §5.4)
```

### 3.1 ComplianceDomainPrompt (mandatory)

All `domain.py` files inherit `ComplianceDomainPrompt` from `app.domains.compliance_base`. This enforces:
- LGPD/fairness/anti-bias instructions injected into every system prompt
- Multi-tenancy `company_id` validation
- Audit trail via `AuditService`

**Rationale:** compliance cannot be opt-in. Inheriting from the wrong base silently removes all guardrails. Mandatory inheritance + conformance test make it structural.

### 3.2 capabilities.yaml (intent routing)

Every registered domain (except `job_creation` — §5.2) MUST have `config/capabilities.yaml` with an `intent_keywords` dict mapping PT-BR/EN phrases → action names. Used by `KeywordIntentMatcher` for lightweight intent routing before LLM dispatch.

```yaml
domain: <domain_id>
intent_keywords:
  "frase em português": action_name
  "english phrase": action_name
```

### 3.3 @register_domain decorator

`domain.py` MUST use `@register_domain` from `app.domains.registry`. This auto-registers the domain for intent routing and Agent Studio discovery. Without it, the domain is invisible to the system.

---

## 4. Agent Studio Registration — platform_tools.yaml

**Single source of truth:** `app/domains/agent_studio/config/platform_tools.yaml`

Replaces 3 previously inline Python dicts in `custom_agent_runtime.py`.

### 4.1 Structure

```yaml
tools:          # 31 tools — access: read|write
hitl_required:  # 7 write tools that require human confirmation
domains:        # 10 loader paths — domain_key → Python function path
```

**Current counts (2026-06-13):**
- Tools: 31 (23 read-only, 8 write)
- HITL-required: 7 (`publish_job`, `send_offer`, `reject_candidate`, `bulk_update_candidates`, `send_email_bulk`, `bulk_reject_candidates`, `send_whatsapp_bulk`)
- Domain loaders: 10 (`sourcing`, `pipeline`→cv_screening, `screening`→cv_screening, `communication`, `analytics`, `job_management`, `automation`, `interview_intelligence`, `talent_intelligence`, `workforce`)

### 4.2 Loader (platform_tools_loader.py)

Thin wrapper with `lru_cache(maxsize=1)`. Exposes:
- `get_platform_tools_registry() → dict[str, str]`
- `get_hitl_required_tools() → frozenset[str]`
- `get_domain_tool_loaders() → dict[str, str]`

### 4.3 Registry Sync Invariant

`platform_tools.yaml` domain keys and `_REGISTERED_DOMAINS` (conformance test) serve different purposes:

- `platform_tools.yaml` keys = domains that Agent Studio can load tools from at runtime
- `_REGISTERED_DOMAINS` = domains that must satisfy the canonical file contract

Overlap is expected but not identical. `screening` in platform_tools is an alias that loads from `cv_screening` (which is registered). Domains in `_REGISTERED_DOMAINS` that are not in `platform_tools.yaml` (e.g., `offer`, `ats_integration`) participate in intent routing but don't expose tools to custom agents directly.

**Invariant:** every domain in `platform_tools.yaml` MUST also be in `_REGISTERED_DOMAINS` OR be a documented alias (like `screening`→`cv_screening`).

---

## 5. Accepted Exceptions

### 5.1 agent_studio — top-level orchestration files

`agent_studio` is the orchestration hub; its top-level complexity is inherent to its role. Accepted files:

```
_audit_helper.py          — dev tooling for agent catalog validation
custom_agent_runtime.py   — custom agent execution runtime
platform_tools_loader.py  — YAML loader (§4.2)
reasoning_trace_builder.py — trace enrichment
whatsapp_agent_plugin.py  — WhatsApp channel plugin
```

All listed in `_TOP_LEVEL_EXCEPTIONS["agent_studio"]` in the conformance test.

### 5.2 job_creation — LangGraph wizard exception

`job_creation` uses LangGraph for multi-step job creation wizard. It has:
- No `capabilities.yaml` (listed in `_SKIP_CAPABILITIES_YAML`) — LangGraph graph, not intent-routed
- No `actions.py` — wizard nodes replace action dispatch
- Multiple top-level files: `graph.py`, `schemas.py`, `state.py`, `compliance.py`, `feature_flag.py`, `policy_gate.py`, `api_client.py`, `dispatch_messages.py`

All listed in `_TOP_LEVEL_EXCEPTIONS["job_creation"]` and `_SKIP_CAPABILITIES_YAML` in the conformance test. **No change planned.**

### 5.3 Domains with actions inline in domain.py

`candidate_self_service`, `company_settings`, `hiring_policy`, `offer`, `pipeline` — actions declared directly in `domain.py` instead of a separate `actions.py`. Accepted when the action list is small and stable.

**Rule:** if actions exceed ~10 items or need independent testing, extract to `actions.py`.

### 5.4 tools/ instead of agents/

`interview_intelligence` and `talent_intelligence` use `tools/` (not `agents/`) for their tool registry. Accepted because these are pure tool libraries (no agent orchestration logic). Listed in `_NON_CANONICAL_TOOL_DIR` if added to conformance test.

---

## 6. Known Gaps (Future Work)

### 6.1 __domain_type__ missing from established registered domains

`__domain_type__` annotation in `__init__.py` is present in:
- All 13 service domains (`"service"`)
- New agentic domains: `interview_intelligence`, `talent_intelligence`, `workforce` (`"agentic"`)
- `recruitment_campaign` (`"service"` — correctly marked)

Missing from: all other registered domains (analytics, ats_integration, automation, etc.)

**Not enforced by conformance test.** Recommended: add `"agentic"` to all registered domain `__init__.py` files + add conformance check for `__domain_type__ in {"service", "agentic"}`.

### 6.2 G9 — WorkOS Full Auth Abstraction (DEFERRED)

`auth_provider.py` was created as prep (ADR-G7 sensor added). Full migration of all sub-app endpoints to use `AuthContext` from the new abstraction is a dedicated sprint. Current state: provider file exists, partial adoption.

**Not a regression** — old auth paths still work. ADR will be updated when migration completes.

### 6.3 G11 — PostgreSQL Schema Separation by Domain (EXPLICITLY OUT OF SCOPE)

Separating the single `public` PostgreSQL schema into per-domain schemas (e.g., `schema_cv_screening`, `schema_billing`) would provide stronger isolation but requires:
- Downtime for schema migration
- Cascade migration rewrite across ~200 Alembic migrations
- Cross-domain JOIN rewrite (currently used freely)

**Decision:** not doing this. Multi-tenancy isolation is enforced at the application layer (company_id in every query, ADR-001 repository pattern). PostgreSQL-level schema separation is a future architectural investment, not a current need.

---

## 7. Conformance Test Baseline (2026-06-13)

**File:** `tests/contract/test_domain_structure_conformance.py`  
**Result:** 245 passed, 59 skipped — CI blocking

Test classes:
- `TestDomainInit` — every domain dir has `__init__.py`
- `TestRegisteredDomains` — domain.py, ComplianceDomainPrompt, capabilities.yaml, capabilities valid
- `TestUnregisteredHasNoDomainPy` — service domains don't accidentally have domain.py
- `TestAgentsDirectory` — non-registered domains without agents/ exception don't have agents/
- `TestNoEmptyDirs` — no empty subdirectories
- `TestNoStrayFiles` — no unexpected top-level .py files (with documented exceptions)

---

## 8. Commit History (key ADR-related commits)

| Hash | Description |
|---|---|
| `37e3013e1` | P2 cleanup: ghost actions removed, billing tests relocated |
| `fa412b117` | Register interview_intelligence, talent_intelligence, workforce |
| *(session)* | PLATFORM_TOOLS_REGISTRY: Python dict → platform_tools.yaml |
| *(session)* | test_platform_tools_yaml.py: 13 contract tests |
| `1cf329b26` | G1-G2-G3: critical events outbox, LLM constants, trace_id |
| `eaae3f18b` | G10-LLM: lib lia-llm — ModelTierResolver + LLMResponseEnvelope |
| `1da4edd81` | G10-PII: lib lia-pii — pii_masking + field_visibility |
| `2648d79cc` | Strangler Fig: sub-app api-admin |
| `ede573189` | Strangler Fig: sub-app api-comunicacao |
| `09daab398` | Strangler Fig: sub-app api-triagem |
| `cdd21f355` | Strangler Fig: sub-app api-agentes |

---

## 9. Decision Summary

| Decision | Rationale |
|---|---|
| ComplianceDomainPrompt mandatory for all registered domains | Compliance cannot be opt-in; structural enforcement via inheritance |
| capabilities.yaml required (except job_creation) | Declarative intent routing; YAML over code for non-technical editability |
| platform_tools.yaml replaces 3 inline Python dicts | Single source of truth; declarative; testable; no hardcoded state in runtime |
| _REGISTERED_DOMAINS enforced by CI-blocking conformance test | Prevents drift; new domain requires explicit registration decision |
| G11 (schema separation) explicitly deferred | Application-layer multi-tenancy is sufficient; migration cost > benefit now |
| G9 (WorkOS abstraction) partially done | auth_provider.py exists; full migration is sprint work |

---

## 10. API Organization — Strangler Fig Sub-Apps

### 10.1 Pattern

The monolith (`app/`) is being decomposed via the **Strangler Fig** pattern into independent FastAPI sub-applications under `apps/`. Each sub-app imports routers from `app/api/v1/` (monolith), adds its own middleware stack, and will eventually be standalone.

**Current sub-apps (2026-06-13): 7**

| Sub-app | Port | Domain responsibility |
|---|---|---|
| `api-vagas` | 8001 | Job vacancies, JD generation, WSI, wizard |
| `api-funil` | 8002 | Pipeline, kanban, stage transitions |
| `api-agentes` | 8003 | Agent Studio, chat SSE, LLM config, digital twins, HITL |
| `api-comunicacao` | 8004 | Email, WhatsApp, voice, notifications |
| `api-admin` | 8005 | Platform admin, billing, compliance, LGPD |
| `api-triagem` | 8003 | Screening, WSI, Big Five, CV parser |
| `api-onboarding` | 8003 | WorkOS auth, company setup, benefits |

### 10.2 Each sub-app structure

```
apps/<sub-app>/
├── CLAUDE.md         # sub-app specific guidelines
├── Dockerfile
├── main.py           # FastAPI app + router includes + middleware
└── pyproject.toml    # independent dependencies
```

`main.py` follows a strict template:
1. Sentry + logging init
2. Lifespan (DB init, background tasks)
3. FastAPI app with `debug=False` + global exception handler (ADR-PYDANTIC-R5)
4. CORS + RateLimit + RequestId + StructuredLogging middleware
5. Router includes from `app/api/v1/` with `/api/v1` prefix

### 10.3 MONOLITH-IMPORT markers

Sub-apps currently import from monolith `app/` for infrastructure not yet extracted to shared libs. These are marked `# MONOLITH-IMPORT: <reason>` for tracking. Sensor `check_sub_apps_structure.py` (G6) monitors these.

**Current count:** 67 MONOLITH-IMPORT markers across all sub-apps.

Target: reduce to 0 as libs (`lia-config`, `lia-llm`, `lia-pii`, `lia-utils`) absorb the shared infrastructure. `lia-llm` and `lia-pii` already extracted (commits `eaae3f18b`, `1da4edd81`).

### 10.4 Route organization within app/api/v1/

Routes live in `app/api/v1/<resource>.py` or `app/api/v1/<domain>/` for complex domains. No route logic in domain services — routers call domain services, services call repositories.

**Rule:** A route file belongs to one sub-app. Cross-sub-app routes are a smell — resolve by extracting shared service or moving to the correct sub-app.

### 10.5 Monolith (app/) vs sub-apps (apps/)

During the Strangler Fig transition:
- **Development target:** sub-apps (`apps/`)
- **Production today:** monolith still runs as single FastAPI app on port 8001
- **Migration gate:** a sub-app is "standalone-ready" when its `MONOLITH-IMPORT` count = 0 and all dependencies resolve from `pyproject.toml` without `app/`

This ADR will be updated when the first sub-app reaches standalone-ready status.
