"""Sensor canonical — domain id `job_management` resolve pro agente correto.

Frente 4 (2026-05-29). Mismatch de domain id: toda a camada de roteamento
(domain_routing.yaml, domain_mappings.py, intents_config.py, fast_router.py,
context_adapter.py, llm_cascade.py) + o nome do package Python usam
`job_management` (singular). Mas o agente estava registrado só como
`jobs_management` (plural) + alias `jobs_mgmt` — SEM `job_management`.

Consequência (REGRA 4 anti-silent-fallback): `_get_agent("job_management")`
não achava o agente no registry e caía no `fallback_id="talent"` —
mensagens de gestão de vaga eram silenciosamente tratadas pelo agente de
talent/funnel (agente errado), sem sinal pro usuário.

Fix: canonical id passou a ser `job_management`, com `jobs_management` e
`jobs_mgmt` como aliases (backward-compat pra callers diretos).

Nível do sensor: registro/resolução de CLASSE (env-independente). Não
instancia o agente — instanciação exige checkpointer com event loop, que
não está disponível em unit test.
"""
from __future__ import annotations


def _maps():
    from app.shared.agents import agent_registry as ar
    return ar._AGENT_REGISTRY, ar._AGENT_ALIASES


def _resolve_class(token: str):
    """Resolve um id/alias pra classe registrada, espelhando _resolve_id +
    _AGENT_REGISTRY.get do AgentRegistry — sem instanciar."""
    reg, aliases = _maps()
    canonical = aliases.get(token, token)
    return reg.get(canonical)


def _ensure_loaded():
    # Dispara os decorators @register_agent (idempotente).
    from app.api.v1.agent_chat_ws import _ensure_agents_loaded
    _ensure_agents_loaded()


def test_job_management_domain_resolves_to_jobs_management_agent():
    """O domain id canônico de roteamento `job_management` DEVE resolver
    pra classe JobsManagementReActAgent — não None (que cairia no
    fallback 'talent')."""
    _ensure_loaded()
    cls = _resolve_class("job_management")
    assert cls is not None, (
        "domain `job_management` não resolve nenhum agente registrado — "
        "_get_agent cairá no fallback 'talent'. Registre `job_management` "
        "como id (ou alias) do JobsManagementReActAgent."
    )
    assert cls.__name__ == "JobsManagementReActAgent", (
        f"domain `job_management` resolveu pra classe errada: {cls.__name__}"
    )


def test_legacy_jobs_aliases_resolve_to_same_class():
    """`jobs_management` e `jobs_mgmt` (backward-compat) resolvem pra mesma
    classe que `job_management`."""
    _ensure_loaded()
    target = _resolve_class("job_management")
    assert target is not None
    for legacy in ("jobs_management", "jobs_mgmt"):
        assert _resolve_class(legacy) is target, (
            f"alias legacy `{legacy}` não resolve pra mesma classe que "
            f"`job_management` ({target.__name__})"
        )
