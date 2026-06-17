"""
F4 (AUDIT 2026-04) — FairnessGuard no InterviewGraph (paridade WSI).

Valida que ``InterviewGraph`` aplica ``FairnessGuard.check()`` sobre o texto
candidate-bound em CADA nó relevante (saudação, perguntas, follow-ups,
encerramento) com política BLOCK + REGENERATE (1 retry) +
``audit_service.log_decision`` no caminho de bloqueio.

Acceptance criteria do task TA:
  (a) ``FairnessGuard.check()`` é chamado nos nós (via ``check_fairness``
      middleware que internamente usa ``FairnessGuard``).
  (b) bloqueio impede envio (mensagem original substituída por fallback).
  (c) audit registrado com ``decision="block"``,
      ``criteria_used=["fairness_guard"]``, ``agent_name="interview_graph"``.
  (d) regeneração tenta uma vez antes de cair em fallback seguro.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import importlib

ig_module = importlib.import_module(
    "app.domains.interview_scheduling.agents.interview_graph"
)


# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------


def _make_check_fairness_stub(call_log: list[str], block_attempts: int = 1):
    """Cria um stub de ``check_fairness`` que retorna warnings nas primeiras
    ``block_attempts`` chamadas e limpo a partir daí.
    """
    counter = {"n": 0}

    def _stub(texts, context: str = "", company_id: str = "", raise_on_block: bool = False):
        counter["n"] += 1
        call_log.append(context)
        out = MagicMock()
        if counter["n"] <= block_attempts:
            out.has_warnings = True
            out.is_blocked = False
            out.warnings = ["L2: 'energia jovem' pode ser proxy etário."]
            blocked_result = MagicMock()
            blocked_result.blocked_terms = ["energia jovem"]
            out.blocked_result = blocked_result
        else:
            out.has_warnings = False
            out.is_blocked = False
            out.warnings = []
            out.blocked_result = None
        return out

    return _stub, counter


# ---------------------------------------------------------------------------
# Testes do helper canônico (_fairness_check_and_regenerate)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fairness_helper_passa_quando_mensagem_esta_limpa():
    call_log: list[str] = []
    stub, counter = _make_check_fairness_stub(call_log, block_attempts=0)

    audit_mock = AsyncMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness", side_effect=stub
    ), patch(
        "app.shared.compliance.audit_service.audit_service.log_decision", audit_mock
    ):
        msg, blocked, warnings = await ig_module._fairness_check_and_regenerate(
            message="Sua entrevista foi agendada para amanhã.",
            node_name="interview_response_planner",
            session_id="sess-1",
            company_id="comp-1",
            candidate_id="cand-1",
            job_id="job-1",
        )

    assert msg == "Sua entrevista foi agendada para amanhã."
    assert blocked is False
    assert warnings == []
    assert counter["n"] == 1
    audit_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fairness_helper_regenera_uma_vez_e_passa():
    """Acceptance (d): regeneração tenta UMA vez antes de cair em fallback."""
    call_log: list[str] = []
    # 1 bloqueio na primeira tentativa, retry passa.
    stub, counter = _make_check_fairness_stub(call_log, block_attempts=1)
    audit_mock = AsyncMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness", side_effect=stub
    ), patch(
        "app.shared.compliance.audit_service.audit_service.log_decision", audit_mock
    ):
        msg, blocked, warnings = await ig_module._fairness_check_and_regenerate(
            message="Buscamos energia jovem para o time.",
            node_name="interview_response_planner",
            session_id="sess-1",
            company_id="comp-1",
            candidate_id="cand-1",
            job_id="job-1",
        )

    # Houve regeneração: termo bloqueado removido; check chamado 2x (orig + retry).
    assert counter["n"] == 2
    assert "[REMOVIDO]" in msg or "energia jovem" not in msg
    assert blocked is False  # retry passou — não caiu em fallback
    # Audit é chamado pois houve warnings na origem.
    audit_mock.assert_called_once()
    kwargs = audit_mock.call_args.kwargs
    assert kwargs["agent_name"] == "interview_graph"
    assert kwargs["decision"] == "block"
    assert kwargs["criteria_used"] == ["fairness_guard"]


@pytest.mark.asyncio
async def test_fairness_helper_cai_em_fallback_quando_retry_falha():
    """Acceptance (b)+(d): bloqueio impede envio quando retry também falha."""
    call_log: list[str] = []
    # Bloqueia na primeira E na segunda chamada → fallback.
    stub, counter = _make_check_fairness_stub(call_log, block_attempts=99)
    audit_mock = AsyncMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness", side_effect=stub
    ), patch(
        "app.shared.compliance.audit_service.audit_service.log_decision", audit_mock
    ):
        msg, blocked, warnings = await ig_module._fairness_check_and_regenerate(
            message="Buscamos energia jovem para o time.",
            node_name="interview_response_planner",
            session_id="sess-1",
            company_id="comp-1",
            candidate_id="cand-1",
            job_id="job-1",
        )

    assert counter["n"] == 2  # 1 original + 1 retry — não tenta uma terceira vez
    assert msg == ig_module._FAIRNESS_BLOCK_FALLBACK_MESSAGE
    assert blocked is True
    assert warnings  # warnings preservadas para observabilidade

    # Acceptance (c): audit registrado com a forma canônica.
    audit_mock.assert_called_once()
    kwargs = audit_mock.call_args.kwargs
    assert kwargs["agent_name"] == "interview_graph"
    assert kwargs["decision"] == "block"
    assert kwargs["criteria_used"] == ["fairness_guard"]
    assert kwargs["candidate_id"] == "cand-1"
    assert kwargs["job_vacancy_id"] == "job-1"
    assert kwargs["human_review_required"] is True


@pytest.mark.asyncio
async def test_fairness_helper_noop_em_mensagem_vazia():
    audit_mock = AsyncMock()
    fg_mock = MagicMock()
    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness", fg_mock
    ), patch(
        "app.shared.compliance.audit_service.audit_service.log_decision", audit_mock
    ):
        msg, blocked, warnings = await ig_module._fairness_check_and_regenerate(
            message="",
            node_name="interview_response_planner",
            session_id=None,
            company_id=None,
            candidate_id=None,
            job_id=None,
        )

    assert msg == ""
    assert blocked is False
    assert warnings == []
    fg_mock.assert_not_called()
    audit_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Testes do wrapper de nó
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wrap_node_chama_fairness_e_substitui_mensagem_quando_bloqueada():
    """Acceptance (a)+(b): wrapper invoca FG e substitui msg por fallback."""

    async def _fake_node(state):
        wd = dict(state.get("workflow_data") or {})
        wd["response_data"] = {"message": "Buscamos energia jovem para o time."}
        return {**state, "workflow_data": wd}

    wrapped = ig_module._wrap_node_with_fairness(
        _fake_node, "interview_response_planner"
    )

    call_log: list[str] = []
    stub, counter = _make_check_fairness_stub(call_log, block_attempts=99)
    audit_mock = AsyncMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness", side_effect=stub
    ), patch(
        "app.shared.compliance.audit_service.audit_service.log_decision", audit_mock
    ):
        result = await wrapped({
            "session_id": "s1",
            "company_id": "c1",
            "candidate_id": "cand-1",
            "job_id": "job-1",
            "workflow_data": {},
        })

    rd = result["workflow_data"]["response_data"]
    assert rd["message"] == ig_module._FAIRNESS_BLOCK_FALLBACK_MESSAGE
    assert rd.get("fairness_blocked") is True
    assert rd.get("fairness_warnings")
    # Acceptance (a): FG chamado (orig + retry)
    assert counter["n"] == 2
    # Acceptance (c): audit chamado
    audit_mock.assert_called_once()
    assert "interview_graph::interview_response_planner" in call_log[0]


@pytest.mark.asyncio
async def test_wrap_node_passa_quando_mensagem_limpa():
    async def _fake_node(state):
        wd = dict(state.get("workflow_data") or {})
        wd["response_data"] = {"message": "Sua entrevista está confirmada."}
        return {**state, "workflow_data": wd}

    wrapped = ig_module._wrap_node_with_fairness(
        _fake_node, "interview_response_planner"
    )
    call_log: list[str] = []
    stub, counter = _make_check_fairness_stub(call_log, block_attempts=0)
    audit_mock = AsyncMock()

    with patch(
        "app.shared.compliance.fairness_guard_middleware.check_fairness", side_effect=stub
    ), patch(
        "app.shared.compliance.audit_service.audit_service.log_decision", audit_mock
    ):
        result = await wrapped({
            "session_id": "s1",
            "company_id": "c1",
            "candidate_id": None,
            "job_id": None,
            "workflow_data": {},
        })

    rd = result["workflow_data"]["response_data"]
    assert rd["message"] == "Sua entrevista está confirmada."
    assert "fairness_blocked" not in rd
    assert counter["n"] == 1
    audit_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Smoke: o builder do grafo registra os nós com wrapper FG
# ---------------------------------------------------------------------------


def test_guarded_nodes_cobrem_geradores_de_texto_candidate_bound():
    """
    Acceptance: ``grep -c "FairnessGuard" interview_graph.py > 0`` em todos
    os nós relevantes — garantido pela tupla ``_FAIRNESS_GUARDED_NODES``,
    que define a fonte canônica dos nós cobertos.
    """
    # Os 4 nós que escrevem ``response_data`` (incluindo coleta, validação,
    # execução do agendamento e planejamento de resposta) estão cobertos.
    assert "interview_response_planner" in ig_module._FAIRNESS_GUARDED_NODES
    assert "interview_details_collector" in ig_module._FAIRNESS_GUARDED_NODES
    assert "interview_scheduler_executor" in ig_module._FAIRNESS_GUARDED_NODES
    assert "interview_validator" in ig_module._FAIRNESS_GUARDED_NODES


def test_no_swallowing_de_erros_amplo_no_helper():
    """O helper deve usar ``except Exception as exc`` apenas com log debug
    (narrow + relog), nunca ``except: pass`` engolindo silenciosamente.
    """
    import inspect

    src = inspect.getsource(ig_module._fairness_check_and_regenerate)
    # Não pode ter um `except: pass` solto.
    assert "except:\n        pass" not in src
    assert "except Exception:\n        pass" not in src
    # Toda captura precisa estar relogada (debug/warning/error).
    assert src.count("except Exception") <= src.count("logger.debug") + src.count("logger.warning")


# ---------------------------------------------------------------------------
# Regression tests F4 review-fix 2026-04-19 — fail-CLOSED on guard error.
# ---------------------------------------------------------------------------


def test_helper_fail_closed_quando_check_fairness_import_falha(monkeypatch):
    """Se `check_fairness` falha ao importar, o helper DEVE devolver a
    mensagem de fallback segura + blocked=True. Conteúdo candidate-bound
    NUNCA pode escapar sem checagem por erro interno do gate.
    """
    import sys
    import asyncio as _asyncio

    # Remove o módulo do cache e injeta um substituto que estoura ao acessar
    # o atributo `check_fairness` — simula falha de import dentro do helper.
    monkeypatch.setitem(
        sys.modules,
        "app.shared.compliance.fairness_guard_middleware",
        None,  # `import ... from None` levanta TypeError no caminho do try/except
    )

    msg, blocked, warns = _asyncio.run(
        ig_module._fairness_check_and_regenerate(
            message="Mensagem candidate-bound qualquer.",
            node_name="test_fail_closed",
            session_id="s",
            company_id="c",
            candidate_id="cand",
            job_id="job",
        )
    )
    assert msg == ig_module._FAIRNESS_BLOCK_FALLBACK_MESSAGE
    assert blocked is True
    assert any("fairness_guard_unavailable" in w for w in warns), warns


def test_outbox_callback_nao_usa_shield_em_create_task():
    """Regressão: o callback NÃO pode envolver a coroutine em `asyncio.shield`
    antes de `create_task` — `shield` devolve Future e `create_task` exige
    coroutine, levantando TypeError silencioso (engolido pelo except defensivo).
    """
    import inspect
    from app.shared.observability import usage_tracking_callback as cb_mod

    src = inspect.getsource(cb_mod.build_usage_callback)
    assert "create_task(asyncio.shield(" not in src, (
        "Regressão F4/TC: shield+create_task levanta TypeError silencioso. "
        "Use loop.create_task(_enqueue()) — a robustez vem do outbox durável."
    )
