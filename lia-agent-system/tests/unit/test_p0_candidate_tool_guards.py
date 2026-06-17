"""Fix P0 (2026-06-06): view_candidate_profile crashava com candidate_id=''
(asyncpg invalid UUID) e compare_candidates com <2 ids devolvia vazio -> IA
improvisava candidatos errados. Guards = falha graciosa, sem crash."""
import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.shared.entity_resolver import set_active_candidate, get_active_candidate
from app.domains.recruiter_assistant.agents import talent_tool_registry as tr

_CID = "00000000-0000-4000-a000-000000000001"


def test_active_candidate_contextvar():
    set_active_candidate("cand-123")
    assert get_active_candidate() == "cand-123"
    set_active_candidate("")
    assert get_active_candidate() == ""
    set_active_candidate(None)
    assert get_active_candidate() == ""


@pytest.mark.asyncio
async def test_view_profile_id_vazio_nao_crasha():
    tok = _current_company_id.set(_CID)
    try:
        set_active_candidate("")  # sem fallback
        out = await tr._wrap_view_candidate_profile(candidate_id="")
        assert out.get("success") is False
        assert out.get("needs_clarification") is True
    finally:
        _current_company_id.reset(tok)
        set_active_candidate("")


@pytest.mark.asyncio
async def test_view_profile_usa_active_candidate_fallback():
    tok = _current_company_id.set(_CID)
    try:
        set_active_candidate("cand-from-context")
        # nao passa candidate_id -> usa o active; nao retorna o guard de id vazio
        out = await tr._wrap_view_candidate_profile()
        assert out.get("needs_clarification") is not True
    finally:
        _current_company_id.reset(tok)
        set_active_candidate("")


@pytest.mark.asyncio
async def test_compare_menos_de_2_ids_graceful():
    tok = _current_company_id.set(_CID)
    try:
        out = await tr._wrap_compare_candidates(candidate_ids=["", ""])
        assert out.get("success") is False
        assert out.get("needs_clarification") is True
    finally:
        _current_company_id.reset(tok)
