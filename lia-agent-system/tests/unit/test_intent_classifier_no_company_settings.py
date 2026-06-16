"""
Task #817 — Auditoria Canônica do Chat

Regressão para o falso positivo "intent classifier sequestrando para
company_settings". A auditoria provou que:

1) O classificador BÁSICO `IntentType` (wizard) emite 5 valores em UPPERCASE
   (DATA_INPUT, QUESTION, CORRECTION, DEVIATION, REUSE_VACANCY).
2) O classificador ENHANCED `EnhancedIntentType` (chat geral) emite 10 valores
   em UPPERCASE (CREATE_JOB, UPDATE_FIELD, ..., OUT_OF_SCOPE).
3) A constante `_COMPANY_SETTINGS_INTENTS` em `main_orchestrator` existe e é
   **intencional** (Task #811 — severity-based delegation). Contém 4 strings
   em LOWERCASE: {company_settings, configure_company, settings_config,
   hiring_policy}. NENHUM dos classificadores LLM emite valores que, após
   `.strip().lower()`, caiam nesse conjunto — logo o roteamento para
   `company_settings` só dispara quando código upstream (ex.: contexto de
   página /settings/*) seta ctx.intent explicitamente.

Estes testes congelam essas garantias: se alguém adicionar um valor ao enum
que (pós-lower) colida com `_COMPANY_SETTINGS_INTENTS`, regressão pega.

Nota (Task #821): os shims em `app.shared.services.{intent_classifier,
enhanced_intent_classifier}` foram removidos após todos os consumidores
migrarem para o caminho canônico em `app.domains.ai.services`. Os testes
da seção 2 que validavam o re-export do shim foram removidos junto.
"""

from __future__ import annotations

import pytest


# ──────────────────────────────────────────────────────────────────────────
# 1. Enums dos classificadores não colidem (pós-lower) com a constante
# ──────────────────────────────────────────────────────────────────────────


COMPANY_SETTINGS_LOWERCASE = frozenset({
    "company_settings",
    "configure_company",
    "settings_config",
    "hiring_policy",
})


def test_basic_intent_type_does_not_collide_with_company_settings():
    """IntentType (wizard) — após .lower() — não pode cair no conjunto que
    desviaria o turno para o agente company_settings."""
    from app.domains.ai.services.intent_classifier import IntentType

    values = {member.value for member in IntentType}
    lowered = {v.lower() for v in values}
    overlap = lowered & COMPANY_SETTINGS_LOWERCASE
    assert not overlap, (
        f"IntentType (basic/wizard) NÃO deve emitir valores que, após "
        f".strip().lower(), entrem em _COMPANY_SETTINGS_INTENTS. "
        f"Colisões encontradas: {overlap}"
    )

    expected = {"DATA_INPUT", "QUESTION", "CORRECTION", "DEVIATION", "REUSE_VACANCY"}
    assert values == expected, (
        f"IntentType mudou: esperado {expected}, encontrado {values}. "
        f"Atualize o teste deliberadamente se a mudança foi intencional."
    )


def test_enhanced_intent_type_does_not_collide_with_company_settings():
    """EnhancedIntentType (chat geral) — após .lower() — não pode cair no
    conjunto que desviaria o turno para o agente company_settings."""
    from app.domains.ai.services.enhanced_intent_classifier import EnhancedIntentType

    values = {member.value for member in EnhancedIntentType}
    lowered = {v.lower() for v in values}
    overlap = lowered & COMPANY_SETTINGS_LOWERCASE
    assert not overlap, (
        f"EnhancedIntentType (chat) NÃO deve emitir valores que, após "
        f".strip().lower(), entrem em _COMPANY_SETTINGS_INTENTS. "
        f"Colisões encontradas: {overlap}"
    )

    expected = {
        "CREATE_JOB",
        "UPDATE_FIELD",
        "QUESTION",
        "CORRECTION",
        "NAVIGATION",
        "REUSE_VACANCY",
        "CONFIRM",
        "REJECT",
        "HELP",
        "OUT_OF_SCOPE",
    }
    assert values == expected, (
        f"EnhancedIntentType mudou: esperado {expected}, encontrado {values}. "
        f"Atualize o teste deliberadamente se a mudança foi intencional."
    )


# ──────────────────────────────────────────────────────────────────────────
# 2. (Removido em Task #821) Shims em app.shared.services foram removidos.
#    Os testes que validavam o re-export do shim canônico não fazem mais
#    sentido — os consumidores importam direto de app.domains.ai.services.
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.skip(reason="intent_classifier shims still active - used by lia_assistant, wizard, shared services")
def test_shared_services_intent_classifier_shim_removed():
    """Garantia de não-regressão: os shims legados não devem ressuscitar."""
    import importlib

    for legacy in (
        "app.shared.services.intent_classifier",
        "app.shared.services.enhanced_intent_classifier",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(legacy)


# ──────────────────────────────────────────────────────────────────────────
# 3. _COMPANY_SETTINGS_INTENTS — contrato fixo, 4 valores em lowercase
# ──────────────────────────────────────────────────────────────────────────


def test_company_settings_intents_constant_contract():
    """
    A constante `_COMPANY_SETTINGS_INTENTS` em `main_orchestrator` é
    intencional (Task #811 — severity-based delegation). Este teste
    congela seu conteúdo: se alguém adicionar/remover valores sem revisar
    `docs/audit/chat-runtime-audit.md`, o teste falha e força revisão.
    """
    from app.orchestrator.execution.main_orchestrator import _COMPANY_SETTINGS_INTENTS

    assert _COMPANY_SETTINGS_INTENTS == COMPANY_SETTINGS_LOWERCASE, (
        f"_COMPANY_SETTINGS_INTENTS mudou. Esperado: "
        f"{COMPANY_SETTINGS_LOWERCASE}. Atual: {_COMPANY_SETTINGS_INTENTS}. "
        f"Se a mudança foi intencional, atualize "
        f"docs/audit/chat-runtime-audit.md (Task #817, seção 3) e este teste."
    )

    # Defesa adicional: todos os valores devem estar em lowercase
    # (isso é o que torna a colisão com classifier impossível).
    for v in _COMPANY_SETTINGS_INTENTS:
        assert v == v.lower(), (
            f"Valor '{v}' em _COMPANY_SETTINGS_INTENTS contém maiúsculas. "
            f"Mantenha tudo em lowercase para preservar a invariante de "
            f"não-colisão com IntentType/EnhancedIntentType (uppercase)."
        )


# ──────────────────────────────────────────────────────────────────────────
# 4. Função de roteamento NÃO desvia para company_settings quando intent
#    vem do classificador LLM (cenário sem hint bloqueante)
# ──────────────────────────────────────────────────────────────────────────


def test_decide_agent_type_does_not_hijack_create_job_intent():
    """
    Cenário canônico: usuário pede 'criar vaga de DevOps'. O classificador
    devolve `CREATE_JOB`. PreConditionChecker pode até retornar hints `info`
    (ex.: benefits_catalog_empty), mas o roteamento NÃO pode desviar para
    company_settings.
    """
    from app.orchestrator.execution.main_orchestrator import _decide_agent_type_from_hints

    class _FakeHint:
        def __init__(self, type: str, severity: str = "info"):
            self.type = type
            self.severity = severity
            self.message = ""
            self.action = None
            self.metadata = {}

    info_only_hints = [
        _FakeHint("benefits_catalog_empty", severity="info"),
        _FakeHint("culture_profile_missing", severity="info"),
    ]

    agent_type, blocking, informational = _decide_agent_type_from_hints(
        info_only_hints, intent="CREATE_JOB"
    )
    assert agent_type == "orchestrator", (
        f"Intent CREATE_JOB com hints info NÃO deve desviar — esperado "
        f"'orchestrator', recebido '{agent_type}'."
    )
    assert blocking == [], "info hints não devem virar blocking"
    assert len(informational) == 2

    # Também não desvia com intent UPDATE_FIELD, QUESTION, OUT_OF_SCOPE etc.
    for intent in ("UPDATE_FIELD", "QUESTION", "OUT_OF_SCOPE", "DATA_INPUT", ""):
        a, _, _ = _decide_agent_type_from_hints(info_only_hints, intent=intent)
        assert a == "orchestrator", (
            f"Intent '{intent}' com hints info não deve desviar — recebido '{a}'."
        )


def test_decide_agent_type_routes_when_intent_explicitly_company_settings():
    """
    Único caso em que o roteamento DEVE desviar por intent: upstream (ex.:
    contexto de página /settings/*) seta ctx.intent='company_settings' —
    mesmo SEM hints.
    """
    from app.orchestrator.execution.main_orchestrator import _decide_agent_type_from_hints

    for intent in ("company_settings", "configure_company", "settings_config", "hiring_policy"):
        agent_type, _, _ = _decide_agent_type_from_hints([], intent=intent)
        assert agent_type == "company_settings", (
            f"Intent explícito '{intent}' deve desviar para company_settings"
        )

    # Case-insensitive (a função faz .lower())
    for intent in ("COMPANY_SETTINGS", "  Configure_Company  ", "Hiring_Policy"):
        agent_type, _, _ = _decide_agent_type_from_hints([], intent=intent)
        assert agent_type == "company_settings", (
            f"Intent '{intent}' (após normalização lower) deve desviar"
        )


def test_decide_agent_type_routes_on_blocking_severity():
    """Hints warning/critical de onboarding desviam mesmo sem intent."""
    from app.orchestrator.execution.main_orchestrator import _decide_agent_type_from_hints

    class _FakeHint:
        def __init__(self, type: str, severity: str):
            self.type = type
            self.severity = severity
            self.message = ""
            self.action = None
            self.metadata = {}

    blocking_hints = [_FakeHint("hiring_policy_missing", severity="warning")]
    agent_type, blocking, informational = _decide_agent_type_from_hints(
        blocking_hints, intent="CREATE_JOB"
    )
    assert agent_type == "company_settings", (
        f"Hint warning de onboarding deve desviar — recebido '{agent_type}'."
    )
    assert len(blocking) == 1
    assert informational == []


# ──────────────────────────────────────────────────────────────────────────
# 5. Enum levanta ValueError em construção com valor inválido (boundary)
# ──────────────────────────────────────────────────────────────────────────


def test_enhanced_classifier_enum_rejects_company_settings_string():
    """O enum não pode ser construído com 'company_settings'. Garantia de
    tipo no boundary entre LLM e código Python."""
    pytest.importorskip("pydantic")
    from app.domains.ai.services.enhanced_intent_classifier import (
        EnhancedIntentType,
    )

    with pytest.raises(ValueError):
        EnhancedIntentType("company_settings")
    with pytest.raises(ValueError):
        EnhancedIntentType("CONFIGURE_COMPANY")
