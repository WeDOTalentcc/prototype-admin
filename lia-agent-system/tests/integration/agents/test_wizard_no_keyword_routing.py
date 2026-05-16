"""Task #1130 (GA) — sentinela arquitetural anti-regressão.

Garante que, com o flag ``LIA_WIZARD_LLM_GATES`` em seu default GA (ON),
TODOS os 4 stages HITL do wizard (``jd_enrichment``, ``competency``,
``wsi_questions``, ``review``) são roteados para o classifier LLM
canônico — NUNCA para os heurísticos keyword-based legados
(``"aprov"``/``"compact"``/``"refaz"``/``"manda"``).

Por que isso é crítico:
- O bug reportado no screenshot original (sessão T6 #993) reabria o
  caminho keyword brittle quando alguém adicionava um novo stage HITL
  e esquecia o early-return ``if _llm_gates_enabled(): return {...}``.
- A função ``_llm_gates_enabled()`` agora retorna ``True`` por default
  em TODOS os ambientes (graph.py:140) — qualquer regressão para
  ``return False`` quebra esta sentinela.
- ``route_after_jd``/``route_after_competency``/``route_after_wsi``/
  ``route_after_review`` em ``graph.py`` continuam existindo como
  caminho de rollback emergencial (``LIA_WIZARD_LLM_GATES=0``), mas
  ``domain.py::_route_by_stage`` JAMAIS pode atingir suas heurísticas
  quando o flag está em default.

REMOVE (junto com graph.py:125-129): 2026-09-01 — após 30 dias de
baseline pós-GA sem regressão, deletar os 4 ``route_after_*`` keyword
de ``graph.py`` + a heurística inteira pós-``return`` em
``domain.py::_route_by_stage`` (o sentinela vira "nunca aparecer
keyword no router" e a flag deixa de existir).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domains.job_creation.domain import JobCreationDomain
from app.domains.job_creation.graph import _llm_gates_enabled


# ---------------------------------------------------------------------------
# S1 — flag default = ON (GA #1130)
# ---------------------------------------------------------------------------

def test_s1_llm_gates_default_is_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """``LIA_WIZARD_LLM_GATES`` ausente do env → True (GA default)."""
    monkeypatch.delenv("LIA_WIZARD_LLM_GATES", raising=False)
    assert _llm_gates_enabled() is True, (
        "REGRESSÃO #1130: _llm_gates_enabled() deve retornar True por "
        "default em TODOS os ambientes pós-GA. Se você precisa do path "
        "legado, exporte LIA_WIZARD_LLM_GATES=0 explicitamente."
    )


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "yes", "on", "On"])
def test_s1b_llm_gates_truthy_values(raw: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIA_WIZARD_LLM_GATES", raw)
    assert _llm_gates_enabled() is True


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", "no", "off"])
def test_s1c_llm_gates_falsy_values_explicit_only(
    raw: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Caminho de rollback emergencial — preservado, mas exige opt-in explícito."""
    monkeypatch.setenv("LIA_WIZARD_LLM_GATES", raw)
    assert _llm_gates_enabled() is False


# ---------------------------------------------------------------------------
# S2 — _route_by_stage rota TODOS os 4 stages HITL para o LLM gate
# ---------------------------------------------------------------------------

LLM_GATE_ACTIONS = {
    "jd_enrichment": "gate_jd",
    "competency": "gate_competency",
    "wsi_questions": "gate_wsi_questions",
    "review": "gate_review",
}

# Mensagens que ATIVAM as heurísticas keyword legadas — se o early-return
# do LLM gate desaparecer, o router vai cair NESSAS frases e devolver
# ``approve_jd``/``set_screening_mode``/``approve_questions``/``publish_job``
# (o bug que esta sentinela impede).
KEYWORD_BAITS = {
    "jd_enrichment": ["aprovo", "aceito", "fica bom", "ok", "sim", "rejeito", "mudar"],
    "competency": ["compacto", "7 perguntas", "7q", "full", "completo", "12 perguntas"],
    "wsi_questions": ["aprovo", "ok", "sim", "regenere", "refaz", "outra"],
    "review": ["publica", "manda", "public"],
}


@pytest.fixture
def domain() -> JobCreationDomain:
    """JobCreationDomain — só exercita o router puro (_route_by_stage)."""
    return JobCreationDomain()


@pytest.mark.parametrize("stage, expected_action", LLM_GATE_ACTIONS.items())
def test_s2_default_flag_routes_to_llm_gate(
    domain: JobCreationDomain,
    stage: str,
    expected_action: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sem env override, cada stage HITL → gate LLM (não keyword)."""
    monkeypatch.delenv("LIA_WIZARD_LLM_GATES", raising=False)
    ctx = MagicMock()
    for bait in KEYWORD_BAITS[stage]:
        out = domain._route_by_stage(bait, stage, ctx)
        assert out.get("action_id") == expected_action, (
            f"REGRESSÃO #1130: stage={stage!r} com mensagem {bait!r} "
            f"deveria rotar para {expected_action!r} (LLM gate). Recebeu "
            f"{out.get('action_id')!r} — o early-return "
            "`if _llm_gates_enabled(): return {...}` foi removido ou "
            "desordenado."
        )
        assert out.get("source") == "llm_gate"


@pytest.mark.parametrize("stage", LLM_GATE_ACTIONS.keys())
def test_s2b_flag_off_falls_to_keyword_path(
    domain: JobCreationDomain,
    stage: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rollback emergencial: flag OFF → caminho legado keyword-based ativo."""
    monkeypatch.setenv("LIA_WIZARD_LLM_GATES", "0")
    ctx = MagicMock()
    bait = KEYWORD_BAITS[stage][0]
    out = domain._route_by_stage(bait, stage, ctx)
    assert out.get("action_id") != LLM_GATE_ACTIONS[stage], (
        "Caminho de rollback emergencial quebrado: flag OFF deveria "
        f"cair em heurística keyword para stage={stage!r}."
    )


# ---------------------------------------------------------------------------
# S3 — Os 4 gate_nodes canônicos existem e importam o classifier
# ---------------------------------------------------------------------------

GATE_NODES = [
    "jd_gate_node",
    "competency_gate_node",
    "wsi_questions_gate_node",
    "review_gate_node",
]


def test_s3_all_4_gate_nodes_exist_and_use_classifier() -> None:
    """Inventário canônico: 4 gate_nodes registrados em graph.py.

    Se alguém adicionar um 5º stage HITL sem migrá-lo para gate_node LLM,
    esta sentinela quebra junto com a contagem.
    """
    from app.domains.job_creation import graph as g

    missing = [name for name in GATE_NODES if not hasattr(g, name)]
    assert not missing, f"gate_nodes canônicos ausentes: {missing}"

    import inspect

    for name in GATE_NODES:
        src = inspect.getsource(getattr(g, name))
        assert "wizard_gate_classifier" in src, (
            f"{name} não importa wizard_gate_classifier — caminho LLM "
            "foi removido ou substituído por heurística keyword."
        )
        assert "_make_fallback" in src, (
            f"{name} perdeu o helper _make_fallback (classify failure "
            "deve cair em clarify-question, NUNCA em canned reply)."
        )
