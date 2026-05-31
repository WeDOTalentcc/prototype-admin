"""Salvar exige email (reveal Apify no save) + opcao de salvar sem email (Paulo).

- sem email + Apify revela -> importado com email
- sem email + Apify falha + save_without_email=False -> NAO importado (skipped_no_email)
- sem email + Apify falha + save_without_email=True -> importado mesmo assim (escolha)
"""
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.candidate_search.import_export import import_pearch_candidates
from app.api.v1.candidate_search._shared import (
    ImportCandidateDTO,
    ImportCandidatesRequest,
)


def _empty_db():
    db = MagicMock()
    res = MagicMock()
    res.scalars.return_value.first.return_value = None  # nada existente -> branch de criacao
    db.execute = AsyncMock(return_value=res)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    return db


def _dto(pid, email=None):
    return ImportCandidateDTO(
        pearch_id=pid, name="Ana Lima",
        linkedin_url="https://linkedin.com/in/ana", email=email,
    )


def _enrich(has_email):
    fake = MagicMock()
    fake.enrich_by_linkedin_url = AsyncMock(return_value={
        "success": True, "has_contact": has_email,
        "email": "ana@x.com" if has_email else None, "phone": None,
    })
    return patch(
        "app.domains.sourcing.services.contact_enrichment_service.get_contact_enrichment_service",
        return_value=fake,
    )


async def _run(req):
    user = types.SimpleNamespace(id="u1", company_id="comp-A")
    with patch("app.api.v1.candidate_search.import_export.get_user_company_id", return_value="comp-A"):
        return await import_pearch_candidates(req, current_user=user, db=_empty_db(), company_id="comp-A")


@pytest.mark.asyncio
async def test_no_email_apify_reveals_then_imported():
    req = ImportCandidatesRequest(candidates=[_dto("p1")])
    with _enrich(has_email=True):
        resp = await _run(req)
    assert resp.imported_count == 1
    assert resp.skipped_no_email_ids == []


@pytest.mark.asyncio
async def test_no_email_apify_fails_default_skips():
    req = ImportCandidatesRequest(candidates=[_dto("p1")])
    with _enrich(has_email=False):
        resp = await _run(req)
    assert resp.imported_count == 0
    assert "p1" in resp.skipped_no_email_ids


@pytest.mark.asyncio
async def test_no_email_apify_fails_save_without_email_imports():
    req = ImportCandidatesRequest(candidates=[_dto("p1")], save_without_email=True)
    with _enrich(has_email=False):
        resp = await _run(req)
    assert resp.imported_count == 1
    assert resp.skipped_no_email_ids == []


@pytest.mark.asyncio
async def test_email_already_present_no_reveal_call():
    req = ImportCandidatesRequest(candidates=[_dto("p1", email="ja@x.com")])
    with _enrich(has_email=True) as _:
        resp = await _run(req)
    assert resp.imported_count == 1
    assert resp.skipped_no_email_ids == []
