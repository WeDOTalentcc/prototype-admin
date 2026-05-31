"""Consolidação WSI Fase 3.1: scorer 9-dim JD canônico em cv_screening.

Pina a lógica determinística D1-D9 + bands + can_generate. Testes puros.
Antes vivia inline no endpoint /jd-evaluate; agora canônico (endpoint + wizard
delegam). _shared re-exporta para compat.
"""
import pytest

from app.domains.cv_screening.services.wsi_service.jd_quality import (
    evaluate_jd_quality,
    _jd_get_band,
)


@pytest.mark.medium
def test_excellent_jd_scores_high():
    r = evaluate_jd_quality(
        description=(
            "Nossa empresa de tecnologia busca um engenheiro senior para a equipe de "
            "plataforma. Trabalho colaborativo em time multidisciplinar de um setor de "
            "saúde digital. " + ("contexto detalhado " * 30)
        ),
        job_title="Engenheiro de Software Sênior",
        department="Tecnologia",
        seniority="senior",
        responsibilities=["r1", "r2", "r3", "r4", "r5"],
        technical_skills=[f"s{i}" for i in range(9)],
        behavioral_competencies=["c1", "c2", "c3", "c4", "c5"],
    )
    assert r["score"] >= 85
    assert r["band"] == "excelente"
    assert r["can_generate"] is True
    assert len(r["indicators"]) == 9
    assert {i["dimension"] for i in r["indicators"]} == {f"D{n}" for n in range(1, 10)}


@pytest.mark.medium
def test_critical_jd_blocks():
    r = evaluate_jd_quality(
        description="vaga", job_title="analista", responsibilities=[],
        technical_skills=[], behavioral_competencies=[],
    )
    assert r["score"] < 30
    assert r["band"] == "critico"
    assert r["can_generate"] is False


@pytest.mark.medium
def test_d8_bias_detection_zeroes_dimension():
    r = evaluate_jd_quality(
        description="buscamos jovem com boa aparência",
        job_title="vendedor", seniority="pleno",
        responsibilities=["r1", "r2"], technical_skills=["a", "b", "c"],
        behavioral_competencies=["x", "y"],
    )
    d8 = next(i for i in r["indicators"] if i["dimension"] == "D8")
    assert d8["earned"] == 0
    assert d8["status"] == "insufficient"
    assert r["details"]["bias_terms_found"]  # detectou viés


@pytest.mark.medium
def test_d6_contradiction_detection():
    r = evaluate_jd_quality(
        description="trabalho com autonomia mas tudo precisa de aprovação " + ("x " * 90),
        job_title="analista sênior", seniority="senior",
        responsibilities=["r1", "r2", "r3"], technical_skills=["a", "b", "c"],
        behavioral_competencies=["x", "y"],
    )
    d6 = next(i for i in r["indicators"] if i["dimension"] == "D6")
    assert d6["earned"] == 0
    assert r["details"]["has_inconsistency"] is True


@pytest.mark.medium
def test_bands_thresholds():
    assert _jd_get_band(90) == ("excelente", "Excelente")
    assert _jd_get_band(72) == ("bom", "Bom")
    assert _jd_get_band(55) == ("adequado", "Adequado")
    assert _jd_get_band(35) == ("insuficiente", "Insuficiente")
    assert _jd_get_band(10) == ("critico", "Crítico")


@pytest.mark.medium
def test_shared_reexports_canonical():
    # _shared deve re-exportar do canônico (single source, sem drift).
    from app.api.v1.wsi import _shared
    from app.domains.cv_screening.services.wsi_service import jd_quality
    assert _shared._BIAS_TERMS is jd_quality._BIAS_TERMS
    assert _shared._JD_BANDS is jd_quality._JD_BANDS
    assert _shared.evaluate_jd_quality is jd_quality.evaluate_jd_quality
