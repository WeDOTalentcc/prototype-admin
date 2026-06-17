"""
TDD A2b: triagem_session_service/completion.py publica ScreeningCompletedEvent
no barramento Redis ao completar triagem WSI.

Cobertura:
  1. publish_platform_event chamado com ScreeningCompletedEvent
  2. payload: candidate_id, vacancy_id, wsi_final_score, candidate_name
  3. company_id vem de session.company_id (nao do payload)
  4. falha no publish e fail-soft — _trigger_post_completion retorna normalmente
  5. actions dict tem chave redis_event em sucesso
  6. sem wsi_session_id (persistencia falhou) nao publica
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── helpers ────────────────────────────────────────────────────────────────

def _make_session(**overrides):
    s = MagicMock()
    s.candidate_id = "cand-abc"
    s.job_id = "vac-xyz"
    s.company_id = "co-001"
    s.candidate_name = "Ana Lima"
    s.wsi_final_score = 8.5
    s.recommendation = "aprovado"
    s.token = "tok-001"
    s.metadata_json = {}
    s.job_title = "Engenheiro de Software"
    s.candidate_email = None  # suprime bloco de email
    s.id = "sess-001"
    s.current_block = 1
    s.company_name = "AcmeCorp"
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


def _make_db():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.get = AsyncMock(return_value=None)
    return db


_MODULE = "app.domains.recruitment.services.triagem_session_service.completion"
_EVENTS = "app.shared.messaging.platform_events"


def _std_patches():
    """Retorna lista de patches padrao para isolar _trigger_post_completion."""
    return [
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"),
        patch(f"{_MODULE}._get_event_dispatcher"),
    ]


async def _invoke(session=None, db=None):
    from app.domains.recruitment.services.triagem_session_service.completion import (
        _trigger_post_completion,
    )
    return await _trigger_post_completion(
        db=db or _make_db(),
        session=session or _make_session(),
        response_scores=[],
    )


# ── 1. publish_platform_event chamado com ScreeningCompletedEvent ──────────

@pytest.mark.asyncio
async def test_a2b_publish_called_on_success():
    with patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock) as mock_pub:
        for p in _std_patches():
            p.start()
        try:
            _get_event_dispatcher_fn = __import__(
                "app.domains.recruitment.services.triagem_session_service.completion",
                fromlist=["_get_event_dispatcher"],
            )._get_event_dispatcher
        except Exception:
            pass

        # patch dispatcher inline
        with patch(f"{_MODULE}._get_event_dispatcher") as mock_disp:
            mock_disp.return_value.on_screening_completed = AsyncMock()
            with patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None):
                with patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"):
                    actions = await _invoke()

        # cleanup
        for p in _std_patches():
            try:
                p.stop()
            except Exception:
                pass

    from app.shared.messaging.platform_events import ScreeningCompletedEvent
    assert mock_pub.called, "publish_platform_event deve ter sido chamado"
    published = mock_pub.call_args[0][0]
    assert isinstance(published, ScreeningCompletedEvent)


# ── versao limpa (sem gambiarra acima) usando context managers aninhados ──

@pytest.mark.asyncio
async def test_a2b_publish_called_clean():
    session = _make_session()

    with (
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"),
        patch(f"{_MODULE}._get_event_dispatcher") as mock_disp,
        patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock) as mock_pub,
    ):
        mock_disp.return_value.on_screening_completed = AsyncMock()
        await _invoke(session=session)

    from app.shared.messaging.platform_events import ScreeningCompletedEvent
    assert mock_pub.called
    assert isinstance(mock_pub.call_args[0][0], ScreeningCompletedEvent)


# ── 2. payload tem campos corretos ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_a2b_payload_fields():
    session = _make_session(wsi_final_score=7.3, candidate_name="Bruno Souza")

    with (
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"),
        patch(f"{_MODULE}._get_event_dispatcher") as mock_disp,
        patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock) as mock_pub,
    ):
        mock_disp.return_value.on_screening_completed = AsyncMock()
        await _invoke(session=session)

    event = mock_pub.call_args[0][0]
    assert event.payload["candidate_id"] == "cand-abc"
    assert event.payload["vacancy_id"] == "vac-xyz"
    assert event.payload["wsi_final_score"] == pytest.approx(7.3, rel=0.01)
    assert event.payload["candidate_name"] == "Bruno Souza"


# ── 3. company_id vem de session, nao do payload ───────────────────────────

@pytest.mark.asyncio
async def test_a2b_company_id_from_session():
    session = _make_session(company_id="co-tenant-X")

    with (
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"),
        patch(f"{_MODULE}._get_event_dispatcher") as mock_disp,
        patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock) as mock_pub,
    ):
        mock_disp.return_value.on_screening_completed = AsyncMock()
        await _invoke(session=session)

    event = mock_pub.call_args[0][0]
    assert event.company_id == "co-tenant-X"
    assert "company_id" not in event.payload  # nao vaza company_id no payload


# ── 4. falha no publish e fail-soft ────────────────────────────────────────

@pytest.mark.asyncio
async def test_a2b_publish_fail_soft():
    with (
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"),
        patch(f"{_MODULE}._get_event_dispatcher") as mock_disp,
        patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock) as mock_pub,
    ):
        mock_disp.return_value.on_screening_completed = AsyncMock()
        mock_pub.side_effect = ConnectionError("Redis indisponivel")
        # Nao deve levantar
        actions = await _invoke()

    assert isinstance(actions, dict)


# ── 5. actions tem redis_event em sucesso ─────────────────────────────────

@pytest.mark.asyncio
async def test_a2b_actions_redis_event_key():
    with (
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value="wsi-001"),
        patch(f"{_MODULE}._get_event_dispatcher") as mock_disp,
        patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock),
    ):
        mock_disp.return_value.on_screening_completed = AsyncMock()
        actions = await _invoke()

    assert "redis_event" in actions


# ── 6. sem wsi_session_id nao publica ─────────────────────────────────────

@pytest.mark.asyncio
async def test_a2b_no_publish_without_wsi_session_id():
    with (
        patch(f"{_MODULE}.find_job_vacancy_for_triagem", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._persist_wsi_results", new_callable=AsyncMock, return_value=None),
        patch(f"{_MODULE}._get_event_dispatcher") as mock_disp,
        patch(f"{_EVENTS}.publish_platform_event", new_callable=AsyncMock) as mock_pub,
    ):
        mock_disp.return_value.on_screening_completed = AsyncMock()
        actions = await _invoke()

    assert not mock_pub.called, "Sem wsi_session_id nao deve publicar"
