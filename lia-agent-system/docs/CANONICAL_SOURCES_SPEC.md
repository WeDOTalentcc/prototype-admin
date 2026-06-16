# Canonical Sources Specification

> Single source of truth for "where does this responsibility live?". When two
> modules look like they could each own the same concern, this document
> arbitrates. Any divergence between this file and the codebase is a bug —
> fix the code, not the spec.

---

## 1. Observability — `app/shared/observability/`

**Status:** canonical (Task #343, 2026-04-16). Enforced by
`scripts/check_forbidden_imports.py` (pre-commit hook `G5` + CI).
See ADR-017 in `ARCHITECTURE.md`.

Tracing, structured logging, LLM callbacks, agent monitoring, drift
detection, token tracking, token budgeting, WSI observability, and the
LangSmith client all live in one package. Eleven previously scattered
modules were collapsed into this single home and the legacy paths were
deleted (no shims left behind).

### 1.1 Module map (canonical → concern)

| Module | Concern | Replaces (deleted in #343) |
|---|---|---|
| `app/shared/observability/tracing.py` | Sentry + OpenTelemetry setup, span helpers | `app/shared/tracing.py` |
| `app/shared/observability/structured_logging.py` | structlog config, JSON logging, request-id propagation | `app/shared/structured_logging.py` |
| `app/shared/observability/callbacks.py` | LangChain `BaseCallbackHandler` for LLM I/O capture | `app/shared/llm/callbacks.py` |
| `app/shared/observability/agent_monitoring_service.py` | Per-agent latency, error rate, success metrics | `app/shared/governance/agent_monitoring_service.py`, `app/domains/analytics/services/agent_monitoring_service.py` |
| `app/shared/observability/agent_health_alert_service.py` | Threshold-based alerts on agent health | `app/shared/services/agent_health_alert_service.py` |
| `app/shared/observability/model_drift_service.py` | Output / embedding drift detection for LLM-backed agents | `app/shared/services/model_drift_service.py`, `app/domains/ai/services/model_drift_service.py` |
| `app/shared/observability/drift_alert_service.py` | Notification fan-out when drift thresholds trip | `app/shared/services/drift_alert_service.py`, `app/domains/lgpd/services/drift_alert_service.py` |
| `app/shared/observability/token_tracking_service.py` | Per-call token / cost recording | `app/shared/services/token_tracking_service.py`, `app/domains/analytics/services/token_tracking_service.py` |
| `app/shared/observability/token_budget_service.py` | Tenant-level token / spend budget enforcement | `app/shared/services/token_budget_service.py`, `app/domains/credits/services/token_budget_service.py` |
| `app/shared/observability/wsi_observability.py` | WSI scoring telemetry (latency, calibration drift, BARS coverage) | `app/domains/analytics/services/wsi_observability.py` |
| `app/shared/observability/langsmith.py` | LangSmith client / project / tracer config | `app/config/langsmith.py` |

### 1.2 Import contract

**Correct:**

```python
from app.shared.observability.tracing import setup_tracing
from app.shared.observability.structured_logging import get_logger
from app.shared.observability.callbacks import LIACallbackHandler
from app.shared.observability.langsmith import configure_langsmith
from app.shared.observability.agent_monitoring_service import AgentMonitoringService
from app.shared.observability.agent_health_alert_service import AgentHealthAlertService
from app.shared.observability.model_drift_service import ModelDriftService
from app.shared.observability.drift_alert_service import DriftAlertService
from app.shared.observability.token_tracking_service import TokenTrackingService
from app.shared.observability.token_budget_service import TokenBudgetService
from app.shared.observability.wsi_observability import WSIObservability
```

**Forbidden** (every pattern below is in
`scripts/check_forbidden_imports.py:FORBIDDEN_PATTERNS` and breaks CI):

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

### 1.3 Why one package

1. **Single mental model.** "I need to log / trace / measure / alert" → open
   one folder. New contributors do not have to discover that drift detection
   used to live under three different domain folders.
2. **No duplicate registrations.** The deleted re-export shims caused
   double-registration of structlog processors, OpenTelemetry exporters, and
   LangChain callbacks (the same root cause as ADR-002 / ADR-012).
3. **Dependency direction.** Observability is a leaf: it depends on `app.core`
   and external SDKs only. Pulling it out of `domains/*` enforces that
   domains depend on observability and never the reverse.
4. **Lint-enforceable.** A flat list of legacy paths is trivial to grep for;
   the lint rule (§1.2) catches regressions in milliseconds.

### 1.4 Run the lint locally

```bash
cd lia-agent-system
python3 scripts/check_forbidden_imports.py
```

Exit code `0` = clean. Exit code `1` prints `path:line: offending import`
for every violation, including the observability legacy paths above and
the model / messaging paths covered by ADR-002 / ADR-012.

---

*Last updated: 2026-04-17 — Task #363 (documents the consolidation
performed in Task #343).*
