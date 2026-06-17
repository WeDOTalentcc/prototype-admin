"""
D1 — JobReportModal: wire backend real
Testa GET /api/v1/jobs/{job_id}/report
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestJobReportEndpoint:

    def _make_vc(self, stage="screening", source="linkedin", lia_score=80.0):
        vc = MagicMock()
        vc.stage = stage
        vc.source = source
        vc.lia_score = lia_score
        vc.match_percentage = 75
        vc.created_at = None
        return vc

    def _make_candidate(self, name="Ana Silva"):
        c = MagicMock()
        c.name = name
        return c

    @pytest.mark.asyncio
    async def test_get_job_report_returns_funnel_metrics(self):
        """GET /jobs/{job_id}/report retorna funnel_metrics com dados reais."""
        from app.api.v1.job_vacancies import get_job_report

        job_id = uuid4()
        mock_job = MagicMock()
        mock_job.title = "Engenheiro Senior"

        vcs = [
            self._make_vc("screening", "linkedin", 90),
            self._make_vc("interview", "website", 85),
            self._make_vc("hired", "linkedin", 95),
        ]

        mock_db = AsyncMock()
        # 1st execute: job lookup
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_job)),
            # 2nd: vacancy candidates
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=vcs)))),
            # 3rd: avg time query
            MagicMock(scalar=MagicMock(return_value=None)),
            # 4th: top candidates join
            MagicMock(all=MagicMock(return_value=[])),
        ]

        mock_user = MagicMock()
        with patch(
            "app.api.v1.job_vacancies.get_user_company_id",
            return_value="comp-1",
        ):
            result = await get_job_report(
                job_id=job_id,
                db=mock_db,
                current_user=mock_user,
            )

        assert result.vacancy_id == str(job_id)
        assert result.vacancy_title == "Engenheiro Senior"
        assert result.funnel_metrics.total_candidates == 3
        assert result.funnel_metrics.hired == 1
        assert result.funnel_metrics.screening >= 1
        assert result.funnel_metrics.interview >= 1

    @pytest.mark.asyncio
    async def test_get_job_report_channel_performance(self):
        """channel_performance agrupa candidatos por fonte."""
        from app.api.v1.job_vacancies import get_job_report

        job_id = uuid4()
        mock_job = MagicMock()
        mock_job.title = "Analista"

        vcs = [
            self._make_vc("screening", "linkedin", 80),
            self._make_vc("screening", "linkedin", 70),
            self._make_vc("hired", "website", 90),
        ]

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_job)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=vcs)))),
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(all=MagicMock(return_value=[])),
        ]

        mock_user = MagicMock()
        with patch("app.api.v1.job_vacancies.get_user_company_id", return_value="comp-1"):
            result = await get_job_report(job_id=job_id, db=mock_db, current_user=mock_user)

        channels = {c.channel: c for c in result.channel_performance}
        assert "linkedin" in channels
        assert channels["linkedin"].candidates == 2
        assert "website" in channels
        assert channels["website"].hired == 1

    @pytest.mark.asyncio
    async def test_get_job_report_top_candidates(self):
        """top_candidates retorna top 5 por lia_score."""
        from app.api.v1.job_vacancies import get_job_report

        job_id = uuid4()
        mock_job = MagicMock()
        mock_job.title = "Dev"

        mock_db = AsyncMock()
        cand = self._make_candidate("Ana Silva")
        vc = self._make_vc("interview", "linkedin", 92)
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_job)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[vc])))),
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(all=MagicMock(return_value=[(vc, cand)])),
        ]

        with patch("app.api.v1.job_vacancies.get_user_company_id", return_value="comp-1"):
            result = await get_job_report(job_id=job_id, db=mock_db, current_user=MagicMock())

        assert len(result.top_candidates) == 1
        assert result.top_candidates[0].name == "Ana Silva"
        assert result.top_candidates[0].score == 92.0

    @pytest.mark.asyncio
    async def test_get_job_report_404_if_job_not_found(self):
        """Retorna 404 quando a vaga não existe ou não pertence à empresa."""
        from app.api.v1.job_vacancies import get_job_report
        from fastapi import HTTPException

        job_id = uuid4()
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        with patch("app.api.v1.job_vacancies.get_user_company_id", return_value="comp-1"):
            with pytest.raises(HTTPException) as exc_info:
                await get_job_report(job_id=job_id, db=mock_db, current_user=MagicMock())

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_report_conversion_rate(self):
        """conversion_rate calculada corretamente: hired/total*100."""
        from app.api.v1.job_vacancies import get_job_report

        job_id = uuid4()
        mock_job = MagicMock()
        mock_job.title = "X"
        vcs = [self._make_vc("hired", "linkedin", 90)] * 2 + [self._make_vc("screening", "linkedin", 70)] * 8

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_job)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=vcs)))),
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(all=MagicMock(return_value=[])),
        ]

        with patch("app.api.v1.job_vacancies.get_user_company_id", return_value="comp-1"):
            result = await get_job_report(job_id=job_id, db=mock_db, current_user=MagicMock())

        assert result.funnel_metrics.total_candidates == 10
        assert result.funnel_metrics.hired == 2
        assert result.funnel_metrics.conversion_rate == 20.0
