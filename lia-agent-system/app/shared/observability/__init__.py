# Observability — Sentry, LangSmith, OpenTelemetry
#
# Single source of truth for tracing, structured logging, LLM callbacks,
# agent monitoring, drift detection, token tracking/budget, and LangSmith
# configuration. The legacy paths (app.shared.tracing, app.shared.llm.callbacks,
# app.shared.governance.agent_monitoring_service, app.shared.services.{...},
# app.domains.{ai,lgpd,analytics,credits}.services.{...}, app.config.langsmith)
# were removed in task #343 — see scripts/check_forbidden_imports.py.
