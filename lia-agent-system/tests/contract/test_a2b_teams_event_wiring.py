"""Sensor A2b: TeamsProactivityEngine wirado ao event bus de candidatos/triagem.

Antes (censo 2026-06-09): on_candidate_applied e on_screening_complete existiam
no engine mas nunca eram chamados por eventos do sistema — so via REST manual
(POST /teams/notify-new-candidate e /teams/proactive/screening-complete).
O event bus publicava "candidate_applied" e "screening.wsi.completed" mas nenhum
handler chamava o engine de Teams.

A2b (2026-06-10): adicionado handle_candidate_applied_teams registrado em
"candidate_applied" + chamada on_screening_complete dentro de
handle_screening_completed_event.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_event(event_type: str, company_id: str = "comp-123", payload: dict | None = None):
    """Cria um PlatformEvent fake compatível com os handlers."""
    from app.shared.messaging.platform_events import PlatformEvent

    return PlatformEvent(
        event_type=event_type,
        company_id=company_id,
        source_api="lia-agent-system",
        payload=payload or {},
    )


def _mock_candidate(company_id: str = "comp-123", name: str = "Ana Lima"):
    c = MagicMock()
    c.company_id = company_id
    c.name = name
    return c


def _mock_vacancy(company_id: str = "comp-123", title: str = "Dev Sênior"):
    v = MagicMock()
    v.company_id = company_id
    v.title = title
    return v


# ---------------------------------------------------------------------------
# Test 1 — handle_candidate_applied_teams: happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_applied_handler_calls_teams_engine():
    """Quando candidato se inscreve, on_candidate_applied é chamado com args corretos."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "candidate_applied",
        company_id="comp-123",
        payload={"candidate_id": "cand-1", "vacancy_id": "vac-1"},
    )

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[
        _mock_candidate("comp-123", "Ana Lima"),   # Candidate lookup
        _mock_vacancy("comp-123", "Dev Sênior"),    # JobVacancy lookup
    ])
    mock_db.close = AsyncMock()

    engine = MagicMock()
    engine.on_candidate_applied = AsyncMock(return_value=True)

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
    ):
        await handlers_mod.handle_candidate_applied_teams(event)

    engine.on_candidate_applied.assert_awaited_once()
    call_kwargs = engine.on_candidate_applied.call_args.kwargs
    assert call_kwargs["candidate_id"] == "cand-1"
    assert call_kwargs["candidate_name"] == "Ana Lima"
    assert call_kwargs["vacancy_id"] == "vac-1"
    assert call_kwargs["vacancy_title"] == "Dev Sênior"
    assert call_kwargs["company_id"] == "comp-123"


# ---------------------------------------------------------------------------
# Test 2 — tenant mismatch: candidato pertence a outra empresa
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_applied_tenant_mismatch_candidate_skipped():
    """Se candidate.company_id != event.company_id, engine NÃO é chamado."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "candidate_applied",
        company_id="comp-123",
        payload={"candidate_id": "cand-1", "vacancy_id": "vac-1"},
    )

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[
        _mock_candidate("ANOTHER-COMPANY", "Ana Lima"),  # mismatch!
        _mock_vacancy("comp-123", "Dev Sênior"),
    ])
    mock_db.close = AsyncMock()

    engine = MagicMock()
    engine.on_candidate_applied = AsyncMock()

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
    ):
        await handlers_mod.handle_candidate_applied_teams(event)

    engine.on_candidate_applied.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 3 — tenant mismatch: vaga pertence a outra empresa
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_candidate_applied_tenant_mismatch_vacancy_skipped():
    """Se vacancy.company_id != event.company_id, engine NÃO é chamado."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "candidate_applied",
        company_id="comp-123",
        payload={"candidate_id": "cand-1", "vacancy_id": "vac-1"},
    )

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[
        _mock_candidate("comp-123", "Ana Lima"),
        _mock_vacancy("ANOTHER-COMPANY", "Dev Sênior"),  # mismatch!
    ])
    mock_db.close = AsyncMock()

    engine = MagicMock()
    engine.on_candidate_applied = AsyncMock()

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
    ):
        await handlers_mod.handle_candidate_applied_teams(event)

    engine.on_candidate_applied.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 4 — handle_screening_completed_event chama on_screening_complete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_screening_completed_calls_teams_on_screening_complete():
    """handle_screening_completed_event chama teams_proactivity_engine.on_screening_complete."""
    import app.api.v1.platform_event_handlers as handlers_mod
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    event = _make_event(
        "screening.wsi.completed",
        company_id="comp-123",
        payload={
            "candidate_id": "cand-1",
            "vacancy_id": "vac-1",
            "candidate_name": "Bruno Costa",
            "job_title": "Engenheiro Backend",
            "wsi_final_score": "4.1",
            "wsi_scores": {},
            "response_scores": [],
            "seniority_level": "pleno",
        },
    )

    engine = MagicMock()
    engine.on_screening_complete = AsyncMock(return_value=True)

    # Precisamos suprimir tudo que não é o alvo do teste no handler pesado.
    # Patches mínimos necessários para o handler não explodir.
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.get = AsyncMock(return_value=None)
    mock_db.flush = AsyncMock()
    mock_db.close = AsyncMock()

    noop_validate = AsyncMock(return_value=(True, None))  # multi-tenancy passes
    noop_handle = AsyncMock()

    with (
        patch.object(handlers_mod, "_get_db", AsyncMock(return_value=mock_db)),
        patch.object(tpe_mod, "teams_proactivity_engine", engine),
        patch(
            "app.domains.automation.services.automation_handlers.validate_multi_tenancy",
            noop_validate,
        ),
        patch(
            "app.domains.automation.services.automation_handlers.handle_screening_completed",
            noop_handle,
        ),
        patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.WSI_CUTOFFS",
            {"approved_auto": 3.75, "review_min": 3.0},
        ),
        patch("app.api.v1.platform_event_handlers._create_activity", AsyncMock()),
        patch("app.api.v1.platform_event_handlers._get_vacancy_candidate", AsyncMock(return_value=None)),
        patch(
            "app.domains.cv_screening.services.wsi_feedback_generator.WSIFeedbackGenerator",
            MagicMock(return_value=MagicMock(generate=MagicMock(return_value={"plain_text": ""}))),
        ),
    ):
        await handlers_mod.handle_screening_completed_event(event)

    engine.on_screening_complete.assert_awaited_once()
    call_kwargs = engine.on_screening_complete.call_args.kwargs
    assert call_kwargs["candidate_id"] == "cand-1"
    assert call_kwargs["vacancy_id"] == "vac-1"
    assert call_kwargs["candidate_name"] == "Bruno Costa"
    assert call_kwargs["job_title"] == "Engenheiro Backend"
    assert abs(call_kwargs["match_score"] - 4.1) < 0.01
    assert call_kwargs["recommendation"] in ("approved", "review", "rejected")
    assert call_kwargs["company_id"] == "comp-123"


# ---------------------------------------------------------------------------
# Test 5 — candidate_applied registrado no event bus
# ---------------------------------------------------------------------------

def test_candidate_applied_registered_in_event_bus():
    """register_all_handlers() deve registrar 'candidate_applied' apontando para o handler A2b."""
    from app.shared.messaging.platform_events import _event_handlers, register_event_handler
    import app.api.v1.platform_event_handlers as handlers_mod

    # Limpa registro para garantir idempotência do teste.
    _event_handlers.clear()

    handlers_mod.register_all_handlers()

    assert "candidate_applied" in _event_handlers, (
        "'candidate_applied' nao registrado — A2b nao wired ao event bus"
    )
    handler_fns = _event_handlers["candidate_applied"]
    assert any(
        getattr(fn, "__name__", "") == "handle_candidate_applied_teams"
        for fn in handler_fns
    ), "handle_candidate_applied_teams nao esta na lista de handlers de 'candidate_applied'"
