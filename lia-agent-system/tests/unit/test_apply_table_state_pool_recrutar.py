"""Unit tests for _wrap_apply_table_state — talent_pool and recrutar surfaces.

Covers the _pool_patch and _recrutar_patch helpers introduced in Fase 2
(ponte in-page).  All tests are pure (no DB / no network); they inject the
company_id ContextVar so that @tool_handler does not short-circuit.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def _tenant():
    """Inject a fake company_id into the auth ContextVar."""
    from app.middleware.auth_enforcement import _current_company_id
    tok = _current_company_id.set("test-company-uuid")
    yield
    _current_company_id.reset(tok)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _call(**kwargs):
    """Invoke _wrap_apply_table_state with given kwargs."""
    from app.domains.recruiter_assistant.agents.ui_tool_registry import _wrap_apply_table_state
    return await _wrap_apply_table_state(**kwargs)


def _patch(result):
    """Extract the patch dict from a successful apply_table_state result."""
    return result["data"]["ui_action_params"]["patch"]


# ===========================================================================
# talent_pool surface
# ===========================================================================

class TestTalentPoolSurface:

    @pytest.mark.asyncio
    async def test_pool_stage_filter_valid(self, _tenant):
        """stage='screened' -> success=True, patch={"stage": "screened"}"""
        result = await _call(surface="talent_pool", stage="screened")
        assert result["success"] is True
        assert _patch(result) == {"stage": "screened"}

    @pytest.mark.asyncio
    async def test_pool_stage_all_becomes_null(self, _tenant):
        """stage='all' -> success=True, patch={"stage": None}"""
        result = await _call(surface="talent_pool", stage="all")
        assert result["success"] is True
        assert _patch(result)["stage"] is None

    @pytest.mark.asyncio
    async def test_pool_stage_invalid_rejected(self, _tenant):
        """stage='invalid_stage' -> success=False, 'invalida' in message"""
        result = await _call(surface="talent_pool", stage="invalid_stage")
        assert result["success"] is False
        assert "invalida" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_pool_tab_switch_valid(self, _tenant):
        """pool_tab='sourcing' -> success=True, patch={"tab": "sourcing"}"""
        result = await _call(surface="talent_pool", pool_tab="sourcing")
        assert result["success"] is True
        assert _patch(result) == {"tab": "sourcing"}

    @pytest.mark.asyncio
    async def test_pool_tab_invalid_rejected(self, _tenant):
        """pool_tab='nonexistent' -> success=False, 'invalida' in message"""
        result = await _call(surface="talent_pool", pool_tab="nonexistent")
        assert result["success"] is False
        assert "invalida" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_pool_empty_patch_rejected(self, _tenant):
        """No stage, no pool_tab -> success=False (nothing to apply)"""
        result = await _call(surface="talent_pool")
        assert result["success"] is False


# ===========================================================================
# recrutar surface
# ===========================================================================

class TestRecrutarSurface:

    @pytest.mark.asyncio
    async def test_recrutar_stage_select(self, _tenant):
        """stage='triagem_whatsapp' -> success=True, patch={"stage": "triagem_whatsapp"}"""
        result = await _call(surface="recrutar", stage="triagem_whatsapp")
        assert result["success"] is True
        assert _patch(result) == {"stage": "triagem_whatsapp"}

    @pytest.mark.asyncio
    async def test_recrutar_stage_deselect(self, _tenant):
        """stage=None explicitly -> success=True, patch={"stage": None}"""
        result = await _call(surface="recrutar", stage=None)
        assert result["success"] is True
        assert _patch(result)["stage"] is None

    @pytest.mark.asyncio
    async def test_recrutar_no_args_rejected(self, _tenant):
        """No stage kwarg at all -> success=False (no fields to apply)"""
        result = await _call(surface="recrutar")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_recrutar_stage_too_long_rejected(self, _tenant):
        """stage='x'*200 -> success=False (string too long)"""
        result = await _call(surface="recrutar", stage="x" * 200)
        assert result["success"] is False
