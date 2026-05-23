"""
Migration sensor — ``app.domains.policy`` → ``app.domains.hiring_policy``.

WHY THIS SENSOR EXISTS
======================
Recovery #10 (2026-05-23) descobriu que ``PolicySetupAgent`` em
``app/domains/policy/agents/agent.py`` é LEGACY DEPRECATED — não bug ativo.

O canonical novo é:
- ``app/domains/hiring_policy/agents/policy_react_agent.py``:
  ``PolicyReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)``
- Plus 5 arquivos canonical: stage_context, system_prompt, tool_registry (9 tools),
  policy_react_agent, __init__

DeprecationWarning explícito no import path legacy:
``app.domains.policy is deprecated. Use app.domains.hiring_policy instead.
Scheduled for removal in Sprint VI.``

RAM TOP 10 sugeriu PolicySetupAgent shim como BUG ATIVO. Audit revelou que:
1. Shim em ``app/agents/policy_setup_agent.py`` AINDA FUNCIONA (importa de
   legacy path que ainda existe).
2. Legacy ``PolicySetupAgent`` class EXISTE em ``app/domains/policy/agents/agent.py``
   (reduced form, but operational).
3. Canonical novo coexiste em ``app/domains/hiring_policy/``.

Sensor garante:
1. Canonical NOVO (PolicyReActAgent + canonical files) permanece.
2. Legacy continua importável (compatibilidade shim).
3. Migration progress trackable (Sprint VI cleanup).

Pattern: BLOCKING.
"""
from __future__ import annotations


def test_canonical_hiring_policy_agent_exists():
    """
    ``PolicyReActAgent`` canonical novo deve permanecer em
    ``app.domains.hiring_policy.agents.policy_react_agent``.
    """
    from app.domains.hiring_policy.agents.policy_react_agent import (  # noqa: F401
        PolicyReActAgent,
    )

    assert hasattr(PolicyReActAgent, "__init__"), (
        "PolicyReActAgent canonical sem __init__ — não é classe real."
    )


def test_canonical_hiring_policy_modules_exist():
    """
    Os 4 módulos canonical do agente hiring_policy devem existir.
    """
    import importlib

    canonical_modules = [
        "app.domains.hiring_policy.agents.policy_react_agent",
        "app.domains.hiring_policy.agents.policy_stage_context",
        "app.domains.hiring_policy.agents.policy_system_prompt",
        "app.domains.hiring_policy.agents.policy_tool_registry",
    ]

    for mod_path in canonical_modules:
        try:
            importlib.import_module(mod_path)
        except ImportError as exc:
            raise AssertionError(
                f"Canonical module {mod_path} ausente: {exc}. "
                f"Migration app.domains.policy → app.domains.hiring_policy "
                f"quebrada — restaurar."
            )


def test_legacy_policy_shim_removed():
    """
    W4-033 (2026-05-23) removeu o shim ``app/agents/policy_setup_agent.py``.
    Zero callers de produção confirmados antes da deleção.
    Sensor atualizado: verifica que o shim NÃO existe.
    """
    import importlib.util
    spec = importlib.util.find_spec("app.agents.policy_setup_agent")
    assert spec is None, (
        "Shim app/agents/policy_setup_agent.py foi restaurado indevidamente. "
        "W4-033 deletou este shim (zero callers confirmados 2026-05-23). "
        "Use app.domains.hiring_policy.agents.policy_react_agent diretamente."
    )


def test_legacy_path_emits_deprecation_warning():
    """
    Import via legacy path ``app.domains.policy`` deve emitir DeprecationWarning
    apontando pra hiring_policy.

    Garante que devs vejam o aviso e migrem pra canonical.
    """
    import warnings
    import importlib

    # Force re-import pra capturar warning (caso já tenha sido importado antes)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.import_module("app.domains.policy")
        # Re-trigger via reload se já estava cached
        import app.domains.policy as _policy_mod
        importlib.reload(_policy_mod)

    deprecation_msgs = [
        str(w.message) for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "hiring_policy" in str(w.message).lower()
    ]
    assert deprecation_msgs, (
        "Legacy app.domains.policy NÃO emite DeprecationWarning apontando pra "
        "hiring_policy. Devs não verão aviso pra migrar."
    )
