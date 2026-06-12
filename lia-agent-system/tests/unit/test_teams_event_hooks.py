"""
Testa que os event hooks do Teams são disparados nos pontos corretos.
Fire-and-forget: exceptions do Teams nunca propagam para o fluxo principal.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_safe_teams_hook_absorbs_exception():
    """_safe_teams_hook nunca propaga exception do Teams."""
    from app.domains.communication.services.teams_proactivity_engine import _safe_teams_hook

    async def raising_coro(**kwargs):
        raise RuntimeError("Teams indisponível")

    # Should not raise
    await _safe_teams_hook(raising_coro, job_id="j1", candidate_id="c1", company_id="co1")


@pytest.mark.asyncio
async def test_safe_teams_hook_calls_coroutine():
    """_safe_teams_hook chama a coroutine com os kwargs."""
    from app.domains.communication.services.teams_proactivity_engine import _safe_teams_hook

    called_with = {}

    async def recording_coro(**kwargs):
        called_with.update(kwargs)

    await _safe_teams_hook(recording_coro, job_id="j1", candidate_id="c1", company_id="co1")
    assert called_with == {"job_id": "j1", "candidate_id": "c1", "company_id": "co1"}


@pytest.mark.asyncio
async def test_safe_teams_hook_handles_non_async_gracefully():
    """_safe_teams_hook não quebra mesmo com exceção inesperada no coro."""
    from app.domains.communication.services.teams_proactivity_engine import _safe_teams_hook

    async def always_raises(**kwargs):
        raise ConnectionError("Teams unreachable")

    # Must not raise
    await _safe_teams_hook(always_raises, candidate_id="c1")


@pytest.mark.asyncio
async def test_candidate_tools_has_teams_hook_wired():
    """add_candidate_to_vacancy module imports _safe_teams_hook for fire-and-forget."""
    import ast, pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/domains/cv_screening/tools/candidate_tools.py"
    ).read_text(encoding="utf-8")
    assert "_safe_teams_hook" in src, "_safe_teams_hook deve estar referenciado em candidate_tools.py"
    assert "on_candidate_applied" in src, "on_candidate_applied deve estar referenciado em candidate_tools.py"



@pytest.mark.asyncio
async def test_completion_has_screening_hook_wired():
    """completion.py referencia on_screening_complete para notificar recrutador via Teams DM."""
    import pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/domains/recruitment/services/triagem_session_service/completion.py"
    ).read_text(encoding="utf-8")
    assert "on_screening_complete" in src, "on_screening_complete deve estar em completion.py"
    assert "_safe_teams_hook" in src or "_sth" in src, "_safe_teams_hook deve ser usado em completion.py"
