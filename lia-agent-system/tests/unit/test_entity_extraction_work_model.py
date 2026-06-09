"""
TDD — BUG: extrator de entidades em jd_search.py coloca 'remoto'/'híbrido'
em location em vez de work_model.

Causa raiz: work_models estava em all_locations → match devolvia
entities.location = "Remoto" (work model value, não cidade).

Ref: diagnóstico busca híbrida 2026-06-09.
"""
import re
import pytest


def _extract_entities(query: str) -> dict:
    """
    Replica a lógica de extração de entidades de jd_search.py.
    Deve ser atualizada junto com a função real.
    Usamos import direto do módulo para garantir ground-truth.
    """
    from app.api.v1.candidate_search.jd_search import _extract_search_entities
    return _extract_search_entities(query)


class TestEntityExtractionWorkModel:
    def test_remoto_goes_to_work_model_not_location(self):
        """BUG: antes 'remoto' ia para location='Remoto'. Agora deve ir para work_model."""
        result = _extract_entities("product manager remoto")
        assert result.get("work_model") == "remote"
        assert result.get("location") != "Remoto"
        assert result.get("location") is None or result.get("location") == ""

    def test_hibrido_goes_to_work_model(self):
        result = _extract_entities("desenvolvedor híbrido")
        assert result.get("work_model") == "hybrid"
        assert result.get("location") != "Híbrido"

    def test_presencial_goes_to_work_model(self):
        result = _extract_entities("analista presencial")
        assert result.get("work_model") == "onsite"
        assert result.get("location") != "Presencial"

    def test_location_sao_paulo_is_still_extracted(self):
        """Cidades reais devem continuar funcionando."""
        result = _extract_entities("desenvolvedor São Paulo")
        assert result.get("location") is not None
        assert "paulo" in result.get("location", "").lower()

    def test_work_model_and_location_both_present(self):
        """Query com modelo DE TRABALHO e CIDADE separados."""
        result = _extract_entities("product manager remoto São Paulo")
        assert result.get("work_model") == "remote"
        assert result.get("location") is not None
        assert "paulo" in result.get("location", "").lower()

    def test_job_title_still_extracted(self):
        result = _extract_entities("product manager remoto")
        assert result.get("job_title") is not None
        assert "product manager" in result.get("job_title", "").lower()
