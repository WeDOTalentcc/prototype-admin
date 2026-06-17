"""
Contract sensor — analytics_actions.py dispatcher e intents_config.py devem
ficar sincronizados.

WHY THIS SENSOR EXISTS
======================
Audit Recovery #4 (2026-05-23) descobriu que o merge commit 02361f41c removeu
SIMULTANEAMENTE de 3 lugares coordenados:
  - 2 helpers em ``analytics_actions.py``
  - 2 ``elif`` branches em ``execute_analytics_action`` (dispatcher)
  - 2 entries em ``intents_config.py``

Se qualquer um dos 3 ficar fora de sincronia, a cadeia LLM → intent matcher →
dispatcher → handler quebra silenciosamente: LLM dispara um action_id que cai
no ``return None`` do dispatcher OU intent name pt-BR vira inacessível.

Pattern: BLOCKING. Cadeia analítica é canonical "sync trio" — qualquer
adicionar/remover de uma action_id deve tocar os 3 lugares juntos.
"""
from __future__ import annotations

import inspect

from app.orchestrator.action_executor import intents_config
from app.orchestrator.action_handlers import analytics_actions


# 5 actions canonical do dispatcher (estado pós-Recovery #4). Atualizar este set
# em PR explícito se uma action for adicionada/removida — força revisor a ver.
_CANONICAL_ANALYTICS_ACTIONS = {
    "generate_kpi_report",
    "job_health_check",
    "analyze_funnel",
    "vacancies_without_candidates",
    "list_candidates_by_stage",
}


def _extract_dispatched_action_ids() -> set[str]:
    """Parse execute_analytics_action source pra extrair action_ids despachados."""
    src = inspect.getsource(analytics_actions.execute_analytics_action)
    # Captura literais string em comparações `action_id == "..."`
    import re
    return set(re.findall(r'action_id\s*==\s*"([^"]+)"', src))


def _extract_intents_config_analytics_action_ids() -> set[str]:
    """Coleta action_ids do intents_config com domain_id == analytics."""
    return {
        entry["action_id"]
        for entry in intents_config.ACTIONABLE_INTENTS.values()  # type: ignore[attr-defined]
        if entry.get("domain_id") == "analytics"
        and "action_id" in entry
    }


def test_dispatcher_handles_all_canonical_actions():
    """
    execute_analytics_action deve despachar exatamente as 5 actions canonical.

    Se test falha:
    - Faltando action: alguém adicionou em intents_config sem implementar handler
    - Sobrando action: alguém adicionou handler sem registrar intent
    - Recovery #4 pegou exatamente esse cenário (incident removeu de
      analytics_actions mas adicionar de volta em intents_config sem sync
      criaria mesma quebra ao contrário).
    """
    dispatched = _extract_dispatched_action_ids()
    assert dispatched == _CANONICAL_ANALYTICS_ACTIONS, (
        f"Dispatcher action_ids = {sorted(dispatched)}\n"
        f"Canonical esperado = {sorted(_CANONICAL_ANALYTICS_ACTIONS)}\n"
        f"Diff: missing={_CANONICAL_ANALYTICS_ACTIONS - dispatched}, "
        f"extra={dispatched - _CANONICAL_ANALYTICS_ACTIONS}"
    )


def test_intents_config_lists_all_canonical_actions():
    """
    intents_config.ACTIONABLE_INTENTS (entries com domain_id='analytics') deve
    cobrir as 5 actions canonical.
    """
    registered = _extract_intents_config_analytics_action_ids()
    assert _CANONICAL_ANALYTICS_ACTIONS.issubset(registered), (
        f"intents_config missing analytics action_ids: "
        f"{_CANONICAL_ANALYTICS_ACTIONS - registered}\n"
        f"Registered: {sorted(registered)}"
    )


def test_helpers_exist_for_all_dispatched_actions():
    """
    Pra cada action_id despachado pelo execute_analytics_action, deve existir
    uma função helper privada `_<action_id>` no módulo.
    """
    dispatched = _extract_dispatched_action_ids()
    for action in dispatched:
        helper_name = f"_{action}"
        assert hasattr(analytics_actions, helper_name), (
            f"Dispatcher referencia action_id '{action}' mas helper "
            f"`{helper_name}` não existe em analytics_actions module. "
            "Trio canonical quebrado (dispatcher / handler / intent_config)."
        )
