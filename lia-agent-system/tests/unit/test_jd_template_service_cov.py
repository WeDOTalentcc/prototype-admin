"""
Coverage tests for app/domains/job_management/services/jd_template_service.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture
def service():
    with patch("app.domains.job_management.services.jd_template_service.skills_catalog_service") as mock_catalog:
        mock_catalog.suggest_skills.return_value = {
            "technical_skills": ["Python", "Docker"],
            "behavioral_competencies": [{"name": "Comunicação"}, "Trabalho em equipe"],
        }
        from app.domains.job_management.services.jd_template_service import JDTemplateService
        svc = JDTemplateService()
        yield svc


@pytest.fixture
def gen_request():
    from app.schemas.job_description import JDGenerationRequest, WorkModel, ContractType
    return JDGenerationRequest(
        company_id="comp-1",
        title="Desenvolvedor Senior Python",
        department="Engenharia",
        seniority="Senior",
        num_positions=2,
        work_model=WorkModel.HYBRID,
        office_days_per_week=3,
        contract_type=ContractType.CLT,
        location="São Paulo",
        is_affirmative=True,
        affirmative_type="Vaga PCD",
        description="Desenvolver microserviços em Python",
        detected_responsibilities=["Escrever código Python", "Fazer code reviews"],
        detected_technical_skills=["Python", "FastAPI"],
        detected_behavioral_skills=["Liderança"],
        salary_min=15000,
        salary_max=25000,
        bonus_percentage=10.0,
    )


# ── _build_responsibilities ──────────────────────────────────────────────────

class TestBuildResponsibilities:
    @pytest.mark.easy
    def test_detected_only(self, service):
        result = service._build_responsibilities(
            detected=["Task A", "Task B"],
            role="Analyst",
            seniority="Pleno",
            include_suggestions=False,
        )
        assert len(result) == 2
        assert all(not r.is_new for r in result)

    @pytest.mark.easy
    def test_with_suggestions(self, service):
        result = service._build_responsibilities(
            detected=["Task A"],
            role="Desenvolvedor Senior",
            seniority="Senior",
            include_suggestions=True,
        )
        assert len(result) > 1
        assert any(r.is_new for r in result)

    @pytest.mark.easy
    def test_no_duplicate_suggestions(self, service):
        """Suggested responsibilities already in detected should not duplicate."""
        result = service._build_responsibilities(
            detected=["Desenvolver e manter aplicações de alta qualidade"],
            role="Desenvolvedor",
            seniority="Junior",
            include_suggestions=True,
        )
        descriptions = [r.description for r in result]
        assert len(descriptions) == len(set(d.lower() for d in descriptions))


# ── _get_suggested_responsibilities ──────────────────────────────────────────

class TestGetSuggestedResponsibilities:
    @pytest.mark.easy
    def test_dev_role(self, service):
        result = service._get_suggested_responsibilities("Desenvolvedor Python", "Junior")
        assert len(result) == 4
        assert any("código" in r.lower() or "aplicações" in r.lower() for r in result)

    @pytest.mark.easy
    def test_dev_senior(self, service):
        result = service._get_suggested_responsibilities("Software Engineer", "Senior")
        assert len(result) == 4

    @pytest.mark.easy
    def test_dev_lead(self, service):
        result = service._get_suggested_responsibilities("Dev Lead", "Líder")
        assert len(result) == 4

    @pytest.mark.easy
    def test_product_role(self, service):
        result = service._get_suggested_responsibilities("Product Manager", "Pleno")
        assert len(result) == 4
        assert any("roadmap" in r.lower() for r in result)

    @pytest.mark.easy
    def test_design_role(self, service):
        result = service._get_suggested_responsibilities("UX Designer", None)
        assert len(result) == 4

    @pytest.mark.easy
    def test_data_role(self, service):
        result = service._get_suggested_responsibilities("Data Engineer", "Pleno")
        assert len(result) == 4

    @pytest.mark.easy
    def test_rh_role(self, service):
        result = service._get_suggested_responsibilities("Recursos Humanos", None)
        assert len(result) == 4

    @pytest.mark.easy
    def test_sales_role(self, service):
        result = service._get_suggested_responsibilities("Sales Manager", None)
        assert len(result) == 4

    @pytest.mark.easy
    def test_marketing_role(self, service):
        result = service._get_suggested_responsibilities("Marketing Analyst", None)
        assert len(result) == 4

    @pytest.mark.easy
    def test_unknown_role(self, service):
        result = service._get_suggested_responsibilities("Astronaut", None)
        assert len(result) == 4


# ── _build_competencies ──────────────────────────────────────────────────────

class TestBuildCompetencies:
    @pytest.mark.easy
    def test_detected_only(self, service):
        tech, beh = service._build_competencies(
            detected_technical=["Python", "SQL"],
            detected_behavioral=["Proatividade"],
            role="Dev",
            seniority="Pleno",
            include_suggestions=False,
        )
        assert len(tech) == 2
        assert len(beh) == 1

    @pytest.mark.easy
    def test_with_suggestions(self, service):
        tech, beh = service._build_competencies(
            detected_technical=["Go"],
            detected_behavioral=[],
            role="Dev",
            seniority="Pleno",
            include_suggestions=True,
        )
        # Should include catalog suggestions
        assert len(tech) >= 2  # Go + Docker (Python already excluded? no, Go != Python)
        assert any(c.is_new for c in tech)


# ── _build_compensation ──────────────────────────────────────────────────────

class TestBuildCompensation:
    @pytest.mark.easy
    def test_below_market(self, service):
        comp = service._build_compensation(
            salary_min=2000, salary_max=3000, bonus_percentage=None,
            company_id="c1", role="Desenvolvedor", seniority="Senior",
        )
        assert comp.has_alert is True
        assert comp.market_comparison == "abaixo"
        assert comp.market_percentile == 25

    @pytest.mark.easy
    def test_above_market(self, service):
        comp = service._build_compensation(
            salary_min=50000, salary_max=60000, bonus_percentage=5.0,
            company_id="c1", role="Desenvolvedor", seniority="Junior",
        )
        assert comp.market_comparison == "acima"
        assert comp.market_percentile == 90

    @pytest.mark.easy
    def test_aligned_market(self, service):
        comp = service._build_compensation(
            salary_min=14000, salary_max=18000, bonus_percentage=None,
            company_id="c1", role="Desenvolvedor", seniority="Senior",
        )
        assert comp.market_comparison == "alinhado"
        assert 25 <= comp.market_percentile <= 75

    @pytest.mark.easy
    def test_no_salary(self, service):
        comp = service._build_compensation(
            salary_min=None, salary_max=None, bonus_percentage=None,
            company_id="c1", role="Dev", seniority="Pleno",
        )
        assert comp.has_alert is False
        assert comp.market_comparison is None


# ── _estimate_market_salary ──────────────────────────────────────────────────

class TestEstimateMarketSalary:
    @pytest.mark.easy
    def test_junior(self, service):
        result = service._estimate_market_salary("Analyst", "Júnior")
        assert result == (4000, 7000)

    @pytest.mark.easy
    def test_senior_tech(self, service):
        result = service._estimate_market_salary("DevOps Engineer", "Senior")
        assert result[0] > 12000  # tech multiplier

    @pytest.mark.easy
    def test_default_seniority(self, service):
        result = service._estimate_market_salary("Generic Role", None)
        assert result is not None

    @pytest.mark.easy
    def test_gerente(self, service):
        result = service._estimate_market_salary("Analyst", "Gerente")
        assert result == (20000, 35000)

    @pytest.mark.easy
    def test_diretor(self, service):
        result = service._estimate_market_salary("Analyst", "Diretor")
        assert result == (30000, 50000)


# ── generate_preview ─────────────────────────────────────────────────────────

class TestGeneratePreview:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_preview_success(self, service, gen_request):
        with patch.object(service, "_get_company_info", new_callable=AsyncMock, return_value=None):
            result = await service.generate_preview(gen_request)
        assert result.success is True
        assert result.preview is not None
        assert result.markdown is not None
        assert "Desenvolvedor Senior Python" in result.markdown

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_preview_no_suggestions(self, service, gen_request):
        with patch.object(service, "_get_company_info", new_callable=AsyncMock, return_value=None):
            result = await service.generate_preview(gen_request, include_suggestions=False)
        assert result.success is True
        assert result.suggestions_applied == 0

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_preview_error_handling(self, service, gen_request):
        with patch.object(service, "_build_responsibilities", side_effect=Exception("boom")):
            result = await service.generate_preview(gen_request)
        assert result.success is False
        assert "boom" in result.error


# ── _render_preview_markdown ─────────────────────────────────────────────────

class TestRenderPreviewMarkdown:
    @pytest.mark.easy
    def test_renders_all_sections(self, service, gen_request):
        from app.schemas.job_description import (
            JobDescriptionPreview, Responsibility, Competency,
            CompensationData, SuggestionSource, RequirementLevel, WorkModel,
        )
        preview = JobDescriptionPreview(
            title="Dev Python",
            department="Eng",
            seniority="Senior",
            num_positions=2,
            work_model=WorkModel.HYBRID,
            office_days_per_week=3,
            location="SP",
            is_affirmative=True,
            affirmative_type="PCD",
            description="Build stuff",
            responsibilities=[
                Responsibility(description="Code", source=SuggestionSource.DETECTED, is_new=False),
                Responsibility(description="Review", source=SuggestionSource.LIA_CATALOG, is_new=True),
            ],
            technical_competencies=[
                Competency(name="Python", level=RequirementLevel.REQUIRED, source=SuggestionSource.DETECTED, is_new=False),
                Competency(name="Docker", level=RequirementLevel.NICE_TO_HAVE, source=SuggestionSource.LIA_CATALOG, is_new=True),
            ],
            behavioral_competencies=[
                Competency(name="Comunicação", level=RequirementLevel.REQUIRED, source=SuggestionSource.DETECTED, is_new=False),
            ],
            compensation=CompensationData(salary_min=10000, salary_max=20000, has_alert=True, alert_message="Abaixo"),
            company=None,
            suggestions_count=2,
            alerts_count=1,
            completeness_score=0.8,
        )
        md = service._render_preview_markdown(preview)
        assert "Dev Python" in md
        assert "2 vagas" in md
        assert "PCD" in md
        assert "Python" in md
        assert "Docker" in md


# ── generate_final ───────────────────────────────────────────────────────────

class TestGenerateFinal:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_final_success(self, service, gen_request):
        with patch.object(service, "_get_company_info", new_callable=AsyncMock, return_value=None), \
             patch.object(service, "_get_company_interview_stages", new_callable=AsyncMock, return_value=[]):
            result = await service.generate_final(gen_request)
        assert result.success is True

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_final_error(self, service, gen_request):
        with patch.object(service, "_get_company_info", new_callable=AsyncMock, side_effect=Exception("fail")):
            result = await service.generate_final(gen_request)
        assert result.success is False


# ── _calculate_timeline ──────────────────────────────────────────────────────

class TestCalculateTimeline:
    @pytest.mark.easy
    def test_short_pipeline(self, service):
        from app.schemas.job_description import InterviewStage
        stages = [
            InterviewStage(order=1, name="Phone Screen"),
            InterviewStage(order=2, name="Technical"),
        ]
        result = service._calculate_timeline(stages)
        assert "1-2" in result

    @pytest.mark.easy
    def test_medium_pipeline(self, service):
        from app.schemas.job_description import InterviewStage
        stages = [InterviewStage(order=i, name=f"Stage {i}") for i in range(4)]
        result = service._calculate_timeline(stages)
        assert "2-3" in result

    @pytest.mark.easy
    def test_long_pipeline(self, service):
        from app.schemas.job_description import InterviewStage
        stages = [InterviewStage(order=i, name=f"Stage {i}") for i in range(6)]
        result = service._calculate_timeline(stages)
        assert "3-4" in result

    @pytest.mark.easy
    def test_empty_stages(self, service):
        result = service._calculate_timeline([])
        assert "1-2" in result
