"""Sensor — start_session deve ser FAIL-CLOSED quando a checagem de consent LGPD lanca (audit 2026-06-05 #13).

Antes: except -> log "prosseguindo" -> status="started" (fail-OPEN: triagem rodava sem
consent verificado). Agora: falha na verificacao => sessao BLOQUEADA.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.domains.recruitment.services.triagem_session_service import lifecycle


class _FakeSession:
    def __init__(self):
        self.status = "invited"
        self.candidate_id = "cand-1"
        self.company_id = "co-1"
        self.started_at = None
        self.voice_mode = False

    def to_dict(self):
        return {"id": "sess-1", "status": self.status}


@pytest.mark.asyncio
async def test_start_session_fail_closed_quando_consent_check_lanca():
    fake_session = _FakeSession()
    fake_repo = MagicMock()
    fake_repo.get_session_by_token = AsyncMock(return_value=fake_session)

    with patch.object(lifecycle, "TriagemSessionRepository", return_value=fake_repo), \
         patch(
            "app.domains.lgpd.services.consent_checker_service.ConsentCheckerService.check_candidate_consent",
            new=AsyncMock(side_effect=RuntimeError("consent service indisponivel")),
         ):
        result = await lifecycle.start_session(AsyncMock(), "tok-123")

    # fail-closed: retorna erro de bloqueio e NAO promove a sessao a "started"
    assert result.get("error") == "lgpd_consent_check_failed", f"esperava bloqueio, veio: {result!r}"
    assert fake_session.status == "invited", "sessao NAO pode virar 'started' quando consent nao foi verificado"
