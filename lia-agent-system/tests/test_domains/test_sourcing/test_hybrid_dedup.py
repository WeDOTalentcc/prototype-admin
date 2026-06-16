"""G-14: dedup Pearch x local por identidade (linkedin_url).

docid local (PK) != docid Pearch, entao o docid_blacklist nao dedupava o mesmo
humano persistido de uma busca anterior. Agora dedup por linkedin_url normalizado.
"""
from app.domains.sourcing.services.pearch_service import PearchService
from lia_models.pearch import CandidateProfile


def _c(name, url):
    return CandidateProfile(docid=name, name=name, linkedin_url=url)


def test_removes_pearch_dup_by_linkedin():
    local = [_c("Ana", "https://www.linkedin.com/in/ana/")]
    pearch = [
        _c("Ana", "http://linkedin.com/in/ana"),  # mesma pessoa, variante de URL
        _c("Bob", "https://linkedin.com/in/bob"),
    ]
    out = PearchService._dedup_pearch_against_local(local, pearch)
    names = [c.name for c in out]
    assert names == ["Bob"]  # Ana removida (ja no local)


def test_no_local_urls_returns_all():
    local = [_c("X", None)]
    pearch = [_c("Bob", "https://linkedin.com/in/bob")]
    out = PearchService._dedup_pearch_against_local(local, pearch)
    assert len(out) == 1


def test_no_overlap_keeps_all():
    local = [_c("Ana", "https://linkedin.com/in/ana")]
    pearch = [_c("Bob", "https://linkedin.com/in/bob"), _c("Carol", "https://linkedin.com/in/carol")]
    out = PearchService._dedup_pearch_against_local(local, pearch)
    assert len(out) == 2


def test_url_normalization_variants_match():
    local = [_c("Ana", "LinkedIn.com/in/Ana/")]
    pearch = [_c("Ana2", "https://www.linkedin.com/in/ana?utm=x")]
    out = PearchService._dedup_pearch_against_local(local, pearch)
    assert out == []  # casa apesar de protocolo/www/case/querystring/trailing slash
