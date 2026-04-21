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



## 6. Governance enforcement — `ToolDefinition.governance_tags` (ADR-019)

- **Canonical dataclass:** `app/tools/registry.py::ToolDefinition`
- **Campos canônicos (pós FIX 3+4+8):**
  - `governance_tags: list[str]` — compliance/safety flags
  - `related_tools: list[str]` — proactive suggestions after execution
  - `side_effects: list[str]` — retry/idempotency classification
- **Fonte da verdade dos valores:** `app/tools/tool_registry_metadata.yaml`
- **Enforcement:** `app/tools/executor.py::ToolExecutor.execute()`
  - `"requires_hitl"` → retorna `ToolResult(result={"status": "pending_hitl_confirmation"})` sem chamar handler (pode ser bypassed com `parameters["_hitl_confirmed"]=True`)
  - `"fairness_guard"` → `_check_fairness()` invoca `FairnessGuard.check()` em text params (ver ADR-019)
- **FairnessGuard canonical:** `app/shared/compliance/fairness_guard.py::FairnessGuard`
- See **ADR-019** (`docs/specs/ai/ADR-019-governance-and-observability.md`).

### 6.1 Forbidden patterns

- Fairness check chamado via import de `app/shared/compliance/fairness_guard_middleware.py` DENTRO de tool handlers → proibido; o middleware é para endpoints FastAPI, não para handlers. Handlers devem relying no executor.
- Reimplementar check de `requires_hitl` em domain handlers (duplicação) — proibido; enforcement é no `ToolExecutor`.

---

## 7. Tool call observability — `app.shared.observability` (ADR-019)

> **NOTA DE MIGRAÇÃO:** Em FIX 12 (commit `3f7245f18`) criamos `app/core/observability.py` com `emit_tool_call()` + `emit_hitl_pending()`. Isso **viola** a regra de Section 1 desta spec (todo observability deve ficar em `app/shared/observability/`). Um **follow-up fix é requerido** para mover o módulo para o path canônico antes do merge em main.

- **Canonical target (pós-migração):** `app.shared.observability.tool_metrics`
- **Funções públicas:**
  - `emit_tool_call(**kwargs)` — structured log + opcional LangSmith forward
  - `emit_hitl_pending(**kwargs)` — audit trail de HITL
- **Current location (a migrar):** `app.core.observability` — mantido temporariamente para estabilizar os commits FIX 12
- **LangSmith client:** usar `app.shared.observability.langsmith` (Section 1.1) como source de `Client()`
- See **ADR-019**.

### 7.1 Migration TODO

**Action item para próxima sessão:**
```bash
# 1. Mover arquivo
git mv app/core/observability.py app/shared/observability/tool_metrics.py

# 2. Atualizar imports (2 callers)
sed -i 's|from app.core.observability|from app.shared.observability.tool_metrics|g' \
    app/orchestrator/agentic_loop.py \
    app/orchestrator/main_orchestrator.py

# 3. Atualizar test
sed -i 's|from app.core.observability|from app.shared.observability.tool_metrics|g' \
    tests/unit/test_fix12_hitl_obs.py

# 4. Atualizar LangSmith init para reutilizar app.shared.observability.langsmith
#    (evita duplicação de client init)

# 5. Rodar CI guard
python scripts/check_forbidden_imports.py

# 6. Commit
git commit -m "refactor(obs): move tool_metrics to canonical app.shared.observability path (ADR-019)"
```

### 7.2 Forbidden patterns (post-migration)

- `from app.core.observability import emit_tool_call` → bloqueado após migração
- Redefinir `emit_tool_call` em outros módulos → duplicação de concerna (Section 1 rule)
- Invocar `langsmith.Client()` diretamente → usar wrapper de `app.shared.observability.langsmith`

---

## 8. Intent confirmation resolver — `intents_config.resolve_requires_confirmation` (ADR-019)

- **Canonical:** `app/orchestrator/action_executor/intents_config.py::resolve_requires_confirmation(intent, action_id)`
- **Precedência:** `ACTIONABLE_INTENTS[intent]["requires_confirmation"]` → `DomainAction.requires_confirmation` → `False`
- **Fontes vivas (não consolidar):**
  - `ACTIONABLE_INTENTS[intent]["requires_confirmation"]` (intent-level, contexto de invocação)
  - `DomainAction.requires_confirmation` (action-level, dangerousness inerente)
- **Uso:** callers que precisam saber "esta invocação exige confirmação?" devem chamar o resolver, NÃO as duas fontes diretamente.

### 8.1 Forbidden patterns

- `if ACTIONABLE_INTENTS[intent]["requires_confirmation"]: ...` fora do resolver → duplica lógica de precedência
- Ler `DomainAction.requires_confirmation` diretamente no orchestrator sem fallback para intent → perde contexto

---

*Atualizado: 2026-04-21 (FIX 1-12, ADR-019). Última atualização anterior: 2026-04-17 (Tarefa #372).*
