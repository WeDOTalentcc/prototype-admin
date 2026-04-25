"""Tests for severity- + intent-based delegation in MainOrchestrator (task-811).

Cobertura dos quatro cenários definidos no plano da task:

  (a) pedido + hints só `info`              → mantém orchestrator
  (b) pedido + hint `warning|critical`      → delega para company_settings
  (c) intent explícito de configuração      → delega (independente de hints)
  (d) sem hints e sem intent                → comportamento atual preservado

Os testes batem direto na função pura `_decide_agent_type_from_hints`,
extraída do orquestrador justamente para deixar essa decisão testável sem
mockar o `PreConditionChecker`, o `LLMService` e o `agentic_loop`.
"""
from __future__ import annotations

import pytest

from app.orchestrator.main_orchestrator import (
    _BLOCKING_HINT_SEVERITIES,
    _COMPANY_SETTINGS_INTENTS,
    _ONBOARDING_HINT_TYPES,
    _decide_agent_type_from_hints,
)
from app.orchestrator.precondition_checker import ProactiveHint


def _hint(type_: str, severity: str) -> ProactiveHint:
    return ProactiveHint(type=type_, message=f"hint {type_}", severity=severity)


# ─────────────────────────────────────────────────────────────────────────────
# Sanity checks on the rule sets themselves
# ─────────────────────────────────────────────────────────────────────────────


def test_blocking_severities_contains_warning_and_critical():
    assert "warning" in _BLOCKING_HINT_SEVERITIES
    assert "critical" in _BLOCKING_HINT_SEVERITIES
    assert "info" not in _BLOCKING_HINT_SEVERITIES


def test_onboarding_hint_types_match_precondition_checker():
    """Os 6 tipos cobertos batem com o que `PreConditionChecker` emite."""
    assert _ONBOARDING_HINT_TYPES == frozenset({
        "missing_company_id",
        "incomplete_company_profile",
        "company_website_missing",
        "culture_profile_missing",
        "benefits_catalog_empty",
        "hiring_policy_missing",
    })


# ─────────────────────────────────────────────────────────────────────────────
# (d) Sem hints → orchestrator
# ─────────────────────────────────────────────────────────────────────────────


def test_no_hints_keeps_orchestrator():
    agent_type, blocking, informational = _decide_agent_type_from_hints([])
    assert agent_type == "orchestrator"
    assert blocking == []
    assert informational == []


# ─────────────────────────────────────────────────────────────────────────────
# (a) Apenas hints info → orchestrator
# ─────────────────────────────────────────────────────────────────────────────


def test_info_only_hints_keep_orchestrator():
    """Bug original: 3 hints info disparavam delegação indevida.

    `benefits_catalog_empty`, `culture_profile_missing` e
    `hiring_policy_missing` são todos emitidos como `info` pelo
    `PreConditionChecker`. Antes da correção, qualquer um deles trocava o
    `_agent_type` para `company_settings` mesmo quando o usuário pediu para
    criar uma vaga.
    """
    hints = [
        _hint("benefits_catalog_empty", "info"),
        _hint("culture_profile_missing", "info"),
        _hint("hiring_policy_missing", "info"),
    ]
    agent_type, blocking, informational = _decide_agent_type_from_hints(hints)
    assert agent_type == "orchestrator", (
        "Hints info nunca devem desviar a intenção primária — eles viram "
        "sugestão proativa anexada ao prompt."
    )
    assert blocking == []
    assert {h.type for h in informational} == {
        "benefits_catalog_empty",
        "culture_profile_missing",
        "hiring_policy_missing",
    }


def test_incomplete_company_profile_info_keeps_orchestrator():
    """`incomplete_company_profile` é info por padrão → não delega."""
    hints = [_hint("incomplete_company_profile", "info")]
    agent_type, blocking, informational = _decide_agent_type_from_hints(hints)
    assert agent_type == "orchestrator"
    assert blocking == []
    assert len(informational) == 1


def test_company_website_missing_info_keeps_orchestrator():
    hints = [_hint("company_website_missing", "info")]
    agent_type, _, informational = _decide_agent_type_from_hints(hints)
    assert agent_type == "orchestrator"
    assert len(informational) == 1


# ─────────────────────────────────────────────────────────────────────────────
# (b) e (c) Hint bloqueante → delega
# ─────────────────────────────────────────────────────────────────────────────


def test_missing_company_id_warning_delegates():
    """`missing_company_id` é warning — sem company_id, criar vaga é
    impossível, então faz sentido desviar para configuração."""
    hints = [_hint("missing_company_id", "warning")]
    agent_type, blocking, informational = _decide_agent_type_from_hints(hints)
    assert agent_type == "company_settings"
    assert len(blocking) == 1 and blocking[0].type == "missing_company_id"
    assert informational == []


def test_critical_severity_delegates():
    """Severity `critical` também bloqueia."""
    hints = [_hint("incomplete_company_profile", "critical")]
    agent_type, blocking, _ = _decide_agent_type_from_hints(hints)
    assert agent_type == "company_settings"
    assert len(blocking) == 1


def test_mixed_blocking_and_info_delegates():
    """Quando coexistem hints bloqueantes e info, a presença de qualquer
    bloqueante delega — e os info ainda são reportados separadamente."""
    hints = [
        _hint("missing_company_id", "warning"),
        _hint("benefits_catalog_empty", "info"),
        _hint("culture_profile_missing", "info"),
    ]
    agent_type, blocking, informational = _decide_agent_type_from_hints(hints)
    assert agent_type == "company_settings"
    assert {h.type for h in blocking} == {"missing_company_id"}
    assert {h.type for h in informational} == {
        "benefits_catalog_empty",
        "culture_profile_missing",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Hints fora do escopo de onboarding nunca participam da decisão
# ─────────────────────────────────────────────────────────────────────────────


def test_non_onboarding_warning_does_not_delegate():
    """`vacancy_no_screening_questions` é warning mas NÃO está em
    `_ONBOARDING_HINT_TYPES` — esse hint é tratado em outro fluxo
    (sugestão de perguntas de triagem) e não deve trocar o agente."""
    hints = [_hint("vacancy_no_screening_questions", "warning")]
    agent_type, blocking, informational = _decide_agent_type_from_hints(hints)
    assert agent_type == "orchestrator"
    assert blocking == []
    assert informational == []


def test_non_onboarding_critical_does_not_delegate():
    hints = [_hint("candidates_missing_contact", "critical")]
    agent_type, blocking, _ = _decide_agent_type_from_hints(hints)
    assert agent_type == "orchestrator"
    assert blocking == []


# ─────────────────────────────────────────────────────────────────────────────
# Robustez: hints malformados não devem quebrar a decisão (fail-open)
# ─────────────────────────────────────────────────────────────────────────────


def test_hint_without_severity_treated_as_info():
    class BareHint:
        type = "benefits_catalog_empty"

    agent_type, blocking, informational = _decide_agent_type_from_hints([BareHint()])
    assert agent_type == "orchestrator"
    assert blocking == []
    assert len(informational) == 1


def test_hint_without_type_is_ignored():
    class TypelessHint:
        severity = "warning"

    agent_type, blocking, informational = _decide_agent_type_from_hints([TypelessHint()])
    assert agent_type == "orchestrator"
    assert blocking == []
    assert informational == []


# ─────────────────────────────────────────────────────────────────────────────
# Parametrização do cenário completo
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "hint_specs,expected_agent",
    [
        ([], "orchestrator"),
        ([("benefits_catalog_empty", "info")], "orchestrator"),
        ([("culture_profile_missing", "info")], "orchestrator"),
        ([("hiring_policy_missing", "info")], "orchestrator"),
        ([("missing_company_id", "warning")], "company_settings"),
        ([("incomplete_company_profile", "warning")], "company_settings"),
        (
            [
                ("benefits_catalog_empty", "info"),
                ("culture_profile_missing", "info"),
                ("hiring_policy_missing", "info"),
            ],
            "orchestrator",
        ),
        (
            [
                ("benefits_catalog_empty", "info"),
                ("missing_company_id", "warning"),
            ],
            "company_settings",
        ),
    ],
)
def test_severity_decision_matrix(hint_specs, expected_agent):
    hints = [_hint(t, s) for t, s in hint_specs]
    agent_type, _, _ = _decide_agent_type_from_hints(hints)
    assert agent_type == expected_agent


# ─────────────────────────────────────────────────────────────────────────────
# (c) Intent explícito de configuração da empresa → delega
# ─────────────────────────────────────────────────────────────────────────────


def test_company_settings_intents_set_is_well_formed():
    assert "company_settings" in _COMPANY_SETTINGS_INTENTS
    assert "configure_company" in _COMPANY_SETTINGS_INTENTS
    assert "settings_config" in _COMPANY_SETTINGS_INTENTS
    assert "hiring_policy" in _COMPANY_SETTINGS_INTENTS
    # Sanity: criar vaga, listar vagas, etc. NÃO devem estar no conjunto
    assert "create_job_vacancy" not in _COMPANY_SETTINGS_INTENTS
    assert "list_jobs" not in _COMPANY_SETTINGS_INTENTS
    assert "search_candidates" not in _COMPANY_SETTINGS_INTENTS


def test_intent_company_settings_delegates_without_hints():
    """Cenário (c): usuário pede explicitamente 'configurar empresa' →
    delega mesmo sem nenhum hint emitido."""
    agent_type, blocking, informational = _decide_agent_type_from_hints(
        [], intent="company_settings"
    )
    assert agent_type == "company_settings"
    assert blocking == []
    assert informational == []


def test_intent_configure_company_delegates_with_only_info_hints():
    """Cenário (c) variante: intent explícito + hints info → delega.
    Aqui a delegação vem do INTENT, não dos hints (que são só informativos)."""
    hints = [
        _hint("benefits_catalog_empty", "info"),
        _hint("hiring_policy_missing", "info"),
    ]
    agent_type, blocking, informational = _decide_agent_type_from_hints(
        hints, intent="configure_company"
    )
    assert agent_type == "company_settings"
    assert blocking == [], (
        "Quando a delegação é por intent, blocking_hints deve ficar vazio "
        "para o telemetry distinguir as duas razões de delegação."
    )
    assert {h.type for h in informational} == {
        "benefits_catalog_empty",
        "hiring_policy_missing",
    }


@pytest.mark.parametrize(
    "intent",
    ["company_settings", "configure_company", "settings_config", "hiring_policy"],
)
def test_all_company_settings_intents_delegate(intent):
    agent_type, _, _ = _decide_agent_type_from_hints([], intent=intent)
    assert agent_type == "company_settings"


@pytest.mark.parametrize(
    "intent",
    [
        "create_job_vacancy",
        "list_jobs",
        "search_candidates",
        "wsi_screening",
        "analytics",
        "",
        None,
    ],
)
def test_non_company_settings_intent_keeps_orchestrator_when_no_blocking(intent):
    """Intents NÃO relacionados a configuração + sem hints bloqueantes
    → preservam orchestrator. Cobre o caso real do bug original
    ('create_job_vacancy' + hints info)."""
    hints = [
        _hint("benefits_catalog_empty", "info"),
        _hint("culture_profile_missing", "info"),
    ]
    agent_type, blocking, informational = _decide_agent_type_from_hints(
        hints, intent=intent
    )
    assert agent_type == "orchestrator"
    assert blocking == []
    assert len(informational) == 2


def test_intent_normalization_is_case_insensitive():
    """Classifier pode devolver intent em case variado — normalizar."""
    for variant in ("Company_Settings", "COMPANY_SETTINGS", "  company_settings  "):
        agent_type, _, _ = _decide_agent_type_from_hints([], intent=variant)
        assert agent_type == "company_settings", f"Failed for variant {variant!r}"


def test_blocking_hint_wins_over_non_settings_intent():
    """Mesmo com intent não-relacionado a configuração, hint warning ainda delega."""
    hints = [_hint("missing_company_id", "warning")]
    agent_type, blocking, _ = _decide_agent_type_from_hints(
        hints, intent="create_job_vacancy"
    )
    assert agent_type == "company_settings"
    assert len(blocking) == 1
    assert blocking[0].type == "missing_company_id"
