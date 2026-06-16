# app/shared/ Module Inventory

**Generated:** 2026-06-15  
**Branch:** feat/benefits-prv-canonical  
**Scope:** All `.py` files and subdirectories under `lia-agent-system/app/shared/`  
**Method:** `grep -rl "shared.<module>"` caller count across `app/` (excluding self), manual verification for edge cases.  
**Vulture scan:** `vulture app/shared/ --min-confidence 80` — 23 findings, all minor (unused vars/imports within canonical files, not dead modules). See [Vulture findings](#vulture-findings) below.

---

## Summary

| Classification | Count | Action |
|---|---|---|
| CANONICAL | 45 modules/dirs | Keep, no action |
| LEGACY | 15 modules/dirs | Monitor, migrate callers |
| DEAD | 10 modules/dirs | Remove (separate tickets) |
| RAILS-DEAD | 2 modules | Remove after RAILS-elimination audit |

---

## CANONICAL — Actively used (>2 external callers or critical infrastructure)

### Foundation (100+ callers)
| Module | Callers | Description |
|---|---|---|
| `security/` | 341 | `require_company_id`, JWT, multi-tenancy — **security foundation** |
| `types.py` | 269 | `WeDoBaseModel`, `JobIdParam`, type aliases — **schema foundation** |
| `services/` | 250 | 90+ service files (token_budget, consent, lia_context_builder, etc.) — **service layer** |
| `compliance/` | 190 | `FairnessGuard`, audit trail, LGPD, prompt injection — **compliance critical** |

### Core infrastructure (30–100 callers)
| Module | Callers | Description |
|---|---|---|
| `prompts/` | 65 | `SystemPromptBuilder`, `lia_persona.yaml`, prompt registry |
| `agents/` | 56 | `CrewExecutor`, `AgentBus`, `TenantAwareAgent`, crew models |
| `tool_handler.py` | 55 | `@tool_handler` decorator — multi-tenancy fail-closed gate |
| `pii_masking.py` | 54 | `mask_pii`, `strip_pii_for_llm_prompt`, `mask_pii_outbound` — ADR-LGPD-002 |
| `providers/` | 51 | Anthropic/OpenAI/Gemini LLM clients, voice provider |
| `tenant_guard.py` | 30 | `get_verified_company_id`, `require_company_id` — cross-tenant defense |
| `encryption/` | 25 | `EncryptedFieldMixin` — field-level encryption |

### Standard infrastructure (10–30 callers)
| Module | Callers | Description |
|---|---|---|
| `intelligence/` | 21 | `EmbeddingService`, `SemanticSearchService`, `SmartExtractor` |
| `messaging/` | 19 | `UnifiedEventPublisher`, event bus |
| `hitl/` | 18 | `HITLGate`, `HITLApprovalContext` — human-in-the-loop |
| `tenant_llm_context.py` | 17 | Per-tenant LLM context with budget/policy |
| `learning/` | 15 | Feedback loops, correction capture, learning service |
| `robustness/` | 14 | Error handling, input validation, idempotency, security patterns |
| `governance/` | 12 | `AgentMonitoringService`, `FeatureFlagService` |
| `value_objects/` | 11 | `CompanyId` value object |
| `tracing.py` | 11 | OTel / Sentry tracing |
| `errors.py` | 10 | Domain error hierarchy |

### Active (5–9 callers)
| Module | Callers | Description |
|---|---|---|
| `runtime_context.py` | 8 | `RuntimeContext`, ContextVar registry — ADR-029 |
| `exceptions/` | 8 | `TenantErrors`, domain exception hierarchy |
| `sessions/` | 7 | `ThreadId` — LangGraph checkpoint session |
| `tenant_session.py` | 7 | Per-tenant session data |
| `entity_resolver.py` | 6 | Fuzzy entity resolution for chat (candidate/job lookup) |
| `trigger_mode_validation.py` | 6 | `validate_trigger_mode` — agent deployment |
| `execution/` | 6 | `ActionPlanner`, `PlanExecutor`, discrete action framework |
| `automation/` | 5 | `TriggerTypesCanonical`, `ConditionsCanonical` |
| `channels/` | 5 | `ChannelAdapter`, `MultiChannelService` |
| `chat_event_serializer.py` | 5 | SSE event serialization |
| `wsi_skill_taxonomy.py` | 5 | Dreyfus skill taxonomy for WSI scoring |

### In use (3–4 callers)
| Module | Callers | Description |
|---|---|---|
| `canonical_pages.py` | 4 | `CanonicalPage` enum — orchestrator routing |
| `websocket/` | 4 | `WSManager`, WS message schemas |
| `eligibility_matching.py` | 3 | Eligibility question matching logic |
| `hitl_pending_sink.py` | 3 | HITL pending action queue |
| `structured_logging.py` | 3 | Structured log helpers |
| `tool_catalog.py` | 3 | `_CANONICAL_SOURCES` — capability registry |
| `async_processing/` | 3 | `TaskManager`, `TaskQueue`, `TaskScheduler` |
| `capabilities/` | 3 | `JobCreationCapabilities` |
| `constants/` | 3 | Prompt constants, webhook constants |
| `pii_masking/` | 3 | `PIIMaskingFilter` log filter (alongside `pii_masking.py`) |

---

## LEGACY — Low callers, active but deprecating

| Module | Callers | Status | Notes |
|---|---|---|---|
| `ab_testing.py` | 1 | LEGACY | Only `prompt_version_loader.py` imports `get_experiment_manager`. Full implementation lives in `learning/ab_testing_service.py`. Migrate caller → `learning/` |
| `bars_evaluator.py` | 1 | LEGACY | Root-level; `evaluation/bars_evaluator.py` is the canonical. 1 caller is just a comment in `evaluation/bars_evaluator.py` saying they're distinct. Effectively dead. |
| `delegation_fallback.py` | 1 | LEGACY | `job_management/domain.py:139` only. Pattern replaced by proper tool routing. |
| `agent_templates/` | 1 | LEGACY | `sector_templates.py` — 1 caller (job template scaffolding). |
| `entities/` | 1 | LEGACY | `entities/registry.py` — entity registry pattern not widely adopted. |
| `events/` | 1 | LEGACY | `AgentLifecycleEmitter` — 1 caller in `agent_events.py`. Partially superseded by `messaging/`. |
| `ml/` | 1 | LEGACY | `ttf_predictor.py` — 1 conditional lazy import in `ml_predictions_dashboard.py`. Low-priority feature. |
| `models/` | 1 | LEGACY | 1 caller. Likely superseded by domain-specific models. |
| `chat_types.py` | 1 | LEGACY | 1 caller. Chat type definitions partially migrated to domain schemas. |
| `cache_strategy.py` | 2 | LEGACY | 2 callers. Simple cache abstraction; callers could use Redis directly. |
| `ui_action_sink.py` | 2 | LEGACY | 2 callers (`agent_chat_sse.py`, `orchestrator/legacy`). Phase 0-32 wired. Monitor. |
| `admin/` | 2 | LEGACY | `cross_tenant_session.py` — 2 callers (admin ops). |
| `api/` | 2 | LEGACY | `response.py` — 2 callers. Thin wrapper. |
| `tools/` | 2 | LEGACY | `export_tools.py`, `insight_tools.py`, `proactive_tools.py` — low adoption. |
| `evaluation/` | 0 | LEGACY | `bars_evaluator.py` + `fact_checker.py` — 0 external callers. Content is canonical (compliance use), but unused. |

---

## DEAD — 0 external callers, safe to remove

| Module | Evidence | Removal Risk |
|---|---|---|
| `batch_service.py` | 0 callers. No tests. Batch ops moved to Celery/Sidekiq. | LOW |
| `hitl_decorator.py` | Self-import only (`from app.shared.hitl_decorator import require_hitl` is inside the file itself). Superseded by `hitl/agent_gate.py`. | LOW |
| `session_bridge.py` | 0 callers. `memory_resolver.py:247` is a comment only. Session persistence uses Redis directly. | LOW |
| `upload_limits.py` | 0 callers. Upload limits defined inline in endpoints. | LOW |
| `upload_validators.py` | 0 callers. `file_router.py` has its own `validate_file` (not importing shared). | LOW |
| `wizard_suggestion_priority.py` | 0 callers. `WizardSuggestion*` in APIs are unrelated response schemas. | LOW |
| `auth/` | 0 external callers. `auth/auth_provider.py` only self-imports. Auth handled by `security/` + WorkOS SDK directly. | MEDIUM |
| `health/` | 0 callers. `providers_health.py` unused. FastAPI `/health` endpoint defined inline in main router. | LOW |
| `permissions/` | 0 callers. Permission logic absorbed into `security/`. | LOW |
| `serializers/` | 0 callers. Serialization moved to Pydantic schemas. | LOW |

**Estimated removal LOC:** ~1,200 lines across 10 modules.

---

## RAILS-DEAD — Dead because RAILS_ENABLED=False

| Module | Status | Notes |
|---|---|---|
| `integration/rails_client.py` | DEAD | All callers guarded by `if RAILS_ENABLED` (= `False`). `RAILS_API_URL` not set in Replit. See Rails Elimination canonical (CLAUDE.md). Remove once all callers are cleaned up. |
| `rails_client.py` (root) | LEGACY SHIM | Deprecation shim (W2-010 Phase A). Re-exports from `integration/rails_client.py`. 0 active callers after RAILS_ENABLED=False. Phase B = delete. |

---

## Vulture Findings (min-confidence 80%)

All 23 findings are **minor** within canonical modules — no entire dead modules found by vulture.

| File | Finding | Action |
|---|---|---|
| `compliance/audit_service.py:423` | Unreachable `else` expression | Cleanup (P2) |
| `encryption/encrypted_field_mixin.py:200,203` | Unused vars `owner`, `objtype` in descriptor | Descriptor convention — ignore |
| `intelligence/smart_extractor.py:169` | Unused var `available_actions` | Cleanup (P2) |
| `learning/learning_loop_service.py:1116` | Unused var `response_metadata` | Cleanup (P2) |
| `messaging/unified_event_publisher.py:44` | Unused import `validate_event_version` | Remove import (P2) |
| `pii_masking.py:17` | 9 unused imports from `_pii_impl` | Star-export privates — may be intentional |
| `prompts/system_prompt_builder.py:554,556` | Unused vars `partial_context`, `is_ongoing_conversation` | Cleanup (P2) |
| `providers/anthropic_client.py:37-39` | 3 unused lazy alias imports | Lazy-import pattern — ignore |
| `services/approval_notification_service.py:217` | Unused var `approvers_count` | Cleanup (P2) |
| `services/bias_audit_service.py:42` | Unused import `_chi2_dist` | Remove import (P2) |

---

## Removal Tickets (DEAD modules)

### T1 — Remove `batch_service.py`, `session_bridge.py`, `hitl_decorator.py`
- Files: `app/shared/batch_service.py`, `app/shared/session_bridge.py`, `app/shared/hitl_decorator.py`
- Risk: LOW — 0 callers confirmed
- Sensor: grep check post-removal

### T2 — Remove `upload_limits.py`, `upload_validators.py`, `wizard_suggestion_priority.py`
- Files: 3 files in `app/shared/`
- Risk: LOW — 0 callers, no tests
- Action: Delete files, run smoke test

### T3 — Remove `health/`, `permissions/`, `serializers/` directories
- Dirs: `app/shared/health/`, `app/shared/permissions/`, `app/shared/serializers/`
- Risk: LOW — 0 external callers
- Action: Delete dirs, run `check_capability_catalog_sync.py` after

### T4 — Audit and remove `auth/` directory
- Dir: `app/shared/auth/`
- Risk: MEDIUM — verify no dynamic imports or route registration hidden from grep
- Action: Read `auth_provider.py` fully, confirm 0 real callers, then delete

### T5 (RAILS) — Remove `integration/rails_client.py`, `rails_client.py` shim
- Files: `app/shared/integration/rails_client.py`, `app/shared/rails_client.py`
- Risk: MEDIUM — callers exist but guarded by `RAILS_ENABLED=False`; remove callers first
- Prerequisite: Complete rails_adapter.py cleanup, rh_dashboard.py, candidate_portal.py
