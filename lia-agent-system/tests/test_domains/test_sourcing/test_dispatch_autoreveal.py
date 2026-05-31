"""Auto-reveal lazy no disparo de triagem (decisao Paulo).

Quando o canal precisa de email/telefone e o contato esta ausente, o dispatch
revela via Apify-first -> Pearch (enrich_candidate_contact) e persiste, antes de
desistir. Falha graciosa: None -> guard 'sem contato' assume.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.communication.services.transition_dispatch_service import (
    TransitionDispatchService,
)


@pytest.fixture
def svc():
    return TransitionDispatchService(db=MagicMock())


def _patch_enrichment(return_value=None, raises=None):
    fake = MagicMock()
    if raises is not None:
        fake.enrich_candidate_contact = AsyncMock(side_effect=raises)
    else:
        fake.enrich_candidate_contact = AsyncMock(return_value=return_value)
    return patch(
        "app.domains.sourcing.services.contact_enrichment_service.get_contact_enrichment_service",
        return_value=fake,
    ), fake


@pytest.mark.asyncio
async def test_reveal_email_success(svc):
    cd = {"candidate_id": "11111111-1111-1111-1111-111111111111"}
    cm, fake = _patch_enrichment({"success": True, "has_contact": True, "email": "ana@x.com", "phone": None})
    with cm:
        out = await svc._reveal_contact_for_dispatch(cd, "email", "comp-A")
    assert out == "ana@x.com"
    assert cd["email"] == "ana@x.com"  # sincroniza candidate_data
    fake.enrich_candidate_contact.assert_awaited_once()


@pytest.mark.asyncio
async def test_reveal_phone_success(svc):
    cd = {"candidate_id": "11111111-1111-1111-1111-111111111111"}
    cm, _ = _patch_enrichment({"success": True, "has_contact": True, "email": None, "phone": "+5511999999999"})
    with cm:
        out = await svc._reveal_contact_for_dispatch(cd, "phone", "comp-A")
    assert out == "+5511999999999"
    assert cd["phone"] == "+5511999999999"


@pytest.mark.asyncio
async def test_reveal_failure_returns_none(svc):
    cd = {"candidate_id": "11111111-1111-1111-1111-111111111111"}
    cm, _ = _patch_enrichment({"success": False})
    with cm:
        out = await svc._reveal_contact_for_dispatch(cd, "email", "comp-A")
    assert out is None


@pytest.mark.asyncio
async def test_reveal_exception_is_graceful(svc):
    cd = {"candidate_id": "11111111-1111-1111-1111-111111111111"}
    cm, _ = _patch_enrichment(raises=RuntimeError("apify down"))
    with cm:
        out = await svc._reveal_contact_for_dispatch(cd, "email", "comp-A")
    assert out is None  # nao propaga, guard assume


@pytest.mark.asyncio
async def test_no_candidate_id_returns_none(svc):
    out = await svc._reveal_contact_for_dispatch({}, "email", "comp-A")
    assert out is None
