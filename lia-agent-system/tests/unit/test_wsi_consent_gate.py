"""
SEG-4 — Testes do gate de consentimento LGPD no WSI (load_context).

Cobre:
  1. Consentimento revogado → estado ERROR com LGPD_CONSENT_REVOKED
  2. Consentimento ausente (soft warning) → prossegue normalmente
  3. Consent check falha → prossegue (fail-safe, não bloqueia WSI)
  4. Estado sem candidate_id → pula o check completamente
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class ConsentResultStub:
    def __init__(self, allowed=True, reason=None, soft_warning=False):
        self.allowed = allowed
        self.reason = reason
        self.soft_warning = soft_warning


def _make_state(candidate_id: str = "cand-wsi"):
    from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewState
    return WSIInterviewState(
        session_id="sess-wsi",
        company_id="co-wsi",
        candidate_id=candidate_id,
        job_id="job-wsi",
    )


class TestWSIConsentGate:
    """Gate de consentimento no primeiro nó do WSI (load_context)."""

    @pytest.mark.asyncio
    async def test_consent_revoked_sets_error_state(self):
        """Consentimento revogado deve abortar o WSI com LGPD_CONSENT_REVOKED."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewNodes,
            WSIInterviewStage,
        )

        nodes = WSIInterviewNodes()
        state = _make_state()
        revoked = ConsentResultStub(allowed=False, reason="revoked")

        with patch("app.core.database.AsyncSessionLocal") as MockSession, \
             patch("app.services.consent_checker_service.ConsentCheckerService") as MockSvc:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            MockSession.return_value = mock_ctx
            MockSvc.return_value.check_candidate_consent = AsyncMock(return_value=revoked)

            result = await nodes.load_context(state)

        assert result.error == "LGPD_CONSENT_REVOKED"
        assert result.stage == WSIInterviewStage.ERROR

    @pytest.mark.asyncio
    async def test_consent_absent_soft_warning_continues(self):
        """Consentimento ausente (soft_warning) deve prosseguir."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewNodes,
            WSIInterviewStage,
        )

        nodes = WSIInterviewNodes()
        state = _make_state()
        absent = ConsentResultStub(allowed=True, soft_warning=True)

        with patch("app.core.database.AsyncSessionLocal") as MockSession, \
             patch("app.services.consent_checker_service.ConsentCheckerService") as MockSvc:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            MockSession.return_value = mock_ctx
            MockSvc.return_value.check_candidate_consent = AsyncMock(return_value=absent)

            result = await nodes.load_context(state)

        assert result.error != "LGPD_CONSENT_REVOKED"

    @pytest.mark.asyncio
    async def test_consent_check_failure_continues(self):
        """Falha no check de consentimento não deve bloquear o WSI (fail-safe)."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes

        nodes = WSIInterviewNodes()
        state = _make_state()

        with patch("app.core.database.AsyncSessionLocal") as MockSession:
            MockSession.side_effect = Exception("DB unavailable")

            result = await nodes.load_context(state)

        assert result.error != "LGPD_CONSENT_REVOKED"

    @pytest.mark.asyncio
    async def test_no_candidate_id_skips_consent(self):
        """Estado sem candidate_id deve pular o check (evita crash)."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewNodes,
        )

        nodes = WSIInterviewNodes()
        state = _make_state(candidate_id="")  # sem candidate_id

        with patch("app.services.consent_checker_service.ConsentCheckerService") as MockSvc:
            result = await nodes.load_context(state)
            MockSvc.assert_not_called()
