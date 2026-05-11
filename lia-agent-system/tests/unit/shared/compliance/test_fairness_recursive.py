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

from app.shared.compliance import fairness_recursive
from app.shared.compliance.fairness_recursive import (
    RecursiveFairnessResult,
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


# ─── (f) fail-CLOSED em estouro de limite ──────────────────────────────


def test_depth_limit_fails_closed(monkeypatch):
    """Code review (PR3): estourar `_MAX_DEPTH` NÃO pode passar
    silenciosamente — precisa retornar bloqueado com category
    `fairness_validation_limit`."""
    # Limite minúsculo só pra forçar o caminho.
    monkeypatch.setattr(fairness_recursive, "_MAX_DEPTH", 3)
    guard = _FakeGuard()
    # Profundidade > 3
    deep: Any = "valor inocente"
    for _ in range(8):
        deep = {"k": deep}
    result = validate_fairness_recursive(deep, guard=guard, root_label="root")
    assert result.is_blocked is True, "fail-CLOSED quebrado: payload profundo passou"
    assert result.category == "fairness_validation_limit"
    assert isinstance(result.educational_message, str)


def test_node_limit_fails_closed(monkeypatch):
    """Code review (PR3): estourar `_MAX_NODES` também precisa fail-CLOSED."""
    monkeypatch.setattr(fairness_recursive, "_MAX_NODES", 5)
    guard = _FakeGuard()
    payload = ["a", "b", "c", "d", "e", "f", "g", "h"]
    result = validate_fairness_recursive(payload, guard=guard, root_label="big_list")
    assert result.is_blocked is True
    assert result.category == "fairness_validation_limit"


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


def test_returns_dataclass_instance():
    """Contrato: o retorno SEMPRE é RecursiveFairnessResult (não None,
    não dict). Os 5 wrappers dependem disso para checar `.is_blocked`."""
    result = validate_fairness_recursive({})
    assert isinstance(result, RecursiveFairnessResult)
    assert result.is_blocked is False
