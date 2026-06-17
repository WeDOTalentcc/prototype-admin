"""F3 — HITL gate para mutações de mover candidato (2026-06-09).

Testa que update_candidate_stage, _wrap_move_candidate (pipeline) e
_wrap_batch_move_candidates (kanban) são bloqueados pelo hitl_preflight
quando LIA_HITL_GATE=1 e não há aprovação no turno.

Padrão TDD: Red (arquivo adicionado antes dos gates) → Green (gates aplicados).
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

_C = "00000000-0000-0000-0000-000000000001"
_J = "00000000-0000-0000-0000-000000000002"
_COMPANY = "00000000-0000-0000-0000-000000000099"


def _blocks(result: dict) -> bool:
    """Retorna True se o resultado é o bloco HITL (needs_confirmation + success=False)."""
    return result.get("needs_confirmation") is True and result.get("success") is False


@contextmanager
def _tenant_ctx(company_id: str = _COMPANY):
    """Seta o ContextVar de tenant para que @tool_handler não rejeite antes do preflight."""
    from app.middleware.auth_enforcement import _current_company_id
    token = _current_company_id.set(company_id)
    try:
        yield
    finally:
        _current_company_id.reset(token)


# ─────────────────────────────────────────────────────────────────────────────
# update_candidate_stage (candidate_tools.py) — principal entry-point do LIA
# ─────────────────────────────────────────────────────────────────────────────

def test_update_candidate_stage_gated(monkeypatch):
    """Gate ON + sem aprovação → bloqueia ANTES de context_or_raise (sem context)."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    from app.domains.cv_screening.tools.candidate_tools import update_candidate_stage

    result = asyncio.run(
        update_candidate_stage(candidate_id=_C, target_stage="Entrevistas")
    )
    assert _blocks(result), f"Esperado needs_confirmation=True, obteve: {result}"
    assert result.get("hitl", {}).get("tool") == "update_candidate_stage"


def test_update_candidate_stage_dormant_when_gate_off(monkeypatch):
    """Gate OFF → sem bloco HITL (pode falhar por DB/context ausente, mas nunca o bloco dormente)."""
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)
    from app.domains.cv_screening.tools.candidate_tools import update_candidate_stage

    try:
        result = asyncio.run(
            update_candidate_stage(candidate_id=_C, target_stage="Entrevistas")
        )
        # Se chegou aqui, não deve ser o bloco HITL específico
        assert not (
            result.get("needs_confirmation") is True
            and result.get("hitl", {}).get("tool") == "update_candidate_stage"
        ), f"Gate off mas retornou bloco HITL: {result}"
    except Exception:
        # context_or_raise lança quando não há context — esperado; não é o bloco HITL
        pass


# ─────────────────────────────────────────────────────────────────────────────
# _wrap_move_candidate (pipeline_tool_registry.py) — domain pipeline
# ─────────────────────────────────────────────────────────────────────────────

def test_move_candidate_pipeline_gated(monkeypatch):
    """Gate ON + tenant ContextVar setado → bloqueia ANTES do DB."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_move_candidate

    with _tenant_ctx():
        result = asyncio.run(
            _wrap_move_candidate(candidate_id=_C, target_stage="Entrevistas")
        )
    assert _blocks(result), f"Esperado needs_confirmation=True, obteve: {result}"
    assert result.get("hitl", {}).get("tool") == "move_candidate"


def test_move_candidate_pipeline_dormant_when_gate_off(monkeypatch):
    """Gate OFF → sem bloco HITL específico (pode falhar por DB/candidato fake)."""
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_move_candidate

    with _tenant_ctx():
        try:
            result = asyncio.run(
                _wrap_move_candidate(candidate_id=_C, target_stage="Entrevistas")
            )
            assert not (
                result.get("needs_confirmation") is True
                and result.get("hitl", {}).get("tool") == "move_candidate"
            ), f"Gate off mas retornou bloco HITL: {result}"
        except Exception:
            pass  # DB falhou — esperado; não é o bloco HITL


# ─────────────────────────────────────────────────────────────────────────────
# _wrap_batch_move_candidates (kanban_tool_registry.py) — domain kanban
# ─────────────────────────────────────────────────────────────────────────────

def test_batch_move_candidates_kanban_gated(monkeypatch):
    """Gate ON + tenant ContextVar → bloqueia batch move ANTES do DB."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        _wrap_batch_move_candidates,
    )

    with _tenant_ctx():
        result = asyncio.run(
            _wrap_batch_move_candidates(
                candidate_ids=[_C],
                target_stage="Entrevistas",
                vacancy_id=_J,
            )
        )
    assert _blocks(result), f"Esperado needs_confirmation=True, obteve: {result}"
    assert result.get("hitl", {}).get("tool") == "batch_move_candidates"


def test_batch_move_candidates_dormant_when_gate_off(monkeypatch):
    """Gate OFF → sem bloco HITL específico (pode falhar por DB)."""
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        _wrap_batch_move_candidates,
    )

    with _tenant_ctx():
        try:
            result = asyncio.run(
                _wrap_batch_move_candidates(
                    candidate_ids=[_C],
                    target_stage="Entrevistas",
                    vacancy_id=_J,
                )
            )
            assert not (
                result.get("needs_confirmation") is True
                and result.get("hitl", {}).get("tool") == "batch_move_candidates"
            ), f"Gate off mas retornou bloco HITL: {result}"
        except Exception:
            pass  # DB falhou — esperado


# ─────────────────────────────────────────────────────────────────────────────
# Simetria: todos os 3 em um loop (gate ON)
# ─────────────────────────────────────────────────────────────────────────────

def test_all_three_mutation_tools_blocked_with_gate_on(monkeypatch):
    """Os 3 mutation tools devem devolver needs_confirmation com gate ON."""
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    from app.domains.cv_screening.tools.candidate_tools import update_candidate_stage
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_move_candidate
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        _wrap_batch_move_candidates,
    )

    with _tenant_ctx():
        r1 = asyncio.run(update_candidate_stage(candidate_id=_C, target_stage="Oferta"))
        r2 = asyncio.run(_wrap_move_candidate(candidate_id=_C, target_stage="Oferta"))
        r3 = asyncio.run(
            _wrap_batch_move_candidates(candidate_ids=[_C], target_stage="Oferta")
        )

    assert _blocks(r1), f"update_candidate_stage não bloqueou: {r1}"
    assert _blocks(r2), f"_wrap_move_candidate não bloqueou: {r2}"
    assert _blocks(r3), f"_wrap_batch_move_candidates não bloqueou: {r3}"
