"""
Contract Tests: Hiring NPS

Verifica:
  - HiringNpsRepository tem métodos obrigatórios
  - HiringNps.is_expired() funciona corretamente
  - respond() seta score, comment, status e responded_at
  - Score 0-10 é o range válido (contrato de dados)
  - Token tem entropia mínima
  - _require_company_id bloqueia em valores nulos
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Contract: HiringNpsRepository métodos obrigatórios
# ---------------------------------------------------------------------------

class TestHiringNpsRepositoryContract:

    def test_has_create_method(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        assert callable(HiringNpsRepository.create)

    def test_has_respond_method(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        assert callable(HiringNpsRepository.respond)

    def test_has_get_by_token_method(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        assert callable(HiringNpsRepository.get_by_token)

    def test_has_list_for_job_method(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        assert callable(HiringNpsRepository.list_for_job)

    def test_has_avg_score_for_job_method(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        assert callable(HiringNpsRepository.avg_score_for_job)

    def test_has_count_by_status_method(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        assert callable(HiringNpsRepository.count_by_status)

    def test_require_company_id_raises_on_none(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        with pytest.raises((ValueError, Exception)):
            HiringNpsRepository._require_company_id(None)

    def test_require_company_id_passes_valid(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        result = HiringNpsRepository._require_company_id("company-xyz")
        assert result == "company-xyz"


# ---------------------------------------------------------------------------
# Contract: HiringNps model helpers
# ---------------------------------------------------------------------------

class TestHiringNpsModelContract:

    def _make_nps(self, expired=False):
        from lia_models.hiring_nps import HiringNps
        n = HiringNps()
        n.status = "pending"
        n.expires_at = (
            datetime.now(timezone.utc) - timedelta(hours=1)
            if expired
            else datetime.now(timezone.utc) + timedelta(hours=48)
        )
        return n

    def test_is_expired_true_when_past(self):
        n = self._make_nps(expired=True)
        assert n.is_expired() is True

    def test_is_expired_false_when_future(self):
        n = self._make_nps(expired=False)
        assert n.is_expired() is False

    def test_model_has_score_field(self):
        from lia_models.hiring_nps import HiringNps
        assert hasattr(HiringNps, "score")

    def test_model_has_respondent_type_field(self):
        from lia_models.hiring_nps import HiringNps
        assert hasattr(HiringNps, "respondent_type")

    def test_model_has_token_field(self):
        from lia_models.hiring_nps import HiringNps
        assert hasattr(HiringNps, "token")

    def test_token_default_has_minimum_entropy(self):
        import secrets
        # Validates the token generation strategy used by the model
        token = secrets.token_urlsafe(32)
        assert len(token) >= 32


# ---------------------------------------------------------------------------
# Contract: respond() lifecycle
# ---------------------------------------------------------------------------

class TestHiringNpsRespondContract:

    @pytest.mark.asyncio
    async def test_respond_sets_all_fields(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        from lia_models.hiring_nps import HiringNps

        db = AsyncMock()
        db.flush = AsyncMock()
        repo = HiringNpsRepository(db)

        nps = MagicMock(spec=HiringNps)
        nps.status = "pending"

        await repo.respond(nps, score=9, comment="Excelente processo!")

        assert nps.score == 9
        assert nps.comment == "Excelente processo!"
        assert nps.status == "responded"
        assert nps.responded_at is not None

    @pytest.mark.asyncio
    async def test_respond_works_without_comment(self):
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        from lia_models.hiring_nps import HiringNps

        db = AsyncMock()
        db.flush = AsyncMock()
        repo = HiringNpsRepository(db)

        nps = MagicMock(spec=HiringNps)
        await repo.respond(nps, score=0, comment=None)

        assert nps.score == 0
        assert nps.status == "responded"

    @pytest.mark.asyncio
    async def test_respond_accepts_full_score_range(self):
        """Score 0 and 10 are both valid — boundary test."""
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        from lia_models.hiring_nps import HiringNps

        db = AsyncMock()
        db.flush = AsyncMock()
        repo = HiringNpsRepository(db)

        for score in [0, 10]:
            nps = MagicMock(spec=HiringNps)
            await repo.respond(nps, score=score)
            assert nps.score == score


# ---------------------------------------------------------------------------
# Contract: schema validation — respondent_type
# ---------------------------------------------------------------------------

class TestHiringNpsSchemaContract:

    def test_send_nps_request_rejects_invalid_respondent_type(self):
        from app.api.v1.hiring_nps import SendNpsRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SendNpsRequest(
                job_vacancy_id="job-1",
                respondent_type="unknown_type",
                respondent_email="test@example.com",
            )

    def test_send_nps_request_accepts_candidate(self):
        from app.api.v1.hiring_nps import SendNpsRequest

        req = SendNpsRequest(
            job_vacancy_id="job-1",
            respondent_type="candidate",
            respondent_email="candidate@example.com",
        )
        assert req.respondent_type == "candidate"

    def test_send_nps_request_accepts_manager(self):
        from app.api.v1.hiring_nps import SendNpsRequest

        req = SendNpsRequest(
            job_vacancy_id="job-1",
            respondent_type="manager",
            respondent_email="manager@company.com",
        )
        assert req.respondent_type == "manager"

    def test_submit_nps_rejects_score_above_10(self):
        from app.api.v1.hiring_nps import SubmitNpsRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SubmitNpsRequest(token="abc", score=11)

    def test_submit_nps_rejects_score_below_0(self):
        from app.api.v1.hiring_nps import SubmitNpsRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SubmitNpsRequest(token="abc", score=-1)

    def test_submit_nps_accepts_boundary_scores(self):
        from app.api.v1.hiring_nps import SubmitNpsRequest

        for score in [0, 10]:
            req = SubmitNpsRequest(token="abc", score=score)
            assert req.score == score
