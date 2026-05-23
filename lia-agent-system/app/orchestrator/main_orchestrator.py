# app/orchestrator/main_orchestrator.py
# W4-035 Fase 2 compatibility stub -- arquivo real: app/orchestrator/execution/main_orchestrator.py
# Exporta todos os simbolos (publicos e privados) necessarios por importadores existentes.
from app.orchestrator.execution.main_orchestrator import *  # noqa: F401, F403
from app.orchestrator.execution.main_orchestrator import (  # noqa: F401
    MainOrchestrator,
    ChatResponse,
    get_main_orchestrator,
    get_perf_summary,
    _is_plan_service_enabled,
    _is_fallback_react_enabled,
    _decide_agent_type_from_hints,
    _COMPANY_SETTINGS_INTENTS,
    _get_suggested_prompts,
    _extract_param_value,
)
