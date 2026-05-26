"""Tests integration de migração Tipo E (PR-6): _emit_*_gate_audit helpers
em graph.py usam emit_audit_fire_and_forget() canonical em vez do antipattern
get_event_loop + asyncio.run fallback redundante.

Categoria Tipo E descoberta pelo Agent A durante validação Onda 2.
Sites migrados:
- _emit_jd_gate_audit (graph.py ~3491)
- _emit_competency_gate_audit (graph.py ~3770)
- _emit_wsi_questions_gate_audit (graph.py ~4254)
- _emit_review_gate_audit (graph.py ~4888)

Regression test scenario: helper executado dentro de running loop (sync node
no LangGraph SEMPRE roda dentro de loop) não levanta RuntimeError; audit
log_decision é chamado fire-and-forget; helper retorna sem bloquear.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.job_creation.graph import (
    _emit_competency_gate_audit,
    _emit_jd_gate_audit,
    _emit_review_gate_audit,
    _emit_wsi_questions_gate_audit,
)


def _fake_output(intent="approve", extracted_data=None):
    """Build minimal GateOutput-like object usado pelos helpers."""
    return SimpleNamespace(
        intent=intent,
        confidence=0.95,
        conversational_reply="Ok, prosseguindo.",
        extracted_data=extracted_data or {},
    )


def _fake_state():
    return {
        "workspace_id": "11111111-1111-1111-1111-111111111111",
        "company_id": "11111111-1111-1111-1111-111111111111",
        "session_id": "session-pr6",
        "jd_approved": False,
        "gate_last_intent": None,
        "jd_quality_score": 0.0,
        "jd_enriched": {},
    }


@pytest.mark.asyncio
async def test_emit_jd_gate_audit_fires_without_runtime_error():
    """PR-6: _emit_jd_gate_audit dentro de loop ativo não quebra (era
    asyncio.run em loop ativo → RuntimeError em Py 3.12+)."""
    mock_log = AsyncMock()
    with patch(
        "app.shared.compliance.audit_service.audit_service",
        MagicMock(log_decision=mock_log),
    ):
        # Não deve raise
        _emit_jd_gate_audit(_fake_state(), "Aprovado!", _fake_output("approve"))
        # Yield p/ task fire-and-forget rodar
        for _ in range(3):
            await asyncio.sleep(0)
    assert mock_log.await_count == 1, (
        "audit_service.log_decision deveria ter sido awaited via task"
    )
    kwargs = mock_log.await_args.kwargs
    assert kwargs["agent_name"] == "wizard_jd_gate_classifier"
    assert kwargs["action"] == "jd_gate_classify"


@pytest.mark.asyncio
async def test_emit_competency_gate_audit_fires_without_runtime_error():
    """PR-6: _emit_competency_gate_audit migration regression."""
    mock_log = AsyncMock()
    state = _fake_state()
    # competency helper exige campos extras de competency
    state["screening_mode"] = "compact"
    state["competency_approved"] = False
    with patch(
        "app.shared.compliance.audit_service.audit_service",
        MagicMock(log_decision=mock_log),
    ):
        _emit_competency_gate_audit(state, "compact", _fake_output("select_compact"))
        for _ in range(3):
            await asyncio.sleep(0)
    assert mock_log.await_count == 1
    assert mock_log.await_args.kwargs["agent_name"] == (
        "wizard_competency_gate_classifier"
    )


@pytest.mark.asyncio
async def test_emit_wsi_questions_gate_audit_fires_without_runtime_error():
    """PR-6: _emit_wsi_questions_gate_audit migration regression."""
    mock_log = AsyncMock()
    state = _fake_state()
    state["wsi_questions"] = []
    state["questions_approved"] = False
    with patch(
        "app.shared.compliance.audit_service.audit_service",
        MagicMock(log_decision=mock_log),
    ):
        _emit_wsi_questions_gate_audit(
            state, "ok", _fake_output("approve", extracted_data={"foo": "bar"})
        )
        for _ in range(3):
            await asyncio.sleep(0)
    assert mock_log.await_count == 1
    assert mock_log.await_args.kwargs["agent_name"] == (
        "wizard_wsi_questions_gate_classifier"
    )


@pytest.mark.asyncio
async def test_emit_review_gate_audit_fires_without_runtime_error():
    """PR-6: _emit_review_gate_audit migration regression.

    Confirmation method é forwarded em criteria_used (SOX/EU AI Act trail).
    """
    mock_log = AsyncMock()
    state = _fake_state()
    state["review_approved"] = False
    with patch(
        "app.shared.compliance.audit_service.audit_service",
        MagicMock(log_decision=mock_log),
    ):
        _emit_review_gate_audit(
            state,
            "publicar",
            _fake_output("approve_publish"),
            confirmation_method="button",
        )
        for _ in range(3):
            await asyncio.sleep(0)
    assert mock_log.await_count == 1
    kwargs = mock_log.await_args.kwargs
    assert kwargs["agent_name"] == "wizard_review_gate_classifier"
    assert any(
        "confirmation_method:button" in c for c in kwargs.get("criteria_used", [])
    ), "confirmation_method deve aparecer em criteria_used (SOX trail)"


@pytest.mark.asyncio
async def test_emit_audit_no_company_id_short_circuits():
    """Helpers retornam early sem chamar audit quando company_id está vazio
    (defesa multi-tenancy)."""
    mock_log = AsyncMock()
    state = _fake_state()
    state["workspace_id"] = ""
    state["company_id"] = ""
    with patch(
        "app.shared.compliance.audit_service.audit_service",
        MagicMock(log_decision=mock_log),
    ):
        _emit_jd_gate_audit(state, "x", _fake_output())
        _emit_competency_gate_audit(state, "x", _fake_output())
        _emit_wsi_questions_gate_audit(state, "x", _fake_output())
        _emit_review_gate_audit(state, "x", _fake_output())
        for _ in range(3):
            await asyncio.sleep(0)
    assert mock_log.await_count == 0, (
        "Sem company_id, audit não deveria ter sido emitido"
    )
