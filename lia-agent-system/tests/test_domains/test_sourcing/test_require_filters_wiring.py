"""Anti-ghost-setting: filtros require_emails/require_phone_numbers fluem ponta-a-ponta.

Bug (pre-fix): a UI mandava require_emails/require_phone_numbers, o SearchRequestDTO
recebia, mas a rota montava HybridSearchRequest SEM esses campos (o modelo nem os tinha)
e o hybrid_search montava PearchSearchRequest com require_*=False default. O filtro
"so candidatos com email/telefone" era silenciosamente ignorado.

Estes sensores pinam o contrato em cada elo da cadeia.
"""
import inspect

from lia_models.pearch import HybridSearchRequest, PearchSearchRequest, SearchType
from app.api.v1.candidate_search._shared import SearchRequestDTO


def test_dto_carries_require_flags():
    f = SearchRequestDTO.model_fields
    assert "require_emails" in f
    assert "require_phone_numbers" in f


def test_hybrid_request_carries_require_flags():
    # antes do fix, HybridSearchRequest NAO tinha esses campos
    f = HybridSearchRequest.model_fields
    assert "require_emails" in f, "HybridSearchRequest deve propagar require_emails"
    assert "require_phone_numbers" in f, "HybridSearchRequest deve propagar require_phone_numbers"


def test_hybrid_request_accepts_and_stores_flags():
    h = HybridSearchRequest(
        query="dev", require_emails=True, require_phone_numbers=True,
    )
    assert h.require_emails is True
    assert h.require_phone_numbers is True


def test_route_copies_require_flags_into_hybrid_request():
    # garante que a rota nao volte a "esquecer" de copiar os flags
    from app.api.v1.candidate_search import search as search_module
    src = inspect.getsource(search_module.search_candidates)
    assert "require_emails=request.require_emails" in src
    assert "require_phone_numbers=request.require_phone_numbers" in src


def test_hybrid_search_sets_require_flags_on_pearch_request():
    from app.domains.sourcing.services.pearch_service import PearchService
    src = inspect.getsource(PearchService.hybrid_search)
    assert "require_emails=request.require_emails" in src
    assert "require_phone_numbers=request.require_phone_numbers" in src


def test_pearch_request_both_required_is_AND_semantics():
    # "ambos" = email E telefone obrigatorios (decisao Paulo): os dois flags True
    r = PearchSearchRequest(query="dev", type=SearchType.FAST,
                            require_emails=True, require_phone_numbers=True)
    assert r.require_emails is True and r.require_phone_numbers is True
