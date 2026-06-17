"""Reveal-sob-demanda: enrich_and_filter_candidates NAO descarta nem enriquece por padrao.

Antes: enriquecia via Apify (lento -> 504) e descartava candidatos sem contato revelado
(causava "Sem resultados" mesmo com Pearch retornando candidatos). Agora, com a flag
SEARCH_EAGER_CONTACT_ENRICHMENT off (default), e pass-through: mantem todos, sem Apify.
"""
import types
import pytest
from unittest.mock import MagicMock, patch

from app.api.v1.candidate_search._shared import enrich_and_filter_candidates


def _cand(cid, source="pearch", email=None, phone=None):
    return types.SimpleNamespace(
        id=cid, source=source, email=email, phone=phone,
        has_email=True, has_phone=False, linkedin_url=f"https://linkedin.com/in/{cid}",
        contact_source=None,
    )


@pytest.mark.asyncio
async def test_passthrough_keeps_all_candidates():
    # candidato sem contato revelado NAO deve ser descartado (modelo reveal-sob-demanda)
    cands = [_cand("1", email="a@x.com"), _cand("2", email=None, phone=None)]
    out = await enrich_and_filter_candidates(db=None, candidates=cands, company_id="comp-A")
    assert len(out) == 2
    ids = {c.id for c in out}
    assert ids == {"1", "2"}


@pytest.mark.asyncio
async def test_passthrough_does_not_call_apify():
    cands = [_cand("2", email=None)]
    fake = MagicMock()
    with patch(
        "app.domains.sourcing.services.contact_enrichment_service.get_contact_enrichment_service",
        return_value=fake,
    ):
        await enrich_and_filter_candidates(db=None, candidates=cands, company_id="comp-A")
    # nenhuma chamada de enriquecimento Apify no caminho padrao
    fake.enrich_batch.assert_not_called()
    fake.enrich_by_linkedin_url.assert_not_called()


@pytest.mark.asyncio
async def test_sets_contact_source_label():
    cands = [_cand("1", source="pearch"), _cand("2", source="local")]
    out = await enrich_and_filter_candidates(db=None, candidates=cands, company_id="comp-A")
    by_id = {c.id: c for c in out}
    assert by_id["1"].contact_source == "pearch"
    assert by_id["2"].contact_source == "local"
