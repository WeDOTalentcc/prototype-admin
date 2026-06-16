"""TDD Fase 4 — inverter jd_enrichment: consumir confirmed_*, não gerar do zero.

Quando há competências confirmadas (Fase 3), o jd_enrichment usa-as VERBATIM
(garantia computacional — sem drift do LLM) e gera o JD consistente com elas.
Sem confirmed_* → comportamento legado (gera competências). quality_score vira
mode-aware (não penaliza compact 5+2 com os thresholds 9/5 do modo legado).

Run:
    cd lia-agent-system && python -m pytest tests/unit/test_jd_enrichment_inversion_fase4.py -v --no-cov
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _llm_json_with_different_competencies():
    """LLM devolve competências DIFERENTES das confirmadas (para provar override)."""
    return json.dumps({
        "titulo_padronizado": "Engenheiro de Software",
        "senioridade_confirmada": "senior",
        "about_role": "Papel consistente com as competências fornecidas.",
        "responsabilidades": ["r1", "r2", "r3", "r4", "r5"],
        "skills_obrigatorias": [{"skill": "LLM_INVENTOU_TEC", "contexto": "x"}],
        "skills_desejaveis": ["extra1"],
        "competencias_comportamentais": [
            {"competencia": "LLM_INVENTOU_COMP", "contexto": "x", "trait_big_five": "openness"},
        ],
        "context_signals": {
            "nivel_autonomia": "alto", "nivel_inovacao": "alto",
            "nivel_pressao": "medio", "nivel_colaboracao": "alto",
        },
        "alteracoes_realizadas": [],
        "fairness_corrections": [],
    })


def _make_service_with_llm(llm_json):
    from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
    svc = JdEnrichmentService()
    svc._llm = mock.MagicMock()
    svc._llm.invoke.return_value = SimpleNamespace(content=llm_json)
    return svc


CONFIRMED_TECH = [
    {"skill": "Python", "contexto": "core do backend"},
    {"skill": "PostgreSQL", "contexto": "persistência"},
    {"skill": "Docker", "contexto": "deploy"},
    {"skill": "FastAPI", "contexto": "APIs"},
    {"skill": "Git", "contexto": "versionamento"},
]
CONFIRMED_BEHAV = [
    {"competencia": "Comunicação", "contexto": "alinhamento com squad", "trait_big_five": "extraversion"},
    {"competencia": "Autonomia", "contexto": "toca tarefas sozinho", "trait_big_five": "conscientiousness"},
]


# ── 1. enrich consome confirmed_* (override determinístico) ──────────────────

class TestEnrichConsumesConfirmed:
    def test_skills_obrigatorias_are_confirmed_verbatim(self):
        svc = _make_service_with_llm(_llm_json_with_different_competencies())
        enriched, _, _ = svc.enrich(
            jd_raw="vaga de engenheiro", title="Engenheiro de Software", seniority="senior",
            confirmed_technical=CONFIRMED_TECH, confirmed_behavioral=CONFIRMED_BEHAV,
            screening_mode="compact",
        )
        skills = [s.skill for s in enriched.skills_obrigatorias]
        assert "Python" in skills and "PostgreSQL" in skills
        assert "LLM_INVENTOU_TEC" not in skills, "confirmadas devem sobrescrever o LLM"
        assert len(enriched.skills_obrigatorias) == 5

    def test_behavioral_are_confirmed_verbatim(self):
        svc = _make_service_with_llm(_llm_json_with_different_competencies())
        enriched, _, _ = svc.enrich(
            jd_raw="vaga", title="Eng", seniority="senior",
            confirmed_technical=CONFIRMED_TECH, confirmed_behavioral=CONFIRMED_BEHAV,
            screening_mode="compact",
        )
        comps = [c.competencia for c in enriched.competencias_comportamentais]
        assert "Comunicação" in comps and "Autonomia" in comps
        assert "LLM_INVENTOU_COMP" not in comps
        assert len(enriched.competencias_comportamentais) == 2

    def test_behavioral_trait_preserved(self):
        svc = _make_service_with_llm(_llm_json_with_different_competencies())
        enriched, _, _ = svc.enrich(
            jd_raw="vaga", title="Eng", seniority="senior",
            confirmed_technical=CONFIRMED_TECH, confirmed_behavioral=CONFIRMED_BEHAV,
            screening_mode="compact",
        )
        by_name = {c.competencia: c.trait_big_five for c in enriched.competencias_comportamentais}
        assert by_name["Comunicação"] == "extraversion"
        assert by_name["Autonomia"] == "conscientiousness"

    def test_llm_prose_preserved(self):
        """about_role/responsabilidades vêm do LLM (JD consistente com competências)."""
        svc = _make_service_with_llm(_llm_json_with_different_competencies())
        enriched, _, _ = svc.enrich(
            jd_raw="vaga", title="Eng", seniority="senior",
            confirmed_technical=CONFIRMED_TECH, confirmed_behavioral=CONFIRMED_BEHAV,
            screening_mode="compact",
        )
        assert "consistente" in enriched.about_role.lower()
        assert len(enriched.responsabilidades) == 5


# ── 2. Sem confirmed_* → comportamento legado ────────────────────────────────

class TestLegacyPathWithoutConfirmed:
    def test_no_confirmed_uses_llm_generated(self):
        svc = _make_service_with_llm(_llm_json_with_different_competencies())
        enriched, _, _ = svc.enrich(
            jd_raw="vaga de engenheiro", title="Eng", seniority="senior",
        )
        skills = [s.skill for s in enriched.skills_obrigatorias]
        # Sem confirmadas, mantém o que o LLM gerou
        assert "LLM_INVENTOU_TEC" in skills


# ── 3. quality_score mode-aware ───────────────────────────────────────────────

class TestQualityScoreModeAware:
    def _enriched_compact(self):
        from app.domains.job_creation.schemas import (
            EnrichedJobDescription, TechnicalSkill, BehavioralCompetency,
        )
        return EnrichedJobDescription(
            titulo_padronizado="Dev",
            about_role="x" * 40,
            responsabilidades=["r1", "r2", "r3", "r4", "r5"],
            skills_obrigatorias=[TechnicalSkill(skill=f"S{i}") for i in range(5)],
            competencias_comportamentais=[BehavioralCompetency(competencia=f"C{i}") for i in range(2)],
        )

    def test_default_thresholds_backward_compat(self):
        from app.domains.job_creation.services.jd_enrichment import calculate_quality_score
        e = self._enriched_compact()
        # default (9/5): 5 técnicas + 2 comportamentais → parcial
        score, warnings = calculate_quality_score(e)
        assert score < 100.0  # penalizado por contagem no modo legado

    def test_mode_aware_compact_not_penalized(self):
        from app.domains.job_creation.services.jd_enrichment import calculate_quality_score
        e = self._enriched_compact()
        legacy, _ = calculate_quality_score(e)
        compact, warnings = calculate_quality_score(e, min_technical=5, min_behavioral=2)
        assert compact > legacy, "modo compact não deve ser penalizado pelos thresholds 9/5"
        assert compact >= 50.0, "JD compact válido não pode cair no warning/blocked por contagem"

    def test_enrich_compact_confirmed_scores_well(self):
        """enrich com 5+2 confirmadas + screening_mode=compact → score não-penalizado."""
        svc = _make_service_with_llm(_llm_json_with_different_competencies())
        _, score, _ = svc.enrich(
            jd_raw="vaga", title="Eng", seniority="senior",
            confirmed_technical=CONFIRMED_TECH, confirmed_behavioral=CONFIRMED_BEHAV,
            screening_mode="compact",
        )
        assert score >= 50.0, f"score compact penalizado indevidamente: {score}"


# ── 4. Fallback honra confirmed_* ─────────────────────────────────────────────

class TestFallbackHonorsConfirmed:
    def test_fallback_enrichment_sets_confirmed(self):
        from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
        svc = JdEnrichmentService()
        enriched = svc._fallback_enrichment(
            "vaga de eng", "Eng", "senior",
            confirmed_technical=CONFIRMED_TECH, confirmed_behavioral=CONFIRMED_BEHAV,
        )
        skills = [s.skill for s in enriched.skills_obrigatorias]
        comps = [c.competencia for c in enriched.competencias_comportamentais]
        assert "Python" in skills
        assert "Comunicação" in comps

    def test_fallback_without_confirmed_is_empty(self):
        """Backward compat: fallback legado (3 args) continua com listas vazias."""
        from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
        svc = JdEnrichmentService()
        enriched = svc._fallback_enrichment("vaga", "Eng", "senior")
        assert enriched.skills_obrigatorias == []
        assert enriched.competencias_comportamentais == []


# ── 5. Node wiring — passa confirmed_* + screening_mode ao enrich ────────────

class TestNodePassesConfirmedToEnrich:
    def test_node_forwards_confirmed_and_mode(self):
        import importlib
        node_mod = importlib.import_module("app.domains.job_creation.nodes.jd_enrichment")

        captured = {}

        class _FakeService:
            def enrich(self, **kwargs):
                from app.domains.job_creation.schemas import EnrichedJobDescription
                captured.update(kwargs)
                e = EnrichedJobDescription(
                    titulo_padronizado="Eng", about_role="ok",
                    responsabilidades=["a", "b", "c", "d", "e"],
                )
                return e, 75.0, []

            def _fallback_enrichment(self, *a, **k):
                from app.domains.job_creation.schemas import EnrichedJobDescription
                return EnrichedJobDescription()

        jd_text = (
            "Buscamos Engenheiro de Software Sênior para atuar no backend "
            "com Python, FastAPI e PostgreSQL. Responsável por APIs, deploy "
            "em Docker e qualidade de código. Trabalho remoto."
        )
        state = {
            "raw_input": jd_text,
            "jd_raw": jd_text,
            "parsed_title": "Engenheiro de Software",
            "parsed_seniority": "senior",
            "parsed_department": "Tecnologia",
            "screening_mode": "compact",
            "confirmed_technical_competencies": CONFIRMED_TECH,
            "confirmed_behavioral_competencies": CONFIRMED_BEHAV,
            "jd_enriched": None,
            "user_query": jd_text,
        }

        with mock.patch("app.domains.job_creation.graph._get_jd_service", return_value=_FakeService()):
            node_mod.jd_enrichment_node(state)

        assert captured.get("confirmed_technical") == CONFIRMED_TECH, (
            f"node deve repassar confirmed_technical; captured keys={list(captured.keys())}"
        )
        assert captured.get("confirmed_behavioral") == CONFIRMED_BEHAV
        assert captured.get("screening_mode") == "compact"
