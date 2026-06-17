"""PR3 (Task #1003) — Unit tests for the recursive FairnessGuard helper.

Cobre os 4 anti-padrões exigidos pelo `Done looks like` da task #1003:
  (a) string CURTA com bias direto (bypass legado `len > 10`);
  (b) list[str] com bias em um item (bypass legado: filtrava só str topo);
  (c) dict aninhado com bias num valor folha;
  (d) lista de dicts (formato `import_benefits_from_data`).

Bonus PR3 hardening (vindo do code review):
  (e) bias na CHAVE de um dict (default_salary_ranges = {"Junior Homem": "5k"});
  (f) fail-CLOSED quando o payload estoura `_MAX_DEPTH` ou `_MAX_NODES`.

Não depende de DB nem de LLM — usa um FakeGuard determinístico para garantir
que estamos testando o WALK, não o detector.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import logging

from app.shared.compliance import fairness_recursive
from app.shared.compliance.fairness_recursive import (
    RecursiveFairnessResult,
    check_payload_limits,
    validate_fairness_recursive,
)


class _FakeGuard:
    """FairnessGuard fake: bloqueia qualquer string que contenha um dos
    `triggers` (case-insensitive) e devolve metadata estável.
    """

    def __init__(self, triggers: tuple[str, ...] = ("jovens", "homens", "homem")):
        self.triggers = tuple(t.lower() for t in triggers)
        self.calls: list[str] = []

    def check(self, text: str) -> SimpleNamespace:
        self.calls.append(text)
        lower = text.lower()
        hit = next((t for t in self.triggers if t in lower), None)
        return SimpleNamespace(
            is_blocked=hit is not None,
            blocked_terms=[hit] if hit else [],
            category="idade" if hit == "jovens" else ("gênero" if hit else None),
            educational_message=(
                "Evite restringir por demografia."
                if hit
                else None
            ),
        )


# ─── (a) string CURTA com bias ──────────────────────────────────────────


def test_short_biased_string_is_blocked():
    """Bypass legado: o caller filtrava `len > 10`. 'só homens' tem 9 chars
    e PRECISA ser bloqueada."""
    guard = _FakeGuard()
    result = validate_fairness_recursive("só homens", guard=guard, root_label="value")
    assert result.is_blocked is True
    assert result.offending_field == "value"
    assert result.offending_signal == "só homens"
    assert result.category == "gênero"
    assert "homens" in (result.blocked_terms or [])


# ─── (b) list[str] com bias em um item ─────────────────────────────────


def test_list_of_strings_blocks_first_offender():
    """Bypass legado: listas eram completamente ignoradas (filtro pegava só
    `isinstance(value, str)`). Agora cada item da lista é varrido."""
    guard = _FakeGuard()
    payload = ["aprendizado contínuo", "diversidade", "só jovens"]
    result = validate_fairness_recursive(payload, guard=guard, root_label="dei_initiatives")
    assert result.is_blocked is True
    assert result.offending_field == "dei_initiatives[2]"
    assert result.offending_signal == "só jovens"
    assert result.category == "idade"


# ─── (c) dict aninhado com bias num valor folha ────────────────────────


def test_nested_dict_leaf_value_is_blocked():
    """Bypass legado: dicts não eram inspecionados. Agora o walk desce
    em qualquer profundidade e reporta dot-notation."""
    guard = _FakeGuard()
    payload = {
        "communication_rules": {
            "lia_tone": "tom firme",
            "auto_rejection_feedback": "feedback para jovens é dispensável",
        }
    }
    result = validate_fairness_recursive(payload, guard=guard, root_label="rules")
    assert result.is_blocked is True
    assert result.offending_field == "rules.communication_rules.auto_rejection_feedback"
    assert "jovens" in result.offending_signal


# ─── (d) lista de dicts (formato benefits) ─────────────────────────────


def test_list_of_dicts_benefits_payload_is_blocked():
    """Bypass legado: `import_benefits_from_data` NUNCA chamava o guard.
    Agora cada `{name, category, description}` é varrido."""
    guard = _FakeGuard()
    benefits = [
        {"name": "Vale-refeição", "category": "alimentação"},
        {"name": "Vale-creche", "description": "Apenas para mães solteiras com homens em casa"},
    ]
    result = validate_fairness_recursive(benefits, guard=guard, root_label="benefits")
    assert result.is_blocked is True
    # Caminho dot-notation com índice de lista + chave de dict
    assert result.offending_field == "benefits[1].description"
    assert "homens" in (result.blocked_terms or [])


# ─── (e) bias na CHAVE de um dict (hardening do code review) ──────────


def test_dict_key_with_bias_is_blocked():
    """Code review (PR3): chave de dict também é veículo de viés.
    `default_salary_ranges = {"Junior Homem": "5k"}` precisa ser vetado
    mesmo que o VALOR seja inofensivo."""
    guard = _FakeGuard()
    payload = {"default_salary_ranges": {"Junior Homem": "5000"}}
    result = validate_fairness_recursive(payload, guard=guard, root_label="culture")
    assert result.is_blocked is True
    # Caminho marca explicitamente que foi a chave que disparou.
    assert "<key:Junior Homem>" in result.offending_field
    assert result.offending_signal == "Junior Homem"


# ─── (f) fail-OPEN local em estouro de limite (Task #1010) ────────────


def test_depth_limit_fails_open_with_warning(monkeypatch, caplog):
    """Task #1010 — quando o walk recursivo estoura `_MAX_DEPTH`, o
    contrato é fail-OPEN local: retorna **não-bloqueado** (a save tool
    segue para auditoria) E emite warning estruturado para SRE. A
    rejeição preventiva por abuso é responsabilidade do
    ``check_payload_limits`` no caller."""
    monkeypatch.setattr(fairness_recursive, "_MAX_DEPTH", 3)
    guard = _FakeGuard()
    deep: Any = "valor inocente"
    for _ in range(8):
        deep = {"k": deep}
    with caplog.at_level(logging.WARNING, logger="app.shared.compliance.fairness_recursive"):
        result = validate_fairness_recursive(deep, guard=guard, root_label="root")
    assert result.is_blocked is False, "walk deve ser fail-OPEN local (Task #1010)"
    assert result.category == "fairness_validation_limit"
    assert isinstance(result.educational_message, str)
    # Warning estruturado precisa ter sido emitido — é o sinal SRE.
    assert any(
        getattr(r, "fairness_recursive_stage", None) == "recursive_walk"
        for r in caplog.records
    ), "estouro silencioso no walk: warning não emitido"


def test_node_limit_fails_open_with_warning(monkeypatch, caplog):
    """Task #1010 — mesmo contrato fail-OPEN+warn para `_MAX_NODES`."""
    monkeypatch.setattr(fairness_recursive, "_MAX_NODES", 5)
    guard = _FakeGuard()
    payload = ["a", "b", "c", "d", "e", "f", "g", "h"]
    with caplog.at_level(logging.WARNING, logger="app.shared.compliance.fairness_recursive"):
        result = validate_fairness_recursive(payload, guard=guard, root_label="big_list")
    assert result.is_blocked is False
    assert result.category == "fairness_validation_limit"
    assert any(
        getattr(r, "fairness_recursive_stage", None) == "recursive_walk"
        for r in caplog.records
    )


# ─── Sanity: payload limpo passa ───────────────────────────────────────


def test_clean_payload_passes():
    guard = _FakeGuard()
    payload = {
        "values": ["aprendizado", "transparência", "respeito"],
        "benefits": [{"name": "Vale-refeição"}, {"name": "Plano de saúde"}],
    }
    result = validate_fairness_recursive(payload, guard=guard, root_label="culture")
    assert result.is_blocked is False
    assert result.offending_field is None
    # Confirma que o walk visitou strings (smoke do percurso)
    assert any("Vale-refeição" in c for c in guard.calls)


# ─── Task #1010 — pre-check de tamanho + warning estruturado ──────────


def test_check_payload_limits_passes_for_clean_payload():
    """Payload pequeno: pre-check devolve None (sem rejeição)."""
    assert check_payload_limits(
        {"values": ["a", "b"]},
        tool_name="save_company_field",
        tenant_id="tenant-x",
    ) is None


def test_check_payload_limits_rejects_deep_payload(monkeypatch, caplog):
    """Estouro de profundidade: caller recebe rejeição 4xx-equivalente
    (`reason="payload_too_large"`) e o warning estruturado carrega
    `tool_name` + `tenant_id` para SRE rastrear abuso/bug."""
    monkeypatch.setattr(fairness_recursive, "_MAX_DEPTH", 3)

    deep: Any = "ok"
    for _ in range(8):
        deep = {"k": deep}

    with caplog.at_level(logging.WARNING, logger="app.shared.compliance.fairness_recursive"):
        result = check_payload_limits(
            deep, tool_name="save_company_section", tenant_id="tenant-abc",
        )

    assert result is not None
    assert result["success"] is False
    assert result["reason"] == "payload_too_large"
    assert result["limit_kind"] == "depth"
    assert "lotes menores" in result["message"].lower() or "menores" in result["message"].lower()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings, "esperava warning estruturado de pre_check"
    rec = warnings[-1]
    assert rec.fairness_recursive_tool == "save_company_section"
    assert rec.fairness_recursive_tenant_id == "tenant-abc"
    assert rec.fairness_recursive_stage == "pre_check"
    assert rec.fairness_recursive_limit_kind == "depth"


def test_check_payload_limits_rejects_wide_payload(monkeypatch, caplog):
    """Estouro de quantidade de nós: mesma rejeição + warning estruturado."""
    monkeypatch.setattr(fairness_recursive, "_MAX_NODES", 5)

    with caplog.at_level(logging.WARNING, logger="app.shared.compliance.fairness_recursive"):
        result = check_payload_limits(
            ["a", "b", "c", "d", "e", "f", "g", "h"],
            tool_name="import_workforce_plan",
            tenant_id="tenant-42",
        )

    assert result is not None
    assert result["limit_kind"] == "nodes"
    assert any(
        getattr(r, "fairness_recursive_tool", None) == "import_workforce_plan"
        and getattr(r, "fairness_recursive_stage", None) == "pre_check"
        for r in caplog.records
    )


def test_recursive_walk_emits_structured_warning_when_limit_hit(monkeypatch, caplog):
    """Defesa em profundidade: se um caller pular o pre-check e os limites
    estourarem dentro do walk, o warning estruturado dispara igual (com
    `stage="recursive_walk"`) — para SRE detectar o caller que esqueceu."""
    monkeypatch.setattr(fairness_recursive, "_MAX_DEPTH", 2)
    guard = _FakeGuard()

    deep: Any = "ok"
    for _ in range(6):
        deep = {"k": deep}

    with caplog.at_level(logging.WARNING, logger="app.shared.compliance.fairness_recursive"):
        result = validate_fairness_recursive(
            deep, guard=guard, root_label="root",
            tool_name="save_company_field", tenant_id="tenant-xyz",
        )

    # Task #1010 — walk é fail-OPEN local: NÃO bloqueia, mas emite warning.
    assert result.is_blocked is False
    assert result.category == "fairness_validation_limit"

    matching = [
        r for r in caplog.records
        if getattr(r, "fairness_recursive_tool", None) == "save_company_field"
        and getattr(r, "fairness_recursive_tenant_id", None) == "tenant-xyz"
        and getattr(r, "fairness_recursive_stage", None) == "recursive_walk"
    ]
    assert matching, "warning estruturado deveria ter sido emitido pelo walk"


def test_returns_dataclass_instance():
    """Contrato: o retorno SEMPRE é RecursiveFairnessResult (não None,
    não dict). Os 5 wrappers dependem disso para checar `.is_blocked`."""
    result = validate_fairness_recursive({})
    assert isinstance(result, RecursiveFairnessResult)
    assert result.is_blocked is False
