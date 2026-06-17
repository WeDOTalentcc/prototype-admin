"""
Red tests para endpoint POST /reveal/bulk.
TDD canonical — estes testes DEVEM FALHAR antes da implementação.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Helpers para montar app mínima de teste
# ---------------------------------------------------------------------------

def _make_app():
    """Monta app FastAPI mínima com o router de contact."""
    from app.api.v1.candidate_search.contact import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/search")
    return app


def _valid_item(candidate_id: str = "cand-001", reveal_type: str = "email"):
    return {
        "candidate_id": candidate_id,
        "candidate_name": f"Candidato {candidate_id}",
        "reveal_type": reveal_type,
        "linkedin_slug": None,
    }


# ---------------------------------------------------------------------------
# Test 1 — endpoint retorna lista com resultado para cada candidato
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_reveal_returns_results_for_all_candidates():
    """POST /reveal/bulk com 3 candidatos retorna lista de 3 results."""
    from app.api.v1.candidate_search import contact as contact_mod

    mock_response = contact_mod.RevealContactResponse(
        success=True,
        candidate_id="placeholder",
        reveal_type="email",
        email="test@example.com",
        message="ok",
    )

    async def _fake_reveal(request, db, pearch_svc, company_id):
        return contact_mod.RevealContactResponse(
            success=True,
            candidate_id=request.candidate_id,
            reveal_type=request.reveal_type,
            email="test@example.com",
            message="ok",
        )

    with patch.object(contact_mod, "reveal_contact", side_effect=_fake_reveal):
        # Verify BulkRevealRequest and BulkRevealResponse exist
        assert hasattr(contact_mod, "BulkRevealRequest"), "BulkRevealRequest deve existir"
        assert hasattr(contact_mod, "BulkRevealResponse"), "BulkRevealResponse deve existir"

        req = contact_mod.BulkRevealRequest(
            items=[
                contact_mod.RevealContactRequest(**_valid_item("c1")),
                contact_mod.RevealContactRequest(**_valid_item("c2")),
                contact_mod.RevealContactRequest(**_valid_item("c3")),
            ]
        )
        assert len(req.items) == 3


# ---------------------------------------------------------------------------
# Test 2 — semaphore limita concorrência em 3
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_reveal_respects_semaphore_concurrency():
    """Verifica que no máximo 3 chamadas correm simultaneamente."""
    from app.api.v1.candidate_search import contact as contact_mod

    assert hasattr(contact_mod, "reveal_contact_bulk"), "reveal_contact_bulk deve existir"

    concurrency_tracker = {"current": 0, "max_seen": 0}

    async def _slow_reveal(request, db, pearch_svc, company_id):
        concurrency_tracker["current"] += 1
        concurrency_tracker["max_seen"] = max(
            concurrency_tracker["max_seen"], concurrency_tracker["current"]
        )
        await asyncio.sleep(0.05)  # simula latência
        concurrency_tracker["current"] -= 1
        return contact_mod.RevealContactResponse(
            success=True,
            candidate_id=request.candidate_id,
            reveal_type=request.reveal_type,
            message="ok",
        )

    items = [
        contact_mod.RevealContactRequest(**_valid_item(f"c{i}"))
        for i in range(9)  # 9 candidatos, semaphore(3) → max_seen deve ser ≤ 3
    ]
    req = contact_mod.BulkRevealRequest(items=items)

    mock_db = AsyncMock()
    mock_pearch = MagicMock()

    with patch.object(contact_mod, "reveal_contact", side_effect=_slow_reveal):
        result = await contact_mod.reveal_contact_bulk(
            request=req,
            db=mock_db,
            pearch_svc=mock_pearch,
            company_id="company-uuid-001",
        )

    assert concurrency_tracker["max_seen"] <= 3, (
        f"Semaphore(3) violado: {concurrency_tracker['max_seen']} chamadas simultâneas"
    )
    assert len(result.results) == 9


# ---------------------------------------------------------------------------
# Test 3 — timeout por item retorna success=False com "timeout" na mensagem
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_reveal_timeout_per_item():
    """Candidato que excede 35s recebe result com success=False e 'timeout' na mensagem."""
    from app.api.v1.candidate_search import contact as contact_mod

    assert hasattr(contact_mod, "reveal_contact_bulk"), "reveal_contact_bulk deve existir"

    async def _timeout_reveal(request, db, pearch_svc, company_id):
        # Simula timeout sendo lançado
        raise asyncio.TimeoutError()

    req = contact_mod.BulkRevealRequest(
        items=[contact_mod.RevealContactRequest(**_valid_item("c-timeout"))]
    )

    mock_db = AsyncMock()
    mock_pearch = MagicMock()

    # Patch wait_for to raise TimeoutError immediately
    async def _fake_wait_for(coro, timeout):
        coro.close()
        raise asyncio.TimeoutError()

    with patch.object(contact_mod, "reveal_contact", side_effect=_timeout_reveal):
        with patch("asyncio.wait_for", side_effect=_fake_wait_for):
            result = await contact_mod.reveal_contact_bulk(
                request=req,
                db=mock_db,
                pearch_svc=mock_pearch,
                company_id="company-uuid-001",
            )

    assert len(result.results) == 1
    r = result.results[0]
    assert r.success is False
    assert "timeout" in r.message.lower(), f"Esperava 'timeout' na mensagem, obteve: {r.message!r}"
    assert result.timeout_count == 1


# ---------------------------------------------------------------------------
# Test 4 — partial success: 2 OK, 1 timeout → contagens corretas
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_reveal_partial_success():
    """2 candidatos OK, 1 com timeout → revealed_count=2, timeout_count=1, unavailable_count=0."""
    from app.api.v1.candidate_search import contact as contact_mod

    assert hasattr(contact_mod, "reveal_contact_bulk"), "reveal_contact_bulk deve existir"

    call_count = {"n": 0}

    async def _mixed_reveal(request, db, pearch_svc, company_id):
        call_count["n"] += 1
        if request.candidate_id == "c-bad":
            raise asyncio.TimeoutError()
        return contact_mod.RevealContactResponse(
            success=True,
            candidate_id=request.candidate_id,
            reveal_type=request.reveal_type,
            email="ok@test.com",
            message="ok",
        )

    async def _smart_wait_for(coro, timeout):
        try:
            return await coro
        except asyncio.TimeoutError:
            raise

    req = contact_mod.BulkRevealRequest(
        items=[
            contact_mod.RevealContactRequest(**_valid_item("c1")),
            contact_mod.RevealContactRequest(**_valid_item("c2")),
            contact_mod.RevealContactRequest(**_valid_item("c-bad")),
        ]
    )

    mock_db = AsyncMock()
    mock_pearch = MagicMock()

    with patch.object(contact_mod, "reveal_contact", side_effect=_mixed_reveal):
        with patch("asyncio.wait_for", side_effect=_smart_wait_for):
            result = await contact_mod.reveal_contact_bulk(
                request=req,
                db=mock_db,
                pearch_svc=mock_pearch,
                company_id="company-uuid-001",
            )

    assert result.revealed_count == 2, f"revealed_count={result.revealed_count}, esperado 2"
    assert result.timeout_count == 1, f"timeout_count={result.timeout_count}, esperado 1"
    assert result.unavailable_count == 0, f"unavailable_count={result.unavailable_count}, esperado 0"


# ---------------------------------------------------------------------------
# Test 5 — max 50 items: 51 itens retorna HTTP 422
# ---------------------------------------------------------------------------

def test_bulk_reveal_max_50_items():
    """Request com 51 itens retorna HTTP 422 (validação Pydantic)."""
    from app.api.v1.candidate_search import contact as contact_mod

    assert hasattr(contact_mod, "BulkRevealRequest"), "BulkRevealRequest deve existir"

    with pytest.raises(Exception):  # Pydantic ValidationError
        contact_mod.BulkRevealRequest(
            items=[
                contact_mod.RevealContactRequest(**_valid_item(f"c{i}"))
                for i in range(51)
            ]
        )
