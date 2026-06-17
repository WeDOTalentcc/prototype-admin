"""
Testes — Sector Benchmark Service (D.3 — Anti-sycophancy)

Referência: wedo-governance Crença #11 (Anti-sycophancy)
"""
import pytest
from unittest.mock import patch, AsyncMock

from app.domains.analytics.services.sector_benchmark_service import (
    SectorBenchmarkService,
    sector_benchmark_service,
    BenchmarkProfile,
    _normalize_area,
    _normalize_seniority,
)


# ---------------------------------------------------------------------------
# Testes de normalização de área e senioridade
# ---------------------------------------------------------------------------

class TestNormalization:
    """Testa normalização de aliases de área e senioridade."""

    def test_normalize_area_canonical(self):
        assert _normalize_area("software_engineering") == "software_engineering"

    def test_normalize_area_alias(self):
        assert _normalize_area("dev") == "software_engineering"
        assert _normalize_area("data") == "data_science"
        assert _normalize_area("juridico") == "legal"
        assert _normalize_area("produto") == "product_management"
        assert _normalize_area("pm") == "product_management"

    def test_normalize_area_case_insensitive(self):
        assert _normalize_area("DEV") == "software_engineering"
        assert _normalize_area("Data Science") == "data_science"

    def test_normalize_area_unknown_returns_none(self):
        assert _normalize_area("fintech_xyz") is None

    def test_normalize_area_empty_returns_none(self):
        assert _normalize_area("") is None

    def test_normalize_seniority_canonical(self):
        assert _normalize_seniority("senior") == "senior"
        assert _normalize_seniority("pleno") == "pleno"
        assert _normalize_seniority("junior") == "junior"
        assert _normalize_seniority("staff") == "staff"

    def test_normalize_seniority_aliases(self):
        assert _normalize_seniority("sr") == "senior"
        assert _normalize_seniority("jr") == "junior"
        assert _normalize_seniority("mid") == "pleno"
        assert _normalize_seniority("principal") == "staff"
        assert _normalize_seniority("trainee") == "junior"

    def test_normalize_seniority_empty_returns_none(self):
        assert _normalize_seniority("") is None

    def test_normalize_seniority_unknown_returns_none(self):
        assert _normalize_seniority("clt_specialist") is None


# ---------------------------------------------------------------------------
# Testes de perfis de benchmark
# ---------------------------------------------------------------------------

class TestBenchmarkProfiles:
    """Testa que os perfis de benchmark têm dados corretos."""

    def test_all_supported_areas_have_senior(self):
        """Todas as áreas principais devem ter perfil sênior."""
        service = SectorBenchmarkService()
        for area in ["software_engineering", "data_science", "legal", "product_management"]:
            profile = service.get_profile(area, "senior")
            assert profile is not None, f"Área '{area}' sem perfil senior"

    def test_profile_fields_valid(self):
        """Todos os perfis devem ter campos válidos."""
        service = SectorBenchmarkService()
        for combo in service.list_supported():
            profile = service.get_profile(*combo)
            assert profile is not None
            assert 0 <= profile.score_p50 <= 99
            assert profile.score_p75 >= profile.score_p50
            assert profile.min_expected <= profile.score_p50
            assert 0 < profile.approval_rate <= 1.0
            assert len(profile.key_signals) >= 1
            assert len(profile.calibration_note) > 10

    def test_seniority_progression_software_engineering(self):
        """Score P50 deve crescer com senioridade: junior < pleno < senior < staff."""
        service = SectorBenchmarkService()
        p_jr = service.get_profile("software_engineering", "junior")
        p_pl = service.get_profile("software_engineering", "pleno")
        p_sr = service.get_profile("software_engineering", "senior")
        p_st = service.get_profile("software_engineering", "staff")

        assert p_jr.score_p50 < p_pl.score_p50 < p_sr.score_p50 < p_st.score_p50, (
            "Score P50 deve crescer monotonicamente: junior < pleno < senior < staff"
        )

    def test_min_supported_combinations(self):
        """O serviço deve suportar ao menos 12 combinações área+senioridade."""
        service = SectorBenchmarkService()
        combos = service.list_supported()
        assert len(combos) >= 12, f"Esperado >= 12 combinações, got {len(combos)}"


# ---------------------------------------------------------------------------
# Testes de get_benchmark_context
# ---------------------------------------------------------------------------

class TestGetBenchmarkContext:
    """Testa que get_benchmark_context retorna string válida ou vazia."""

    def test_returns_context_for_known_combination(self):
        """Contexto não-vazio para combinação suportada."""
        ctx = sector_benchmark_service.get_benchmark_context(
            area="software_engineering", seniority="senior"
        )
        assert len(ctx) > 0
        assert "Benchmark" in ctx or "score" in ctx.lower() or "Score" in ctx

    def test_returns_empty_for_unknown_area(self):
        """Retorna vazio para área desconhecida (sem exceção)."""
        ctx = sector_benchmark_service.get_benchmark_context(area="desconhecido_xyz", seniority="senior")
        assert ctx == ""

    def test_returns_empty_for_unknown_seniority(self):
        """Retorna vazio para senioridade desconhecida (sem exceção)."""
        ctx = sector_benchmark_service.get_benchmark_context(area="software_engineering", seniority="diretor")
        assert ctx == ""

    def test_returns_empty_for_empty_inputs(self):
        """Retorna vazio para inputs vazios (sem exceção)."""
        ctx = sector_benchmark_service.get_benchmark_context(area="", seniority="")
        assert ctx == ""

    def test_context_contains_score_references(self):
        """Contexto deve conter referências de score para calibração."""
        ctx = sector_benchmark_service.get_benchmark_context(area="data_science", seniority="pleno")
        assert "Score" in ctx or "pts" in ctx or "score" in ctx.lower()

    def test_context_contains_calibration_note(self):
        """Contexto deve conter instrução de calibração (anti-sycophancy)."""
        ctx = sector_benchmark_service.get_benchmark_context(area="legal", seniority="senior")
        # A nota de calibração ou instrução anti-sycophancy deve aparecer
        assert "CALIBRA" in ctx.upper() or "Calibr" in ctx or "score acima" in ctx.lower() or "IMPORTAN" in ctx.upper()

    def test_context_uses_aliases(self):
        """Aliases devem produzir o mesmo contexto que o nome canônico."""
        ctx_canonical = sector_benchmark_service.get_benchmark_context(
            area="software_engineering", seniority="senior"
        )
        ctx_alias = sector_benchmark_service.get_benchmark_context(
            area="dev", seniority="sr"
        )
        assert ctx_canonical == ctx_alias

    def test_never_raises_exception(self):
        """get_benchmark_context nunca deve levantar exceção."""
        for area in ["", "xyz", "software_engineering", None or ""]:
            for seniority in ["", "xyz", "senior", None or ""]:
                try:
                    result = sector_benchmark_service.get_benchmark_context(area=area, seniority=seniority)
                    assert isinstance(result, str)
                except Exception as e:
                    pytest.fail(f"get_benchmark_context levantou exceção: {e}")


# ---------------------------------------------------------------------------
# Testes de integração com rubric_evaluation_service
# ---------------------------------------------------------------------------

class TestRubricEvaluationBenchmarkIntegration:
    """Testa que o benchmark é injetado no prompt em evaluate_candidate()."""

    @pytest.mark.asyncio
    async def test_benchmark_injected_when_area_seniority_present(self):
        """
        Quando candidate_data tem area + seniority conhecidos,
        o prompt deve incluir '## Benchmark Setorial'.
        """
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        captured_prompt = {}

        async def _capture_and_fail(prompt):
            captured_prompt["value"] = prompt
            return "{}"

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", side_effect=_capture_and_fail), \
             patch.object(service, "_parse_llm_response", return_value=([], [], [], "Avaliação técnica.")):
            await service.evaluate_candidate(
                {
                    "id": "bench-001",
                    "area": "software_engineering",
                    "seniority": "senior",
                    "cv_content": "Candidato com 10 anos de experiência em Python.",
                },
                [JobRequirementCreate(
                    requirement="Python sênior",
                    priority=RequirementPriorityEnum.ESSENTIAL,
                    description="Python",
                    weight=1.0,
                )],
                use_cache=False,
            )

        assert "## Benchmark Setorial" in captured_prompt.get("value", ""), (
            "O benchmark setorial deve ser injetado no prompt quando area+seniority são conhecidos"
        )

    @pytest.mark.asyncio
    async def test_benchmark_not_injected_when_area_missing(self):
        """
        Quando candidate_data não tem area, o prompt NÃO deve incluir benchmark.
        """
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        captured_prompt = {}

        async def _capture_and_fail(prompt):
            captured_prompt["value"] = prompt
            return "{}"

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", side_effect=_capture_and_fail), \
             patch.object(service, "_parse_llm_response", return_value=([], [], [], "Avaliação técnica.")):
            await service.evaluate_candidate(
                {"id": "bench-002"},  # sem area nem seniority
                [JobRequirementCreate(
                    requirement="Python",
                    priority=RequirementPriorityEnum.ESSENTIAL,
                    description="Python",
                    weight=1.0,
                )],
                use_cache=False,
            )

        assert "## Benchmark Setorial" not in captured_prompt.get("value", ""), (
            "O benchmark NÃO deve ser injetado quando area não é fornecida"
        )
