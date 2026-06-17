"""TDD Fase 2 — CompetencyBenchmarkService (espelho do MarketBenchmarkService).

Sugere competências técnicas + comportamentais por (título + senioridade +
departamento + modo de triagem). Dimensionado pelo modo via SCREENING_MODE_CONFIG.

Testa:
  1. SCREENING_MODE_CONFIG estendido: split técnica/comportamental por modo (soma = total_questions)
  2. suggest_competencies: retorna technical + behavioral dimensionados pelo modo
  3. Schema: technical={skill,contexto}; behavioral={competencia,contexto,trait_big_five}
  4. trait_big_five válido (Literal Big Five)
  5. Fairness: sugestões com termo bloqueado são filtradas
  6. Fallback determinístico quando LLM falha (is_estimate=True, confidence=low)
  7. Multi-tenancy: company_id participa da cache key
  8. Cache hit evita 2ª chamada LLM
  9. Singleton getter

Run:
    cd lia-agent-system && python -m pytest tests/unit/test_competency_benchmark_service_fase2.py -v --no-cov
"""
from __future__ import annotations
import json
from unittest.mock import AsyncMock, patch

import pytest

VALID_TRAITS = {
    "openness", "conscientiousness", "extraversion",
    "agreeableness", "stability",
}


# ── 1. SCREENING_MODE_CONFIG estendido ───────────────────────────────────────

class TestScreeningModeConfigCompetencySplit:
    def test_compact_has_competency_split(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        assert "technical_competencies" in SCREENING_MODE_CONFIG["compact"]
        assert "behavioral_competencies" in SCREENING_MODE_CONFIG["compact"]

    def test_full_has_competency_split(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        assert "technical_competencies" in SCREENING_MODE_CONFIG["full"]
        assert "behavioral_competencies" in SCREENING_MODE_CONFIG["full"]

    def test_compact_split_sums_to_total_questions(self):
        """Invariante: técnica + comportamental == total_questions (compact)."""
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        c = SCREENING_MODE_CONFIG["compact"]
        assert c["technical_competencies"] + c["behavioral_competencies"] == c["total_questions"]

    def test_full_split_sums_to_total_questions(self):
        """Invariante: técnica + comportamental == total_questions (full)."""
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        f = SCREENING_MODE_CONFIG["full"]
        assert f["technical_competencies"] + f["behavioral_competencies"] == f["total_questions"]

    def test_full_has_more_competencies_than_compact(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        c = SCREENING_MODE_CONFIG["compact"]
        f = SCREENING_MODE_CONFIG["full"]
        c_total = c["technical_competencies"] + c["behavioral_competencies"]
        f_total = f["technical_competencies"] + f["behavioral_competencies"]
        assert f_total > c_total


# ── Fixtures de LLM ───────────────────────────────────────────────────────────

def _llm_competency_json(n_tech=5, n_behav=2):
    """Resposta LLM bem-formada com n_tech técnicas + n_behav comportamentais."""
    technical = [
        {"skill": f"Skill Técnica {i}", "contexto": f"contexto {i}"}
        for i in range(1, n_tech + 1)
    ]
    behavioral = [
        {"competencia": f"Competência {i}", "contexto": f"ctx {i}", "trait_big_five": "conscientiousness"}
        for i in range(1, n_behav + 1)
    ]
    return json.dumps({"technical": technical, "behavioral": behavioral})


def _make_service():
    from app.domains.analytics.services.competency_benchmark_service import (
        CompetencyBenchmarkService,
    )
    svc = CompetencyBenchmarkService()
    svc.clear_cache()
    return svc


# ── 2. suggest_competencies — estrutura e dimensionamento ─────────────────────

class TestSuggestCompetencies:
    @pytest.mark.asyncio
    async def test_returns_technical_and_behavioral_keys(self):
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value=_llm_competency_json(5, 2)),
        ):
            result = await svc.suggest_competencies(
                title="Engenheiro de Software",
                seniority="senior",
                department="Tecnologia",
                screening_mode="compact",
                company_id="cid-1",
            )
        assert "technical" in result
        assert "behavioral" in result
        assert isinstance(result["technical"], list)
        assert isinstance(result["behavioral"], list)

    @pytest.mark.asyncio
    async def test_technical_schema_shape(self):
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value=_llm_competency_json(5, 2)),
        ):
            result = await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="compact", company_id="cid-1",
            )
        assert len(result["technical"]) > 0
        for t in result["technical"]:
            assert "skill" in t
            assert "contexto" in t

    @pytest.mark.asyncio
    async def test_behavioral_schema_shape_with_valid_trait(self):
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value=_llm_competency_json(5, 2)),
        ):
            result = await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="compact", company_id="cid-1",
            )
        assert len(result["behavioral"]) > 0
        for b in result["behavioral"]:
            assert "competencia" in b
            assert "trait_big_five" in b
            assert b["trait_big_five"] in VALID_TRAITS

    @pytest.mark.asyncio
    async def test_compact_returns_fewer_than_full(self):
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value=_llm_competency_json(8, 4)),
        ):
            compact = await svc.suggest_competencies(
                title="Dev", seniority="senior", screening_mode="compact", company_id="cid-1",
            )
            full = await svc.suggest_competencies(
                title="Dev", seniority="senior", screening_mode="full", company_id="cid-2",
            )
        compact_total = len(compact["technical"]) + len(compact["behavioral"])
        full_total = len(full["technical"]) + len(full["behavioral"])
        assert compact_total < full_total, f"compact={compact_total} full={full_total}"

    @pytest.mark.asyncio
    async def test_compact_caps_at_config_targets(self):
        """LLM devolve demais → serviço corta para os targets do modo compact."""
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value=_llm_competency_json(20, 20)),
        ):
            result = await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="compact", company_id="cid-1",
            )
        c = SCREENING_MODE_CONFIG["compact"]
        assert len(result["technical"]) <= c["technical_competencies"]
        assert len(result["behavioral"]) <= c["behavioral_competencies"]


# ── 3. Fairness — filtra sugestões bloqueadas ────────────────────────────────

class TestFairnessFiltering:
    @pytest.mark.asyncio
    async def test_blocked_suggestion_is_filtered(self):
        """Uma competência cujo texto é bloqueado pelo FairnessGuard deve ser removida."""
        svc = _make_service()
        # LLM devolve 3 técnicas, uma delas com texto que será 'bloqueado' pelo mock
        payload = json.dumps({
            "technical": [
                {"skill": "Python", "contexto": "ok"},
                {"skill": "BLOQUEAR_ESTA", "contexto": "viés"},
                {"skill": "SQL", "contexto": "ok"},
            ],
            "behavioral": [
                {"competencia": "Comunicação", "contexto": "ok", "trait_big_five": "extraversion"},
            ],
        })

        from app.shared.compliance.fairness_guard import FairnessCheckResult

        def fake_check(text):
            blocked = "BLOQUEAR_ESTA" in (text or "")
            return FairnessCheckResult(
                is_blocked=blocked,
                blocked_terms=["BLOQUEAR_ESTA"] if blocked else [],
                original_query=text,
                educational_message="bloqueado" if blocked else None,
            )

        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value=payload),
        ), patch(
            "app.domains.analytics.services.competency_benchmark_service.FairnessGuard"
        ) as MockGuard:
            MockGuard.return_value.check.side_effect = fake_check
            result = await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="full", company_id="cid-1",
            )

        tech_skills = [t["skill"] for t in result["technical"]]
        assert "BLOQUEAR_ESTA" not in tech_skills
        assert "Python" in tech_skills
        assert "SQL" in tech_skills


# ── 4. Fallback determinístico ────────────────────────────────────────────────

class TestFallback:
    @pytest.mark.asyncio
    async def test_fallback_when_llm_raises(self):
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(side_effect=RuntimeError("llm down")),
        ):
            result = await svc.suggest_competencies(
                title="Desenvolvedor Python", seniority="pleno",
                screening_mode="compact", company_id="cid-1",
            )
        # Fallback deve devolver listas não-vazias e marcar is_estimate
        assert len(result["technical"]) > 0
        assert len(result["behavioral"]) > 0
        assert result.get("is_estimate") is True
        assert result.get("confidence") == "low"

    @pytest.mark.asyncio
    async def test_fallback_when_llm_returns_garbage(self):
        svc = _make_service()
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=AsyncMock(return_value="isto não é JSON algum"),
        ):
            result = await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="compact", company_id="cid-1",
            )
        assert len(result["technical"]) > 0
        assert result.get("is_estimate") is True


# ── 5. Multi-tenancy + cache ──────────────────────────────────────────────────

class TestMultiTenancyAndCache:
    @pytest.mark.asyncio
    async def test_company_id_in_cache_key(self):
        """Companies diferentes => cache keys diferentes (isolamento)."""
        svc = _make_service()
        k1 = svc._generate_cache_key("competency", title="Dev", seniority="pleno",
                                     department=None, screening_mode="compact", company_id="cid-A")
        k2 = svc._generate_cache_key("competency", title="Dev", seniority="pleno",
                                     department=None, screening_mode="compact", company_id="cid-B")
        assert k1 != k2

    @pytest.mark.asyncio
    async def test_cache_hit_avoids_second_llm_call(self):
        svc = _make_service()
        mock_gen = AsyncMock(return_value=_llm_competency_json(5, 2))
        with patch(
            "app.domains.analytics.services.competency_benchmark_service.llm_service.generate",
            new=mock_gen,
        ):
            await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="compact", company_id="cid-1",
            )
            await svc.suggest_competencies(
                title="Dev", seniority="pleno", screening_mode="compact", company_id="cid-1",
            )
        assert mock_gen.await_count == 1, "2ª chamada deve vir do cache"


# ── 6. Singleton getter ───────────────────────────────────────────────────────

class TestSingleton:
    def test_get_service_returns_instance(self):
        from app.domains.analytics.services.competency_benchmark_service import (
            get_competency_benchmark_service, CompetencyBenchmarkService,
        )
        svc = get_competency_benchmark_service()
        assert isinstance(svc, CompetencyBenchmarkService)
