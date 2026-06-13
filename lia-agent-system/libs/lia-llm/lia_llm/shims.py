"""
Shims para módulos que ainda vivem no monolito mas são re-exportados por lia-llm.

token_budget_service vive em app.domains.credits.services.token_budget_service
porque tem muitas dependências de infra (lia_config.database, lia_models.billing,
Redis). Extrair seria prematura — shim provê acesso via lia_llm quando necessário.

USO (somente dentro do lia-agent-system):
    from lia_llm.shims import check_budget, increment_usage, get_plan_limit
    # equivalente a importar direto do canonical
"""
from __future__ import annotations

# Token budget — canonical vive em app.domains.credits.services.token_budget_service
# Shim re-exporta o essencial para consumers que preferem import via lia_llm
try:
    from app.domains.credits.services.token_budget_service import (  # noqa: F401
        check_budget,
        check_request_budget,
        check_request_budget_before_llm,
        estimate_request_tokens,
        get_budget_status,
        get_plan_limit,
        get_plan_for_company,
        get_request_limit,
        increment_usage,
        track_llm_usage_start,
        PLAN_DAILY_LIMITS,
        PLAN_REQUEST_LIMITS,
        AGENT_TYPE_REQUEST_OVERRIDES,
        DEFAULT_DAILY_LIMIT,
        DEFAULT_REQUEST_LIMIT,
        RequestBudgetExceededError,
    )
except ImportError:
    # Fora do monolito (standalone / test) — shim não disponível
    pass
