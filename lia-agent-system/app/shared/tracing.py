"""Shim: re-exports canonical tracing module.

Sprint 13.5 hotfix (2026-05-24): this file used to be a duplicate of
`app/shared/observability/tracing.py`. Both called `set_tracer_provider()`
on module import, causing OpenTelemetry to error out with
"Overriding of current TracerProvider is not allowed" — which BLOCKED
OTLP export to Grafana Cloud.

Per CLAUDE.md REGRA #0 (canonical-fix): collapse duplicates. Canonical
producer = `app/shared/observability/tracing.py`. This shim re-exports
everything so legacy imports `from app.shared.tracing import ...`
continue to work without breaking 4+ callers:
- app/orchestrator/routing/cascaded_router.py
- app/api/v1/traces.py
- app/jobs/tasks/_utils.py
- app/domains/cv_screening/services/hitl_service.py
- app/domains/ai/services/rag_pipeline_service.py
- app/shared/learning/learning_loop_service.py

Migration plan: gradually update callers to import directly from
`app.shared.observability.tracing` and eventually delete this shim.
"""
from app.shared.observability.tracing import *  # noqa: F401, F403
from app.shared.observability.tracing import (  # noqa: F401 — explicit re-exports
    trace_span,
    get_tracer,
    _TRACES_ENABLED,
    is_otlp_active,
    finish_span,
    get_recent_traces,
    get_trace_stats,
    enrich_llm_span,  # UC-P1-07: LLM span enrichment — callers: llm_factory, tests
    _try_init_otlp,  # Z6-Z7: OTLP init helper re-exported for test_z6_z7_features
)
