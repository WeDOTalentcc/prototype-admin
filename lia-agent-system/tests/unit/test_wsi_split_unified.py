"""Sensor #3 (audit 2026-06-05): split WSI unificado na fonte per-senioridade.

Pina que sugestao de competencias, auto-complete e validador concordam no split
por (modo, senioridade) -- elimina a 13a pergunta (gerava 8+4, validador exigia
7+5 para senior full). Decisao Paulo: per-senioridade (YAML) e canonical.
"""
import pytest


class TestBlockDistribution:
    def test_full_senior_7_5(self):
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution
        assert block_distribution("full", "senior") == {"technical": 7, "behavioral": 5}
        assert block_distribution("full", "sênior") == {"technical": 7, "behavioral": 5}

    def test_full_pleno_8_4(self):
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution
        assert block_distribution("full", "pleno") == {"technical": 8, "behavioral": 4}

    def test_compact_senior_4_3(self):
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution
        assert block_distribution("compact", "senior") == {"technical": 4, "behavioral": 3}

    def test_default_pleno_quando_senioridade_desconhecida(self):
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution
        # "alien" nao existe -> cai em pleno do modo.
        assert block_distribution("compact", "alien") == {"technical": 5, "behavioral": 2}

    def test_invariante_soma_eh_total(self):
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution
        for sen in ("estagiario", "junior", "pleno", "senior", "lead", "diretor"):
            c = block_distribution("compact", sen)
            f = block_distribution("full", sen)
            assert c["technical"] + c["behavioral"] == 7
            assert f["technical"] + f["behavioral"] == 12


class TestConsumidoresConcordam:
    def test_graph_delega_ao_helper(self):
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution
        from app.domains.job_creation.graph import _get_question_distribution
        for mode in ("compact", "full"):
            for sen in ("estagiario", "junior", "pleno", "senior", "lead", "diretor"):
                assert block_distribution(mode, sen) == _get_question_distribution(mode, sen)

    def test_competency_target_counts_seniority_aware(self):
        from app.domains.analytics.services.competency_benchmark_service import (
            CompetencyBenchmarkService,
        )
        svc = CompetencyBenchmarkService()
        # O caso real do bug: senior full -> 7+5 (antes era 8+4).
        assert svc._target_counts("full", "senior") == (7, 5)
        assert svc._target_counts("full", "pleno") == (8, 4)
        assert svc._target_counts("compact", "senior") == (4, 3)

    def test_jd_thresholds_seniority_aware(self):
        from app.domains.job_creation.services.jd_enrichment import (
            _resolve_quality_thresholds,
        )
        confirmed = [{"x": 1}]
        # full/senior -> 7+5 (com confirmadas + modo conhecido).
        assert _resolve_quality_thresholds("full", confirmed, confirmed, "senior") == (7, 5)
        assert _resolve_quality_thresholds("full", confirmed, confirmed, "pleno") == (8, 4)
