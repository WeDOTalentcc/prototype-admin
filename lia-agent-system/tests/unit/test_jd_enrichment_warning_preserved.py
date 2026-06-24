"""Sensor (audit C9/#15 2026-06-05): o marker de falha do fallback de enrichment
NAO pode ser silenciosamente sobrescrito pelos warnings de quality_score.

Bug: em ``JdEnrichmentService.enrich``, quando o parse do LLM falha, o
``_fallback_enrichment`` seta ``wsi_quality_warnings=["Enriquecimento por LLM
falhou — usando fallback minimo"]``, mas a linha seguinte fazia
``enriched.wsi_quality_warnings = warnings`` (de calculate_quality_score),
apagando o sinal de que o enrich nao foi confiavel. Falha silenciosa = anti-harness.
"""
from unittest.mock import MagicMock

from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService

_MARKER = "Enriquecimento por LLM falhou"


def _enrich_with_broken_llm():
    svc = JdEnrichmentService()
    fake = MagicMock()
    # content nao-JSON -> json.loads levanta -> caminho de fallback
    fake.invoke.return_value = MagicMock(content="isto nao e json valido")
    svc._llm = fake
    return svc.enrich(
        jd_raw="Engenheiro de dados com SQL e Python para pipelines de ETL.",
        title="Engenheiro de Dados",
        seniority="pleno",
    )


def test_fallback_marker_survives_in_field():
    enriched, _score, _warnings = _enrich_with_broken_llm()
    assert any(_MARKER in w for w in (enriched.wsi_quality_warnings or [])), (
        "marker de falha do fallback perdido em enriched.wsi_quality_warnings: "
        f"{enriched.wsi_quality_warnings}. "
        "-> Fix: em jd_enrichment.py, NAO sobrescrever wsi_quality_warnings; "
        "fazer merge-dedup preservando os warnings previos (fallback/circuit breaker)."
    )


def test_fallback_marker_survives_in_returned_tuple():
    _enriched, _score, warnings = _enrich_with_broken_llm()
    assert any(_MARKER in w for w in (warnings or [])), (
        "marker de falha do fallback perdido na tupla de warnings retornada: "
        f"{warnings}. Callers nao conseguem detectar que o enrich caiu no fallback."
    )
