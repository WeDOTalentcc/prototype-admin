"""G-06: map_to_search_dto descarta perfis sem identidade (anti card-fantasma).

Apify (path de fallback quando circuito Pearch abre) pode retornar perfis lixo
de scraping. Antes, viravam um CandidateSearchResultDTO "Unknown" sem link.
Agora o produtor retorna None para perfil sem identidade minima e o consumidor pula.
"""
import pytest

from app.domains.sourcing.services.apify_search_service import ApifySearchService


@pytest.fixture
def service():
    return ApifySearchService()


def test_empty_profile_returns_none(service):
    assert service.map_to_search_dto({}) is None


def test_junk_profile_without_identity_returns_none(service):
    # so chaves irrelevantes — sem nome, headline ou linkedin
    junk = {"connectionCount": 10, "skills": ["X"], "summary": "..."}
    assert service.map_to_search_dto(junk) is None


def test_profile_with_only_linkedin_is_valid(service):
    dto = service.map_to_search_dto({"linkedin_url": "https://linkedin.com/in/ana"})
    assert dto is not None
    assert dto["linkedin_url"] == "https://linkedin.com/in/ana"
    assert dto["source"] == "apify_search"


def test_profile_with_only_headline_is_valid(service):
    dto = service.map_to_search_dto({"headline": "Senior Engineer"})
    assert dto is not None
    assert dto["name"] == "Senior Engineer"


def test_profile_with_name_is_valid(service):
    dto = service.map_to_search_dto({"first_name": "Ana", "last_name": "Lima"})
    assert dto is not None
    assert dto["name"] == "Ana Lima"
    assert dto["first_name"] == "Ana"
