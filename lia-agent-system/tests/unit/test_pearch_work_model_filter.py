"""
TDD — BUG: work_model nunca chega ao Pearch via to_pearch_custom_filters.

Causa raiz: SearchSpec.to_pearch_custom_filters() omite work_model + guarda
work_model values "remoto"/"híbrido" aparecendo erroneamente em location.

Ref: diagnóstico de busca híbrida 2026-06-09 (zero candidatos Pearch).
"""
import pytest
from libs.models.lia_models.pearch import SearchSpec


class TestToPearchCustomFiltersWorkModel:
    def test_work_model_remote_maps_to_remote(self):
        spec = SearchSpec(work_model="remote")
        filters = spec.to_pearch_custom_filters()
        assert filters.get("work_model") == "remote"

    def test_work_model_remoto_maps_to_remote(self):
        """PT value 'remoto' deve ser mapeado para 'remote' (Pearch EN API)."""
        spec = SearchSpec(work_model="remoto")
        filters = spec.to_pearch_custom_filters()
        assert filters.get("work_model") == "remote"

    def test_work_model_hibrido_maps_to_hybrid(self):
        spec = SearchSpec(work_model="híbrido")
        filters = spec.to_pearch_custom_filters()
        assert filters.get("work_model") == "hybrid"

    def test_work_model_presencial_maps_to_onsite(self):
        spec = SearchSpec(work_model="presencial")
        filters = spec.to_pearch_custom_filters()
        assert filters.get("work_model") == "onsite"

    def test_work_model_combined_with_other_filters(self):
        spec = SearchSpec(job_title="Product Manager", seniority="senior", work_model="remoto")
        filters = spec.to_pearch_custom_filters()
        assert filters.get("work_model") == "remote"
        assert filters.get("title") == "Product Manager"
        assert filters.get("seniority") == "senior"

    def test_location_remoto_excluded_from_location_filter(self):
        """'Remoto' em location NÃO deve ser enviado como filtro de cidade ao Pearch."""
        spec = SearchSpec(location="Remoto")
        filters = spec.to_pearch_custom_filters()
        assert "location" not in filters

    def test_location_hibrido_excluded_from_location_filter(self):
        spec = SearchSpec(location="híbrido")
        filters = spec.to_pearch_custom_filters()
        assert "location" not in filters

    def test_location_sao_paulo_is_kept(self):
        """Cidades reais devem passar como location."""
        spec = SearchSpec(location="São Paulo")
        filters = spec.to_pearch_custom_filters()
        assert filters.get("location") == "São Paulo"

    def test_no_work_model_no_key(self):
        """Sem work_model, chave não deve aparecer nos filtros."""
        spec = SearchSpec(job_title="Engineer")
        filters = spec.to_pearch_custom_filters()
        assert "work_model" not in filters
