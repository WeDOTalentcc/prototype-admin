"""Consolidação WSI Fase 3.3: 3 scorers de qualidade de JD → 1 canônico 9-dim.

- evaluate_jd_quality ganha d3_min/d4_min (mode-aware: compact não penalizado).
- job_creation.calculate_quality_score delega (mode-aware via min_technical/min_behavioral).
- job_management._calculate_wsi_quality delega (0-1 derivado de /100).
Testes puros.
"""
import pytest

from app.domains.cv_screening.services.wsi_service.jd_quality import evaluate_jd_quality


@pytest.mark.medium
def test_d3_mode_aware_threshold():
    # 5 skills: com d3_min=9 (full) -> partial; com d3_min=5 (compact) -> sufficient.
    kw = dict(
        description="vaga", job_title="eng sênior", seniority="senior",
        responsibilities=["a", "b", "c"], technical_skills=["s1", "s2", "s3", "s4", "s5"],
        behavioral_competencies=["b1", "b2"],
    )
    full = evaluate_jd_quality(**kw, d3_min=9)
    compact = evaluate_jd_quality(**kw, d3_min=5)
    d3_full = next(i for i in full["indicators"] if i["dimension"] == "D3")
    d3_compact = next(i for i in compact["indicators"] if i["dimension"] == "D3")
    assert d3_full["status"] == "partial"
    assert d3_compact["status"] == "sufficient"
    assert compact["score"] > full["score"]  # compact não penaliza os 5 skills


@pytest.mark.medium
def test_d4_mode_aware_threshold():
    kw = dict(
        description="vaga", job_title="eng", seniority="pleno",
        responsibilities=["a", "b"], technical_skills=["s1"],
        behavioral_competencies=["b1", "b2"],
    )
    full = evaluate_jd_quality(**kw, d4_min=5)
    compact = evaluate_jd_quality(**kw, d4_min=2)
    d4_full = next(i for i in full["indicators"] if i["dimension"] == "D4")
    d4_compact = next(i for i in compact["indicators"] if i["dimension"] == "D4")
    assert d4_full["status"] == "partial"
    assert d4_compact["status"] == "sufficient"


@pytest.mark.medium
def test_default_minimums_unchanged():
    # default d3_min=9, d4_min=5 (paridade /jd-evaluate).
    r = evaluate_jd_quality(
        description="vaga", job_title="eng", responsibilities=[],
        technical_skills=["s1", "s2", "s3"], behavioral_competencies=["b1", "b2"],
    )
    d3 = next(i for i in r["indicators"] if i["dimension"] == "D3")
    assert d3["minimum"] == 9  # default ideal mantido


@pytest.mark.medium
def test_job_creation_calculate_quality_score_delegates():
    """calculate_quality_score agora retorna o score 9-dim canônico (mode-aware)."""
    from app.domains.job_creation.services.jd_enrichment import calculate_quality_score
    from app.domains.job_creation.schemas import (
        EnrichedJobDescription, TechnicalSkill, BehavioralCompetency,
    )
    enriched = EnrichedJobDescription(
        titulo_padronizado="Engenheiro de Software Sênior",
        senioridade_confirmada="senior",
        about_role="Lidera o design de sistemas distribuidos na nossa empresa de tecnologia. " * 5,
        responsabilidades=["r1", "r2", "r3", "r4", "r5"],
        skills_obrigatorias=[TechnicalSkill(skill=f"s{i}", contexto="") for i in range(9)],
        competencias_comportamentais=[BehavioralCompetency(competencia=f"c{i}") for i in range(5)],
    )
    score, warnings = calculate_quality_score(enriched)
    assert 0 <= score <= 100
    assert isinstance(warnings, list)
    # JD completo de alta qualidade → score alto
    assert score >= 70
