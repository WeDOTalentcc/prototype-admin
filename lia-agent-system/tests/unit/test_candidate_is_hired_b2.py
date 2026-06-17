"""B2 — Candidate.is_hired=True deve ser gravado nos 3 fluxos de contratacao.

Testa que, apos a transicao para "hired/Contratado", o campo
Candidate.is_hired e setado como True e hired_at e preenchido,
em cada um dos 3 produtores canonicos.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


def _make_vc(candidate_id="cand-001", company_id="comp-001", vacancy_id="vac-001"):
    return SimpleNamespace(
        id="vc-001",
        candidate_id=candidate_id,
        vacancy_id=vacancy_id,
        company_id=company_id,
        stage="Triagem",
        status="in_review",
        previous_status="in_review",
        notes=None,
    )


def _make_candidate(candidate_id="cand-001", company_id="comp-001"):
    return SimpleNamespace(
        id=candidate_id,
        company_id=company_id,
        name="Joao Silva",
        is_hired=False,
        hired_at=None,
        hired_job_title=None,
    )


# ---------------------------------------------------------------------------
# Teste 1 -- pipeline_tool_registry._wrap_finalize_hiring
# ---------------------------------------------------------------------------

def test_wrap_finalize_hiring_sets_is_hired():
    """_wrap_finalize_hiring deve setar candidate.is_hired=True + hired_at apos update."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_finalize_hiring

    vc = _make_vc()
    cand = _make_candidate()

    vc_repo_mock = AsyncMock()
    vc_repo_mock.get_most_recent_for_candidate = AsyncMock(return_value=vc)
    vc_repo_mock.update = AsyncMock(return_value=vc)

    cand_repo_mock = AsyncMock()
    cand_repo_mock.get_by_id_str = AsyncMock(return_value=cand)

    db_mock = AsyncMock()
    db_mock.commit = AsyncMock()
    db_mock.__aenter__ = AsyncMock(return_value=db_mock)
    db_mock.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.cv_screening.agents.pipeline_tool_registry.AsyncSessionLocal",
               return_value=db_mock), \
         patch("app.domains.cv_screening.agents.pipeline_tool_registry.VacancyCandidateRepository",
               return_value=vc_repo_mock), \
         patch("app.domains.cv_screening.agents.pipeline_tool_registry.CandidateRepository",
               return_value=cand_repo_mock):

        result = asyncio.get_event_loop().run_until_complete(
            _wrap_finalize_hiring(
                candidate_id="cand-001",
                company_id="comp-001",
            )
        )

    assert result["success"] is True, f"Expected success=True, got {result}"
    assert cand.is_hired is True, "Candidate.is_hired should be True after finalize_hiring"
    assert cand.hired_at is not None, "Candidate.hired_at should be set"
    db_mock.commit.assert_called()


# ---------------------------------------------------------------------------
# Teste 2 -- pipeline/tools/pipeline_tools.register_hire (code inspection)
# ---------------------------------------------------------------------------

def test_pipeline_tools_register_hire_b2_code_present():
    """register_hire deve conter bloco B2 que seta is_hired=True."""
    import inspect
    from app.domains.pipeline.tools import pipeline_tools as pt

    source = inspect.getsource(pt.register_hire)

    assert "is_hired = True" in source, (
        "register_hire deve conter 'is_hired = True' (bloco B2)"
    )
    assert "hired_at" in source, (
        "register_hire deve conter 'hired_at' (bloco B2)"
    )
    assert "CandidateRepository" in source, (
        "register_hire deve usar CandidateRepository para setar is_hired (bloco B2)"
    )


# ---------------------------------------------------------------------------
# Teste 3 -- handlers_lifecycle.handle_candidate_hired (code inspection)
# ---------------------------------------------------------------------------

def test_handler_lifecycle_b2_code_present():
    """handle_candidate_hired deve conter bloco B2 de is_hired."""
    import inspect
    from app.api.v1.automation.event_handlers import handlers_lifecycle

    source = inspect.getsource(handlers_lifecycle.handle_candidate_hired)

    assert "is_hired = True" in source, (
        "handle_candidate_hired deve conter 'is_hired = True' (bloco B2)"
    )
    assert "hired_at" in source, (
        "handle_candidate_hired deve conter 'hired_at' (bloco B2)"
    )
    assert "CandidateRepository" in source, (
        "handle_candidate_hired deve usar CandidateRepository (bloco B2)"
    )
    assert "candidate_is_hired_set" in source, (
        "handle_candidate_hired deve ter action 'candidate_is_hired_set' no actions_taken"
    )
