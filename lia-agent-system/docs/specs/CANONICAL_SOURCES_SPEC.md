# Canonical Sources Spec

> **Purpose.** Single-source-of-truth registry of canonical module locations
> for cross-cutting concerns in the LIA backend. New code MUST import from
> the canonical paths listed here. Any path marked **forbidden** is blocked
> by `scripts/check_forbidden_imports.py` (pre-commit hook **G5** + CI).

> **How to use this file.** When you need a piece of cross-cutting
> functionality (tracing, callbacks, drift detection, token budget, audit,
> models, messaging, etc.), look it up here first. If your concern is not
> listed, do not invent a new location — open an ADR in `ARCHITECTURE.md`,
> add the entry here, and update `scripts/check_forbidden_imports.py` if a
> legacy path needs to be blocked.

---

## 1. Observability — `app.shared.observability.*` (Tarefa #343, ADR-017)

All observability code lives under the single package
`app/shared/observability/`. There is **one** canonical import path per
module and **no** re-export shims. The legacy locations — 11 concerns
spread across 16 distinct import paths (some concerns had duplicate
copies in `shared/services/` *and* `domains/*/services/`) — were deleted,
not shimmed, so the CI guard is the only thing standing between the repo
and re-fragmentation.

### 1.1 Canonical modules (11)

| Concern | Canonical import path |
|---|---|
| Sentry / OpenTelemetry tracing | `app.shared.observability.tracing` |
| Structured logging | `app.shared.observability.structured_logging` |
| LLM callbacks (Langfuse + audit) | `app.shared.observability.callbacks` |
| Agent monitoring service | `app.shared.observability.agent_monitoring_service` |
| Agent health alerts | `app.shared.observability.agent_health_alert_service` |
| Model drift detection | `app.shared.observability.model_drift_service` |
| Drift alerting | `app.shared.observability.drift_alert_service` |
| Token tracking | `app.shared.observability.token_tracking_service` |
| Token budget enforcement | `app.shared.observability.token_budget_service` |
| WSI-specific observability | `app.shared.observability.wsi_observability` |
| LangSmith configuration | `app.shared.observability.langsmith` |

### 1.2 Forbidden legacy paths (deleted; CI-blocked)

The following paths existed before Tarefa #343 and were removed without
shims. `scripts/check_forbidden_imports.py` rejects any reintroduction.

- `app.shared.tracing`
- `app.shared.structured_logging`
- `app.shared.llm.callbacks`
- `app.shared.governance.agent_monitoring_service`
- `app.shared.services.agent_health_alert_service`
- `app.shared.services.model_drift_service`
- `app.shared.services.drift_alert_service`
- `app.shared.services.token_tracking_service`
- `app.shared.services.token_budget_service`
- `app.domains.ai.services.model_drift_service`
- `app.domains.lgpd.services.drift_alert_service`
- `app.domains.analytics.services.token_tracking_service`
- `app.domains.analytics.services.wsi_observability`
- `app.domains.analytics.services.agent_monitoring_service`
- `app.domains.credits.services.token_budget_service`
- `app.config.langsmith`

### 1.3 Cross-references

- ADR: `lia-agent-system/ARCHITECTURE.md` — **ADR-017**.
- Package contract: `app/shared/observability/__init__.py` (header lists
  the deleted legacy paths and points back at the CI guard).
- CI guard: `scripts/check_forbidden_imports.py` (FORBIDDEN_PATTERNS
  block, comment "task #343").
- Audit reconciliation:
  `docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` §0 (Stage 6) and
  §1.2 Top-10 #3.

---

## 2. Models — `lia_models.*` (ADR-002, ADR-012)

- Canonical: `from lia_models.<module> import <Model>`
- Forbidden (CI-blocked, see `scripts/check_forbidden_imports.py`):
  - `from libs.models.lia_models.*` / `import libs.models.lia_models.*`
  - `from app.models...` / `import app.models...` (the `app/models/` shim
    layer was deleted in task #242 because the parallel import path
    caused duplicate SQLAlchemy class registrations)
- See `ARCHITECTURE.md` ADR-002 / ADR-012.

## 3. Messaging — `lia_messaging.*` (ADR-012)

- Canonical: `from lia_messaging.<module> import <X>`
- Forbidden (CI-blocked): `from libs.messaging.lia_messaging.*`
- See `ARCHITECTURE.md` ADR-012.

## 4. Tool authoring — `@tool_handler` + `*_tool_registry.py` (ADR-016)

- Authoring surface: `app/shared/tool_handler.py` + `app/domains/*/agents/*_tool_registry.py`
- Execution index: `app/tools/registry.py` (read-only consumer; not an authoring surface)
- Scope/governance: `app/tools/tool_permissions.yaml`
- Forbidden in `app/domains/*/tools/` (CI-blocked):
  `from langchain_core.tools import tool`
- See `ARCHITECTURE.md` ADR-015 (S7.3 + S7.4) and ADR-016.

## 5. Global tool registry — retired (ADR-015 S7.2)

- `app.shared.global_tool_registry` was deleted in Task #350.
- Forbidden (CI-blocked): `from app.shared.global_tool_registry`
- See `ARCHITECTURE.md` ADR-015.

---

*Last updated: 2026-04-17 — Tarefa #372 (observability doc refresh, closing residual from Tarefa #343).*
