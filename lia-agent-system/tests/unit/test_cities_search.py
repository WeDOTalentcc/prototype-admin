"""
Onda 2B — busca de cidades (dataset global IBGE).
"""
from app.domains.job_management.services.cities_service import search_cities


class TestSearchCities:
    def test_finds_sao_paulo(self):
        labels = [c["name"] for c in search_cities("são paulo", limit=10)]
        assert "São Paulo, SP" in labels

    def test_accent_insensitive(self):
        labels = [c["name"] for c in search_cities("sao paulo", limit=10)]
        assert "São Paulo, SP" in labels

    def test_empty_returns_limited(self):
        r = search_cities("", limit=20)
        assert 0 < len(r) <= 20

    def test_limit_respected(self):
        assert len(search_cities("a", limit=5)) <= 5

    def test_shape_id_equals_name(self):
        r = search_cities("rio de janeiro", limit=5)
        assert r
        assert {"id", "name"} <= set(r[0].keys())
        assert r[0]["id"] == r[0]["name"]
