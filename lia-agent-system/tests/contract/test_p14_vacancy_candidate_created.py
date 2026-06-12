"""
P1-4: sourcing_pipeline_service deve criar VacancyCandidate (status=sourced,
stage=initial) além de Interview quando candidato é sourced automaticamente.

TDD Red → Green — testes de contrato.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call


def _make_job(company_id="comp-001"):
    job = MagicMock()
    job.id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    job.title = "Engenheiro de Software"
    job.company_id = company_id
    job.seniority_level = "pleno"
    job.required_skills = []
    job.required_experience_years = 3
    job.created_at = datetime.utcnow()
    return job


def _make_candidate(candidate_id=None, name="Fulano"):
    c = MagicMock()
    c.id = candidate_id or uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    c.name = name
    c.email = f"{name.lower()}@email.com"
    c.lia_score = None
    c.updated_at = None
    c.technical_skills = []
    c.soft_skills = []
    c.certifications = []
    c.years_of_experience = 3
    c.current_title = "Dev"
    return c


class TestP14SourcingCreatesVacancyCandidate:
    """P1-4: pipeline de sourcing deve criar VacancyCandidate."""

    @pytest.mark.asyncio
    async def test_local_sourcing_creates_vacancy_candidate(self):
        """_add_candidates_to_job deve criar VacancyCandidate além de Interview."""
        from app.domains.sourcing.services.sourcing_pipeline_service import SourcingPipelineService

        job = _make_job()
        candidate = _make_candidate()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        vc_repo_mock = AsyncMock()
        vc_repo_mock.create_sourced = AsyncMock(return_value=True)

        interview_repo_mock = AsyncMock()
        interview_repo_mock.get_for_candidate_and_job = AsyncMock(return_value=None)

        with (
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.InterviewRepository",
                return_value=interview_repo_mock,
            ),
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.VacancyCandidateRepository",
                return_value=vc_repo_mock,
            ),
        ):
            service = SourcingPipelineService()
            await service._add_candidates_to_job(db, job, [candidate])

        vc_repo_mock.create_sourced.assert_called_once(), (
            "VacancyCandidateRepository.create_sourced nunca chamado — P1-4 não implementado"
        )

    @pytest.mark.asyncio
    async def test_local_sourcing_vacancy_candidate_has_correct_ids(self):
        """create_sourced deve receber vacancy_id, candidate_id, company_id corretos."""
        from app.domains.sourcing.services.sourcing_pipeline_service import SourcingPipelineService

        job = _make_job(company_id="comp-XYZ")
        candidate = _make_candidate(candidate_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        captured = {}

        async def capture_create_sourced(**kwargs):
            captured.update(kwargs)
            return True

        vc_repo_mock = AsyncMock()
        vc_repo_mock.create_sourced = AsyncMock(side_effect=capture_create_sourced)

        interview_repo_mock = AsyncMock()
        interview_repo_mock.get_for_candidate_and_job = AsyncMock(return_value=None)

        with (
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.InterviewRepository",
                return_value=interview_repo_mock,
            ),
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.VacancyCandidateRepository",
                return_value=vc_repo_mock,
            ),
        ):
            service = SourcingPipelineService()
            await service._add_candidates_to_job(db, job, [candidate])

        assert str(captured.get("vacancy_id")) == str(job.id)
        assert str(captured.get("candidate_id")) == str(candidate.id)
        assert captured.get("company_id") == "comp-XYZ"
        assert captured.get("status") == "sourced"
        assert captured.get("stage") == "initial"

    @pytest.mark.asyncio
    async def test_skip_candidate_already_in_pipeline(self):
        """Quando Interview já existe, não cria VC duplicado."""
        from app.domains.sourcing.services.sourcing_pipeline_service import SourcingPipelineService

        job = _make_job()
        candidate = _make_candidate()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        vc_repo_mock = AsyncMock()
        vc_repo_mock.create_sourced = AsyncMock(return_value=True)

        interview_repo_mock = AsyncMock()
        # interview already exists → candidate is skipped entirely
        interview_repo_mock.get_for_candidate_and_job = AsyncMock(
            return_value=MagicMock()  # non-None = already in pipeline
        )

        with (
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.InterviewRepository",
                return_value=interview_repo_mock,
            ),
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.VacancyCandidateRepository",
                return_value=vc_repo_mock,
            ),
        ):
            service = SourcingPipelineService()
            result = await service._add_candidates_to_job(db, job, [candidate])

        vc_repo_mock.create_sourced.assert_not_called()
        assert result == 0

    @pytest.mark.asyncio
    async def test_pearch_sourcing_creates_vacancy_candidate(self):
        """_add_pearch_candidates_to_job deve criar VacancyCandidate além de Interview."""
        from app.domains.sourcing.services.sourcing_pipeline_service import SourcingPipelineService

        job = _make_job()
        pearch_data = [{"name": "Ciclano", "email": "ciclano@pearch.com", "match_score": 82.0}]
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()

        candidate = _make_candidate(name="Ciclano")

        vc_repo_mock = AsyncMock()
        vc_repo_mock.create_sourced = AsyncMock(return_value=True)

        interview_repo_mock = AsyncMock()
        interview_repo_mock.get_for_candidate_and_job = AsyncMock(return_value=None)

        candidate_repo_mock = AsyncMock()
        candidate_repo_mock.get_by_email = AsyncMock(return_value=None)  # new candidate

        with (
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.InterviewRepository",
                return_value=interview_repo_mock,
            ),
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.VacancyCandidateRepository",
                return_value=vc_repo_mock,
            ),
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.CandidateRepository",
                return_value=candidate_repo_mock,
            ),
        ):
            service = SourcingPipelineService()
            await service._add_pearch_candidates_to_job(db, job, pearch_data)

        vc_repo_mock.create_sourced.assert_called_once(), (
            "VacancyCandidateRepository.create_sourced nunca chamado em pearch path — P1-4 não implementado"
        )

    @pytest.mark.asyncio
    async def test_create_sourced_fails_soft_does_not_abort(self):
        """Se create_sourced lança exceção, não aborta adição do candidato (fail-soft)."""
        from app.domains.sourcing.services.sourcing_pipeline_service import SourcingPipelineService

        job = _make_job()
        candidate = _make_candidate()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        vc_repo_mock = AsyncMock()
        vc_repo_mock.create_sourced = AsyncMock(
            side_effect=Exception("DB constraint simulado")
        )

        interview_repo_mock = AsyncMock()
        interview_repo_mock.get_for_candidate_and_job = AsyncMock(return_value=None)

        with (
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.InterviewRepository",
                return_value=interview_repo_mock,
            ),
            patch(
                "app.domains.sourcing.services.sourcing_pipeline_service.VacancyCandidateRepository",
                return_value=vc_repo_mock,
            ),
        ):
            service = SourcingPipelineService()
            result = await service._add_candidates_to_job(db, job, [candidate])

        # Interview still created despite VC failure
        db.add.assert_called()
        assert result == 1, "candidato deve ser contado como adicionado mesmo com VC fail-soft"
